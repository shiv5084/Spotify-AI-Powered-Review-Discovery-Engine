import os
import json
import logging
from collections import Counter
from typing import List, Dict, Any
from src.processing.llm_client import GroqClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Predefined Theme Registries
# ---------------------------------------------------------------------------

Q1_THEMES = [
    "Repetitive Recommendations",
    "Complex UI Navigation",
    "Lack of Mood/Context Filters",
    "Excessive Ad Interruptions",
    "Poor Search Precision",
]

Q2_THEMES = [
    "Popularity Bias",
    "Limited Genre Diversity",
    "Over-Personalization",
    "Podcast/Audiobook Clutter",
    "Stale Algorithmic Mixes",
]

Q3_THEMES = [
    "Discovering Hidden Gems",
    "Exploring New Genres",
    "Mood/Activity-Based Listening",
    "Relying on Familiar Playlists",
    "Background/Passive Listening",
]

Q4_THEMES = [
    "Comfort Listening",
    "Playlist Dependence",
    "Lack of Trust in Recommendations",
    "Choice Fatigue",
    "Mood Mismatch",
]

Q5_PERSONAS = [
    "Mood-Based Explorers",
    "Playlist Dependents",
    "New Music Seekers",
    "Genre Hoppers",
    "Passive Listener",
]

Q6_THEMES = [
    "Conversational AI Discovery",
    "Context-Aware Recommendations",
    "True Random Shuffle",
    "Smart Playlist Refresh",
    "Cross-Genre Discovery Mode",
]


# ---------------------------------------------------------------------------
# Local Aggregation Helpers
# ---------------------------------------------------------------------------

