import os
import json
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static Fallback Data (shown only when live pipeline returns < 3 items)
# Each entry is flagged is_fallback=True so the frontend can style differently.
# ---------------------------------------------------------------------------

_FALLBACK_BARRIERS = [
    {"theme": "Repetitive Recommendations", "frequency": 0.28, "count": 28, "average_rating": 2.4, "evidence": [], "is_fallback": True},
    {"theme": "Lack of Mood/Context Filters",  "frequency": 0.18, "count": 18, "average_rating": 2.8, "evidence": [], "is_fallback": True},
    {"theme": "Poor Search Precision",       "frequency": 0.12, "count": 12, "average_rating": 3.0, "evidence": [], "is_fallback": True},
]

_FALLBACK_FRUSTRATIONS = [
    {"theme": "Over-Personalization",      "frequency": 0.22, "count": 22, "average_rating": 2.6, "evidence": [], "is_fallback": True},
    {"theme": "Popularity Bias",           "frequency": 0.18, "count": 18, "average_rating": 2.8, "evidence": [], "is_fallback": True},
    {"theme": "Stale Algorithmic Mixes",   "frequency": 0.14, "count": 14, "average_rating": 2.9, "evidence": [], "is_fallback": True},
]

_FALLBACK_LISTENING_GOALS = [
    {"theme": "Discovering Hidden Gems",    "frequency": 0.30, "count": 30, "average_rating": 3.8, "evidence": [], "is_fallback": True},
    {"theme": "Mood/Activity-Based Listening",       "frequency": 0.25, "count": 25, "average_rating": 4.0, "evidence": [], "is_fallback": True},
    {"theme": "Relying on Familiar Playlists",  "frequency": 0.20, "count": 20, "average_rating": 4.2, "evidence": [], "is_fallback": True},
]

_FALLBACK_REPEAT_DRIVERS = [
    {"theme": "Comfort Listening",              "frequency": 0.26, "count": 26, "average_rating": 3.5, "evidence": [], "is_fallback": True},
    {"theme": "Playlist Dependence",            "frequency": 0.20, "count": 20, "average_rating": 3.3, "evidence": [], "is_fallback": True},
    {"theme": "Lack of Trust in Recommendations", "frequency": 0.15, "count": 15, "average_rating": 2.7, "evidence": [], "is_fallback": True},
]

_FALLBACK_SEGMENTS = [
    {
        "segment": "Mood-Based Explorers", "frequency": 0.35, "count": 35, "average_rating": 2.5,
        "severity_score": 0.94, "severity_rank": 1, "evidence": [], "is_fallback": True,
        "discovery_challenges": [
            {"pain_point": "Repetitive Recommendations", "count": 15, "frequency_within_segment": 0.43},
            {"pain_point": "Lack of Mood/Context Filters",  "count": 8,  "frequency_within_segment": 0.23},
            {"pain_point": "Poor Search Precision",       "count": 5,  "frequency_within_segment": 0.14},
        ],
    },
    {
        "segment": "Playlist Dependents", "frequency": 0.30, "count": 30, "average_rating": 3.2,
        "severity_score": 0.54, "severity_rank": 2, "evidence": [], "is_fallback": True,
        "discovery_challenges": [
            {"pain_point": "Excessive Ad Interruptions",  "count": 10, "frequency_within_segment": 0.33},
            {"pain_point": "Repetitive Recommendations",  "count": 6,  "frequency_within_segment": 0.20},
            {"pain_point": "Complex UI Navigation",       "count": 4,  "frequency_within_segment": 0.13},
        ],
    },
    {
        "segment": "New Music Seekers", "frequency": 0.15, "count": 15, "average_rating": 2.8,
        "severity_score": 0.44, "severity_rank": 3, "evidence": [], "is_fallback": True,
        "discovery_challenges": [
            {"pain_point": "Lack of Mood/Context Filters",  "count": 6, "frequency_within_segment": 0.40},
            {"pain_point": "Complex UI Navigation",      "count": 4, "frequency_within_segment": 0.27},
            {"pain_point": "Poor Search Precision",      "count": 3, "frequency_within_segment": 0.20},
        ],
    },
    {
        "segment": "Passive Listener", "frequency": 0.10, "count": 10, "average_rating": 3.5,
        "severity_score": 0.30, "severity_rank": 4, "evidence": [], "is_fallback": True,
        "discovery_challenges": [
            {"pain_point": "Excessive Ad Interruptions", "count": 4, "frequency_within_segment": 0.40},
            {"pain_point": "Repetitive Recommendations", "count": 3, "frequency_within_segment": 0.30},
            {"pain_point": "Complex UI Navigation", "count": 1, "frequency_within_segment": 0.10},
        ],
    },
    {
        "segment": "Genre Hoppers", "frequency": 0.12, "count": 12, "average_rating": 3.0,
        "severity_score": 0.40, "severity_rank": 5, "evidence": [], "is_fallback": True,
        "discovery_challenges": [
            {"pain_point": "Poor Search Precision", "count": 5, "frequency_within_segment": 0.42},
            {"pain_point": "Complex UI Navigation", "count": 3, "frequency_within_segment": 0.25},
            {"pain_point": "Lack of Mood/Context Filters", "count": 2, "frequency_within_segment": 0.17},
        ],
    },
]

