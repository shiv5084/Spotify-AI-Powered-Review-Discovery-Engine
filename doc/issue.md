llm we will use groq LLM_MODEL=llama-3.3-70b-versatile update its references everywhere
add Phase 0 — Project Scaffold & Environment Setup 

-phase 1 will not simulate scraping across channels and generate mock datasets
it will scrape reviews from real urls across different mentioned channels
-first update all the required url across different mentioned channels in phase1 in implementationplan.md for the product spotify  
Google Play Store 
Apple App Store Reviews
Reddit Discussions
Spotify Community Forums
X (Twitter) Conversations
1 Product review website and blog 

in each phase there will be run script like run_phase1.py under /src/script folder to verify the functionality of that phase ,update it in implementationplan.md for each phase
it is not a unit test or integration test, it will execute to run that phase in reality

first write down the tasks u will perform in each phase in implementationplan.md

why reviews.csv got generated in phase2 , processed files   

in phase1, clean the data which will contain, remove emojis,deduplication,remove sentences with less than 5 words, spam detection
update these tasks in implementationplan.md for phase1

why there is only reviews for app_store in phase1.py output?
-ensure to scrape reviews from all the mentioned urls and store the raw reviews separately then combined all the revies and store that separately before cleaned reviews to store in reviews.csv
-and remove any fallback cache reviews, only real runtime reviews are required
-dont run and unit or integration test without asking me, run only run script to verify the functionality of that phase

use google-play-scraper for Google Play Store Reviews
Playwright for Spotify Community Forums,X/Twitter via Nitter,Trustpilot Reviews
**Anti-Bot Considerations:**
- Random delays between scrolls (1–3 seconds)
- Realistic User-Agent headers
- Headless mode with stealth settings
- Rate limiting to avoid IP blocks

https://x.com/Spotify

in reviews.csv why only app store and google play store reviews are present it sud contain revies from all sources and final cleaned data

why task 1 in phase 2 conatins schemas for only sentiment, pain points, recommendation complaints, user segments. when objective is Parsing each review for all these: sentiment, discovery pain points, recommendation frustrations, listening goals/intentions, repeat-listening signals, unmet needs, and segment classification.

in phase 2 ,
each review for: sentiment, discovery pain points, recommendation frustrations, listening goals/intentions, repeat-listening signals, unmet needs, and segment classification from reviews.csv shoud be parsed as an input to llm and not any mock data and llm should return a json format response

//instead of annotated_reviews.csv , llm output response sud be saved as annotated_reviews.json in json format

when running phase 2 getting rate limit error
can you fix it ,also i want system prompt as input to llm sud have proper input format and output format as json which will indicate llm about what the input and output response should be 
i need to run run script for phase2 for sample size of 300 reviews but should not get any rate limit error

check if anything is pending then implement phase 4 as per implementationplan.md

INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12898/12000). Pausing 49.9s...
tions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12453/12000). Pausing 1.5s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 40.
INFO:src.processing.review_processor:Analyzing batch reviews 41 to 45/200...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12342/12000). Pausing 0.8s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 45.
INFO:src.processing.review_processor:Analyzing batch reviews 46 to 50/200...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12357/12000). Pausing 48.7s...

in main.py , make default=200 to 100 , i want when pipeline is triggered then --num-records" default to 100






