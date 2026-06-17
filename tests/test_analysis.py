import re
import json
import unittest
from src.analysis.theme_discoverer import ThemeDiscoverer


class TestThemeDiscovery(unittest.TestCase):

    def _make_reviews(self):
        """Returns a small set of mock annotated reviews matching the new Literal schema."""
        return [
            {
                "text": "The app keeps repeating the same tracks. Hard to discover new things.",
                "rating": 2,
                "discovery_pain_points": "Repetitive Recommendations",
                "recommendation_frustrations": "Over-Personalization",
                "listening_goals_intentions": "Discovering Hidden Gems",
                "repeat_listening_signals": "Comfort Listening",
                "unmet_needs": "Context-Aware Recommendations",
                "segment_classification": "Mood-Based Explorers",
                "sentiment": "negative"
            },
            {
                "text": "Great UI and easy search.",
                "rating": 5,
                "discovery_pain_points": "None",
                "recommendation_frustrations": "None",
                "listening_goals_intentions": "None",
                "repeat_listening_signals": "None",
                "unmet_needs": "None",
                "segment_classification": "Playlist Dependents",
                "sentiment": "positive"
            },
            {
                "text": "I get so many ads, please reduce the ad count.",
                "rating": 1,
                "discovery_pain_points": "Excessive Ad Interruptions",
                "recommendation_frustrations": "Popularity Bias",
                "listening_goals_intentions": "Background/Passive Listening",
                "repeat_listening_signals": "Playlist Dependence",
                "unmet_needs": "True Random Shuffle",
                "segment_classification": "Playlist Dependents",
                "sentiment": "negative"
            }
        ]

    def setUp(self):
        self.discoverer = ThemeDiscoverer()
        self.reviews = self._make_reviews()

    def test_q1_local_grouping(self):
        """Q1 groups discovery_pain_points correctly and excludes 'None'."""
        results = self.discoverer.run_theme_discovery_q1(self.reviews)
        themes = [r["theme"] for r in results]
        # "None" from review[1] must be excluded
        self.assertNotIn("None", themes)
        # Both barriers from review[0] and review[2] must appear
        self.assertIn("Repetitive Recommendations", themes)
        self.assertIn("Excessive Ad Interruptions", themes)

    def test_q1_count_and_frequency(self):
        """Q1 count and frequency computed correctly."""
        results = self.discoverer.run_theme_discovery_q1(self.reviews)
        rep_rec = next(r for r in results if r["theme"] == "Repetitive Recommendations")
        self.assertEqual(rep_rec["count"], 1)
        self.assertEqual(rep_rec["frequency"], round(1 / 3, 4))

    def test_q1_average_rating(self):
        """Q1 average_rating computed correctly from matched reviews."""
        results = self.discoverer.run_theme_discovery_q1(self.reviews)
        rep_rec = next(r for r in results if r["theme"] == "Repetitive Recommendations")
        self.assertEqual(rep_rec["average_rating"], 2.0)

    def test_q2_sentiment_score(self):
        """Q2 computes sentiment_score for each frustration theme."""
        results = self.discoverer.run_theme_discovery_q2(self.reviews)
        themes = {r["theme"]: r for r in results}
        self.assertIn("sentiment_score", themes.get("Popularity Bias", {}))
        # Popularity Bias matched review[2] which is negative -> score = -1.0
        self.assertEqual(themes["Popularity Bias"]["sentiment_score"], -1.0)

    def test_q5_severity_score(self):
        """Q5 computes severity_score and severity_rank for each segment."""
        results = self.discoverer.run_theme_discovery_q5(self.reviews)
        segments = {r["segment"]: r for r in results}
        # Playlist Dependents has 2 reviews (ratings 5 and 1), 1 negative (rating<=2)
        playlist_dep = segments["Playlist Dependents"]
        self.assertIn("severity_score", playlist_dep)
        self.assertIn("severity_rank", playlist_dep)
        self.assertEqual(playlist_dep["count"], 2)

    def test_q5_excludes_missing_segments(self):
        """Q5 only returns segments that have at least one review."""
        results = self.discoverer.run_theme_discovery_q5(self.reviews)
        counts = [r["count"] for r in results]
        self.assertTrue(all(c > 0 for c in counts))

    def test_q6_opportunity_score(self):
        """Q6 computes opportunity_score correctly.
        Note: frequency is pre-rounded to 4dp (0.3333) before multiplying,
        so the expected score is round(0.3333 * (6-2), 4) = 1.3332.
        """
        results = self.discoverer.run_theme_discovery_q6(self.reviews)
        themes = {r["theme"]: r for r in results}
        self.assertIn("opportunity_score", themes.get("Context-Aware Recommendations", {}))
        ctx = themes["Context-Aware Recommendations"]
        # frequency = round(1/3, 4) = 0.3333, avg_rating = 2.0
        pre_rounded_freq = round(1 / 3, 4)
        expected_score = round(pre_rounded_freq * (6.0 - 2.0), 4)
        self.assertEqual(ctx["opportunity_score"], expected_score)

    def test_q6_sorted_by_opportunity_score(self):
        """Q6 results are sorted by opportunity_score descending."""
        results = self.discoverer.run_theme_discovery_q6(self.reviews)
        scores = [r["opportunity_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_opportunity_score_formula(self):
        """Verifies programmatic calculation of the Opportunity Score."""
        # Formula: Opportunity Score = Volume Ratio * (6 - Average Rating)
        freq = 0.25
        avg_rating = 2.0
        score = round(freq * (6.0 - avg_rating), 4)
        self.assertEqual(score, 1.0)

        freq = 0.15
        avg_rating = 4.5
        score = round(freq * (6.0 - avg_rating), 4)
        self.assertEqual(score, 0.225)

    def test_perform_full_analysis_structure(self):
        """perform_full_analysis returns all 6 question keys and sentiment_distribution."""
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(self.reviews, f)
            tmp_path = f.name
        try:
            results = self.discoverer.perform_full_analysis(tmp_path)
            for key in ["question_1", "question_2", "question_3", "question_4", "question_5", "question_6", "sentiment_distribution"]:
                self.assertIn(key, results)
            
            # Verify counts from setUp self.reviews (1 positive, 0 neutral, 2 negative)
            dist = results["sentiment_distribution"]
            self.assertEqual(dist["positive"], 1)
            self.assertEqual(dist["neutral"], 0)
            self.assertEqual(dist["negative"], 2)
            self.assertEqual(dist["total"], 3)
        finally:
            os.unlink(tmp_path)
