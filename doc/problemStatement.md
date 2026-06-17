# Spotify — Automated Weekly Product Review Pulse
## AI-Powered Review Discovery Engine (PRDE)

> [!NOTE]
> **Business Context**  
> Spotify has acquired millions of users and built one of the world's most sophisticated recommendation systems. However, a significant percentage of listening still comes from repeat playlists, familiar artists, and previously discovered tracks. This limits meaningful music discovery and perpetuates repetitive listening behaviors.  
> Before proposing any product solution, Spotify needs a scalable, AI-powered system capable of analyzing large volumes of user feedback across multiple channels to understand why discovery is failing for certain users.

---

## Goal

Build an **AI-Powered Review Discovery Engine (PRDE)** that continuously analyzes user feedback and conversations at scale to identify:
- **Music discovery pain points** and barriers.
- **Recommendation dissatisfaction** patterns.
- **Repeat-listening behaviors** and their underlying drivers.
- **User discovery intentions** and listening goals.
- **Segment-specific** discovery challenges.
- **Emerging unmet needs** that represent product opportunities.

---

## Data Sources

The system must ingest and analyze unstructured feedback from the following channels:
*   **App Stores:** Google Play Store & Apple App Store Reviews
*   **Forums:** Reddit Discussions & Spotify Community Forums
*   **Social Media:** X (Twitter) Conversations
*   **Web:** Product review websites and blogs

---

## Core Business Questions

The engine must be designed to answer the following six core questions:
1. **Why** do users struggle to discover new music?
2. **What** are the most common frustrations with recommendations?
3. **What** listening behaviors or goals are users trying to achieve?
4. **What** causes users to repeatedly listen to the same content?
5. **Which** user segments experience distinct discovery challenges?
6. **What** unmet needs emerge consistently across reviews?

---

## Technical Specifications & Requirements

### 1. Multi-Source Review Ingestion

Collect, ingest, and normalize reviews from the **last 8–12 weeks** from publicly available review sources.

#### Schema Specifications
For each record ingested, the system must capture:
- `source`: The origin platform (e.g., `reddit`, `play_store`).
- `date`: Timestamp/date of the post.
- `title`: Title of the review/post (if available).
- `text`: The raw text content of the review/post.
- `rating`: Rating score (1-5), if applicable.
- `engagement`: Upvotes, retweets, or engagement metrics, if applicable.

> [!IMPORTANT]
> **Compliance & Ingestion Constraints**
> - **Public Data Only:** Only use publicly available datasets or APIs.
> - **No Authenticated Scraping:** Do not scrape behind login walls or authenticate with user accounts.
> - **Zero PII (Personally Identifiable Information):** Strip all usernames, emails, IP addresses, device IDs, or other identifiable information *before* processing.
> - **Normalization & Storage:** Normalize the ingested data into a unified schema and save it as a structured CSV file.
> - **Data Cleaning:** Clean the data during ingestion:
>   - **Remove Emojis:** Strip out all emojis and special non-text symbols from review title and text fields.
>   - **Deduplication:** Filter out duplicate records based on text matching.
>   - **Sentence Length Filter:** Exclude any reviews/text entries containing less than 5 words to filter out uninformative input.
>   - **Spam Detection:** Identify and filter out spam reviews, advertisements, or repeating noise patterns (e.g., "aaaaaa").

---

### 2. Theme Discovery & Analysis (LLM-Powered)

> [!WARNING]
> **Crucial Implementation Instruction**  
> Do **NOT** create a single global list of general categories (e.g., *Recommendations*, *Playlists*, *Search*, *UI*).  
> Instead, perform **independent theme discovery** for **each** of the six business questions below. Each question must have its own distinct set of discovered themes, frequency metrics, supporting quotes, and root-cause analyses.

For every ingested review, the LLM pipeline must:
1. Extract general sentiment.
2. Extract discovery-specific pain points.
3. Extract recommendation-specific frustrations.
4. Extract listening goals and user intentions.
5. Identify repeat-listening signals.
6. Identify unmet product needs.
7. Classify the user segment/persona.

Below are the detailed analytical tasks and expected outputs for each question:

---

#### QUESTION 1: Why do users struggle to discover new music?
*   **Predefined Themes (LLM classifies each review into exactly one):**
    - `Repetitive Recommendations` — Algorithmic repetition / feedback loop
    - `Complex UI Navigation` — Cluttered interface, hard to find features
    - `Lack of Mood/Context Filters` — No filters by mood, vibe, activity, or situational context
    - `Excessive Ad Interruptions` — Too many advertisements in free tier
    - `Poor Search Precision` — Inaccurate query results or voice search
    - `None` — No discovery barrier mentioned
