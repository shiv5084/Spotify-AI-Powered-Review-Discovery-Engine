import os
import json
import time
import random
import logging
import pandas as pd
import groq
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Any, Tuple, Dict
from src.processing.llm_client import GroqClient
from src.processing.sampler import stratified_sample

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ReviewAnalysis(BaseModel):
    """Structured representation of Spotify review metrics."""
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        ...,
        description="Sentiment of the review. Must be exactly 'positive', 'neutral', or 'negative'."
    )
    discovery_pain_points: Literal[
        "Repetitive Recommendations",
        "Complex UI Navigation",
        "Lack of Mood/Context Filters",
        "Excessive Ad Interruptions",
        "Poor Search Precision",
        "None"
    ] = Field(
        ...,
        description=(
            "Classify the discovery barrier into exactly one: "
            "'Repetitive Recommendations' (algorithmic repetition/loop), "
            "'Complex UI Navigation' (cluttered interface), "
            "'Lack of Mood/Context Filters' (no mood, vibe, activity, or situational context filters), "
            "'Excessive Ad Interruptions' (too many ads in free tier), "
            "'Poor Search Precision' (inaccurate search results), "
            "'None' (no discovery barrier mentioned)."
        )
    )
    recommendation_frustrations: Literal[
        "Popularity Bias",
        "Limited Genre Diversity",
        "Over-Personalization",
        "Podcast/Audiobook Clutter",
        "Stale Algorithmic Mixes",
        "None"
    ] = Field(
        ...,
        description=(
            "Classify the recommendation frustration into exactly one: "
            "'Popularity Bias' (over-promoting top 40/mainstream), "
            "'Limited Genre Diversity' (stuck in one or two genres), "
            "'Over-Personalization' (too aligned to listening history), "
            "'Podcast/Audiobook Clutter' (non-music content cluttering music feeds), "
            "'Stale Algorithmic Mixes' (mixes not refreshing), "
            "'None' (no recommendation frustration mentioned)."
        )
    )
    listening_goals_intentions: Literal[
        "Discovering Hidden Gems",
        "Exploring New Genres",
        "Mood/Activity-Based Listening",
        "Relying on Familiar Playlists",
        "Background/Passive Listening",
        "None"
    ] = Field(
        ...,
        description=(
            "Classify the listening goal into exactly one: "
            "'Discovering Hidden Gems' (seeking niche/indie/undiscovered artists), "
            "'Exploring New Genres' (branching out to unfamiliar styles or cross-genre listening), "
            "'Mood/Activity-Based Listening' (matching music to moods, emotions, or activities), "
            "'Relying on Familiar Playlists' (defaulting to the same playlists for comfort/ease), "
            "'Background/Passive Listening' (passive/ambient/low-interaction listening), "
            "'None' (no listening goal expressed)."
        )
    )
    repeat_listening_signals: Literal[
        "Comfort Listening",
        "Playlist Dependence",
        "Lack of Trust in Recommendations",
        "Choice Fatigue",
        "Mood Mismatch",
        "None"
    ] = Field(
        ...,
        description=(
            "Classify the repeat-listening driver into exactly one: "
            "'Comfort Listening' (seeking familiar/nostalgic tracks), "
            "'Playlist Dependence' (looping same playlists for ease), "
            "'Lack of Trust in Recommendations' (distrusting new suggestions), "
            "'Choice Fatigue' (overwhelmed by options), "
            "'Mood Mismatch' (available recommendations do not match current mood/context, reverting to known tracks), "
            "'None' (no repeat-listening driver mentioned)."
        )
    )
    unmet_needs: Literal[
        "Conversational AI Discovery",
        "Context-Aware Recommendations",
        "True Random Shuffle",
        "Smart Playlist Refresh",
        "Cross-Genre Discovery Mode",
        "None"
    ] = Field(
        ...,
        description=(
            "Classify the unmet need into exactly one: "
            "'Conversational AI Discovery' (natural language chat to find music), "
            "'Context-Aware Recommendations' (contextual triggers like time/mood/weather/activity), "
            "'True Random Shuffle' (guaranteed uniform shuffle distribution), "
            "'Smart Playlist Refresh' (auto-refresh stale playlists with fresh, relevant tracks), "
            "'Cross-Genre Discovery Mode' (dedicated mode for exploring across genres with guided transitions), "
            "'None' (no unmet need expressed)."
        )
    )
    segment_classification: Literal[
        "Mood-Based Explorers",
        "Playlist Dependents",
        "New Music Seekers",
        "Genre Hoppers",
        "Passive Listener"
    ] = Field(
        ...,
        description=(
            "Classify the user into one of these exact personas: "
            "'Mood-Based Explorers' (seek music by emotion/activity, not genre. Switch moods frequently), "
            "'Playlist Dependents' (default to same 2-3 playlists, rarely explore beyond comfort zone), "
            "'New Music Seekers' (actively browse for undiscovered artists, top charts and emerging tracks), "
            "'Genre Hoppers' (rapidly switch between genres. Hard to predict but high engagement), "
            "'Passive Listener' (music for background/chill/low interaction)."
        )
    )

