# Architectural & Business Decisions (decision.md)

This document records the foundational technical and business decisions for the **Spotify Review Discovery Engine (PRDE)**.

---

## 1. Programming Language & Core Stack
* **Decision**: Python 3.10+
* **Rationale**: Python is the industry standard for LLM integration, data preprocessing, and scripting. It has first-class library support for APIs, data frames (Pandas/Polars), and test frameworks (pytest).

---

## 2. LLM Provider & SDK
* **Decision**: **Groq API** utilizing model **`llama-3.3-70b-versatile`** with **Structured Outputs** (Pydantic / Tool-calling schema enforcement).
* **Rationale**: 
  - **Llama 3.3 70B** provides state-of-the-art reasoning, clustering, and JSON compliance while maintaining low API latency.
  - **Structured Outputs** via Groq's tool-use/JSON Mode capabilities ensure that model outputs map exactly to our defined Pydantic structures.

---

## 3. PII Scrubbing Methodology
* **Decision**: Hybrid approach using a local Rule-Based Regex Engine combined with Microsoft's open-source **Presidio Analyzer & Anonymizer**.
* **Rationale**: 
  - Sending raw PII to third-party LLM APIs violates privacy compliance.
  - Doing a local scrub of usernames, emails, device IDs, and IP addresses *before* any LLM API calls ensures strict compliance with GDPR/CCPA.
  - Microsoft Presidio is lightweight, can be run locally, and avoids the cost/latency of using an LLM for initial scrubbing.

---

## 4. Theme Discovery & Clustering Strategy
* **Decision**: Two-stage "Map-Reduce" LLM theme discovery rather than pure vector clustering (K-Means/HDBSCAN).
* **Rationale**: 
  - *Stage 1 (Map)*: The LLM processes reviews in chunks, extracting sentiment, segment labels, and raw pain points per review.
  - *Stage 2 (Reduce)*: A secondary LLM run aggregates the extracted pain points, clusters them into distinct themes per business question, counts frequencies, and links representative quotes.
  - Pure vector clustering often groups reviews by superficial semantic similarity (e.g., mentioning "playlist") rather than the *specific action/goal* (e.g., "building mood playlist"). LLM-driven grouping resolves this.

---

## 5. Storage & Database Architecture
* **Decision**: Local File-Based Storage (`data/raw/` and `data/processed/` using CSV and JSON).
* **Rationale**: 
  - The tool runs as a weekly batch script, processing 8–12 weeks of reviews at a time.
  - Data sizes are small enough (tens of thousands of reviews) to fit comfortably in memory/local CSV files.
  - Avoids the maintenance, deployment, and cost overhead of a database (e.g., PostgreSQL/MongoDB) in the initial MVP.

---

## 6. Word Count Enforcement for Pulse Note
* **Decision**: A hybrid heuristic formatting prompt combined with a programmatic truncation/compaction validation step in Python.
* **Rationale**:
  - LLMs are notoriously inaccurate at strictly adhering to exact word count constraints (e.g., "under 550 words").
  - If the generated pulse note exceeds 550 words, a programmatic check will flag it, and a compression LLM prompt will rewrite it to be shorter while retaining key headings.
