# Phase-Wise Testing & Exit Criteria (eval.md)

This document aggregates the testing strategies, test cases, and quality gates required to verify and sign off on each phase of the **Spotify AI-Powered Review Discovery Engine (PRDE)**.

---

## Phase 0: Project Scaffold & Environment Setup

### 1. Test Strategy
Testing focuses on verifying environment consistency, package compatibility, YAML configuration structure, and API SDK registration. A simple script (`tests/test_scaffold.py`) verifies the standard installation workspace.

### 2. Test Cases & Verification Steps
#### Test Case 0.1: Dependency Resolution & Import Checks
* **Goal**: Validate that all packages specified in `requirements.txt` are installed and can be imported in the Python runtime.
* **Verification**: Run `pytest tests/test_scaffold.py` asserting success for imports of `groq`, `pydantic`, `presidio_analyzer`, `presidio_anonymizer`, `pandas`, `yaml`, and `dotenv`.

#### Test Case 0.2: Config Schema Parsing
* **Goal**: Validate that `config.yaml` is formatted correctly and readable by Python.
* **Verification**: Validate that the pipeline configuration loader can retrieve settings such as LLM parameters (`model_name: "llama-3.3-70b-versatile"`) and folder directories without parsing exceptions.

#### Test Case 0.3: Secure Environment Loading
* **Goal**: Confirm that environment variables are loaded securely from `.env` and are not committed to git.
* **Verification**: Confirm `GROQ_API_KEY` is successfully retrieved via `os.environ` or `dotenv.load_dotenv()` when the `.env` file is present.

### 3. Exit Criteria & Quality Gates
- **Module Readiness**: 100% of defined third-party packages import successfully in Python.
- **Config Success**: System paths and settings are successfully extracted from `config.yaml`.
- **Credential Safety**: `.env` is listed in `.gitignore` and is successfully mapped via `python-dotenv`.
- **Unit Test Status**: Run `pytest tests/test_scaffold.py` with green output.

---

## Phase 1: Ingestion & PII Scrubbing

### 1. Test Strategy
Testing will be performed using a synthetic test suite (`tests/test_ingestion.py`) containing simulated reviews with various PII leakage scenarios and non-standard fields.

### 2. Test Cases & Verification Steps
#### Test Case 1.1: Schema Normalization
* **Goal**: Verify that reviews from different sources (Reddit, App Store, Google Play) are parsed and saved under the standard unified schema.
* **Input**: Mock payloads mimicking raw API outputs from Apple App Store, Google Play Store, and Reddit.
* **Expected Result**: 
  - Standardized columns: `source`, `date`, `title`, `text`, `rating`, `engagement`.
  - Empty or missing fields are correctly initialized as `null` or `0`.
  - Date format matches ISO 8601 (`YYYY-MM-DD`).

#### Test Case 1.2: PII Scrubbing Accuracy
* **Goal**: Validate that all sensitive user information is stripped locally prior to CSV storage.
* **Input**: Text reviews seeded with target PII values:
  - *Email*: `"Contact user123@spotify.com for feedback."`
  - *IP Address*: `"Connection error on 192.168.1.10."`
  - *User Handle*: `"Reddit post by u/music_lover_99."`
  - *Email/Phone Pattern*: `"Call 555-0199 or email user@test.org."`
* **Expected Result**:
  - Out: `"Contact [EMAIL] for feedback."`
  - Out: `"Connection error on [IP_ADDRESS]."`
  - Out: `"Reddit post by [USER_HANDLE]."`
  - Out: `"Call [PHONE_NUMBER] or email [EMAIL]."`

### Performance Metrics

| Metric | Target | 
|---|---|
|Google Play Store scrape (500 reviews) | < 120s |
| Apple App Store scrape (400 reviews) | < 120s | 
| Reddit Discussions (20 reviews) |
| Spotify Community Forums (15 reviews) |  
| X (Twitter) (10 reviews) | 
| Trustpilot (Product Reviews) (10 reviews)| 
| Combined Raw reviews |≥600 reviews|
| Cleaned & Processed reviews |≥300 reviews|


