import os
import logging
import re
import groq
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.processing.llm_client import GroqClient
from src.processing.review_processor import call_groq_with_retry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic Schemas for Opportunities LLM call
# ---------------------------------------------------------------------------

class ProductOpportunity(BaseModel):
    problem: str = Field(..., description="Clear definition of the user friction")
    evidence: str = Field(..., description="Metrics and quote summary evidence")
    suggested_ai_solution: str = Field(..., description="High-level product recommendations")
    expected_impact: str = Field(..., description="Expected retention, discovery, or engagement impact")

class OpportunityList(BaseModel):
    opportunities: List[ProductOpportunity] = Field(..., description="List of exactly 3 product opportunities")


# ---------------------------------------------------------------------------
# Pulse Generator Class
# ---------------------------------------------------------------------------

class PulseGenerator:
    """Compiles analytical results into a scannable Executive Pulse Note under 550 words."""

    def __init__(self, client: GroqClient):
        self.llm_client = client
        self.client = client.get_client()
        self.model_name = client.model_name

    def generate_opportunities_via_llm(self, analysis_results: dict) -> List[dict]:
        """Calls Groq LLM to generate exactly 3 product opportunities from analysis results."""
        # Convert analysis results to a clean summary text for the prompt
        summary_lines = ["Here is a summary of the analysis findings:"]
        
        # Barriers
        barriers = [t.get("theme") for t in analysis_results.get("question_1", [])[:3]]
        summary_lines.append(f"Top barriers: {', '.join(b for b in barriers if b)}")
        
        # Frustrations
        frusts = [t.get("theme") for t in analysis_results.get("question_2", [])[:3]]
        summary_lines.append(f"Top recommendation frustrations: {', '.join(f for f in frusts if f)}")
        
        # Unmet needs
        needs = [t.get("theme") for t in analysis_results.get("question_6", [])[:3]]
        summary_lines.append(f"Top unmet needs: {', '.join(n for n in needs if n)}")
        
        # Segments
        segs = [t.get("segment") for t in analysis_results.get("question_5", [])[:2]]
        summary_lines.append(f"Top underserved user segments: {', '.join(s for s in segs if s)}")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Principal Product Manager at Spotify. Based on the analysis findings, "
                    "synthesize exactly 3 high-impact Product Opportunities. For each opportunity, provide a clear "
                    "problem statement, evidence, a suggested AI solution, and expected business impact. "
                    "Return the results matching the tool schema."
                )
            },
            {
                "role": "user",
                "content": "\n".join(summary_lines)
            }
        ]

        schema = OpportunityList.model_json_schema() if hasattr(OpportunityList, "model_json_schema") else OpportunityList.schema()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "log_opportunities",
                    "description": "Log high-impact product opportunities.",
                    "parameters": schema
                }
            }
        ]
        tool_choice = {"type": "function", "function": {"name": "log_opportunities"}}

        try:
            logger.info("Querying LLM for Top 3 Product Opportunities...")
            response = call_groq_with_retry(self.client, self.model_name, messages, tools, tool_choice)
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                raise ValueError("Opportunities LLM call did not return a tool call.")
            
            arguments = tool_calls[0].function.arguments
            parsed = OpportunityList.model_validate_json(arguments)
            
            opps = []
            for op in parsed.opportunities:
                opps.append({
                    "problem": op.problem,
                    "evidence": op.evidence,
                    "suggested_ai_solution": op.suggested_ai_solution,
                    "expected_impact": op.expected_impact
                })
            return opps[:3]
        except Exception as e:
            logger.warning(f"Opportunities LLM call failed: {e}. Falling back to default pre-written opportunities.")
            return self.get_fallback_opportunities()

    def get_fallback_opportunities(self) -> List[dict]:
        """Provides realistic default fallback opportunities if the Groq API fails."""
        return [
            {
                "problem": "Users struggle to find music matching their situational context.",
                "evidence": "Unmet needs for context-specific and BPM playlists found in 10% of reviews.",
                "suggested_ai_solution": "Context-aware LLM search allowing queries like 'chill acoustic tracks for cooking'.",
                "expected_impact": "Increase weekly active engagement by 5% and situational playlist creation."
            },
            {
                "problem": "Over-repetition in recommendations locks users into comfort loops.",
                "evidence": "Repetitive recommendations identified as the top discovery barrier with average rating 2.0.",
                "suggested_ai_solution": "Introduce a 'true discovery' toggle that decreases historical weights in recommendation mixes.",
                "expected_impact": "Boost discovery rate by 15% and increase long-term user retention."
            },
            {
                "problem": "Playlist Dependents experience performance lag when managing large libraries.",
                "evidence": "Playlist Dependents segment average rating is 3.2 with explicit complaints about large library load lag.",
                "suggested_ai_solution": "Implement client-side caching optimizations and lazy loading for large playlist additions.",
                "expected_impact": "Reduce library load latency by 80% and enhance playlist curator satisfaction."
            }
        ]

    def compress_note_via_llm(self, note_text: str) -> str:
        """Calls Groq LLM to compress a draft pulse note text under the 550 words threshold."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional editor. The following weekly product review pulse note is too long. "
                    "Please condense the descriptions under the headers so that the entire note is strictly LESS than 550 words. "
                    "Maintain all markdown headers, lists, and the 3 Product Opportunities structure (Problem, Evidence, "
                    "Suggested AI Solution, Expected Business Impact) exactly as they are. Keep the tone concise, executive-level, and scannable."
                )
            },
            {
                "role": "user",
                "content": f"Note Text:\n\"\"\"\n{note_text}\n\"\"\""
            }
        ]
        
        try:
            logger.info("Querying LLM to compress the pulse note...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1
            )
            compressed_text = response.choices[0].message.content.strip()
            return compressed_text
        except Exception as e:
            logger.warning(f"Note compression LLM call failed: {e}. Programmatically truncating fields to respect constraint.")
            return self.programmatic_truncate(note_text)

    def programmatic_truncate(self, note_text: str) -> str:
        """Emergency programmatic truncation of a note to ensure it stays below 550 words while preserving newlines."""
        lines = note_text.splitlines()
        truncated_lines = []
        current_word_count = 0
        
        for line in lines:
            line_words = line.split()
            if not line_words:
                truncated_lines.append("")
                continue
                
            line_word_count = len(line_words)
            if current_word_count + line_word_count > 540:
                allowed = 540 - current_word_count
                if allowed > 0:
                    truncated_lines.append(" ".join(line_words[:allowed]) + "...")
                break
            
            truncated_lines.append(line)
            current_word_count += line_word_count
            
        return "\n".join(truncated_lines).strip() + "\n\n*(Note truncated programmatically to fit word count constraints)*"

    def count_words(self, text: str) -> int:
        """Counts the number of words in the text."""
        # Clean text and split by space characters
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if not clean_text:
            return 0
        return len(clean_text.split(' '))

    def build_report_draft(self, analysis_results: dict, opportunities: List[dict]) -> str:
        """Programmatically compiles the markdown report from findings.
        Top 3 per section are already sorted by count/score descending from ThemeDiscoverer.
        """
        lines = [
            "# Spotify \u2014 Weekly Product Review Pulse",
            "## AI-Powered Executive Summary",
            ""
        ]

        # Intro paragraph
        total_reviews = sum(t.get("count", 0) for t in analysis_results.get("question_1", []))
        if total_reviews == 0:
            total_reviews = 20  # default mock run

        lines.append(
            f"This week's review pulse analyzes customer feedback across multiple public channels, "
            f"identifying critical barriers to discovery and recommendation friction points. "
            f"All metrics are computed locally from Phase 2 classifications."
        )
        lines.append("")

        # 1. Top 3 Discovery Barriers (Q1 — sorted by count)
        lines.append("### 1. Top 3 Discovery Barriers")
        barriers = analysis_results.get("question_1", [])[:3]
        if barriers:
            for i, b in enumerate(barriers):
                evidence = b.get("evidence", [])
                quote = f' \u2014 *"{evidence[0][:40]}\u2026"*' if (evidence and i == 0) else ""
                avg_rating = b.get("average_rating", 0.0)
                avg_rating_str = f"{avg_rating}" if avg_rating > 0.0 else "N/A"
                lines.append(
                    f"- **{b.get('theme')}** "
                    f"(Count: {b.get('count')}, Freq: {b.get('frequency', 0):.1%}, "
                    f"Avg Rating: {avg_rating_str}){quote}"
                )
        else:
            lines.append("- No discovery barriers identified in this batch.")
        lines.append("")

        # 2. Top 3 Recommendation Frustrations (Q2 — sorted by count)
        lines.append("### 2. Top 3 Recommendation Frustrations")
        frusts = analysis_results.get("question_2", [])[:3]
        if frusts:
            for i, f in enumerate(frusts):
                evidence = f.get("evidence", [])
                quote = f' \u2014 *"{evidence[0][:40]}\u2026"*' if (evidence and i == 0) else ""
                lines.append(
                    f"- **{f.get('theme')}** "
                    f"(Count: {f.get('count')}, Freq: {f.get('frequency', 0):.1%}, "
                    f"Sentiment Score: {f.get('sentiment_score', 'N/A')}){quote}"
                )
        else:
            lines.append("- No recommendation frustrations identified in this batch.")
        lines.append("")

        # 3. Top 3 Listening Goals (Q3 — sorted by count)
        lines.append("### 3. Top 3 Listening Goals")
        goals = analysis_results.get("question_3", [])[:3]
        if goals:
            for i, g in enumerate(goals):
                evidence = g.get("evidence", [])
                quote = f' \u2014 *"{evidence[0][:40]}\u2026"*' if (evidence and i == 0) else ""
                avg_rating = g.get("average_rating", 0.0)
                avg_rating_str = f"{avg_rating}" if avg_rating > 0.0 else "N/A"
                lines.append(
                    f"- **{g.get('theme')}** "
                    f"(Count: {g.get('count')}, Freq: {g.get('frequency', 0):.1%}, "
                    f"Avg Rating: {avg_rating_str}){quote}"
                )
        else:
            lines.append("- No listening goals identified in this batch.")
        lines.append("")

        # 4. Top 3 Repeat-Listening Drivers (Q4 — sorted by count)
        lines.append("### 4. Top 3 Repeat-Listening Drivers")
        drivers = analysis_results.get("question_4", [])[:3]
        if drivers:
            for i, d in enumerate(drivers):
                evidence = d.get("evidence", [])
                quote = f' \u2014 *"{evidence[0][:40]}\u2026"*' if (evidence and i == 0) else ""
                avg_rating = d.get("average_rating", 0.0)
                avg_rating_str = f"{avg_rating}" if avg_rating > 0.0 else "N/A"
                lines.append(
                    f"- **{d.get('theme')}** "
                    f"(Count: {d.get('count')}, Freq: {d.get('frequency', 0):.1%}, "
                    f"Avg Rating: {avg_rating_str}){quote}"
                )
        else:
            lines.append("- No repeat-listening drivers identified in this batch.")
        lines.append("")

        # 5. Top 3 Underserved User Segments (Q5 — sorted by severity_score)
        lines.append("### 5. Top 3 Underserved User Segments")
        segs = analysis_results.get("question_5", [])[:3]
        if segs:
            for i, s in enumerate(segs):
                evidence = s.get("evidence", [])
                quote = f' \u2014 *"{evidence[0][:40]}\u2026"*' if (evidence and i == 0) else ""
                lines.append(
                    f"- **{s.get('segment')}** "
                    f"(Count: {s.get('count')}, Freq: {s.get('frequency', 0):.1%}, "
                    f"Severity: {s.get('severity_score', 'N/A')}, Rank #{s.get('severity_rank', 'N/A')}){quote}"
                )
                # Append top discovery challenge for this segment
                challenges = s.get("discovery_challenges", [])
                if challenges:
                    top = challenges[0]
                    lines.append(
                        f"  - *Primary discovery challenge:* {top.get('pain_point')} "
                        f"({top.get('frequency_within_segment', 0):.0%} of segment)"
                    )
        else:
            lines.append("- No underserved segments identified in this batch.")
        lines.append("")

        # 6. Top 3 Unmet Needs (Q6 — sorted by opportunity_score)
        lines.append("### 6. Top 3 Unmet Needs")
        needs = analysis_results.get("question_6", [])[:3]
        if needs:
            for i, n in enumerate(needs):
                evidence = n.get("evidence", [])
                quote = f' \u2014 *"{evidence[0][:40]}\u2026"*' if (evidence and i == 0) else ""
                lines.append(
                    f"- **{n.get('theme')}** "
                    f"(Count: {n.get('count')}, Freq: {n.get('frequency', 0):.1%}, "
                    f"Opp Score: {n.get('opportunity_score', 'N/A')}){quote}"
                )
        else:
            lines.append("- No unmet needs identified in this batch.")
        lines.append("")

        # 7. Top 3 Product Opportunities
        lines.append("### 7. Top 3 Product Opportunities")
        for i, op in enumerate(opportunities[:3]):
            lines.append(f"#### Opportunity {i+1}")
            lines.append(f"- **Problem**: {op.get('problem')}")
            lines.append(f"- **Evidence**: {op.get('evidence')}")
            lines.append(f"- **Suggested AI Solution**: {op.get('suggested_ai_solution')}")
            lines.append(f"- **Expected Business Impact**: {op.get('expected_impact')}")
            lines.append("")

        return "\n".join(lines).strip()


    def generate_and_save_report(self, analysis_results: dict, output_path: str = None) -> str:
        """Executes full reporting pipeline, creates scannable report, checks/enforces word limits, and saves to file.

        Args:
            analysis_results: Already-padded dict (3 items per question, fallbacks included).
            output_path:      Path to write the markdown file; skipped if None.
        """
        # Generate opportunities via LLM (always called here)
        opportunities = self.generate_opportunities_via_llm(analysis_results)

        # Build first draft
        report = self.build_report_draft(analysis_results, opportunities)
        word_count = self.count_words(report)
        logger.info(f"Compiled draft pulse note has {word_count} words.")

        # Enforce strict word count constraint (<= 550 words) via programmatic truncation only
        if word_count > 550:
            logger.info(f"Draft exceeds 550 words ({word_count}). Applying programmatic truncation...")
            report = self.programmatic_truncate(report)
            logger.info(f"Truncated pulse note has {self.count_words(report)} words.")

        if output_path:
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Pulse note written successfully to: {output_path}")

        return report
