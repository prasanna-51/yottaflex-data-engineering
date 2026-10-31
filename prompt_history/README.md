# AI Prompt History – YottaFlex Data Engineering Challenge

## 1. AI Tool Information

- **AI Tool:** ChatGPT (OpenAI)
- **Date of Use:** October 31, 2026
- **Other AI Tools Used:** None

## 2. Prompt History and Assistance Summary

The following entries summarize the requests made during project development. They are categorized summaries, not verbatim copies of every original prompt.

### Prompt 1 – Project Requirements and Architecture

**Actual prompt:**

I am working on a Data Engineering recruitment challenge. I need to build a batch data pipeline that ingests customer and order CSV files, validates schemas and business rules, transforms records, and publishes curated outputs. Help me understand the requirements and design a suitable Python-based architecture. Explain the components, data flow, design decisions, and trade-offs before implementation.

### Prompt 2 – Project Implementation

Assistance requested for developing the Python batch pipeline, including customer and order CSV ingestion, validation, transformation, publishing, and rejection handling.

### Prompt 3 – Project Execution and Debugging

Assistance requested with Python environment setup, dependency installation, dataset generation, pipeline execution, and troubleshooting.

### Prompt 4 – Database Verification

Assistance requested to inspect SQLite tables, verify record counts, and understand pipeline execution records.

### Prompt 5 – Rejection Analysis

Assistance requested to inspect rejected records, understand validation reasons, and summarize rejections by reason and source file.

### Prompt 6 – Git and GitHub Preparation

Assistance requested with `.gitignore`, project cleanup, repository structure, Git initialization, and GitHub preparation.

### Prompt 7 – Documentation Review

Assistance requested to review architecture, data dictionary, design decisions, and benchmark documentation.

### Prompt 8 – Automated Testing

Assistance requested to execute and interpret pytest results and verify the pipeline's test coverage.

## 3. AI Usage Disclosure

ChatGPT was used as a technical development assistant for project understanding, architecture planning, implementation guidance, debugging, database verification, testing, documentation, and GitHub preparation.


## 4. Final Verification Results

- Automated tests: 6 passed.
- Customer records: 10,000.
- Order records: 100,000.
- Rejection events: 27 across five recorded runs.
- Clean 100,000-order benchmark: successful.
- Idempotent rerun: verified.