### 3. Exit Criteria & Quality Gates
- **PII Leakage**: **0% leakage** of seeded PII (validated via regex and Microsoft Presidio verification runs).
- **Schema Compliance**: **100% of reviews** match the 6 core columns in the saved CSV.
- **Ingestion Target Counts (Per URL/Source)**:
  - **Apple App Store**: $\ge 400$ raw reviews scraped (typically 49).
  - **Google Play Store**: $\ge 500$ raw reviews scraped.
  - **Reddit Discussions**: $\ge 20$ raw posts scraped (typically 25).
  - **Spotify Community Forums**: $\ge 15$ raw ideas scraped (typically 20).
  - **X (Twitter)**: $\ge 10$ raw tweets scraped (typically 11-18).
  - **Trustpilot (Product Reviews)**: $\ge 15$ raw reviews scraped (typically 24).
- **Combined & Processed Targets**:
  - **Combined Raw reviews (`raw_reviews.csv`)**: $\ge 600$ total rows.
  - **Cleaned & Processed reviews (`reviews.csv`)**: $\ge 300$ total rows after emoji removal, deduplication, length check (sentences $\ge 5$ words), spam filtering, and PII scrubbing (assuming a lookback size of 150).
- **Unit Test Status**: All `tests/test_ingestion.py` assertions must pass.

---

## Phase 2: Theme Extraction & Metric Parsing (LLM-Powered)

### 1. Test Strategy
Testing will use a gold-standard validation dataset (`tests/data/gold_standard_reviews.json`) consisting of 100 manually annotated reviews. The output of the LLM pipeline will be compared against this baseline to measure correctness, consistency, and format compliance.

### 2. Test Cases & Verification Steps
#### Test Case 2.1: JSON Schema Compliance (Format Gate)
* **Goal**: Guarantee that the LLM response is parsed successfully by Pydantic and never errors due to malformed JSON.
* **Input**: 100 diverse Spotify reviews.
* **Expected Result**: 
  - 100% of LLM outputs map directly to the `ReviewAnalysis` Pydantic model.
  - Zero JSON decoding exceptions are raised by the runner.

#### Test Case 2.2: Annotation Accuracy (Sentiment & Personas)
* **Goal**: Validate that sentiment extraction and user segment classification align with human judgment.
* **Input**: Gold-standard reviews with pre-labeled sentiments (`positive`, `neutral`, `negative`) and user personas.
* **Expected Result**:
  - Sentiment accuracy (F1-score) $\ge$ 85%.
  - User persona classification matching rate $\ge$ 80% (allowing minor overlaps between close segments like *Playlist Dependents* and *Passive Listener*).

#### Test Case 2.3: Extraction Recall (Pain Points & Goals)
* **Goal**: Ensure the LLM captures actual pain points and listening intentions instead of returning empty lists or generic answers.
* **Input**: Reviews containing explicit recommendation complaints and listening intentions.
* **Expected Result**:
  - Recall score $\ge$ 85% for identifying at least one valid pain point/frustration when one is explicitly present in the source text.

### 3. Exit Criteria & Quality Gates
- **JSON Schema Pass Rate**: **100%** Pydantic validation checks on 100 runs.
- **Sentiment F1-Score**: **$\ge$ 0.85** compared to the manual annotations.
- **Persona Classification F1**: **$\ge$ 0.80** compared to the manual annotations.
- **API Error Rate**: **$< 2\%$** error rate on LLM requests (with retry/backoff handler).
- **Unit Test Status**: All `tests/test_processing.py` assertions must pass.

---

## Phase 3: Analytical Theme Discovery & Cluster Analysis

### 1. Test Strategy
Testing focuses on verifying the integrity of the Map-Reduce aggregation logic. We check for theme isolation, statistical accuracy of frequencies/averages, correctness of the Opportunity Score formula, and structural formatting of JTBD templates.

### 2. Test Cases & Verification Steps
#### Test Case 3.1: Theme Independence (Isolation Check)
* **Goal**: Ensure that theme discovery for each business question is isolated and does not cross-contaminate.
* **Verification**: 
  - Verify that the prompt instructions for each question only request themes addressing that specific prompt.
  - Assert that themes generated for Question 1 (Discovery Barriers) are semantically distinct from themes for Question 4 (Repeat-Listening Drivers).