_FALLBACK_UNMET_NEEDS = [
    {"theme": "Context-Aware Recommendations", "frequency": 0.24, "count": 24, "average_rating": 2.3, "opportunity_score": 0.886, "evidence": [], "is_fallback": True},
    {"theme": "Conversational AI Discovery",   "frequency": 0.18, "count": 18, "average_rating": 2.5, "opportunity_score": 0.630, "evidence": [], "is_fallback": True},
    {"theme": "Cross-Genre Discovery Mode",  "frequency": 0.14, "count": 14, "average_rating": 2.8, "opportunity_score": 0.448, "evidence": [], "is_fallback": True},
]


def _fill_to_three(live_list: list, fallbacks: list, key: str = "theme") -> list:
    """
    Returns up to 3 items, prioritizing live_list entries.
    Appends fallback entries only if live_list has fewer than 3 AND
    the fallback's theme/segment label is not already present in the live list
    (prevents duplicates when live data already contains a theme that
    coincides with a fallback label).

    Args:
        live_list: Items from the live pipeline (always placed first).
        fallbacks: Static fallback entries to pad with.
        key: The field name to deduplicate on ("theme" or "segment").
    """
    result = list(live_list)  # live data always first
    live_labels = {item.get(key, "") for item in result}
    needed = 3 - len(result)
    for fb in fallbacks:
        if needed <= 0:
            break
        if fb.get(key, "") not in live_labels:  # skip if label already present
            result.append(fb)
            live_labels.add(fb.get(key, ""))
            needed -= 1
            logger.debug(f"Padded fallback '{fb.get(key)}' (live count was short).")
    return result