*   **Output Metrics (per theme, calculated locally):**
    - `Theme Name`: One of the predefined theme labels above.
    - `Count`: Total reviews classified into this theme.
    - `Frequency`: Count ÷ total reviews (float).
    - `Average Rating`: Arithmetic mean of star ratings for matching reviews.
    - `Evidence`: Up to 2 verbatim review text quotes from matching reviews.

*Example Output:*
```json
{
  "theme": "Repetitive Recommendations",
  "count": 42,
  "frequency": 0.28,
  "average_rating": 2.4,
  "evidence": [
    "Spotify keeps recommending the same artists over and over."
  ]
}
```

---

#### QUESTION 2: What are the most common frustrations with recommendations?
*   **Predefined Themes (LLM classifies each review into exactly one):**
    - `Popularity Bias` — Over-promoting top 40 or mainstream music
    - `Limited Genre Diversity` — Recommendations stuck in one or two genres
    - `Over-Personalization` — Too aligned to history, no room for new tastes
    - `Podcast/Audiobook Clutter` — Non-music content mixing on music feeds
    - `Stale Algorithmic Mixes` — Playlists not refreshing often enough
    - `None` — No recommendation frustration mentioned
*   **Output Metrics (per theme, calculated locally):**
    - `Theme Name`: One of the predefined theme labels above.
    - `Count`: Total reviews classified into this theme.
    - `Frequency`: Count ÷ total reviews (float).
    - `Average Rating`: Arithmetic mean of star ratings for matching reviews.
    - `Sentiment Score`: Average sentiment score (positive=1, neutral=0, negative=-1).
    - `Evidence`: Up to 2 verbatim review text quotes from matching reviews.

---

#### QUESTION 3: What listening behaviors are users trying to achieve?
*   **Predefined Themes (LLM classifies each review into exactly one):**
    - `Discovering Hidden Gems` — Searching for niche, indie, or rare artists
    - `Exploring New Genres` — Intentionally branching out to unfamiliar styles
    - `Mood/Activity-Based Listening` — Matching music to moods, emotions, or activities (workout, study, sleep)
    - `Relying on Familiar Playlists` — Defaulting to the same playlists for comfort and ease
    - `Background/Passive Listening` — Passive, ambient, low-interaction listening
    - `None` — No specific listening goal expressed
*   **Output Metrics (per theme, calculated locally):**
    - `Theme Name`: One of the predefined theme labels above.
    - `Count`: Total reviews classified into this theme.
    - `Frequency`: Count ÷ total reviews (float).
    - `Average Rating`: Arithmetic mean of star ratings for matching reviews.
    - `Evidence`: Up to 2 verbatim review text quotes from matching reviews.

---

#### QUESTION 4: What causes users to repeatedly listen to the same content?
*   **Predefined Themes (LLM classifies each review into exactly one):**
    - `Comfort Listening` — Seeking familiar, nostalgic, or safe tracks
    - `Playlist Dependence` — Looping the same curated playlists for ease
    - `Lack of Trust in Recommendations` — Distrusting new suggestions, reverting to old
    - `Choice Fatigue` — Overwhelmed by options, defaulting to familiar tracks
    - `Mood Mismatch` — Available recommendations do not match current mood/context, reverting to known tracks
    - `None` — No repeat-listening driver mentioned
*   **Output Metrics (per theme, calculated locally):**
    - `Theme Name`: One of the predefined theme labels above.
    - `Count`: Total reviews classified into this theme.
    - `Frequency`: Count ÷ total reviews (float).
    - `Average Rating`: Arithmetic mean of star ratings for matching reviews.
    - `Evidence`: Up to 2 verbatim review text quotes from matching reviews.

---

#### QUESTION 5: Which user segments experience different discovery challenges?
*   **Predefined Personas (LLM classifies each review into exactly one):** 
    - `Mood-Based Explorers` — Seek music by emotion/activity, not genre. Switch moods frequently
    - `Playlist Dependents` — Default to the same 2-3 playlists. Rarely explore beyond comfort zone
    - `New Music Seekers` — Actively browse for undiscovered artists, top charts and emerging tracks
    - `Genre Hoppers` — Rapidly switch between genres. Hard to predict but high engagement
    - `Passive Listener` — Music for background/chill/low interaction
