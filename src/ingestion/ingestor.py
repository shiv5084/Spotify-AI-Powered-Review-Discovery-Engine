import os
import re
import pandas as pd
import logging
from src.ingestion.scrapers import PublicReviewScraper
from src.ingestion.pii_scrubber import PIIScrubber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def strip_emojis(text: str) -> str:
    """Remove emojis and non-standard symbols."""
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]|[\u2600-\u27ff]|[\u3000-\u303f]|[\u2000-\u206f]',
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def clean_sentence_length(text: str) -> str:
    """Remove sentences containing less than 5 words."""
    # Split text by sentence boundaries (.!? followed by space)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean_sentences = []
    for sentence in sentences:
        words = [w for w in sentence.split() if w.strip()]
        if len(words) >= 5:
            clean_sentences.append(sentence)
    return " ".join(clean_sentences)

def is_spam(text: str) -> bool:
    """Detect if review is spam, contains excessive character repetitions or ads."""
    text_lower = text.lower()
    spam_keywords = ["buy now", "click link", "promo code", "make money", "discount code", "advertisement"]
    if any(kw in text_lower for kw in spam_keywords):
        return True
    # 5+ repeating characters like aaaaa or !!!!!
    if re.search(r'(.)\1{4,}', text_lower):
        return True
    # Three repeating words consecutively
    words = text_lower.split()
    for i in range(len(words) - 2):
        if words[i] == words[i+1] == words[i+2]:
            return True
    return False

class IngestionManager:
    """Orchestrates data collection, cleaning, local PII scrubbing, and schema normalization."""

    def __init__(self, raw_dir: str = "data/raw", processed_dir: str = "data/processed"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        
        # Ensure directories exist
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        self.scraper = PublicReviewScraper()
        self.scrubber = PIIScrubber()

    def run(self, num_records: int = 100) -> pd.DataFrame:
        """Execute the ingestion workflow: Scrape per channel -> Save individually -> Combine -> Save combined -> Clean & Scrub -> Save Processed."""
        logger.info("Starting Multi-Source Review Ingestion...")
        
        # 1. Scrape each channel individually
        app_store = self.scraper.scrape_app_store()
        google_play = self.scraper.scrape_google_play()
        reddit = self.scraper.scrape_reddit()
        spotify_community = self.scraper.scrape_spotify_community()
        twitter = self.scraper.scrape_twitter()
        trustpilot = self.scraper.scrape_trustpilot()
        
        # 2. Store individual raw reviews files under data/raw/
        df_app_store = self._save_raw_channel(app_store, "raw_apple_app_store.csv")
        df_google_play = self._save_raw_channel(google_play, "raw_google_play.csv")
        df_reddit = self._save_raw_channel(reddit, "raw_reddit.csv")
        df_spotify_community = self._save_raw_channel(spotify_community, "raw_spotify_community.csv")
        df_twitter = self._save_raw_channel(twitter, "raw_twitter.csv")
        df_trustpilot = self._save_raw_channel(trustpilot, "raw_trustpilot.csv")
        
        # 3. Combine all raw reviews
        dfs = [df_app_store, df_google_play, df_reddit, df_spotify_community, df_twitter, df_trustpilot]
        raw_df = pd.concat(dfs, ignore_index=True)
        
        # Save combined raw reviews CSV (contains ALL raw reviews from all channels)
        raw_path = os.path.join(self.raw_dir, "raw_reviews.csv")
        raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")
        logger.info(f"Combined raw reviews saved to: {raw_path} ({len(raw_df)} rows)")
        
        # Process all scraped raw reviews to ensure representation of all sources
        processing_df = raw_df
        
        # 4. Normalize and clean data fields
        processed_records = []
        for idx, row in processing_df.iterrows():
            # Get values safely
            source = str(row["source"]).strip()
            date = str(row["date"]).strip()
            title = str(row["title"]).strip() if pd.notna(row["title"]) else ""
            raw_text = str(row["text"]).strip()
            
            # Extract numbers safely
            rating = int(row["rating"]) if pd.notna(row["rating"]) and row["rating"] is not None else None
            engagement = int(row["engagement"]) if pd.notna(row["engagement"]) and row["engagement"] is not None else None
            
            # --- Data Cleaning ---
            # A. Emoji Removal
            cleaned_text = strip_emojis(raw_text)
            cleaned_title = strip_emojis(title)
            
            # B. Sentence Length Filter (remove sentences with less than 5 words)
            cleaned_text = clean_sentence_length(cleaned_text)
            
            # C. Spam Detection
            if is_spam(cleaned_text) or is_spam(cleaned_title):
                logger.info(f"Skipping record {idx}: classified as spam.")
                continue
                
            # Skip if text is empty after sentence filtering
            if not cleaned_text.strip():
                logger.info(f"Skipping record {idx}: empty text after sentence length check.")
                continue
            
            # 5. Apply local PII scrubbing on text fields
            scrubbed_text = self.scrubber.scrub(cleaned_text)
            scrubbed_title = self.scrubber.scrub(cleaned_title)
            
            processed_records.append({
                "source": source,
                "date": date,
                "title": scrubbed_title,
                "text": scrubbed_text,
                "rating": rating,
                "engagement": engagement
            })
            
        processed_df = pd.DataFrame(processed_records)
        
        # D. Deduplication
        if not processed_df.empty:
            processed_df.drop_duplicates(subset=["text"], keep="first", inplace=True)
            processed_df.reset_index(drop=True, inplace=True)
        
        # Slice to respect num_records limit if specified
        if num_records is not None and len(processed_df) > num_records:
            processed_df = processed_df.head(num_records)

        # Save processed CSV
        processed_path = os.path.join(self.processed_dir, "reviews.csv")
        processed_df.to_csv(processed_path, index=False, encoding="utf-8-sig")
        logger.info(f"Processed, scrubbed reviews saved to: {processed_path} ({len(processed_df)} rows)")
        
        return processed_df

    def _save_raw_channel(self, reviews: list, filename: str) -> pd.DataFrame:
        """Helper to format and save a raw channel's scraped reviews list to CSV."""
        cols = ["source", "date", "title", "text", "rating", "engagement"]
        df = pd.DataFrame(reviews)
        if df.empty:
            df = pd.DataFrame(columns=cols)
        else:
            # Ensure all unified columns exist
            for col in cols:
                if col not in df.columns:
                    df[col] = None
            df = df[cols]
        path = os.path.join(self.raw_dir, filename)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"Saved raw channel reviews to: {path} ({len(df)} rows)")
        return df

if __name__ == "__main__":
    manager = IngestionManager()
    manager.run(150)