def pad_analysis_results(analysis_results: dict) -> dict:
    """
    Returns a *new* dict where each of the 6 question lists is padded to
    exactly 3 items using static fallbacks (deduplicated by theme/segment label).
    Live data always comes first and is never replaced.
    This function must be called BEFORE passing analysis_results to both
    pulse_generator.build_report_draft() and json_exporter.export_dashboard_json()
    so that the pulse note and the dashboard JSON stay in sync.
    """
    padded = dict(analysis_results)  # shallow copy — we only replace the list values

    raw_q1 = [dict(b, is_fallback=False) for b in analysis_results.get("question_1", [])]
    raw_q2 = [dict(f, is_fallback=False) for f in analysis_results.get("question_2", [])]
    raw_q3 = [dict(g, is_fallback=False) for g in analysis_results.get("question_3", [])]
    raw_q4 = [dict(d, is_fallback=False) for d in analysis_results.get("question_4", [])]
    raw_q5 = []
    live_q5 = analysis_results.get("question_5", [])
    for s in live_q5:
        s_copy = dict(s, is_fallback=False)
        seg_name = s_copy.get("segment", "")
        # Get live challenges
        live_challenges = list(s_copy.get("discovery_challenges", []))
        
        # Check if we should fall back completely (metrics + challenges) to ensure
        # metric consistency when running under fallback/rate-limited runs.
        # This is triggered if there are no live challenges AND there is at most 1 live segment.
        if len(live_challenges) == 0 and len(live_q5) <= 1:
            fallback_matches = [fb for fb in _FALLBACK_SEGMENTS if fb["segment"] == seg_name]
            if fallback_matches:
                s_copy = dict(fallback_matches[0], is_fallback=True)
                raw_q5.append(s_copy)
                continue

        # Find corresponding fallback segment to get its challenges
        fallback_matches = [fb for fb in _FALLBACK_SEGMENTS if fb["segment"] == seg_name]
        fallback_challenges = fallback_matches[0]["discovery_challenges"] if fallback_matches else []
        # Pad challenges list to exactly 3
        padded_challenges = list(live_challenges)
        existing_points = {c["pain_point"] for c in padded_challenges}
        needed = 3 - len(padded_challenges)
        for fc in fallback_challenges:
            if needed <= 0:
                break
            if fc["pain_point"] not in existing_points:
                padded_challenges.append(fc)
                existing_points.add(fc["pain_point"])
                needed -= 1
        s_copy["discovery_challenges"] = padded_challenges
        raw_q5.append(s_copy)
    raw_q6 = [dict(n, is_fallback=False) for n in analysis_results.get("question_6", [])]

    padded["question_1"] = _fill_to_three(raw_q1, _FALLBACK_BARRIERS,       key="theme")
    padded["question_2"] = _fill_to_three(raw_q2, _FALLBACK_FRUSTRATIONS,   key="theme")
    padded["question_3"] = _fill_to_three(raw_q3, _FALLBACK_LISTENING_GOALS, key="theme")
    padded["question_4"] = _fill_to_three(raw_q4, _FALLBACK_REPEAT_DRIVERS,  key="theme")
    padded_q5 = _fill_to_three(raw_q5, _FALLBACK_SEGMENTS,        key="segment")
    # Sort descending by severity score so that segments are ordered correctly
    padded_q5.sort(key=lambda x: x.get("severity_score", 0.0), reverse=True)
    # Recompute severity rank based on the final sorted list
    for rank, item in enumerate(padded_q5):
        item["severity_rank"] = rank + 1
    padded["question_5"] = padded_q5

    padded["question_6"] = _fill_to_three(raw_q6, _FALLBACK_UNMET_NEEDS,     key="theme")

    return padded


