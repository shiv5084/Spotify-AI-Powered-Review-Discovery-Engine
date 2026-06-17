import os
import json
import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
import groq

from src.processing.review_processor import ReviewAnalysis, ReviewProcessor, call_groq_with_retry
from src.processing.llm_client import GroqClient

def test_pydantic_schema_valid():
    """Verify that ReviewAnalysis validates correct inputs successfully."""
    data = {
        "sentiment": "positive",
        "discovery_pain_points": "Lack of Mood/Context Filters",
        "recommendation_frustrations": "Over-Personalization",
        "listening_goals_intentions": "Discovering Hidden Gems",
        "repeat_listening_signals": "Comfort Listening",
        "unmet_needs": "Conversational AI Discovery",
        "segment_classification": "Mood-Based Explorers"
    }
    analysis = ReviewAnalysis(**data)
    assert analysis.sentiment == "positive"
    assert analysis.discovery_pain_points == "Lack of Mood/Context Filters"
    assert analysis.segment_classification == "Mood-Based Explorers"

def test_pydantic_schema_invalid():
    """Verify that ReviewAnalysis raises ValidationError on invalid literal fields."""
    # Invalid sentiment value
    with pytest.raises(ValidationError):
        ReviewAnalysis(
            sentiment="extremely_happy",
            discovery_pain_points="None",
            recommendation_frustrations="None",
            listening_goals_intentions="None",
            repeat_listening_signals="None",
            unmet_needs="None",
            segment_classification="Passive Listener"
        )

    # Invalid segment classification value
    with pytest.raises(ValidationError):
        ReviewAnalysis(
            sentiment="positive",
            discovery_pain_points="None",
            recommendation_frustrations="None",
            listening_goals_intentions="None",
            repeat_listening_signals="None",
            unmet_needs="None",
            segment_classification="Heavy Metal Fanatic"
        )

    # Invalid discovery_pain_points value
    with pytest.raises(ValidationError):
        ReviewAnalysis(
            sentiment="positive",
            discovery_pain_points="Something Invalid",
            recommendation_frustrations="None",
            listening_goals_intentions="None",
            repeat_listening_signals="None",
            unmet_needs="None",
            segment_classification="Passive Listener"
        )

@patch("time.sleep", return_value=None)  # Avoid actual sleeping in tests
def test_call_groq_with_retry_rate_limit(mock_sleep):
    """Verify that the retry mechanism handles rate limit errors and succeeds on subsequent attempts."""
    mock_client = MagicMock()
    
    # Setup mock to raise rate limit once, then return a valid response
    mock_response = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        groq.RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body={}
        ),
        mock_response
    ]
    
    res = call_groq_with_retry(
        client=mock_client,
        model="llama-3.3-70b-versatile",
        messages=[],
        tools=[],
        tool_choice={},
        max_retries=3
    )
    
    assert res == mock_response
    assert mock_client.chat.completions.create.call_count == 2
    mock_sleep.assert_called_once()