def _aggregate_by_label(
    reviews: List[dict],
    field: str,
    valid_labels: List[str],
    total_len: int,
    sort_key: str = "count",
    extra_fields_fn=None,
) -> List[dict]:
    """
    Groups reviews by a single-value classification field, computes count,
    frequency, average_rating, and evidence quotes. Excludes 'None' values.

    Args:
        reviews: List of annotated review dicts.
        field: The field name in each review dict to group by.
        valid_labels: List of valid theme labels (excludes 'None').
        total_len: Total number of reviews in the dataset for frequency calculation.
        sort_key: Key to sort results by (default 'count').
        extra_fields_fn: Optional callable(label, matched_reviews) -> dict of extra fields.

    Returns:
        List of theme dicts sorted by sort_key descending.
    """
    # Group reviews by label
    buckets: Dict[str, List[dict]] = {label: [] for label in valid_labels}
    for r in reviews:
        label = r.get(field, "None")
        if label and label != "None" and label in buckets:
            buckets[label].append(r)

    results = []
    for label, matched in buckets.items():
        count = len(matched)
        if count == 0:
            continue

        freq = round(count / total_len, 4) if total_len > 0 else 0.0
        ratings = [r.get("rating") for r in matched if r.get("rating") is not None]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        evidence = [r.get("text", "") for r in matched[:2] if r.get("text")]

        entry = {
            "theme": label,
            "count": count,
            "frequency": freq,
            "average_rating": avg_rating,
            "evidence": evidence,
        }
        if extra_fields_fn:
            entry.update(extra_fields_fn(label, matched))

        results.append(entry)

    results.sort(key=lambda x: x[sort_key], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Theme Discoverer Class
# ---------------------------------------------------------------------------

class ThemeDiscoverer:
    """
    Phase 3: Local aggregation engine.
    Groups Phase 2 annotations by predefined Literal fields and computes
    metrics (count, frequency, average_rating) entirely in Python.
    No LLM calls are made.
    """

    def __init__(self, client: GroqClient = None):
        # client retained for API compatibility but not used in Phase 3
        self.llm_client = client

    def run_theme_discovery_q1(self, reviews: List[dict]) -> List[dict]:
        """Q1: Why do users struggle to discover new music?
        Groups by discovery_pain_points Literal field."""
        logger.info("Q1: Aggregating discovery barriers locally...")
        return _aggregate_by_label(
            reviews=reviews,
            field="discovery_pain_points",
            valid_labels=Q1_THEMES,
            total_len=len(reviews),
        )

    def run_theme_discovery_q2(self, reviews: List[dict]) -> List[dict]:
        """Q2: What are the most common frustrations with recommendations?
        Groups by recommendation_frustrations Literal field."""
        logger.info("Q2: Aggregating recommendation frustrations locally...")
        sentiment_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

        def sentiment_extra(label: str, matched: List[dict]) -> dict:
            scores = [sentiment_map.get(r.get("sentiment", "neutral"), 0.0) for r in matched]
            return {"sentiment_score": round(sum(scores) / len(scores), 2) if scores else 0.0}

        return _aggregate_by_label(
            reviews=reviews,
            field="recommendation_frustrations",
            valid_labels=Q2_THEMES,
            total_len=len(reviews),
            extra_fields_fn=sentiment_extra,
        )

    def run_theme_discovery_q3(self, reviews: List[dict]) -> List[dict]:
        """Q3: What listening behaviors are users trying to achieve?
        Groups by listening_goals_intentions Literal field."""
        logger.info("Q3: Aggregating listening goals locally...")
        return _aggregate_by_label(
            reviews=reviews,
            field="listening_goals_intentions",
            valid_labels=Q3_THEMES,
            total_len=len(reviews),
        )

    def run_theme_discovery_q4(self, reviews: List[dict]) -> List[dict]:
        """Q4: What causes users to repeatedly listen to the same content?
        Groups by repeat_listening_signals Literal field."""
        logger.info("Q4: Aggregating repeat-listening drivers locally...")
        return _aggregate_by_label(
            reviews=reviews,
            field="repeat_listening_signals",
            valid_labels=Q4_THEMES,
            total_len=len(reviews),
        )

    def run_theme_discovery_q5(self, reviews: List[dict]) -> List[dict]:
        """Q5: Which user segments experience different discovery challenges?
        Groups by segment_classification Literal field, computes severity score,
        and cross-aggregates discovery_pain_points within each segment to produce
        a ranked discovery_challenges list (top 3 by count)."""
        logger.info("Q5: Aggregating user segments and their discovery challenges locally...")
        total_len = len(reviews)
        buckets: Dict[str, List[dict]] = {p: [] for p in Q5_PERSONAS}

        for r in reviews:
            seg = r.get("segment_classification", "Passive Listener") or "Passive Listener"
            if seg in buckets:
                buckets[seg].append(r)

        segments_list = []
        for seg_name, seg_reviews in buckets.items():
            count = len(seg_reviews)
            if count == 0:
                continue

            freq = round(count / total_len, 4) if total_len > 0 else 0.0
            ratings = [r.get("rating") for r in seg_reviews if r.get("rating") is not None]
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
            evidence = [r.get("text", "") for r in seg_reviews[:2] if r.get("text")]

            neg_count = sum(1 for r in seg_reviews if r.get("rating") is not None and r.get("rating") <= 2)
            neg_pct = neg_count / count if count > 0 else 0.0
            severity_score = round((5.0 - avg_rating) * neg_pct, 2)

            # Cross-aggregate discovery_pain_points within this segment
            pain_point_counts: Counter = Counter()
            for r in seg_reviews:
                pain = r.get("discovery_pain_points", "None")
                if pain and pain != "None":
                    pain_point_counts[pain] += 1

            discovery_challenges = []
            for pain_point, pain_count in pain_point_counts.most_common(3):
                discovery_challenges.append({
                    "pain_point": pain_point,
                    "count": pain_count,
                    "frequency_within_segment": round(pain_count / count, 4),
                })

            segments_list.append({
                "segment": seg_name,
                "count": count,
                "frequency": freq,
                "average_rating": avg_rating,
                "evidence": evidence,
                "severity_score": severity_score,
                "discovery_challenges": discovery_challenges,
            })

        segments_list.sort(key=lambda x: x["severity_score"], reverse=True)
        for rank, item in enumerate(segments_list):
            item["severity_rank"] = rank + 1

        return segments_list

    def run_theme_discovery_q6(self, reviews: List[dict]) -> List[dict]:
        """Q6: What unmet needs emerge consistently across reviews?
        Groups by unmet_needs Literal field and computes Opportunity Score."""
        logger.info("Q6: Aggregating unmet needs locally...")
        total_len = len(reviews)

        def opportunity_extra(label: str, matched: List[dict]) -> dict:
            ratings = [r.get("rating") for r in matched if r.get("rating") is not None]
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
            freq = round(len(matched) / total_len, 4) if total_len > 0 else 0.0
            return {"opportunity_score": round(freq * (6.0 - avg_rating), 4)}

        results = _aggregate_by_label(
            reviews=reviews,
            field="unmet_needs",
            valid_labels=Q6_THEMES,
            total_len=total_len,
            extra_fields_fn=opportunity_extra,
        )
        # Re-sort Q6 by opportunity_score (descending)
        results.sort(key=lambda x: x.get("opportunity_score", 0.0), reverse=True)
        return results

    def compute_sentiment_distribution(self, reviews: List[dict]) -> dict:
        """Counts positive/neutral/negative sentiments across all reviews."""
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for r in reviews:
            sent = r.get("sentiment", "neutral")
            if isinstance(sent, str):
                sent = sent.lower()
            if sent in counts:
                counts[sent] += 1
            else:
                counts["neutral"] += 1

        total = len(reviews)
        return {
            "positive": counts["positive"],
            "neutral": counts["neutral"],
            "negative": counts["negative"],
            "total": total
        }

    def perform_full_analysis(self, input_json_path: str, output_json_path: str = None) -> dict:
        """Loads annotated_reviews.json, runs all 6 local aggregation pipelines, and saves results."""
        if not os.path.exists(input_json_path):
            raise FileNotFoundError(f"Annotated reviews JSON not found at: {input_json_path}")

        with open(input_json_path, "r", encoding="utf-8") as f:
            reviews = json.load(f)

        logger.info(f"Loaded {len(reviews)} annotated reviews for local aggregation...")

        q1_results = self.run_theme_discovery_q1(reviews)
        q2_results = self.run_theme_discovery_q2(reviews)
        q3_results = self.run_theme_discovery_q3(reviews)
        q4_results = self.run_theme_discovery_q4(reviews)
        q5_results = self.run_theme_discovery_q5(reviews)
        q6_results = self.run_theme_discovery_q6(reviews)

        analysis_output = {
            "question_1": q1_results,
            "question_2": q2_results,
            "question_3": q3_results,
            "question_4": q4_results,
            "question_5": q5_results,
            "question_6": q6_results,
            "sentiment_distribution": self.compute_sentiment_distribution(reviews)
        }

        if output_json_path:
            out_dir = os.path.dirname(output_json_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_output, f, indent=2, ensure_ascii=False)
            logger.info(f"Analysis results saved successfully to {output_json_path}")

        return analysis_output