class JSONExporter:
    """Formats and exports executive report and metrics into dashboard_data.json."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def export_dashboard_json(self, analysis_results: dict, opportunities: List[dict], pulse_note_text: str, output_path: str = None) -> dict:
        """Assembles dashboard JSON schema and writes it to disk.

        Live pipeline data always takes priority.
        If any section has fewer than 3 items, static fallback entries
        (flagged with is_fallback=True) are appended so the frontend
        always has exactly 3 items to render per section.
        """

        # Calculate dynamic week_ending date
        week_ending_str = datetime.now().strftime("%Y-%m-%d")

        # --- Map top barriers (Q1) — input already padded by pad_analysis_results() ---
        top_barriers = []
        for b in analysis_results.get("question_1", []):
            top_barriers.append({
                "theme": str(b.get("theme", "")),
                "frequency": float(b.get("frequency", 0.0)),
                "count": int(b.get("count", 0)),
                "average_rating": float(b.get("average_rating", 0.0)),
                "evidence": list(b.get("evidence", [])),
                "is_fallback": bool(b.get("is_fallback", False)),
            })

        # --- Map frustrations (Q2) ---
        top_frustrations = []
        for f in analysis_results.get("question_2", []):
            top_frustrations.append({
                "theme": str(f.get("theme", "")),
                "frequency": float(f.get("frequency", 0.0)),
                "count": int(f.get("count", 0)),
                "average_rating": float(f.get("average_rating", 0.0)),
                "evidence": list(f.get("evidence", [])),
                "is_fallback": bool(f.get("is_fallback", False)),
            })

        # --- Map listening goals (Q3) ---
        listening_goals = []
        for g in analysis_results.get("question_3", []):
            listening_goals.append({
                "theme": str(g.get("theme", "")),
                "frequency": float(g.get("frequency", 0.0)),
                "count": int(g.get("count", 0)),
                "average_rating": float(g.get("average_rating", 0.0)),
                "evidence": list(g.get("evidence", [])),
                "is_fallback": bool(g.get("is_fallback", False)),
            })

        # --- Map repeat drivers (Q4) ---
        repeat_drivers = []
        for d in analysis_results.get("question_4", []):
            repeat_drivers.append({
                "theme": str(d.get("theme", "")),
                "frequency": float(d.get("frequency", 0.0)),
                "count": int(d.get("count", 0)),
                "average_rating": float(d.get("average_rating", 0.0)),
                "evidence": list(d.get("evidence", [])),
                "is_fallback": bool(d.get("is_fallback", False)),
            })

        # --- Map underserved segments (Q5) ---
        underserved_segments = []
        for s in analysis_results.get("question_5", []):
            underserved_segments.append({
                "segment": str(s.get("segment", "")),
                "frequency": float(s.get("frequency", 0.0)),
                "count": int(s.get("count", 0)),
                "average_rating": float(s.get("average_rating", 0.0)),
                "severity_score": float(s.get("severity_score", 0.0)),
                "severity_rank": int(s.get("severity_rank", 0)),
                "evidence": list(s.get("evidence", [])),
                "is_fallback": bool(s.get("is_fallback", False)),
                "discovery_challenges": list(s.get("discovery_challenges", [])),
            })

        # --- Map unmet needs (Q6) ---
        unmet_needs = []
        for n in analysis_results.get("question_6", []):
            unmet_needs.append({
                "theme": str(n.get("theme", "")),
                "frequency": float(n.get("frequency", 0.0)),
                "count": int(n.get("count", 0)),
                "average_rating": float(n.get("average_rating", 0.0)),
                "opportunity_score": float(n.get("opportunity_score", 0.0)),
                "evidence": list(n.get("evidence", [])),
                "is_fallback": bool(n.get("is_fallback", False)),
            })

        # --- Map opportunities (LLM-generated, no fallback needed) ---
        mapped_opportunities = []
        for op in opportunities[:3]:
            mapped_opportunities.append({
                "problem": str(op.get("problem", "")),
                "evidence": str(op.get("evidence", "")),
                "suggested_ai_solution": str(op.get("suggested_ai_solution", "")),
                "expected_impact": str(op.get("expected_impact", ""))
            })

        # Fallback default for sentiment_distribution
        fallback_sentiment = {
            "positive": 15,
            "neutral": 65,
            "negative": 20,
            "total": 100
        }
        sentiment_dist = analysis_results.get("sentiment_distribution", fallback_sentiment)
        if not isinstance(sentiment_dist, dict) or not all(k in sentiment_dist for k in ["positive", "neutral", "negative", "total"]):
            sentiment_dist = fallback_sentiment

        dashboard_data = {
            "week_ending": week_ending_str,
            "pulse_note_text": pulse_note_text,
            "sentiment_distribution": sentiment_dist,
            "metrics": {
                "top_barriers": top_barriers,
                "top_frustrations": top_frustrations,
                "listening_goals": listening_goals,
                "repeat_drivers": repeat_drivers,
                "underserved_segments": underserved_segments,
                "unmet_needs": unmet_needs,
                "opportunities": mapped_opportunities
            }
        }

        if output_path:
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Dashboard data exported successfully to: {output_path}")

            # Also sync to frontend/public/dashboard_data.json if we are in local dev
            try:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                frontend_public_dir = os.path.join(project_root, "frontend", "public")
                if os.path.exists(frontend_public_dir):
                    frontend_public_path = os.path.join(frontend_public_dir, "dashboard_data.json")
                    with open(frontend_public_path, "w", encoding="utf-8") as f:
                        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Synchronized dashboard data to: {frontend_public_path}")
            except Exception as e:
                logger.warning(f"Could not synchronize dashboard data to frontend: {e}")

        return dashboard_data
