# Verification script for Phase 2: Theme Extraction & Metric Parsing (LLM-Powered)
import os
import sys
import pandas as pd

# Add project root to python path to resolve src imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.processing.llm_client import GroqClient
from src.processing.review_processor import ReviewProcessor

def main():
    # Configure stdout to handle utf-8 encoding correctly on Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=" * 60)
    print("RUNNING PHASE 2 VERIFICATION: Theme Extraction & Metric Parsing")
    print("=" * 60)

    # 1. Check if processed reviews from Phase 1 exist
    processed_path = "data/processed/reviews.csv"
    if not os.path.exists(processed_path):
        print(f"[ERROR] Processed reviews CSV not found at '{processed_path}'.")
        print("Please run Phase 1 first via: python src/script/run_phase1.py")
        sys.exit(1)

    print(f"[OK] Found processed reviews file at: {processed_path}")

    # 2. Read processed reviews dataset
    try:
        df = pd.read_csv(processed_path)
        print(f"[OK] Processed reviews loaded successfully. Total records: {len(df)}")
    except Exception as e:
        print(f"[ERROR] Failed to load processed reviews CSV: {e}")
        sys.exit(1)

    if df.empty:
        print("[ERROR] processed/reviews.csv is empty. Cannot perform LLM analysis.")
        sys.exit(1)

    # 3. Initialize GroqClient and ReviewProcessor
    try:
        print("[ ] Initializing Groq client...")
        client = GroqClient()
        processor = ReviewProcessor(client)
        print("[OK] Groq client and ReviewProcessor initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        print("Please verify that GROQ_API_KEY is defined in your .env file.")
        sys.exit(1)

    # 4. Run annotation (check optimization settings first)
    opt_config = client.config.get("optimization", {})
    opt_enabled = opt_config.get("enabled", False)

    if opt_enabled:
        sampling_cfg = opt_config.get("sampling", {})
        sample_size = sampling_cfg.get("sample_size", 500)
        min_floor_sources = sampling_cfg.get("min_floor_sources", ["reddit", "product_reviews", "spotify_community", "twitter"])
        
        gate_cfg = opt_config.get("gate", {})
        gate_enabled = gate_cfg.get("enabled", True)
        gate_batch_size = gate_cfg.get("batch_size", 10)
        gate_model = gate_cfg.get("model", "llama-3.1-8b-instant")
        
        print(f"\n[ ] Running OPTIMIZED pipeline (Strategy 4 + 5)...")
        print(f"    - Target Sample Size: {sample_size}")
        print(f"    - Min-floor sources: {min_floor_sources}")
        print(f"    - Gate enabled: {gate_enabled}")
        if gate_enabled:
            print(f"    - Gate model: {gate_model}")
            print(f"    - Gate batch size: {gate_batch_size}")
            
        try:
            annotated_df, coverage = processor.process_reviews_optimized(
                df,
                sample_size=sample_size,
                min_floor_sources=min_floor_sources,
                gate_enabled=gate_enabled,
                gate_batch_size=gate_batch_size,
                gate_model=gate_model
            )
            print(f"[OK] LLM Annotation batch run: SUCCESS (Annotated {len(annotated_df)} reviews)")
            
            # Print coverage/optimization stats
            print("\n" + "=" * 60)
            print("LLM OPTIMIZATION STATS:")
            print("-" * 60)
            print(f"Total reviews in system      : {coverage.get('total_reviews')}")
            print(f"Sampled reviews (S4)         : {coverage.get('sampled_count')} ({coverage.get('coverage_pct')}% coverage)")
            if gate_enabled:
                print(f"Gate passed (S5 - full LLM)  : {coverage.get('gate_passed')}")
                print(f"Gate rejected (auto-labeled) : {coverage.get('gate_rejected')}")
            print(f"LLM calls made               : {coverage.get('llm_calls_made')}")
            print(f"LLM calls saved vs full run  : {coverage.get('llm_calls_saved_vs_full')}")
            print("=" * 60)
        except Exception as e:
            print(f"[ERROR] LLM Annotation failed: {e}")
            sys.exit(1)
    else:
        sample_size = min(300, len(df))
        print(f"\n[ ] Processing batch of {sample_size} reviews through LLM (non-optimized, rate-limit safe)...")
        try:
            annotated_df = processor.process_reviews(df, num_records=sample_size)
            print(f"[OK] LLM Annotation batch run: SUCCESS (Annotated {len(annotated_df)} reviews)")
        except Exception as e:
            print(f"[ERROR] LLM Annotation failed: {e}")
            sys.exit(1)

    # 5. Output Verification
    annotated_path = "data/processed/annotated_reviews.json"
    if not os.path.exists(annotated_path):
        print(f"[ERROR] Annotated JSON check: FAILED - file missing at {annotated_path}")
        sys.exit(1)

    print(f"[OK] Output file created successfully at: {annotated_path}")

    # 6. Verify required columns
    required_cols = {
        "source", "date", "title", "text", "rating", "engagement",
        "sentiment", "discovery_pain_points", "recommendation_frustrations",
        "listening_goals_intentions", "repeat_listening_signals", "unmet_needs",
        "segment_classification"
    }
    cols = set(annotated_df.columns)
    if not required_cols.issubset(cols):
        print(f"[ERROR] Schema check: FAILED - expected columns {required_cols}, got {cols}")
        sys.exit(1)

    print("[OK] Schema check: SUCCESS (all 13 metrics/original columns are present)")

    # 7. Print Sample Results (first 3 only)
    print("\n" + "-" * 60)
    print("SAMPLE ANNOTATED REVIEWS RESULT (first 3):")
    print("-" * 60)
    
    for idx, row in annotated_df.head(3).iterrows():
        print(f"\nReview {idx + 1} | Source: {row['source']} | Rating: {row['rating']}")
        print(f"Text       : {row['text']}")
        print(f"Sentiment  : {row['sentiment']}")
        print(f"Segment    : {row['segment_classification']}")
        print(f"Pain Points: {row['discovery_pain_points']}")
        print(f"Frustrations: {row['recommendation_frustrations']}")
        print(f"Goals      : {row['listening_goals_intentions']}")
        print(f"Repeat     : {row['repeat_listening_signals']}")
        print(f"Unmet Needs: {row['unmet_needs']}")
        print("-" * 40)

    print("\n[OK] PHASE 2 VERIFICATION COMPLETED: ALL PIPELINE STAGES VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