Initializing pipeline process...
Pipeline started successfully.
INFO:PRDE-Orchestrator:Starting complete end-to-end PRDE pipeline execution...
INFO:PRDE-Orchestrator:Executing Phase 1: Ingestion & PII Scrubbing...
INFO:src.ingestion.pii_scrubber:PIIScrubber initialised (regex-only mode).
INFO:src.ingestion.ingestor:Starting Multi-Source Review Ingestion...
INFO:src.ingestion.scrapers:Scraping App Store reviews page 1 from: https://itunes.apple.com/us/rss/customerreviews/page=1/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 2 from: https://itunes.apple.com/us/rss/customerreviews/page=2/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 3 from: https://itunes.apple.com/us/rss/customerreviews/page=3/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 4 from: https://itunes.apple.com/us/rss/customerreviews/page=4/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 5 from: https://itunes.apple.com/us/rss/customerreviews/page=5/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 6 from: https://itunes.apple.com/us/rss/customerreviews/page=6/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 7 from: https://itunes.apple.com/us/rss/customerreviews/page=7/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 8 from: https://itunes.apple.com/us/rss/customerreviews/page=8/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 9 from: https://itunes.apple.com/us/rss/customerreviews/page=9/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping App Store reviews page 10 from: https://itunes.apple.com/us/rss/customerreviews/page=10/id=324684580/sortBy=mostRecent/json
INFO:src.ingestion.scrapers:Scraping Google Play Store reviews using google-play-scraper package...
INFO:src.ingestion.scrapers:Successfully scraped 500 reviews using google-play-scraper
INFO:src.ingestion.scrapers:Scraping Reddit discussions from: https://www.reddit.com/r/spotify/new.json
WARNING:src.ingestion.scrapers:Error scraping Reddit JSON: HTTP Error 403: Blocked
INFO:src.ingestion.scrapers:Falling back to Reddit RSS feed: https://www.reddit.com/r/spotify/new/.rss
INFO:src.ingestion.scrapers:Successfully scraped 25 posts from Reddit RSS
WARNING:src.ingestion.scrapers:Playwright scraper error on https://community.spotify.com/t5/Live-Ideas/idb-p/ideas_live: BrowserType.launch: Executable doesn't exist at /opt/render/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     playwright install                                     ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
INFO:src.ingestion.scrapers:Scraping Twitter conversations from: https://x.com/Spotify
WARNING:src.ingestion.scrapers:Playwright scraper error on https://x.com/Spotify: BrowserType.launch: Executable doesn't exist at /opt/render/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     playwright install                                     ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
WARNING:src.ingestion.scrapers:Playwright scraper error on https://www.trustpilot.com/review/www.spotify.com: BrowserType.launch: Executable doesn't exist at /opt/render/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     playwright install                                     ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
INFO:src.ingestion.scrapers:Trustpilot returned empty. Falling back to review blog: https://www.musicgateway.com/blog/music-industry/music-streaming/spotify-review
INFO:src.ingestion.ingestor:Saved raw channel reviews to: data/raw/raw_apple_app_store.csv (500 rows)
INFO:src.ingestion.ingestor:Saved raw channel reviews to: data/raw/raw_google_play.csv (500 rows)
INFO:src.ingestion.ingestor:Saved raw channel reviews to: data/raw/raw_reddit.csv (25 rows)
INFO:src.ingestion.ingestor:Saved raw channel reviews to: data/raw/raw_spotify_community.csv (0 rows)
INFO:src.ingestion.ingestor:Saved raw channel reviews to: data/raw/raw_twitter.csv (0 rows)
INFO:src.ingestion.ingestor:Saved raw channel reviews to: data/raw/raw_trustpilot.csv (0 rows)
INFO:src.ingestion.ingestor:Combined raw reviews saved to: data/raw/raw_reviews.csv (1025 rows)
INFO:src.ingestion.ingestor:Skipping record 22: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 40: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 47: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 57: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 61: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 94: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 107: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 129: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 130: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 154: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 158: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 166: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 168: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 169: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 182: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 196: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 232: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 235: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 239: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 241: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 261: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 291: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 298: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 330: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 336: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 338: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 340: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 343: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 351: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 360: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 369: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 384: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 393: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 396: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 401: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 403: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 415: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 447: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 449: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 452: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 457: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 461: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 463: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 488: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 514: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 534: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 556: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 580: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 605: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 619: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 663: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 741: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 750: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 757: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 772: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 791: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 825: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 834: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 847: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 869: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 893: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 911: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 940: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 953: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 989: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 992: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 998: empty text after sentence length check.
INFO:src.ingestion.ingestor:Skipping record 1018: classified as spam.
INFO:src.ingestion.ingestor:Skipping record 1021: classified as spam.
INFO:src.ingestion.ingestor:Processed, scrubbed reviews saved to: data/processed/reviews.csv (100 rows)
INFO:PRDE-Orchestrator:Phase 1 completed successfully. Ingested & processed 100 records.
INFO:PRDE-Orchestrator:Executing Phase 2: Theme Extraction & Metric Parsing...
INFO:src.processing.llm_client:GroqClient successfully initialized using model llama-3.3-70b-versatile.
INFO:src.processing.review_processor:Processing 100 reviews in batches of 5 using Groq model llama-3.3-70b-versatile...
INFO:src.processing.review_processor:Analyzing batch reviews 1 to 5/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 5.
INFO:src.processing.review_processor:Analyzing batch reviews 6 to 10/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 10.
INFO:src.processing.review_processor:Analyzing batch reviews 11 to 15/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 15.
INFO:src.processing.review_processor:Analyzing batch reviews 16 to 20/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 20.
INFO:src.processing.review_processor:Analyzing batch reviews 21 to 25/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12429/12000). Pausing 49.5s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 25.
INFO:src.processing.review_processor:Analyzing batch reviews 26 to 30/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12551/12000). Pausing 1.4s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 30.
INFO:src.processing.review_processor:Analyzing batch reviews 31 to 35/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12675/12000). Pausing 0.9s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 35.
INFO:src.processing.review_processor:Analyzing batch reviews 36 to 40/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12829/12000). Pausing 1.6s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 40.
INFO:src.processing.review_processor:Analyzing batch reviews 41 to 45/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12839/12000). Pausing 1.4s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 45.
INFO:src.processing.review_processor:Analyzing batch reviews 46 to 50/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12893/12000). Pausing 49.2s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 50.
INFO:src.processing.review_processor:Analyzing batch reviews 51 to 55/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12926/12000). Pausing 1.5s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 55.
INFO:src.processing.review_processor:Analyzing batch reviews 56 to 60/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12738/12000). Pausing 2.5s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 60.
INFO:src.processing.review_processor:Analyzing batch reviews 61 to 65/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12649/12000). Pausing 1.9s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 65.
INFO:src.processing.review_processor:Analyzing batch reviews 66 to 70/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12527/12000). Pausing 1.2s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 70.
INFO:src.processing.review_processor:Analyzing batch reviews 71 to 75/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.processing.review_processor:Approaching TPM budget (12509/12000). Pausing 48.5s...
INFO:src.processing.review_processor:Checkpoint saved after batch ending at review 75.
INFO:src.processing.review_processor:Analyzing batch reviews 76 to 80/100...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.processing.review_processor:TPD quota exhausted mid-batch. Proceeding with partial results for Phase 2.
INFO:src.processing.review_processor:Successfully processed 100 reviews. Output saved to /opt/render/project/src/data/processed/annotated_reviews.json.
INFO:PRDE-Orchestrator:Phase 2 completed successfully. Annotated 100 records.
INFO:PRDE-Orchestrator:Executing Phase 3: Analytical Theme Discovery & Clustering...
INFO:src.processing.llm_client:GroqClient successfully initialized using model llama-3.3-70b-versatile.
INFO:src.analysis.theme_discoverer:Loaded 100 annotated reviews for cluster analysis...
INFO:src.analysis.theme_discoverer:Q1: Sending 14 reviews to LLM for theme discovery...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:src.analysis.theme_discoverer:Q2: Sending 18 reviews to LLM for theme discovery...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.analysis.theme_discoverer:Q2 LLM theme discovery failed: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to deterministic local rule-based grouping.
INFO:src.analysis.theme_discoverer:Q3: Sending 40 reviews to LLM for theme discovery...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.analysis.theme_discoverer:Q3 LLM theme discovery failed: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to deterministic local rule-based grouping.
INFO:src.analysis.theme_discoverer:Q4: Sending 27 reviews to LLM for theme discovery...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.analysis.theme_discoverer:Q4 LLM theme discovery failed: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to deterministic local rule-based grouping.
INFO:src.analysis.theme_discoverer:Q5: Querying LLM for segment summary of 'Casual Listener' with 15 reviews...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
ERROR:src.analysis.theme_discoverer:Failed to generate segment summary for 'Casual Listener' via LLM: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default list values.
INFO:src.analysis.theme_discoverer:Q5: Querying LLM for segment summary of 'Passive Listener' with 4 reviews...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
ERROR:src.analysis.theme_discoverer:Failed to generate segment summary for 'Passive Listener' via LLM: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default list values.
INFO:src.analysis.theme_discoverer:Q5: Querying LLM for segment summary of 'Music Explorer' with 8 reviews...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
ERROR:src.analysis.theme_discoverer:Failed to generate segment summary for 'Music Explorer' via LLM: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default list values.
INFO:src.analysis.theme_discoverer:Q5: Querying LLM for segment summary of 'Trend Follower' with 1 reviews...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
ERROR:src.analysis.theme_discoverer:Failed to generate segment summary for 'Trend Follower' via LLM: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default list values.
INFO:src.analysis.theme_discoverer:Q5: Querying LLM for segment summary of 'Playlist Collector' with 2 reviews...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
ERROR:src.analysis.theme_discoverer:Failed to generate segment summary for 'Playlist Collector' via LLM: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default list values.
INFO:src.analysis.theme_discoverer:Q5: Querying LLM for segment summary of 'Power User' with 4 reviews...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
ERROR:src.analysis.theme_discoverer:Failed to generate segment summary for 'Power User' via LLM: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default list values.
INFO:src.analysis.theme_discoverer:Q6: Sending 22 reviews to LLM for theme discovery...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.analysis.theme_discoverer:Q6 LLM theme discovery failed: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to deterministic local rule-based grouping.
INFO:src.analysis.theme_discoverer:Analysis results saved successfully to data/processed/analysis_results.json
INFO:PRDE-Orchestrator:Phase 3 completed successfully. Cluster themes saved.
INFO:PRDE-Orchestrator:Executing Phase 4: Pulse Note Generation & JSON Export...
INFO:PRDE-Orchestrator:Deleted existing Phase 4 output file: data/dashboard_data.json
INFO:src.processing.llm_client:GroqClient successfully initialized using model llama-3.3-70b-versatile.
INFO:src.reporting.pulse_generator:Querying LLM for Top 3 Product Opportunities...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.reporting.pulse_generator:Opportunities LLM call failed: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default pre-written opportunities.
INFO:src.reporting.pulse_generator:Compiled draft pulse note has 447 words.
INFO:src.reporting.pulse_generator:Pulse note written successfully to: data/weekly_pulse_note.md
INFO:src.reporting.pulse_generator:Querying LLM for Top 3 Product Opportunities...
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
ERROR:src.processing.review_processor:Groq daily token quota (TPD) exhausted. No further API calls can succeed until midnight UTC. Aborting Phase 2.
WARNING:src.reporting.pulse_generator:Opportunities LLM call failed: Groq tokens-per-day limit reached. Try again after midnight UTC.. Falling back to default pre-written opportunities.
INFO:src.reporting.json_exporter:Dashboard data exported successfully to: data/dashboard_data.json
INFO:src.reporting.json_exporter:Synchronized dashboard data to: /opt/render/project/src/frontend/public/dashboard_data.json
INFO:PRDE-Orchestrator:Phase 4 completed successfully. Markdown and JSON reports generated.
INFO:PRDE-Orchestrator:E2E pipeline execution completed successfully.
Pipeline finished successfully with exit code 0.
Pipeline completed successfully! Dashboard data updated.

fix below issues
-why raw_reviews.csv has got only 550 reviews whr it is designed to scrape more than thousand reviews
-why ### 6. Top 3 Unmet Needs in weekly_pulse_note.md is empty?
-change the Pulse Note Length** | Strict limit of **≤ 450 words to ≤ 550 and ensure there is no truncation issues
update accordingly every whr, its references and dependencies in docs, code,files, start from doc  then phase 1 and others
-why in dashboard_data.json under /data folder all metrics are empty
is it not used in the project?

-remove Deduplicated Fallbacks from README.md
-analyze and update System Overview & Architecture in README.md as per llm_optimization.md,implementationplan.md, and actual implementation in backend code

u were working on below tasks finish it
-is severity ranking implemented ? why it is not shown in 5. Top 3 Underserved User Segments?
below task is not req leave it for now
- in 6. Top 3 Unmet Needs , put one real review quote in short for each Unmet Needs
-dont make any changes,1st tell me ur implementation plan ,wht changes u will do 

implement as per temporary Implementation Plan Optimizing Review Analysis Reports 
ensure existing functionality sud not break

