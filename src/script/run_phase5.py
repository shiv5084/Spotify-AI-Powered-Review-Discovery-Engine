# Verification script for Phase 5: E2E Pipeline Orchestration & Execution
import os
import sys
import json
import subprocess
import yaml

# Add project root to python path to resolve src imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def main():
    # Configure stdout to handle utf-8 encoding correctly on Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=" * 60)
    print("RUNNING PHASE 5 VERIFICATION: E2E Pipeline Orchestration")
    print("=" * 60)

    # 1. Read config to locate expected output locations
    config_path = "config.yaml"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    paths_cfg = config.get("paths", {})
    pulse_note_file = paths_cfg.get("pulse_note_file", "data/weekly_pulse_note.md")
    dashboard_json_file = paths_cfg.get("dashboard_json_file", "data/dashboard_data.json")

    # Clean existing generated outputs to ensure we test fresh generation
    for fpath in [pulse_note_file, dashboard_json_file]:
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                print(f"[ ] Removed old output file: {fpath}")
            except Exception as e:
                print(f"[WARNING] Could not remove old output file {fpath}: {e}")

    # 2. Trigger orchestration script E2E via subprocess
    # We use a small limit of 5 records to make it run extremely fast and avoid rate limits.
    python_exec = sys.executable or "./venv/Scripts/python"
    cmd = [python_exec, "src/main.py", "--num-records", "5"]
    print(f"\n[ ] Executing E2E pipeline command: {' '.join(cmd)}")
    
    try:
        # Run subprocess with timeout (e.g. 120s for scraping + fallback processing)
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
            encoding="utf-8"
        )
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"[ERROR] Pipeline subprocess failed with exit code: {result.returncode}")
            print(result.stderr)
            sys.exit(1)
            
        print("[OK] Pipeline orchestrator executed successfully (Exit Code 0).")
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Pipeline execution timed out after 180 seconds.")
        sys.exit(1)
    except Exception as err:
        print(f"[ERROR] Subprocess launch failed: {err}")
        sys.exit(1)

    # 3. Output Existence Verification
    if not os.path.exists(pulse_note_file):
        print(f"[ERROR] Verification failed: pulse note file missing at {pulse_note_file}")
        sys.exit(1)
    print(f"[OK] Found compiled weekly pulse note at: {pulse_note_file}")

    if not os.path.exists(dashboard_json_file):
        print(f"[ERROR] Verification failed: dashboard json missing at {dashboard_json_file}")
        sys.exit(1)
    print(f"[OK] Found dashboard data JSON export at: {dashboard_json_file}")

    # 4. Content & Constraints Verification
    # Word Count check
    with open(pulse_note_file, "r", encoding="utf-8") as f:
        pulse_text = f.read()

    # Word Count check — count words directly to avoid instantiating PulseGenerator with None
    word_count = len(pulse_text.split())
    if word_count > 550:
        print(f"[ERROR] Pulse note word count check: FAILED ({word_count} words; limit is 550)")
        sys.exit(1)
    print(f"[OK] Pulse note word count check: SUCCESS ({word_count} words <= 550)")

    # Top 3 Headings check — all 7 sections required by problemStatement.md
    expected_headings = [
        "### 1. Top 3 Discovery Barriers",
        "### 2. Top 3 Recommendation Frustrations",
        "### 3. Top 3 Listening Goals",
        "### 4. Top 3 Repeat-Listening Drivers",
        "### 5. Top 3 Underserved User Segments",
        "### 6. Top 3 Unmet Needs",
        "### 7. Top 3 Product Opportunities",
    ]
    missing_headings = [h for h in expected_headings if h not in pulse_text]
    if missing_headings:
        print(f"[ERROR] Heading check: FAILED — {len(missing_headings)} heading(s) missing:")
        for h in missing_headings:
            print(f"        MISSING: {h}")
        print("\n--- Actual headings found in pulse note ---")
        for line in pulse_text.splitlines():
            if line.startswith("###"):
                print(f"        FOUND:   {line}")
        sys.exit(1)
    print(f"[OK] Heading structures: SUCCESS — all {len(expected_headings)}/7 Top 3 headings present")

    # JSON schema check
    try:
        with open(dashboard_json_file, "r", encoding="utf-8") as f:
            dashboard_data = json.load(f)
            
        required_keys = {"week_ending", "pulse_note_text", "metrics"}
        if not required_keys.issubset(dashboard_data.keys()):
            print("[ERROR] JSON Schema check: FAILED (missing keys)")
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
        
    except Exception as parse_err:
        print(f"[ERROR] JSON loading/parsing failed: {parse_err}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[OK] PHASE 5 VERIFICATION COMPLETED: PIPELINE FULLY INTEGRATED & VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
