# Spotify PRDE — Implementation Plan (implementationplan.md)

This implementation plan outlines the development path for the **Spotify AI-Powered Review Discovery Engine (PRDE)**. The work is split into six distinct phases to ensure a modular, testable, and compliant system.

---

## 1. Project Directory Structure Map
Once fully implemented, the project structure will look as follows:

```
Spotify-AI-Powered Review Discovery Engine/
├── data/
│   ├── raw/                  # Raw, unscrubbed scraper outputs
│   └── processed/            # Cleaned, PII-scrubbed, normalized CSVs
├── doc/
│   ├── problemStatement.md   # Project requirements
│   ├── implementationplan.md # Development phases and timelines
│   ├── decision.md           # Architecture and technical decisions
│   └── eval.md               # Phase-wise testing & exit criteria
├── src/
│   ├── __init__.py
│   ├── ingestion/            # Phase 1: Data scraping & normalization
│   │   ├── __init__.py
│   │   ├── scrapers.py       # Review fetchers for Reddit, App Store, Google Play
│   │   ├── pii_scrubber.py   # PII masking (Microsoft Presidio wrapper)
│   │   └── ingestor.py       # Main ingestion runner
│   ├── processing/           # Phase 2: Core LLM sentiment & metric extractor
│   │   ├── __init__.py
│   │   ├── llm_client.py     # Groq client initialization
│   │   └── review_processor.py
│   ├── analysis/             # Phase 3: Analytical Theme clustering & JTBD
│   │   ├── __init__.py
│   │   └── theme_discoverer.py
│   ├── reporting/            # Phase 4: Executive Pulse Note & JSON export
│   │   ├── __init__.py
│   │   ├── pulse_generator.py # 550-word note generation
│   │   └── json_exporter.py   # Dashboard JSON schema builder
│   └── script/               # Phase verification scripts (Phases 0-5)
│       ├── run_phase0.py
│       ├── run_phase1.py
│       ├── run_phase2.py
│       ├── run_phase3.py
│       ├── run_phase4.py
│       └── run_phase5.py
├── tests/                    # E2E and Unit Tests
│   ├── test_ingestion.py
│   ├── test_processing.py
│   ├── test_analysis.py
│   └── test_reporting.py
├── config.yaml               # Settings (API keys, parameters, thresholds)
├── main.py                   # Main pipeline orchestrator (Phase 5)
└── requirements.txt          # Python packages
```

---

## Phase 0: Project Scaffold & Environment Setup

### Objectives & Scope
- Establish project folder structure (`data/raw/`, `data/processed/`, `src/`, `tests/`, `doc/`).
- Initialize Python virtual environment and define packages in `requirements.txt` (including `groq`, `pydantic`, `presidio-analyzer`, `presidio-anonymizer`, `pandas`, `pyyaml`, `pytest`, `python-dotenv`).
- Configure project pathways, execution limits, and LLM hyperparameters in `config.yaml`.
- Set up credential manager via `.env` and `.env.template` mapping the required `GROQ_API_KEY`.
- Integrate the Groq API SDK using the `llama-3.3-70b-versatile` model.

### Files Created
```
Spotify-AI-Powered Review Discovery Engine/
├── config.yaml
├── requirements.txt
├── .env.template
├── .env
├── doc/
│   ├── problemStatement.md
│   ├── implementationplan.md
│   ├── decision.md
│   └── eval.md
├── src/
│   └── script/
│       └── run_phase0.py
└── tests/
    └── test_scaffold.py
```

### Key Tasks
1. Establish standard project folders (`data/raw/`, `data/processed/`, `src/`, `tests/`, `doc/`).
2. Create `requirements.txt` listing packages (`groq`, `pydantic`, `presidio-analyzer`, `presidio-anonymizer`, `pandas`, `pyyaml`, `pytest`, `python-dotenv`, `click`, `beautifulsoup4`).
3. Setup virtual environment (`venv`) and run pip installations.
4. Setup `config.yaml` specifying paths, default model configs, lookbacks, and parameters.
5. Create `.env` and `.env.template` credential mapping placeholders.
6. Write [run_phase0.py](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/src/script/run_phase0.py) verifying dependency imports and file formats.
7. Write `tests/test_scaffold.py` for automated tests of scaffold settings.