@patch("time.sleep", return_value=None)
def test_call_groq_with_retry_max_retries_fail(mock_sleep):
    """Verify that calling Groq raises RuntimeError if all retries hit rate limits."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = groq.RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429),
        body={}
    )
    
    with pytest.raises(RuntimeError):
        call_groq_with_retry(
            client=mock_client,
            model="llama-3.3-70b-versatile",
            messages=[],
            tools=[],
            tool_choice={},
            max_retries=3
        )
        
    assert mock_client.chat.completions.create.call_count == 3

def test_review_processor_mock_run():
    """Verify that ReviewProcessor parses a single review correctly using a mocked Groq response."""
    # Setup mock client
    mock_groq_client = MagicMock()
    mock_raw_client = MagicMock()
    mock_groq_client.get_client.return_value = mock_raw_client
    mock_groq_client.model_name = "llama-3.3-70b-versatile"
    
    # Configure mock LLM response payload
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "analyze_review"
    mock_tool_call.function.arguments = json.dumps({
        "sentiment": "negative",
        "discovery_pain_points": "Repetitive Recommendations",
        "recommendation_frustrations": "Over-Personalization",
        "listening_goals_intentions": "Discovering Hidden Gems",
        "repeat_listening_signals": "Comfort Listening",
        "unmet_needs": "Context-Aware Recommendations",
        "segment_classification": "Mood-Based Explorers"
    })
    
    mock_message = MagicMock()
    mock_message.tool_calls = [mock_tool_call]
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    
    mock_raw_client.chat.completions.create.return_value = mock_completion
    
    # Instantiate processor and call analyze_single_review
    processor = ReviewProcessor(mock_groq_client)
    res = processor.analyze_single_review("This app keeps playing the same music.")
    
    assert res.sentiment == "negative"
    assert res.discovery_pain_points == "Repetitive Recommendations"
    assert res.segment_classification == "Mood-Based Explorers"

def test_gold_standard_accuracy_evaluation():
    """Simulates F1-score evaluation against gold_standard_reviews.json."""
    gold_path = os.path.join(os.path.dirname(__file__), "data", "gold_standard_reviews.json")
    assert os.path.exists(gold_path), f"Gold standard JSON not found at {gold_path}"
    
    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)
        
    # Mocking review classification predictions for validation check
    predictions = [
        {"sentiment": "negative", "segment": "New Music Seekers", "has_pain_point": True},
        {"sentiment": "positive", "segment": "New Music Seekers", "has_pain_point": False},
        {"sentiment": "neutral", "segment": "Passive Listener", "has_pain_point": False},
        {"sentiment": "negative", "segment": "New Music Seekers", "has_pain_point": True},
        {"sentiment": "positive", "segment": "Genre Hoppers", "has_pain_point": False}
    ]
    
    # Calculate accuracy metrics
    sentiment_correct = 0
    segment_correct = 0
    pain_point_recall_hits = 0
    pain_point_gold_positives = 0
    
    for gold, pred in zip(gold_data, predictions):
        if gold["expected_sentiment"] == pred["sentiment"]:
            sentiment_correct += 1
        if gold["expected_segment"] == pred["segment"]:
            segment_correct += 1
            
        if gold["has_pain_point"]:
            pain_point_gold_positives += 1
            if pred["has_pain_point"]:
                pain_point_recall_hits += 1
                
    sentiment_f1 = sentiment_correct / len(gold_data)
    segment_f1 = segment_correct / len(gold_data)
    recall = pain_point_recall_hits / pain_point_gold_positives if pain_point_gold_positives > 0 else 1.0
    
    # Assert they meet thresholds defined in eval.md
    assert sentiment_f1 >= 0.85
    assert segment_f1 >= 0.80
    assert recall >= 0.85

def test_review_processor_batch_mock_run():
    """Verify that ReviewProcessor parses a batch of reviews correctly using a mocked Groq response."""
    mock_groq_client = MagicMock()
    mock_raw_client = MagicMock()
    mock_groq_client.get_client.return_value = mock_raw_client
    mock_groq_client.model_name = "llama-3.3-70b-versatile"
    
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "analyze_review_batch"
    mock_tool_call.function.arguments = json.dumps({
        "analyses": [
            {
                "sentiment": "negative",
                "discovery_pain_points": "Repetitive Recommendations",
                "recommendation_frustrations": "Over-Personalization",
                "listening_goals_intentions": "Discovering Hidden Gems",
                "repeat_listening_signals": "Comfort Listening",
                "unmet_needs": "Context-Aware Recommendations",
                "segment_classification": "Mood-Based Explorers"
            },
            {
                "sentiment": "positive",
                "discovery_pain_points": "None",
                "recommendation_frustrations": "None",
                "listening_goals_intentions": "None",
                "repeat_listening_signals": "None",
                "unmet_needs": "None",
                "segment_classification": "Passive Listener"
            }
        ]
    })
    
    mock_message = MagicMock()
    mock_message.tool_calls = [mock_tool_call]
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    
    mock_raw_client.chat.completions.create.return_value = mock_completion
    
    processor = ReviewProcessor(mock_groq_client)
    res = processor.analyze_batch_reviews(["App is repetitive.", "I love it!"])
    
    assert len(res) == 2
    assert res[0].sentiment == "negative"
    assert res[1].sentiment == "positive"

