# Verification script for Phase 4: Pulse Note Generation & JSON Export
import os
import sys
import json
import yaml

# Add project root to python path to resolve src imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.processing.llm_client import GroqClient
from src.reporting.pulse_generator import PulseGenerator
from src.reporting.json_exporter import JSONExporter

def main():
    # Configure stdout to handle utf-8 encoding correctly on Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=" * 60)
    print("RUNNING PHASE 4 VERIFICATION: Pulse Note & JSON Export")
    print("=" * 60)

    # Load paths from config.yaml
    config_path = "config.yaml"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    paths_cfg = config.get("paths", {})
    processed_dir = paths_cfg.get("processed_data_dir", "data/processed")
    pulse_note_file = paths_cfg.get("pulse_note_file", "data/weekly_pulse_note.md")
    dashboard_json_file = paths_cfg.get("dashboard_json_file", "data/dashboard_data.json")

    # 1. Check if analysis results from Phase 3 exist
    analysis_path = os.path.join(processed_dir, "analysis_results.json")
    if not os.path.exists(analysis_path):
        print(f"[ERROR] Analysis results JSON not found at '{analysis_path}'.")
        print("Please run Phase 3 verification first via: python src/script/run_phase3.py")
        sys.exit(1)

    print(f"[OK] Found analysis results file at: {analysis_path}")

    # 2. Load analysis results dataset
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis_results = json.load(f)

    # 3. Initialize GroqClient, PulseGenerator, and JSONExporter
    try:
        print("[ ] Initializing Groq client and reporting engines...")
        client = GroqClient()
        generator = PulseGenerator(client)
        exporter = JSONExporter(config)
        print("[OK] Reporting engines initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        print("Please verify that GROQ_API_KEY is defined in your .env file.")
        sys.exit(1)

    # 4. Generate Pulse Note (weekly_pulse_note.md)
    print(f"\n[ ] Compiling weekly pulse note...")
    try:
        pulse_note_text = generator.generate_and_save_report(analysis_results, pulse_note_file)
        print(f"[OK] Pulse note generated and saved to: {pulse_note_file}")
    except Exception as e:
        print(f"[ERROR] Pulse note generation failed: {e}")
        sys.exit(1)

    # 5. Extract Opportunities & Export Dashboard JSON (dashboard_data.json)
    print(f"[ ] Generating dashboard JSON export...")
    try:
        # Re-fetch or generate opportunities to ensure schema completeness
        opps = generator.generate_opportunities_via_llm(analysis_results)
        dashboard_data = exporter.export_dashboard_json(analysis_results, opps, pulse_note_text, dashboard_json_file)
        print(f"[OK] Dashboard data exported successfully to: {dashboard_json_file}")
    except Exception as e:
        print(f"[ERROR] Dashboard JSON export failed: {e}")
        sys.exit(1)

    # 6. Verification Checks
    # Word Count Check
    word_count = generator.count_words(pulse_note_text)
    if word_count > 550:
        print(f"[ERROR] Word Count Limit check: FAILED (Note is {word_count} words; limit is 550)")
        sys.exit(1)
    print(f"[OK] Word Count Limit check: SUCCESS (Note is {word_count} words <= 550)")

    # JSON Schema Verification
    required_keys = {"week_ending", "pulse_note_text", "metrics"}
    if not required_keys.issubset(dashboard_data.keys()):
        print(f"[ERROR] JSON Schema check: FAILED (missing keys)")
        sys.exit(1)

    required_metrics_keys = {
        "top_barriers", "top_frustrations", "listening_goals", 
        "repeat_drivers", "underserved_segments", "unmet_needs", "opportunities"
    }
    metrics_keys = set(dashboard_data["metrics"].keys())
    if not required_metrics_keys.issubset(metrics_keys):
        print(f"[ERROR] JSON metrics keys check: FAILED (missing keys: {required_metrics_keys - metrics_keys})")
        sys.exit(1)

    print("[OK] JSON Dashboard Schema check: SUCCESS")

    # 7. Print Output Pulse Note Markdown Text
    print("\n" + "=" * 60)
    print("GENERATED WEEKLY PULSE NOTE:")
    print("=" * 60)
    print(pulse_note_text)
    print("=" * 60)
    print("\n[OK] PHASE 4 VERIFICATION COMPLETED: ALL PIPELINE STAGES VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