class BatchReviewAnalysis(BaseModel):
    """Container for batch reviews analysis."""
    analyses: List[ReviewAnalysis] = Field(
        ...,
        description="List of structured review analysis results matching the input reviews in order."
    )

class GateBatchResult(BaseModel):
    """Strategy 5 gate: yes/no signal decision per review in a batch."""
    decisions: List[Literal["yes", "no"]] = Field(
        ...,
        description=(
            "List of 'yes'/'no' gate decisions matching the input reviews in order. "
            "'yes' = review contains at least one actionable signal (pain point, frustration, "
            "listening goal, repeat-listening driver, unmet need, or segment marker). "
            "'no' = review is generic or content-free with no useful classification signal."
        )
    )

# ---------------------------------------------------------------------------
# Prompt Templates (JSON input/output contract)
# ---------------------------------------------------------------------------

def _build_single_review_system_prompt(output_schema: dict) -> str:
    return (
        "You are a Senior Product Analyst at Spotify. Analyze user reviews and extract structured metadata.\n\n"
        "## Input Format (JSON)\n"
        "You will receive a single review in this JSON shape:\n"
        '{\n  "review": {\n    "text": "<user review text>"\n  }\n}\n\n'
        "## Output Format (JSON)\n"
        "Respond ONLY by calling the `analyze_review` tool. The tool arguments MUST be valid JSON matching this schema:\n"
        f"{json.dumps(output_schema, indent=2)}\n\n"
        "Rules:\n"
        "- `sentiment` must be exactly one of: positive, neutral, negative.\n"
        "- All classification fields must be exactly one of the allowed literal values in the schema.\n"
        "- Choose 'None' when the review does not mention that specific type of feedback.\n"
        "- `segment_classification` must be exactly one of the allowed persona values in the schema."
    )


def _build_batch_reviews_system_prompt(output_schema: dict) -> str:
    return (
        "You are a Senior Product Analyst at Spotify. Analyze a batch of user reviews and extract structured metadata.\n\n"
        "## Input Format (JSON)\n"
        "You will receive reviews in this JSON shape:\n"
        '{\n  "reviews": [\n    {"index": 0, "text": "<review text>"},\n    {"index": 1, "text": "<review text>"}\n  ]\n}\n\n'
        "## Output Format (JSON)\n"
        "Respond ONLY by calling the `analyze_review_batch` tool. The tool arguments MUST be valid JSON matching this schema:\n"
        f"{json.dumps(output_schema, indent=2)}\n\n"
        "Rules:\n"
        "- `analyses` length MUST equal the number of input reviews.\n"
        "- Preserve the exact input order (index 0 -> analyses[0], etc.).\n"
        "- For empty or irrelevant reviews, use neutral sentiment, 'None' for all classification fields, and Passive Listener.\n"
        "- `sentiment` must be exactly one of: positive, neutral, negative.\n"
        "- All classification fields must be exactly one of the allowed literal values in the schema.\n"
        "- Choose 'None' when the review does not mention that specific type of feedback.\n"
        "- `segment_classification` must be exactly one of the allowed persona values in the schema."
    )


def _build_gate_system_prompt() -> str:
    """Short, cheap system prompt for the Strategy 5 gate pass (runs on small model)."""
    return (
        "You are a review signal classifier. For each review in the input list, decide "
        "whether it contains at least one of the following actionable signals:\n"
        "  - A specific product pain point or usability frustration\n"
        "  - A recommendation dissatisfaction (repetition, popularity bias, etc.)\n"
        "  - A listening goal or behavioral intention\n"
        "  - A repeat-listening pattern or driver\n"
        "  - An unmet product need or feature request\n"
        "  - A clear user segment or usage pattern indicator\n\n"
        "## Input Format (JSON)\n"
        '{"reviews": [{"index": 0, "text": "<review>"}, ...]}\n\n'
        "## Output Format (JSON)\n"
        "Respond ONLY by calling the `gate_reviews` tool with:\n"
        '{"decisions": ["yes", "no", ...]}\n\n'
        "Rules:\n"
        "- `decisions` length MUST equal the number of input reviews.\n"
        "- Answer 'yes' if the review contains ANY of the signals listed above.\n"
        "- Answer 'no' for generic, vague, or content-free reviews "
        '(e.g. \'Great!\', \'Worst app\', \'5 stars\', very short or off-topic text).\n'
        "- Preserve the exact input order.\n"
        "- CRITICAL: Do NOT echo the input reviews or include any other fields (such as 'reviews', 'text', 'index', etc.) in the tool arguments. The tool arguments object MUST ONLY contain the single key 'decisions'."
    )


