# Verification script for Phase 3: Analytical Theme Discovery & Cluster Analysis
import os
import sys
import json

# Add project root to python path to resolve src imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.processing.llm_client import GroqClient
from src.analysis.theme_discoverer import ThemeDiscoverer

def main():
    # Configure stdout to handle utf-8 encoding correctly on Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=" * 60)
    print("RUNNING PHASE 3 VERIFICATION: Theme Discovery & Clustering")
    print("=" * 60)

    # 1. Check if annotated reviews from Phase 2 exist
    annotated_path = "data/processed/annotated_reviews.json"
    if not os.path.exists(annotated_path):
        print(f"[ERROR] Annotated reviews JSON not found at '{annotated_path}'.")
        print("Please run Phase 2 verification first via: python src/script/run_phase2.py")
        sys.exit(1)

    print(f"[OK] Found annotated reviews file at: {annotated_path}")

    # 2. Initialize GroqClient and ThemeDiscoverer
    try:
        print("[ ] Initializing Groq client...")
        client = GroqClient()
        discoverer = ThemeDiscoverer(client)
        print("[OK] Groq client and ThemeDiscoverer initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        print("Please verify that GROQ_API_KEY is defined in your .env file.")
        sys.exit(1)

    # 3. Perform Theme Discovery
    output_path = "data/processed/analysis_results.json"
    print(f"\n[ ] Running theme discovery and cluster analysis pipeline...")
    try:
        results = discoverer.perform_full_analysis(annotated_path, output_path)
        print("[OK] Theme discovery and clustering analysis: SUCCESS")
    except Exception as e:
        print(f"[ERROR] Theme discovery pipeline failed: {e}")
        sys.exit(1)

    # 4. Output Verification
    if not os.path.exists(output_path):
        print(f"[ERROR] Analysis output check: FAILED - file missing at {output_path}")
        sys.exit(1)

    print(f"[OK] Output file created successfully at: {output_path}")

    # 5. Schema verification
    required_keys = {"question_1", "question_2", "question_3", "question_4", "question_5", "question_6"}
    keys = set(results.keys())
    if not required_keys.issubset(keys):
        print(f"[ERROR] Schema check: FAILED - expected keys {required_keys}, got {keys}")
        sys.exit(1)

    print("[OK] Schema check: SUCCESS (All 6 core business questions are mapped)")

    # 6. Sample output print
    print("\n" + "-" * 60)
    print("SAMPLE ANALYSIS RESULTS:")
    print("-" * 60)

    # Q1 print
    print("\nQUESTION 1: Discovery Barriers")
    for item in results["question_1"][:2]:
        print(f"  Theme       : {item['theme']}")
        print(f"  Count/Freq  : {item['count']} ({round(item['frequency'] * 100, 1)}%)")
        print(f"  Avg Rating  : {item['average_rating']}")
        print(f"  Root Cause  : {item['root_cause']}")
        print(f"  Quote (Ex)  : \"{item['evidence'][0] if item['evidence'] else 'N/A'}\"")
        print("  " + "-" * 30)

    # Q3 print
    print("\nQUESTION 3: Listening Behaviors & JTBD")
    for item in results["question_3"][:2]:
        print(f"  Theme       : {item['theme']}")
        print(f"  Count/Freq  : {item['count']} ({round(item['frequency'] * 100, 1)}%)")
        print(f"  JTBD        : {item['jtbd']}")
        print("  " + "-" * 30)

    # Q5 print
    print("\nQUESTION 5: User Segment Profiles (Top Severities)")
    for item in results["question_5"][:2]:
        print(f"  Segment     : {item['segment']}")
        print(f"  Count/Freq  : {item['count']} ({round(item['frequency'] * 100, 1)}%)")
        print(f"  Avg Rating  : {item['average_rating']}")
        print(f"  Severity Rank: {item['severity_rank']} (Score: {item['severity_score']})")
        print(f"  Challenges  : {item['discovery_challenges'][:2]}")
        print("  " + "-" * 30)

    # Q6 print
    print("\nQUESTION 6: Unmet Needs & Opportunity Scores")
    for item in results["question_6"][:2]:
        print(f"  Need        : {item['need']}")
        print(f"  Count/Freq  : {item['count']} ({round(item['frequency'] * 100, 1)}%)")
        print(f"  Avg Rating  : {item['average_rating']}")
        print(f"  Opportunity : {item['opportunity_score']}")
        print("  " + "-" * 30)

    print("\n[OK] PHASE 3 VERIFICATION COMPLETED: ALL PIPELINE STAGES VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
