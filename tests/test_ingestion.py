import os
import pandas as pd
import pytest
from src.ingestion.pii_scrubber import PIIScrubber
from src.ingestion.ingestor import IngestionManager

def test_pii_scrubber_regex():
    scrubber = PIIScrubber()
    
    # Test Email Scrubbing
    assert scrubber.scrub("test email: john.doe@spotify.com") == "test email: [EMAIL]"
    
    # Test IP Address Scrubbing
    assert scrubber.scrub("my IP is 192.168.1.1") == "my IP is [IP_ADDRESS]"
    
    # Test Phone Number Scrubbing
    assert scrubber.scrub("call 555-123-4567 today") == "call [PHONE_NUMBER] today"
    
    # Test Reddit Handle Scrubbing
    assert scrubber.scrub("post by u/music_fan") == "post by [USER_HANDLE]"
    assert scrubber.scrub("check /u/rock_on") == "check [USER_HANDLE]"
    
    # Test Twitter Handle Scrubbing
    assert scrubber.scrub("ping @spotify_help on twitter") == "ping [USER_HANDLE] on twitter"

def test_pii_scrubber_presidio():
    scrubber = PIIScrubber()
    # If Presidio is active, test name scrubbing
    if scrubber.presidio_available:
        text = "Hello, my name is John Smith and my email is john@smith.org"
        scrubbed = scrubber.scrub(text)
        # Verify name is redacted and email is masked
        assert "[REDACTED_NAME]" in scrubbed
        assert "[EMAIL]" in scrubbed
    else:
        # If presidio falls back, regex must still mask email
        assert scrubber.scrub("john@smith.org") == "[EMAIL]"

def test_ingestion_manager_normalization(tmp_path):
    # Setup paths inside temp directory
    raw_dir = os.path.join(tmp_path, "raw")
    processed_dir = os.path.join(tmp_path, "processed")
    
    manager = IngestionManager(raw_dir=raw_dir, processed_dir=processed_dir)
    df = manager.run(num_records=10)
    
    # Assert output shape is within bounds (resilient to spam/short filters)
    assert not df.empty
    assert 0 < len(df) <= 10
    
    # Assert columns match schema
    expected_cols = {"source", "date", "title", "text", "rating", "engagement"}
    assert set(df.columns) == expected_cols
    
    # Verify raw and processed file creations
    assert os.path.exists(os.path.join(raw_dir, "raw_reviews.csv"))
    assert os.path.exists(os.path.join(processed_dir, "reviews.csv"))

def test_normalization_formats(tmp_path):
    raw_dir = os.path.join(tmp_path, "raw")
    processed_dir = os.path.join(tmp_path, "processed")
    
    manager = IngestionManager(raw_dir=raw_dir, processed_dir=processed_dir)
    df = manager.run(num_records=5)
    
    assert 0 < len(df) <= 5
    for _, row in df.iterrows():
        # Check source is string
        assert isinstance(row["source"], str)
        # Check date follows standard YYYY-MM-DD
        assert len(row["date"]) == 10
        assert row["date"][4] == "-"
        assert row["date"][7] == "-"
        # Check rating is numeric or NA
        assert pd.isna(row["rating"]) or isinstance(row["rating"], (int, float))
        # Check engagement is numeric or NA
        assert pd.isna(row["engagement"]) or isinstance(row["engagement"], (int, float))

def test_data_cleaning_logic():
    from src.ingestion.ingestor import strip_emojis, clean_sentence_length, is_spam
    
    # 1. Test Emoji Removal
    assert strip_emojis("Love this app! 😊🎸🔥") == "Love this app! "
    
    # 2. Test Sentence Length check (removes sentences with less than 5 words)
    text_with_short_sentences = "This app is really good. But repeating loop. I like the music discovery feature."
    cleaned = clean_sentence_length(text_with_short_sentences)
    assert "This app is really good." in cleaned
    assert "I like the music discovery feature." in cleaned
    assert "But repeating loop." not in cleaned
    
    # 3. Test Spam Check
    assert is_spam("Buy now click this link to win money!") is True
    assert is_spam("aaaaaa and other repeating characters") is True
    assert is_spam("normal review with a lot of details about music recommendation loops") is False