#### Test Case 3.2: Metric Consistency & Math Verification
* **Goal**: Validate that mathematical fields (`count`, `% of Reviews`, `average_rating`) are computed accurately.
* **Input**: Annotated reviews with known attributes.
* **Expected Result**:
  - The sum of representative counts across all discovered themes matches the total analyzed reviews (or matches the subset mapping to at least one theme).
  - The frequency percentages sum to approximately $100\%$ (allowing for multi-theme assignments if allowed, but verified programmatically).
  - `average_rating` is a float between 1.0 and 5.0, mathematically matching the arithmetic mean of the matching reviews.

#### Test Case 3.3: JTBD Structural Integrity
* **Goal**: Validate that all Jobs-to-be-Done (JTBD) statements generated for Question 3 match the strict syntax requirements.
* **Expected Result**:
  - Every JTBD statement matches the regex or string pattern: `^When I am (.*), I want to (.*), so that I can (.*)\.$`

#### Test Case 3.4: Opportunity Score Logic
* **Goal**: Verify that the calculated Opportunity Score for unmet needs is mathematically sound.
* **Formula**:
  $$\text{Opportunity Score} = \text{Volume Ratio} \times (6 - \text{Average Rating})$$
  *(Where Volume Ratio is the percentage frequency of the unmet need, and Average Rating is the 1-5 star score).*
* **Expected Result**:
  - Lower ratings and higher volumes lead to higher opportunity scores.
  - Scores are within range $[0, 5]$.

### 3. Exit Criteria & Quality Gates
- **Theme Coherence**: **No overlapping themes** (validated by manual review audit or semantic similarity thresholds).
- **Math Integrity**: **100% calculation accuracy** checked via unit tests.
- **JTBD Compliance**: **100% template match** for generated Jobs-to-be-Done strings.
- **Opportunity Score Validation**: High-impact problem areas correctly sort to the top of the unmet needs lists.
- **Unit Test Status**: All `tests/test_analysis.py` assertions must pass.

---

## Phase 4: Pulse Note Generation & JSON Export

### 1. Test Strategy
Testing focuses on constraint enforcement. We check the strict word limit constraint ($\le 550$ words) for the executive note, verify that all seven sections are included in the generated report, and run JSON schema validation against the finalized dashboard export.

### 2. Test Cases & Verification Steps
#### Test Case 4.1: Word Count Enforcement
* **Goal**: Guarantee the weekly note is highly condensed, scannable, and does not exceed the 550-word constraint.
* **Input**: Discovered themes and metrics.
* **Expected Result**: 
  - Word count of the output string (splitting by space) is $\le 550$ words.
  - If a draft exceeds 550 words, the compression parser successfully condenses it below the threshold.

#### Test Case 4.2: Structured Content Verification
* **Goal**: Ensure the executive note contains all 7 mandated list sections and the specified product opportunity format.
* **Expected Result**:
  - The note contains headers/sections for: Top 3 Barriers, Top 3 Recommendation Frustrations, Top 3 Listening Goals, Top 3 Repeat-Listening Drivers, Top 3 Underserved Segments, Top 3 Unmet Needs, and Top 3 Product Opportunities.
  - The 3 Product Opportunities each follow the structure:
    - **Problem**
    - **Evidence**
    - **Suggested AI Solution**
    - **Expected Business Impact**

#### Test Case 4.3: JSON Schema Validation
* **Goal**: Validate that the exported JSON matches the dashboard data model exactly.
* **Expected Result**:
  - Fields match `week_ending`, `pulse_note_text`, and `metrics`.
  - Nested objects inside `metrics` (like `opportunities`, `top_barriers`) have correct sub-keys matching the schema in `problemStatement.md`.
  - Average rating values are formatted as floats, and counts are integers.

### 3. Exit Criteria & Quality Gates
- **Word Count Limit**: **$\le$ 550 words** verified programmatically.
- **Section Completeness**: **100% of 7 sections present** in the generated markdown.
- **JSON Schema Check**: **Passes schema validation** utilizing standard JSON schema models.
- **Unit Test Status**: All `tests/test_reporting.py` assertions must pass.