def _build_single_review_input_payload(review_text: str) -> str:
    return json.dumps({"review": {"text": review_text}}, ensure_ascii=False, indent=2)


def _build_batch_reviews_input_payload(review_texts: List[str]) -> str:
    payload = {
        "reviews": [
            {"index": i, "text": text}
            for i, text in enumerate(review_texts)
        ]
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class GroqRateLimiter:
    """Proactive throttle to stay under Groq RPM/TPM limits."""

    def __init__(
        self,
        min_interval_seconds: float = 3.0,
        tpm_budget_per_minute: int = 20000,
    ):
        self.min_interval = min_interval_seconds
        self.tpm_budget = tpm_budget_per_minute
        self._last_request_at = 0.0
        self._token_window: List[tuple[float, int]] = []

    def wait_before_request(self) -> None:
        elapsed = time.time() - self._last_request_at
        wait_time = self.min_interval - elapsed
        if wait_time > 0:
            logger.debug(f"Rate limiter: waiting {wait_time:.2f}s before next request...")
            time.sleep(wait_time)
        self._last_request_at = time.time()

    def record_token_usage(self, total_tokens: int) -> None:
        if total_tokens <= 0:
            return
        now = time.time()
        self._token_window.append((now, total_tokens))
        self._token_window = [(ts, tokens) for ts, tokens in self._token_window if now - ts < 60]
        tokens_in_window = sum(tokens for _, tokens in self._token_window)
        if tokens_in_window > self.tpm_budget:
            extra_wait = 60 - (now - self._token_window[0][0]) + random.uniform(0.5, 1.5)
            logger.info(
                f"Approaching TPM budget ({tokens_in_window}/{self.tpm_budget}). "
                f"Pausing {extra_wait:.1f}s..."
            )
            time.sleep(extra_wait)


def _extract_retry_after_seconds(error: Exception) -> Optional[float]:
    response = getattr(error, "response", None)
    if response is None:
        return None
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    retry_after = headers.get("retry-after") or headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return float(retry_after)
    except (TypeError, ValueError):
        return None


class GroqTokenDailyLimitError(RuntimeError):
    """Raised when Groq's tokens-per-day (TPD) quota is exhausted.

    Unlike per-minute rate limits (which recover in seconds), TPD resets at
    midnight UTC so there is no point retrying within the same run.
    """


def _is_rate_limit_error(error: Exception) -> bool:
    if isinstance(error, groq.RateLimitError):
        return True
    if isinstance(error, groq.APIStatusError) and getattr(error, "status_code", None) == 429:
        return True
    return False


def _is_tpd_exhausted(error: Exception) -> bool:
    """Return True when the 429 is a tokens-per-*day* limit, not per-minute."""
    msg = str(error).lower()
    return "tokens per day" in msg or "tpd" in msg or "per day" in msg


def call_groq_with_retry(
    client: groq.Groq,
    model: str,
    messages: list,
    tools: list,
    tool_choice: dict,
    max_retries: int = 5,
    initial_backoff: int = 5,
    max_backoff: int = 120,
    rate_limiter: Optional[GroqRateLimiter] = None,
) -> Any:
    """Executes a Groq chat completion call with proactive throttling and retry on rate limits."""
    backoff = initial_backoff
    for attempt in range(max_retries):
        if rate_limiter is not None:
            rate_limiter.wait_before_request()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=0.1
            )
            usage = getattr(response, "usage", None)
            if rate_limiter is not None and usage is not None:
                total_tokens = getattr(usage, "total_tokens", 0) or 0
                if isinstance(total_tokens, (int, float)):
                    rate_limiter.record_token_usage(int(total_tokens))
            return response
        except Exception as e:
            if not _is_rate_limit_error(e):
                logger.error(f"Groq API error: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(backoff + random.uniform(0, 1))
                backoff = min(backoff * 2, max_backoff)
                continue

            # TPD exhaustion: daily quota is gone — abort immediately, no point retrying.
            if _is_tpd_exhausted(e):
                logger.error(
                    "Groq daily token quota (TPD) exhausted. "
                    "No further API calls can succeed until midnight UTC. "
                    "Aborting Phase 2."
                )
                raise GroqTokenDailyLimitError(
                    "Groq tokens-per-day limit reached. Try again after midnight UTC."
                ) from e

            retry_after = _extract_retry_after_seconds(e)
            wait_time = retry_after if retry_after is not None else backoff
            wait_time += random.uniform(0, 1)
            if wait_time > 30:
                logger.warning(f"Rate limit wait time {wait_time:.1f}s is too long (limit 30s). Failing fast to let fallback handle it.")
                raise e
            logger.warning(
                f"Rate limit hit (attempt {attempt + 1}/{max_retries}). "
                f"Retrying in {wait_time:.1f}s..."
            )
            time.sleep(wait_time)
            backoff = min(backoff * 2, max_backoff)

    raise RuntimeError("Failed to get response from Groq API after maximum retries.")

# ---------------------------------------------------------------------------
# Review Processor Class
# ---------------------------------------------------------------------------

class ReviewProcessor:
    """Handles structured LLM sentiment extraction and metric parsing for reviews."""

    def __init__(self, client: GroqClient):
        self.llm_client = client
        self.client = client.get_client()
        self.model_name = client.model_name
        rate_cfg = getattr(client, "rate_limit", None)
        if not isinstance(rate_cfg, dict):
            rate_cfg = {}
        self.batch_size = int(rate_cfg.get("batch_size", 5))
        self.max_retries = int(rate_cfg.get("max_retries", 5))
        self.initial_backoff = int(rate_cfg.get("initial_backoff_seconds", 5))
        self.max_backoff = int(rate_cfg.get("max_backoff_seconds", 120))
        self.rate_limiter = GroqRateLimiter(
            min_interval_seconds=float(rate_cfg.get("min_request_interval_seconds", 3.0)),
            tpm_budget_per_minute=int(rate_cfg.get("tpm_budget", 20000)),
        )

    def _groq_call_kwargs(self) -> dict:
        return {
            "max_retries": self.max_retries,
            "initial_backoff": self.initial_backoff,
            "max_backoff": self.max_backoff,
            "rate_limiter": self.rate_limiter,
        }

    @staticmethod
    def _analysis_to_dict(analysis: ReviewAnalysis) -> dict:
        return {
            "sentiment": analysis.sentiment,
            "discovery_pain_points": analysis.discovery_pain_points,
            "recommendation_frustrations": analysis.recommendation_frustrations,
            "listening_goals_intentions": analysis.listening_goals_intentions,
            "repeat_listening_signals": analysis.repeat_listening_signals,
            "unmet_needs": analysis.unmet_needs,
            "segment_classification": analysis.segment_classification,
        }

    @staticmethod
    def _neutral_analysis_dict() -> dict:
        return {
            "sentiment": "neutral",
            "discovery_pain_points": "None",
            "recommendation_frustrations": "None",
            "listening_goals_intentions": "None",
            "repeat_listening_signals": "None",
            "unmet_needs": "None",
            "segment_classification": "Passive Listener",
        }

    def analyze_single_review(self, review_text: str) -> ReviewAnalysis:
        """Calls Groq LLM with tool schema enforcement to parse a single review text."""
        if not review_text.strip():
            return ReviewAnalysis(**self._neutral_analysis_dict())

        schema = ReviewAnalysis.model_json_schema() if hasattr(ReviewAnalysis, "model_json_schema") else ReviewAnalysis.schema()
        messages = [
            {
                "role": "system",
                "content": _build_single_review_system_prompt(schema),
            },
            {
                "role": "user",
                "content": _build_single_review_input_payload(review_text),
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_review",
                    "description": "Return structured review analysis as JSON.",
                    "parameters": schema
                }
            }
        ]
        tool_choice = {"type": "function", "function": {"name": "analyze_review"}}

        response = call_groq_with_retry(
            self.client,
            self.model_name,
            messages,
            tools,
            tool_choice,
            **self._groq_call_kwargs(),
        )

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ValueError("No tool call returned by the model.")

        arguments = tool_calls[0].function.arguments
        logger.debug("Single review LLM JSON response received.")
        return ReviewAnalysis.model_validate_json(arguments)

    def analyze_batch_reviews(self, review_texts: List[str]) -> List[ReviewAnalysis]:
        """Analyzes a list of reviews in a single LLM prompt call."""
        if not review_texts:
            return []

        schema = BatchReviewAnalysis.model_json_schema() if hasattr(BatchReviewAnalysis, "model_json_schema") else BatchReviewAnalysis.schema()
        messages = [
            {
                "role": "system",
                "content": _build_batch_reviews_system_prompt(schema),
            },
            {
                "role": "user",
                "content": _build_batch_reviews_input_payload(review_texts),
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_review_batch",
                    "description": "Return structured batch review analyses as JSON.",
                    "parameters": schema
                }
            }
        ]
        tool_choice = {"type": "function", "function": {"name": "analyze_review_batch"}}

        response = call_groq_with_retry(
            self.client,
            self.model_name,
            messages,
            tools,
            tool_choice,
            **self._groq_call_kwargs(),
        )

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise ValueError("No tool call returned by the model.")

        arguments = tool_calls[0].function.arguments
        logger.debug("Batch review LLM JSON response received.")
        batch_output = BatchReviewAnalysis.model_validate_json(arguments)
        return batch_output.analyses

    def _build_annotated_records(self, df: pd.DataFrame, results: list) -> list:
        annotated_records = []
        for idx, row in df.iterrows():
            record = {
                "source": str(row.get("source", "")),
                "date": str(row.get("date", "")),
                "title": str(row.get("title", "")) if pd.notna(row.get("title")) else "",
                "text": str(row.get("text", "")),
                "rating": int(row.get("rating")) if pd.notna(row.get("rating")) and row.get("rating") is not None else None,
                "engagement": int(row.get("engagement")) if pd.notna(row.get("engagement")) and row.get("engagement") is not None else None,
            }
            if results[idx] is not None:
                record.update(results[idx])
            else:
                record.update(self._neutral_analysis_dict())
            annotated_records.append(record)
        return annotated_records

    def _save_annotated_json(self, annotated_records: list) -> str:
        processed_dir = self.llm_client.config.get("paths", {}).get("processed_data_dir", "data/processed")
        if not os.path.isabs(processed_dir):
            processed_dir = os.path.abspath(processed_dir)
        os.makedirs(processed_dir, exist_ok=True)
        out_path = os.path.join(processed_dir, "annotated_reviews.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(annotated_records, f, indent=2, ensure_ascii=False)
        return out_path

    def _save_sample_coverage(self, coverage_dict: dict) -> str:
        """Saves Strategy 4+5 coverage metadata to data/processed/sample_coverage.json."""
        processed_dir = self.llm_client.config.get("paths", {}).get("processed_data_dir", "data/processed")
        if not os.path.isabs(processed_dir):
            processed_dir = os.path.abspath(processed_dir)
        os.makedirs(processed_dir, exist_ok=True)
        out_path = os.path.join(processed_dir, "sample_coverage.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(coverage_dict, f, indent=2, ensure_ascii=False)
        return out_path

    def process_reviews(self, df: pd.DataFrame, num_records: int = None) -> pd.DataFrame:
        """Iterates through reviews in configurable batches, queries Groq API, and saves annotated_reviews.json."""
        if df.empty:
            logger.warning("Empty DataFrame passed to process_reviews. Returning empty DataFrame.")
            return df

        if num_records is not None:
            df = df.head(num_records).copy()

        df = df.reset_index(drop=True)
        logger.info(
            f"Processing {len(df)} reviews in batches of {self.batch_size} "
            f"using Groq model {self.model_name}..."
        )

        results = [None] * len(df)
        review_records = list(df.iterrows())
        chunk_size = self.batch_size
        tpd_halt = False
        out_path = None

        for chunk_start in range(0, len(df), chunk_size):
            chunk = review_records[chunk_start : chunk_start + chunk_size]
            chunk_indices = [item[0] for item in chunk]
            chunk_texts = [str(item[1].get("text", "")).strip() for item in chunk]

            logger.info(
                f"Analyzing batch reviews {chunk_start + 1} to "
                f"{min(chunk_start + chunk_size, len(df))}/{len(df)}..."
            )

            success = False
            try:
                batch_analyses = self.analyze_batch_reviews(chunk_texts)
                if len(batch_analyses) == len(chunk):
                    for idx_in_chunk, analysis in enumerate(batch_analyses):
                        global_idx = chunk_indices[idx_in_chunk]
                        results[global_idx] = self._analysis_to_dict(analysis)
                    success = True
                else:
                    logger.warning(
                        f"Batch size mismatch (expected {len(chunk)}, got {len(batch_analyses)}). "
                        "Falling back to sequential queries for this batch."
                    )
            except GroqTokenDailyLimitError:
                logger.warning(
                    "TPD quota exhausted mid-batch. Proceeding with partial results for Phase 2."
                )
                tpd_halt = True
            except Exception as e:
                logger.warning(f"Batch query failed: {e}. Falling back to sequential queries for this batch.")

            if tpd_halt:
                break

            if not success:
                for idx_in_chunk, (global_idx, _row) in enumerate(chunk):
                    review_text = chunk_texts[idx_in_chunk]
                    logger.info(f"Fallback sequential analysis for review {global_idx + 1}/{len(df)}...")
                    try:
                        analysis = self.analyze_single_review(review_text)
                        results[global_idx] = self._analysis_to_dict(analysis)
                    except GroqTokenDailyLimitError:
                        logger.warning(
                            "TPD quota exhausted in sequential fallback. Proceeding with partial results."
                        )
                        tpd_halt = True
                        break
                    except Exception as seq_err:
                        logger.error(f"Sequential fallback also failed for review at index {global_idx}: {seq_err}")
                        results[global_idx] = self._neutral_analysis_dict()

            if tpd_halt:
                break

            annotated_records = self._build_annotated_records(df, results)
            out_path = self._save_annotated_json(annotated_records)
            logger.info(f"Checkpoint saved after batch ending at review {min(chunk_start + chunk_size, len(df))}.")

        if tpd_halt:
            for idx in range(len(results)):
                if results[idx] is None:
                    results[idx] = self._neutral_analysis_dict()
            annotated_records = self._build_annotated_records(df, results)
            out_path = self._save_annotated_json(annotated_records)

        results_df = pd.DataFrame(results)
        annotated_df = pd.concat([df, results_df], axis=1)

        logger.info(f"Successfully processed {len(annotated_df)} reviews. Output saved to {out_path}.")
        return annotated_df

    # -------------------------------------------------------------------------
    # Strategy 5 — Two-Stage Gate
    # -------------------------------------------------------------------------

    def analyze_gate_batch(self, review_texts: List[str], gate_model: str = None) -> List[bool]:
        """
        Strategy 5 gate: cheap yes/no signal filter before full 7-dimension classification.

        Sends a batch of reviews to a small fast Groq model (llama-3.1-8b-instant) and
        returns True (pass → needs full LLM) or False (reject → auto-labelled as neutral/None).

        Falls back to passing all reviews through if the gate call fails, ensuring no data loss.

        Parameters
        ----------
        review_texts : List[str]
            Review texts to evaluate.
        gate_model : str, optional
            Groq model name for the gate. Falls back to self.model_name if None.

        Returns
        -------
        List[bool]
            True  = review passes gate (contains useful signal → full classification).
            False = review rejected (generic/trivial → auto-labelled, saves LLM tokens).
        """
        if not review_texts:
            return []

        model_to_use = gate_model or self.model_name
        schema = (
            GateBatchResult.model_json_schema()
            if hasattr(GateBatchResult, "model_json_schema")
            else GateBatchResult.schema()
        )

        messages = [
            {"role": "system", "content": _build_gate_system_prompt()},
            {"role": "user", "content": _build_batch_reviews_input_payload(review_texts)},
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "gate_reviews",
                    "description": "Return yes/no gate decisions for each review.",
                    "parameters": schema,
                },
            }
        ]
        tool_choice = {"type": "function", "function": {"name": "gate_reviews"}}

        try:
            response = call_groq_with_retry(
                self.client,
                model_to_use,
                messages,
                tools,
                tool_choice,
                **self._groq_call_kwargs(),
            )
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                logger.warning("Gate: no tool call returned. Passing all reviews through.")
                return [True] * len(review_texts)

            result = GateBatchResult.model_validate_json(tool_calls[0].function.arguments)

            if len(result.decisions) != len(review_texts):
                logger.warning(
                    f"Gate batch size mismatch (expected {len(review_texts)}, "
                    f"got {len(result.decisions)}). Passing all through as fallback."
                )
                return [True] * len(review_texts)

            decisions = [d == "yes" for d in result.decisions]
            passed = sum(decisions)
            logger.debug(
                f"Gate batch of {len(review_texts)}: {passed} pass, "
                f"{len(review_texts) - passed} reject."
            )
            return decisions

        except Exception as e:
            logger.warning(
                f"Gate analysis failed ({e}). Passing all {len(review_texts)} reviews through."
            )
            return [True] * len(review_texts)

    # -------------------------------------------------------------------------
    # Strategy 4 + 5 — Optimized Pipeline
    # -------------------------------------------------------------------------

    def process_reviews_optimized(
        self,
        df: pd.DataFrame,
        sample_size: int = 500,
        min_floor_sources: List[str] = None,
        gate_enabled: bool = True,
        gate_batch_size: int = 10,
        gate_model: str = None,
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Optimized Phase 2 pipeline combining Strategy 4 (Stratified Sampling)
        and Strategy 5 (Two-Stage Gate Funnel).

        Pipeline
        --------
        [S4] stratified_sample() selects a representative subset (~500 reviews).
             Minority sources (reddit, twitter, etc.) are fully guaranteed.
        [S5] Gate pass on sample: llama-3.1-8b-instant gives yes/no per review.
             - 'no' → auto-labelled neutral + all-None + Passive Listener (zero LLM cost)
             - 'yes' → full 7-dimension classification via existing batch logic
        Output: annotated_reviews.json (sample only) + sample_coverage.json.

        Note: Non-sampled reviews are not saved. The sample is the analytical
        universe for all downstream phases. Dashboard discloses coverage %.

        Parameters
        ----------
        df : pd.DataFrame
            Full reviews DataFrame from Phase 1.
        sample_size : int
            Target number of reviews to sample (default 500).
        min_floor_sources : List[str]
            Sources whose reviews are always fully included in the sample.
        gate_enabled : bool
            If False, skip gate and classify the entire sample directly (S4 only).
        gate_batch_size : int
            Reviews per gate LLM call (default 10; larger = fewer calls for cheap gate).
        gate_model : str, optional
            Groq model for gate calls (default: llama-3.1-8b-instant from config).

        Returns
        -------
        annotated_df : pd.DataFrame
            Annotated sample with all 7 classification columns.
        coverage : dict
            Coverage + LLM savings metadata (written to sample_coverage.json).
        """
        if min_floor_sources is None:
            min_floor_sources = ["reddit", "product_reviews", "spotify_community", "twitter"]

        if df.empty:
            logger.warning("Empty DataFrame passed to process_reviews_optimized. Returning empty.")
            return df, {}

        total_reviews = len(df)

        # ── Strategy 4: Stratified Sampling ──────────────────────────────────
        logger.info(
            f"[S4] Stratified sampling: target {sample_size} from {total_reviews} reviews..."
        )
        sampled_df, coverage = stratified_sample(df, sample_size, min_floor_sources)
        sampled_df = sampled_df.reset_index(drop=True)
        sampled_count = len(sampled_df)
        logger.info(
            f"[S4] Sample ready: {sampled_count} reviews ({coverage['coverage_pct']}% of total)."
        )

        results = [None] * sampled_count

        if gate_enabled:
            # ── Strategy 5: Two-Stage Gate ────────────────────────────────────
            logger.info(
                f"[S5] Gate pass: {sampled_count} reviews in batches of {gate_batch_size}, "
                f"model={gate_model or self.model_name}..."
            )
            gate_decisions: List[bool] = []

            for gate_start in range(0, sampled_count, gate_batch_size):
                gate_end = min(gate_start + gate_batch_size, sampled_count)
                gate_chunk_texts = [
                    str(sampled_df.iloc[i].get("text", "")).strip()
                    for i in range(gate_start, gate_end)
                ]
                chunk_decisions = self.analyze_gate_batch(
                    gate_chunk_texts, gate_model=gate_model
                )
                gate_decisions.extend(chunk_decisions)

            gate_passed_indices = [i for i, d in enumerate(gate_decisions) if d]
            gate_rejected_indices = [i for i, d in enumerate(gate_decisions) if not d]
            gate_passed = len(gate_passed_indices)
            gate_rejected = len(gate_rejected_indices)

            logger.info(
                f"[S5] Gate complete: {gate_passed} pass (full LLM), "
                f"{gate_rejected} reject (auto-labelled)."
            )

            # Auto-label gate-rejected reviews (neutral + all-None)
            for idx in gate_rejected_indices:
                results[idx] = self._neutral_analysis_dict()

            # Full 7-dimension classification for gate-passed reviews
            if gate_passed_indices:
                pass_texts = [
                    str(sampled_df.iloc[i].get("text", "")).strip()
                    for i in gate_passed_indices
                ]
                tpd_halt = False

                for chunk_start in range(0, gate_passed, self.batch_size):
                    chunk_end = min(chunk_start + self.batch_size, gate_passed)
                    chunk_texts = pass_texts[chunk_start:chunk_end]
                    chunk_global_indices = gate_passed_indices[chunk_start:chunk_end]

                    logger.info(
                        f"  Classifying {chunk_start + 1}–{chunk_end} of {gate_passed} "
                        "gate-passed reviews..."
                    )

                    success = False
                    try:
                        batch_analyses = self.analyze_batch_reviews(chunk_texts)
                        if len(batch_analyses) == len(chunk_texts):
                            for j, analysis in enumerate(batch_analyses):
                                results[chunk_global_indices[j]] = self._analysis_to_dict(analysis)
                            success = True
                        else:
                            logger.warning(
                                f"Batch mismatch (expected {len(chunk_texts)}, "
                                f"got {len(batch_analyses)}). Falling back to sequential."
                            )
                    except GroqTokenDailyLimitError:
                        logger.warning("TPD quota exhausted during optimized classification.")
                        tpd_halt = True
                    except Exception as e:
                        logger.warning(f"Batch failed: {e}. Falling back to sequential.")

                    if tpd_halt:
                        break

                    if not success:
                        for j, global_idx in enumerate(chunk_global_indices):
                            try:
                                analysis = self.analyze_single_review(chunk_texts[j])
                                results[global_idx] = self._analysis_to_dict(analysis)
                            except GroqTokenDailyLimitError:
                                logger.warning("TPD exhausted in sequential fallback.")
                                tpd_halt = True
                                break
                            except Exception as seq_err:
                                logger.error(
                                    f"Sequential fallback failed for index {global_idx}: {seq_err}"
                                )
                                results[global_idx] = self._neutral_analysis_dict()

                    if tpd_halt:
                        break

            # Fill any None left from TPD halt or edge cases
            for idx in range(sampled_count):
                if results[idx] is None:
                    results[idx] = self._neutral_analysis_dict()

            # LLM call accounting (ceiling division via -(-n//d) trick)
            gate_calls = -(-sampled_count // gate_batch_size)
            classify_calls = -(-gate_passed // self.batch_size) if gate_passed > 0 else 0
            llm_calls_made = gate_calls + classify_calls
            llm_calls_full = -(-total_reviews // self.batch_size)

        else:
            # Gate disabled: classify full sample directly (S4 only mode)
            logger.info(
                f"[S4] Gate disabled. Full classification on {sampled_count} reviews..."
            )
            tpd_halt = False

            for chunk_start in range(0, sampled_count, self.batch_size):
                chunk_end = min(chunk_start + self.batch_size, sampled_count)
                chunk_texts = [
                    str(sampled_df.iloc[i].get("text", "")).strip()
                    for i in range(chunk_start, chunk_end)
                ]
                logger.info(f"  Classifying {chunk_start + 1}–{chunk_end} of {sampled_count}...")

                success = False
                try:
                    batch_analyses = self.analyze_batch_reviews(chunk_texts)
                    if len(batch_analyses) == len(chunk_texts):
                        for j, analysis in enumerate(batch_analyses):
                            results[chunk_start + j] = self._analysis_to_dict(analysis)
                        success = True
                    else:
                        logger.warning("Batch mismatch. Falling back to sequential.")
                except GroqTokenDailyLimitError:
                    tpd_halt = True
                except Exception as e:
                    logger.warning(f"Batch failed: {e}. Sequential fallback.")

                if tpd_halt:
                    break

                if not success:
                    for j in range(len(chunk_texts)):
                        try:
                            analysis = self.analyze_single_review(chunk_texts[j])
                            results[chunk_start + j] = self._analysis_to_dict(analysis)
                        except GroqTokenDailyLimitError:
                            tpd_halt = True
                            break
                        except Exception as seq_err:
                            logger.error(f"Sequential fallback failed: {seq_err}")
                            results[chunk_start + j] = self._neutral_analysis_dict()

                if tpd_halt:
                    break

            for idx in range(sampled_count):
                if results[idx] is None:
                    results[idx] = self._neutral_analysis_dict()

            gate_passed = sampled_count
            gate_rejected = 0
            classify_calls = -(-sampled_count // self.batch_size)
            llm_calls_made = classify_calls
            llm_calls_full = -(-total_reviews // self.batch_size)

        # ── Finalize coverage metadata ─────────────────────────────────────────
        coverage.update({
            "gate_passed": gate_passed,
            "gate_rejected": gate_rejected,
            "llm_calls_made": llm_calls_made,
            "llm_calls_saved_vs_full": max(0, llm_calls_full - llm_calls_made),
        })

        # ── Save outputs ───────────────────────────────────────────────────────
        annotated_records = self._build_annotated_records(sampled_df, results)
        out_path = self._save_annotated_json(annotated_records)
        coverage_path = self._save_sample_coverage(coverage)

        logger.info(
            f"Optimized pipeline complete. {sampled_count}/{total_reviews} reviews annotated "
            f"({coverage['coverage_pct']}% coverage). "
            f"Gate: {gate_passed} passed, {gate_rejected} rejected. "
            f"LLM calls: {llm_calls_made} made, {coverage['llm_calls_saved_vs_full']} saved vs full. "
            f"Output → {out_path} | Coverage → {coverage_path}"
        )

        results_df = pd.DataFrame(results)
        annotated_df = pd.concat(
            [sampled_df.reset_index(drop=True), results_df.reset_index(drop=True)], axis=1
        )
        return annotated_df, coverage
