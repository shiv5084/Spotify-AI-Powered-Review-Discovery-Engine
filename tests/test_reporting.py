import unittest
from unittest.mock import MagicMock, patch
from src.reporting.pulse_generator import PulseGenerator
from src.reporting.json_exporter import JSONExporter


class TestReporting(unittest.TestCase):

    def _make_mock_analysis(self):
        return {
            "question_1": [{"theme": "Repetitive Recommendations", "count": 10, "frequency": 0.5, "average_rating": 2.5, "evidence": ["Same songs again and again."]}],
            "question_2": [{"theme": "Over-Personalization", "count": 8, "frequency": 0.4, "average_rating": 2.8, "sentiment_score": -0.7, "evidence": ["Never surfaces new artists."]}],
            "question_3": [{"theme": "Discovering Hidden Gems", "count": 6, "frequency": 0.3, "average_rating": 3.5, "evidence": ["I want to find indie artists."]}],
            "question_4": [{"theme": "Comfort Listening", "count": 7, "frequency": 0.35, "average_rating": 3.0, "evidence": ["I just loop my favorites."]}],
            "question_5": [{"segment": "Mood-Based Explorers", "count": 9, "frequency": 0.45, "average_rating": 2.3, "severity_score": 1.21, "severity_rank": 1, "evidence": ["I can never find good new music."]}],
            "question_6": [{"theme": "Context-Aware Recommendations", "count": 5, "frequency": 0.25, "average_rating": 2.0, "opportunity_score": 1.0, "evidence": ["Wish it knew my mood."]}],
        }

    def _make_mock_opps(self):
        return [
            {"problem": "P1", "evidence": "E1", "suggested_ai_solution": "S1", "expected_impact": "I1"},
            {"problem": "P2", "evidence": "E2", "suggested_ai_solution": "S2", "expected_impact": "I2"},
            {"problem": "P3", "evidence": "E3", "suggested_ai_solution": "S3", "expected_impact": "I3"},
        ]

    def test_word_count_calculation(self):
        """Verifies that the word counter correctly tallies words and ignores extra spacing."""
        generator = PulseGenerator(MagicMock())

        self.assertEqual(generator.count_words("Hello world"), 2)
        self.assertEqual(generator.count_words("  Hello   world  \t  again  "), 3)
        self.assertEqual(generator.count_words(""), 0)

    def test_programmatic_truncator(self):
        """Verifies that programmatic_truncate correctly slices text below 550 words and appends the warning."""
        generator = PulseGenerator(MagicMock())

        # Create a text with 600 words
        long_text = " ".join(["word"] * 600)
        self.assertEqual(generator.count_words(long_text), 600)

        truncated = generator.programmatic_truncate(long_text)
        truncated_count = generator.count_words(truncated)

        self.assertTrue(truncated_count <= 550)
        self.assertIn("programmatically", truncated)

    def test_markdown_pulse_note_structure(self):
        """Verifies that all 7 required sections are included in the generated markdown."""
        generator = PulseGenerator(MagicMock())
        report_text = generator.build_report_draft(self._make_mock_analysis(), self._make_mock_opps())

        # Assert presence of all 7 section headers
        self.assertIn("### 1. Top 3 Discovery Barriers", report_text)
        self.assertIn("### 2. Top 3 Recommendation Frustrations", report_text)
        self.assertIn("### 3. Top 3 Listening Goals", report_text)
        self.assertIn("### 4. Top 3 Repeat-Listening Drivers", report_text)
        self.assertIn("### 5. Top 3 Underserved User Segments", report_text)
        self.assertIn("### 6. Top 3 Unmet Needs", report_text)
        self.assertIn("### 7. Top 3 Product Opportunities", report_text)

    def test_pulse_note_uses_theme_key_for_q1_q6(self):
        """Verifies that Q1-Q4/Q6 use 'theme' key and Q5 uses 'segment' key."""
        generator = PulseGenerator(MagicMock())
        report_text = generator.build_report_draft(self._make_mock_analysis(), self._make_mock_opps())

        # Q1 theme
        self.assertIn("Repetitive Recommendations", report_text)
        # Q2 theme
        self.assertIn("Over-Personalization", report_text)
        # Q5 segment
        self.assertIn("Mood-Based Explorers", report_text)
        # Q6 theme (not 'need')
        self.assertIn("Context-Aware Recommendations", report_text)

    def test_pulse_note_shows_severity_for_q5(self):
        """Q5 section must include Severity and Rank (no discovery_challenges)."""
        generator = PulseGenerator(MagicMock())
        report_text = generator.build_report_draft(self._make_mock_analysis(), self._make_mock_opps())
        self.assertIn("Severity:", report_text)
        self.assertIn("Rank #", report_text)
        # Old field must NOT appear
        self.assertNotIn("discovery_challenges", report_text)

    def test_pulse_note_shows_opportunity_score_for_q6(self):
        """Q6 section must include Opp Score."""
        generator = PulseGenerator(MagicMock())
        report_text = generator.build_report_draft(self._make_mock_analysis(), self._make_mock_opps())
        self.assertIn("Opp Score:", report_text)

    def test_json_exporter_schema_mapping(self):
        """Verifies JSONExporter + pad_analysis_results fills each section to exactly 3 items,
        with live data first and deduplicated fallback items padded at the end.
        """
        from src.reporting.json_exporter import pad_analysis_results

        mock_analysis = self._make_mock_analysis()
        mock_opps = [{"problem": "P1", "evidence": "E1", "suggested_ai_solution": "S1", "expected_impact": "I1"}]

        # Pre-pad (as main.py does) before passing to the exporter
        padded = pad_analysis_results(mock_analysis)

        exporter = JSONExporter()
        data = exporter.export_dashboard_json(padded, mock_opps, "# Pulse Note Draft")

        self.assertIn("week_ending", data)
        self.assertEqual(data["pulse_note_text"], "# Pulse Note Draft")

        metrics = data["metrics"]

        # Each section must have exactly 3 items (1 live + 2 fallback)
        for section_key in ["top_barriers", "top_frustrations", "listening_goals",
                             "repeat_drivers", "underserved_segments", "unmet_needs"]:
            self.assertEqual(len(metrics[section_key]), 3, f"{section_key} should have 3 items")

        # First item in each section is the live data (is_fallback=False)
        self.assertFalse(metrics["top_barriers"][0].get("is_fallback"))
        self.assertEqual(metrics["top_barriers"][0]["theme"], "Repetitive Recommendations")
        self.assertEqual(metrics["top_barriers"][0]["count"], 10)
        self.assertEqual(metrics["top_barriers"][0]["frequency"], 0.5)
        self.assertEqual(metrics["top_barriers"][0]["average_rating"], 2.5)

        # Padded items (index 1 and 2) must be flagged as fallback
        self.assertTrue(metrics["top_barriers"][1].get("is_fallback"))
        self.assertTrue(metrics["top_barriers"][2].get("is_fallback"))

        # No duplicate theme labels across the three entries
        q1_themes = [m["theme"] for m in metrics["top_barriers"]]
        self.assertEqual(len(q1_themes), len(set(q1_themes)), "No duplicate themes in top_barriers")

        # Q2: live item first, no longer has sentiment_score (removed per-frustration)
        self.assertFalse(metrics["top_frustrations"][0].get("is_fallback"))
        self.assertNotIn("sentiment_score", metrics["top_frustrations"][0])

        # Verify sentiment distribution fallback is present
        self.assertIn("sentiment_distribution", data)
        self.assertEqual(data["sentiment_distribution"]["positive"], 15)
        self.assertEqual(data["sentiment_distribution"]["neutral"], 65)
        self.assertEqual(data["sentiment_distribution"]["negative"], 20)
        self.assertEqual(data["sentiment_distribution"]["total"], 100)

        # Q3: live item first, theme key present
        self.assertFalse(metrics["listening_goals"][0].get("is_fallback"))
        self.assertEqual(metrics["listening_goals"][0]["theme"], "Discovering Hidden Gems")

        # Q5: live segment "Mood-Based Explorers" — fallback "Mood-Based Explorers" must be skipped
        q5_segments = [m["segment"] for m in metrics["underserved_segments"]]
        self.assertEqual(len(q5_segments), len(set(q5_segments)), "No duplicate segments in underserved_segments")

        # Q6: live item first, opportunity_score present
        self.assertFalse(metrics["unmet_needs"][0].get("is_fallback"))
        self.assertIn("opportunity_score", metrics["unmet_needs"][0])

        # Opportunities: not padded, only 1 provided
        self.assertEqual(len(metrics["opportunities"]), 1)
        self.assertEqual(metrics["opportunities"][0]["problem"], "P1")