*   **Output Metrics (per segment, calculated locally):**
    - `Segment`: One of the predefined persona labels above.
    - `Count`: Total reviews classified into this segment.
    - `Frequency`: Count ÷ total reviews (float).
    - `Average Rating`: Arithmetic mean of star ratings for matching reviews.
    - `Severity Score`: `(5 − Average Rating) × (Negative Review % in Segment)`.
    - `Severity Rank`: Rank ordering from most to least underserved.
    - `Discovery Challenges`: Top 3 discovery pain points (from Q1 labels) reported by reviewers in this segment, ranked by count. Each entry includes:
      - `pain_point`: The Q1 discovery barrier label.
      - `count`: Number of reviews in this segment with that pain point.
      - `frequency_within_segment`: `count ÷ segment_count` (float).

---

#### QUESTION 6: What unmet needs emerge consistently across reviews?
*   **Predefined Themes (LLM classifies each review into exactly one):**
    - `Conversational AI Discovery` — Natural language chat to find music
    - `Context-Aware Recommendations` — Contextual triggers (time, weather, heart rate)
    - `True Random Shuffle` — Guaranteed uniform distribution avoiding repeat artists
    - `Smart Playlist Refresh` — Auto-refresh stale playlists with fresh, relevant tracks
    - `Cross-Genre Discovery Mode` — Dedicated mode for exploring across genres with guided transitions
    - `None` — No unmet need expressed
*   **Output Metrics (per theme, calculated locally):**
    - `Theme Name`: One of the predefined theme labels above.
    - `Count`: Total reviews classified into this theme.
    - `Frequency`: Count ÷ total reviews (float).
    - `Average Rating`: Arithmetic mean of star ratings for matching reviews.
    - `Opportunity Score`: `Frequency × (6 − Average Rating)`.
    - `Evidence`: Up to 2 verbatim review text quotes from matching reviews.

---

### 3. Weekly Pulse Note & Dashboard Data Generation

After performing the LLM analysis, generate a dual-purpose output:

1.  **Executive Pulse Note (Word/Markdown format):**
    - **Constraint:** Must be **≤ 550 words** and highly scannable.
    - **Content:**
        - Top 3 Discovery Barriers
        - Top 3 Recommendation Frustrations
        - Top 3 Listening Goals
        - Top 3 Repeat-Listening Drivers
        - Top 3 Most Underserved User Segments
        - Top 3 Unmet Needs
        - Top 3 Product Opportunities
    - **Product Opportunity Structure:**
        - *Problem:* Clear definition of the user friction.
        - *Evidence:* Metrics and quote summary.
        - *Suggested AI Solution:* High-level recommendation.
        - *Expected Business Impact:* Retention, discovery rate, or engagement.

2.  **Structured JSON Export:**
    - A JSON file mapping exactly to the dashboard requirements.

#### Example JSON Schema:
```json
{
  "week_ending": "2026-06-16",
  "pulse_note_text": "...",
  "metrics": {
    "top_barriers": [
      { "theme": "Repetitive Recommendations", "frequency": 0.28, "count": 325, "average_rating": 3.1 }
    ],
    "top_frustrations": [],
    "listening_goals": [],
    "repeat_drivers": [],
    "underserved_segments": [
      {
        "segment": "Mood-Based Explorers",
        "frequency": 0.35,
        "count": 42,
        "average_rating": 2.5,
        "severity_score": 0.94,
        "severity_rank": 1,
        "discovery_challenges": [
          { "pain_point": "Repetitive Recommendations", "count": 18, "frequency_within_segment": 0.43 },
          { "pain_point": "Lack of Mood/Context Filters",  "count": 10, "frequency_within_segment": 0.24 },
          { "pain_point": "Poor Search Precision",       "count": 6,  "frequency_within_segment": 0.14 }
        ]
      }
    ],
    "unmet_needs": [],
    "opportunities": [
      {
        "problem": "Users struggle to find music matching their exact mood or situational context.",
        "evidence": "Mentioned in 15% of Reddit discussions with an average review rating of 2.1.",
        "suggested_ai_solution": "Context-aware LLM search allowing queries like 'upbeat acoustic tracks for cooking dinner'.",
        "expected_impact": "Increase weekly active engagement by 5% and playlist creation rates by 12%."
      }
    ]
  }
}
```

---

## Summary of Constraints

| Constraint | Requirement |
| :--- | :--- |
| **Data Privacy** | **Zero PII.** Scrub all usernames, emails, and device identifiers prior to ingestion/processing. |
| **Ingestion Scope** | Last **8–12 weeks** of feedback; public datasets only (no authenticated/login-wall scraping). |
| **Output Format** | Structured CSV for raw data; JSON and Markdown for final reports. |
| **Pulse Note Length** | Strict limit of **≤ 550 words** for the text note. |
| **Analysis Method** | Independent theme discovery for *each* core business question (no unified global themes). |