### Exit Criteria & Testing
Refer to [eval.md](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/doc/eval.md#phase-0-project-scaffold--environment-setup) for details. Key exit criteria:
- **Environment Integrity**: Run `pytest tests/test_scaffold.py` to confirm that all required packages import successfully.
- **Config Load Verification**: Ensure `config.yaml` is fully readable by PyYAML and correctly populates environment constants.

### Run Verification Script
To verify Phase 0 setup:
```powershell
./venv/Scripts/python src/script/run_phase0.py
```

---

## Phase 1: Ingestion Pipeline & PII Scrubbing

### Objectives & Scope
- **Real-URL Scraping**: Scraping/collecting publicly available review data across different channels using real public URLs for Spotify (without authentication/login walls):
  - **Google Play Store**: `https://play.google.com/store/apps/details?id=com.spotify.music` (fetching reviews via public page scraping)
  - **Apple App Store Reviews**: `https://itunes.apple.com/us/rss/customerreviews/id=324684580/sortBy=mostRecent/json` (Structured JSON feed containing customer reviews)
  - **Reddit Discussions**: `https://www.reddit.com/r/spotify/new.json` (Recent Reddit posts and threads in JSON format)
  - **Spotify Community Forums**: `https://community.spotify.com/t5/Live-Ideas/idb-p/ideas_active` (Active feature ideas and user suggestions)
  - **X (Twitter) Conversations**: `https://nitter.net/search?q=spotify+recommendations` (Nitter public query search for recent tweets)
  - **Product Review Website**: `https://www.trustpilot.com/review/www.spotify.com` (Public consumer rating/review board)
- **Field Normalization**: Parsing and standardizing fields: `source`, `date`, `title`, `text`, `rating`, `engagement`.
- **Data Cleaning Pipeline**:
  - **Emoji Removal**: Stripping all emojis and special non-standard unicode symbols from titles and text.
  - **Deduplication**: Eliminating duplicate reviews or posts based on the text content to keep unique records.
  - **Sentence Length Filtering**: Parsing sentences and removing any sentence containing less than 5 words to retain substantial feedback.
  - **Spam Detection**: Implementing custom rule-based spam detection (filtering repetitive characters, promotional keywords, or repetitive word sequences).
- **PII Scrubbing**: Stripping all PII (usernames, emails, device IDs, IP addresses) locally before data is saved.
- **CSV Output**: Saving clean, standardized records in `data/processed/reviews.csv`.


### Files Created
```
Spotify-AI-Powered Review Discovery Engine/
├── data/
│   ├── raw/
│   └── processed/
├── doc/
│   └── eval.md
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── scrapers.py
│   │   ├── pii_scrubber.py
│   │   └── ingestor.py
│   └── script/
│       └── run_phase1.py
└── tests/
    └── test_ingestion.py
```

### Key Tasks
1. Implement `src/ingestion/pii_scrubber.py` combining regex and Presidio for email, IP, phone, and name masking.
2. Implement `src/ingestion/scrapers.py` to scrape reviews from real public Spotify URLs (JSON App Store reviews, Reddit json feed, Google Play JSON-LD schema, Twitter via Nitter searches, and Trustpilot static HTML reviews).
3. Implement data cleaning in `src/ingestion/ingestor.py` including:
   - Emoji and non-standard symbol removal.
   - Text deduplication (drop duplicates by text body).
   - Sentence filtering (remove any sentence with less than 5 words).
   - Spam detection (regex for character repetitions, consecutive repeating words, and advertising keywords).
   - Safe PII scrubbing on all cleaned text and title fields, writing normalized output to the processed CSV.
4. Write [run_phase1.py](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/src/script/run_phase1.py) execution runner to run ingestion and display sample results.
5. Write `tests/test_ingestion.py` verifying schema normalization, regex/Presidio scrubbing patterns, emoji removal, short sentence filters, and spam detection.

### Exit Criteria & Testing
Refer to [eval.md](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/doc/eval.md#phase-1-ingestion--pii-scrubbing) for details. Key exit criteria:
- **PII Leakage Check**: 100% of emails, usernames, and IP addresses in a mock validation dataset are successfully masked.
- **Normalization Match**: 100% of reviews ingested match the specified CSV header schema.
- **Data Target Volume**:
  - Apple App Store ($\ge 400$), Google Play ($\ge 1000$), Reddit ($\ge 20$), Spotify Community ($\ge 15$), Twitter ($\ge 10$), and Trustpilot ($\ge 15$).
  - Combined Raw Reviews: $\ge 1100$ rows in `raw_reviews.csv`.
  - Processed Cleaned Reviews: $\ge 800$ rows in `reviews.csv` after filtering, deduplication, and local PII scrubbing.

### Run Verification Script
To execute ingestion and check CSV outputs:
```powershell
./venv/Scripts/python src/script/run_phase1.py
```

---

## Phase 2: Theme Extraction & Metric Parsing (LLM-Powered)

### Objectives & Scope
- Setting up the Groq API client with structured outputs (using `llama-3.3-70b-versatile`).
- Constructing Pydantic models for individual review annotation.
- Parsing each review for: sentiment, discovery pain points, recommendation frustrations, listening goals/intentions, repeat-listening signals, unmet needs, and segment classification.
- Saving results as an intermediate annotated dataset.

### Files Created
```
Spotify-AI-Powered Review Discovery Engine/
├── doc/
│   └── eval.md
├── src/
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   └── review_processor.py
│   └── script/
│       └── run_phase2.py
└── tests/
    └── test_processing.py
```

### Key Tasks
1. Build Pydantic classification models (defining schemas for sentiment, discovery pain points, recommendation frustrations, listening goals/intentions, repeat-listening signals, unmet needs, and segment classification).
2. Implement `src/processing/llm_client.py` initializing the Groq API SDK with `llama-3.3-70b-versatile` model.
3. Implement `src/processing/review_processor.py` chunking reviews, sending prompts to Groq API using JSON structured validation, and saving the annotated reviews dataset.
4. Write [run_phase2.py](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/src/script/run_phase2.py) executing LLM annotation on a small review batch.
5. Write `tests/test_processing.py` to assert parser formatting robustness and output structure mapping.

### Exit Criteria & Testing
Refer to [eval.md](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/doc/eval.md#phase-2-theme-extraction--metric-parsing-llm-powered) for details. Key exit criteria:
- **Format Stability**: 0% JSON formatting errors on 100 sample runs using Groq structured outputs.
- **Classification Consistency**: Multi-label classification (sentiment, segment) matches a human-labeled test subset with a correlation/F1 score $> 0.82$.

### Run Verification Script
To run batch extraction and test parser logic:
```powershell
./venv/Scripts/python src/script/run_phase2.py
```

---

## Phase 3: Analytical Theme Discovery & Cluster Analysis

### Objectives & Scope
- Running **independent** theme discovery runs for each of the 6 core business questions.(LLM-powered)
- Clustered theme generation with metrics: count, frequency, average rating, supporting quotes, and root-cause analysis.
- Jobs-to-be-Done (JTBD) statement generation for behaviors (Question 3).
- Severity ranking for user segments (Question 5).
- Opportunity Score calculation for unmet needs (Question 6).

### Files Created
```
Spotify-AI-Powered Review Discovery Engine/
├── doc/
│   └── eval.md
├── src/
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── theme_discoverer.py
│   └── script/
│       └── run_phase3.py
└── tests/
    └── test_analysis.py
```

### Key Tasks
1. Implement `src/analysis/theme_discoverer.py` managing clustering and theme reductions.
2. Set up Map-Reduce LLM pipelines for each of the 6 core business questions.
3. Add statistical calculators to output counts, percentages, and averages.
4. Build Jobs-to-be-Done (JTBD) statement generators mapping context and expected outcomes.
5. Implement Opportunity Score sorting logic for unmet needs.
6. Write [run_phase3.py](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/src/script/run_phase3.py) execution script compiling theme discoverers.
7. Write `tests/test_analysis.py` asserting clustering independence and metrics accuracy.

### Exit Criteria & Testing
Refer to [eval.md](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/doc/eval.md#phase-3-analytical-theme-discovery--cluster-analysis) for details. Key exit criteria:
- **Zero Global Theme Leaks**: Themes for Question 1 do not leak or overlap with Question 2.
- **JTBD Compliance**: Every theme in Question 3 produces a valid, grammatically complete JTBD statement.

### Run Verification Script
To execute theme aggregation and clustering analysis:
```powershell
./venv/Scripts/python src/script/run_phase3.py
```

---

## Phase 4: Pulse Note Generation & JSON Export

### Objectives & Scope
- Designing the executive summary compiler.
- Compacting results to fit the **$\le$ 550 words** constraint.
- Formatting the report as scannable markdown with the 7 required sections.
- Exporting the dashboard-compatible JSON file.

### Files Created
```
Spotify-AI-Powered Review Discovery Engine/
├── doc/
│   └── eval.md
├── src/
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── pulse_generator.py
│   │   └── json_exporter.py
│   └── script/
│       └── run_phase4.py
└── tests/
    └── test_reporting.py
```

### Key Tasks
1. Implement `src/reporting/pulse_generator.py` converting analysis results into a scannable weekly report.
2. Setup programmatic length check to strictly enforce the $\le$ 550 words limit.
3. Implement `src/reporting/json_exporter.py` validating the JSON schema matches dashboard structures.
4. Write [run_phase4.py](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/src/script/run_phase4.py) runner executing pulse generation and printing the output note.
5. Write `tests/test_reporting.py` checking output JSON structures and word limits.

### Exit Criteria & Testing
Refer to [eval.md](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/doc/eval.md#phase-4-pulse-note-generation--json-export) for details. Key exit criteria:
- **Word Count Enforcement**: Pulse note is strictly $\le$ 550 words.
- **JSON Schema Compliance**: JSON validates against the dashboard input schema.

### Run Verification Script
To verify pulse note generation and JSON schema exports:
```powershell
./venv/Scripts/python src/script/run_phase4.py
```

---

## Phase 5: E2E Pipeline Orchestration & Execution

### Objectives & Scope
- Creating the core CLI entrypoint (`main.py`) to chain all phases together.
- Adding configuration parameters in `config.yaml` (dates, API keys, sample limits).
- Implementing loggers, error-handling, retry mechanisms, and final verification metrics.

### Files Created
```
Spotify-AI-Powered Review Discovery Engine/
├── config.yaml
├── main.py
└── requirements.txt
```

### Key Tasks
1. Develop `main.py` pipeline orchestrator connecting all phases sequentially.
2. Hook in loggers, error alerts, and dotenv configurations.
3. Write [run_phase5.py](file:///c:/Users/HP/OneDrive/Desktop/shiv1/programming%20project/Git_hub%20project/Spotify-AI-Powered%20Review%20Discovery%20Engine/src/script/run_phase5.py) triggering the complete pipeline.
4. Verify the complete output files `weekly_pulse_note.md` and `dashboard_data.json` generated correctly.

### Exit Criteria & Testing
- **E2E Success**: Running `python main.py` runs ingestion, annotation, analysis, and outputs the JSON/markdown files with zero exceptions.


### Run Verification Script
To launch and test the entire integrated pipeline end-to-end:
```powershell
./venv/Scripts/python src/script/run_phase5.py
```

---

## Phase 6: Web UI Dashboard (Next.js Frontend)

### Objectives & Scope

Build a modern, responsive **executive dashboard** using **Next.js** (App Router) that consumes the `dashboard_data.json` produced by the PRDE pipeline and renders all 7 Top 3 metric sections as interactive, scannable visualizations.

The frontend serves two audiences:
- **Product Managers**: Quick weekly digest of top review insights.
- **Analysts**: Drill-down into theme clusters, opportunity scores, and JTBD statements.

---

### Tech Stack

| Layer | Technology |
|---|---|
| Framework | **Next.js 14+** (App Router, React Server Components) |
| Language | **TypeScript** |
| Styling | **Vanilla CSS** (CSS Modules, no Tailwind) |
| Charts | **Recharts** (bar charts for frequency/ratings) |
| Markdown rendering | **react-markdown** (for pulse note tab) |
| Data source | `data/dashboard_data.json` served via Next.js API route |
| Dev server | `npm run dev` (port 3000) |

---

### Directory Structure

```
Spotify-AI-Powered Review Discovery Engine/
└── frontend/                          # Next.js app root
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── public/
    │   └── spotify-logo.svg
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx             # Root layout: navbar + global styles
    │   │   ├── page.tsx               # Home → redirects to /dashboard
    │   │   ├── dashboard/
    │   │   │   └── page.tsx           # Main dashboard page (all 7 metric cards)
    │   │   ├── pulse-note/
    │   │   │   └── page.tsx           # Full rendered markdown pulse note
    │   │   ├── opportunities/
    │   │   │   └── page.tsx           # Expanded Top 3 Opportunities detail view
    │   │   └── api/
    │   │       └── dashboard/
    │   │           └── route.ts       # GET /api/dashboard → serves dashboard_data.json
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── Navbar.tsx          # Top nav: logo, week label, pipeline trigger btn
    │   │   │   └── Sidebar.tsx         # Section jump links (barriers, goals, segments…)
    │   │   ├── dashboard/
    │   │   │   ├── MetricCard.tsx      # Reusable card: theme name, count, avg rating bar
    │   │   │   ├── BarriersSection.tsx # § 1 Top 3 Discovery Barriers
    │   │   │   ├── FrustrationsSection.tsx # § 2 Top 3 Recommendation Frustrations
    │   │   │   ├── ListeningGoalsSection.tsx # § 3 Top 3 Listening Goals (+ JTBD)
    │   │   │   ├── RepeatDriversSection.tsx  # § 4 Top 3 Repeat-Listening Drivers
    │   │   │   ├── SegmentsSection.tsx # § 5 Top 3 Underserved User Segments
    │   │   │   ├── UnmetNeedsSection.tsx     # § 6 Top 3 Unmet Needs (opp score bar)
    │   │   │   └── OpportunitiesSection.tsx  # § 7 Top 3 Product Opportunities (cards)
    │   │   ├── charts/
    │   │   │   ├── RatingBar.tsx       # Inline horizontal rating bar (0–5 scale)
    │   │   │   └── FrequencyBadge.tsx  # % frequency pill badge
    │   │   └── pulse/
    │   │       └── PulseNoteViewer.tsx # react-markdown renderer for pulse_note_text
    │   ├── lib/
    │   │   ├── types.ts               # TypeScript types matching dashboard_data.json
    │   │   └── fetchDashboard.ts      # Client/server data fetching utility
    │   └── styles/
    │       ├── globals.css            # CSS variables, resets, typography
    │       ├── dashboard.module.css   # Dashboard grid & card styles
    │       ├── navbar.module.css
    │       └── pulse.module.css
```

---

### Pages & Routes

| Route | Component | Description |
|---|---|---|
| `/` | `page.tsx` | Redirects to `/dashboard` |
| `/dashboard` | `dashboard/page.tsx` | Main view — all 7 metric sections with cards & charts |
| `/pulse-note` | `pulse-note/page.tsx` | Full pulse note rendered as styled markdown |
| `/opportunities` | `opportunities/page.tsx` | Expanded opportunity cards with full details |
| `GET /api/dashboard` | `api/dashboard/route.ts` | Returns `dashboard_data.json` content as JSON |

---

### API Route Design

**`GET /api/dashboard`** — `src/app/api/dashboard/route.ts`

```typescript
// Reads dashboard_data.json from the Python pipeline output
// Returns the full JSON response with cache headers
import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  const filePath = path.resolve(process.cwd(), '../data/dashboard_data.json');
  const raw = fs.readFileSync(filePath, 'utf-8');
  const data = JSON.parse(raw);
  return NextResponse.json(data, {
    headers: { 'Cache-Control': 'no-store' }
  });
}
```

---

### TypeScript Data Contract

`src/lib/types.ts` — mirroring `dashboard_data.json` exactly:

```typescript
export interface Barrier {
  theme: string;
  frequency: number;
  count: number;
  average_rating: number;
}

export interface ListeningGoal {
  theme: string;
  frequency: number;
  count: number;
  average_rating: number;
  jtbd?: string;
}

export interface UnmetNeed {
  need: string;
  frequency: number;
  count: number;
  average_rating: number;
  opportunity_score: number;
}

export interface Opportunity {
  problem: string;
  evidence: string;
  suggested_ai_solution: string;
  expected_impact: string;
}

export interface DashboardMetrics {
  top_barriers: Barrier[];
  top_frustrations: Barrier[];
  listening_goals: ListeningGoal[];
  repeat_drivers: Barrier[];
  underserved_segments: { segment: string; frequency: number; count: number; average_rating: number }[];
  unmet_needs: UnmetNeed[];
  opportunities: Opportunity[];
}

export interface DashboardData {
  week_ending: string;
  pulse_note_text: string;
  metrics: DashboardMetrics;
}
```

---

### Key Tasks

1. **Initialize Next.js app** in `frontend/` using `npx create-next-app@latest` (TypeScript, App Router, no Tailwind).
2. **Implement API route** `GET /api/dashboard` reading `../data/dashboard_data.json` relative to project root.
3. **Define TypeScript types** in `src/lib/types.ts` matching `DashboardData` schema exactly.
4. **Build `fetchDashboard.ts`** utility for server-side and client-side data fetching.
5. **Implement `layout.tsx`** with `Navbar` (week label from `week_ending`) and sidebar navigation.
6. **Build the 7 metric section components** (one per Top 3 category), each receiving typed props and rendering:
   - Theme/need/segment name as heading
   - Inline `RatingBar` for `average_rating` (0–5 scale, color-coded)
   - `FrequencyBadge` showing `%` frequency
   - Count badge
   - JTBD statement (where applicable — Listening Goals)
   - Opportunity score bar (Unmet Needs)
7. **Build `OpportunitiesSection`** rendering structured opportunity cards with Problem / Evidence / AI Solution / Business Impact layout.
8. **Build `PulseNoteViewer`** using `react-markdown` to render `pulse_note_text` with custom heading and list styles.
9. **Design CSS** using CSS Modules with a dark Spotify-inspired theme (deep blacks, Spotify green `#1DB954`, white typography).
10. **Write `run_phase6.py`** verification script checking:
    - `frontend/` directory exists and `package.json` is valid.
    - `GET /api/dashboard` returns HTTP 200 with correct JSON keys.
    - All 7 section components are present in `src/components/dashboard/`.

---

### Files Created

```
Spotify-AI-Powered Review Discovery Engine/
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── public/
    │   └── spotify-logo.svg
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx
        │   ├── dashboard/page.tsx
        │   ├── pulse-note/page.tsx
        │   ├── opportunities/page.tsx
        │   └── api/dashboard/route.ts
        ├── components/
        │   ├── layout/Navbar.tsx
        │   ├── layout/Sidebar.tsx
        │   ├── dashboard/MetricCard.tsx
        │   ├── dashboard/BarriersSection.tsx
        │   ├── dashboard/FrustrationsSection.tsx
        │   ├── dashboard/ListeningGoalsSection.tsx
        │   ├── dashboard/RepeatDriversSection.tsx
        │   ├── dashboard/SegmentsSection.tsx
        │   ├── dashboard/UnmetNeedsSection.tsx
        │   ├── dashboard/OpportunitiesSection.tsx
        │   ├── charts/RatingBar.tsx
        │   ├── charts/FrequencyBadge.tsx
        │   └── pulse/PulseNoteViewer.tsx
        ├── lib/
        │   ├── types.ts
        │   └── fetchDashboard.ts
        └── styles/
            ├── globals.css
            ├── dashboard.module.css
            ├── navbar.module.css
            └── pulse.module.css
src/script/
└── run_phase6.py                      # Phase 6 verification script
```

---

### Design Principles

- **Spotify-inspired dark theme**: Background `#121212`, card surface `#1E1E1E`, accent `#1DB954` (Spotify green).
- **Scannable layout**: Each metric section is a self-contained card grid — no scrolling walls of text.
- **Empty state handling**: Sections with empty arrays (e.g., `top_frustrations: []`) display a graceful "No data in this batch" message rather than a blank card.
- **Responsive**: CSS Grid layout adapts from 1-column mobile to 3-column desktop.
- **No external UI libraries**: Pure CSS Modules only (per project constraints).

---

### Exit Criteria & Testing

- **Dashboard renders all 7 sections** without runtime errors when `dashboard_data.json` is present.
- **API route returns HTTP 200** with all required keys: `week_ending`, `pulse_note_text`, `metrics`.
- **Empty section fallback** renders correctly when a metric array is empty.
- **Pulse note page** renders full markdown without raw syntax leaking.
- **TypeScript build** passes with zero type errors: `npm run build`.
- **All 7 component files** exist in `src/components/dashboard/`.

### Run Verification Script
```powershell
# Start the dev server
cd frontend
npm run dev

# Run Phase 6 Python verification (checks file structure + API)
./venv/Scripts/python src/script/run_phase6.py
```
