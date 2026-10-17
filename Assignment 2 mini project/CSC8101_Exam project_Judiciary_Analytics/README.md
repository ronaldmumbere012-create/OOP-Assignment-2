# Judiciary Case Management and Performance Analytics System

CSC8101 Object-Oriented Programming | MSc Data Science and Analytics | Advent 2026

## Features
- Upload CSV or use included synthetic dataset (6 courts, 2021–2026).
- Validated records, aggregate performance indicators, interactive court and time filters.
- Court comparisons, annual trends, two forecasting strategies and CSV export.
- OOP: encapsulation, abstraction, inheritance, polymorphism and composition.
- 15 offline unit tests.

## Setup
Python 3.10 or later recommended. In a terminal opened in this folder:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

To run tests:

```bash
python -m unittest discover -s tests -v
```

## CSV format
`court,region,year,opening,registered,disposed,backlog_opening,backlog_closing`

Each row is one court in one year. Counts must be non-negative integers. `disposed <= opening + registered`, `backlog_opening <= opening` and `backlog_closing <= closing`. Court/year combinations must be unique.

## Indicator definitions
- Caseload = opening + registered
- Closing = opening + registered − disposed
- Clearance (%) = disposed / registered × 100
- Disposal (%) = disposed / caseload × 100
- Backlog share (%) = backlog_closing / closing × 100

The model **does not infer backlog** from case age; this field must be supplied. Division by zero is reported as unavailable. Clearance may exceed 100% when old pending cases are disposed.

## Design
`CourtRecord` (immutable data and validation) → `CourtRepository` (CSV and storage) → `PerformanceAnalyzer` (rates) → Streamlit UI. An abstract `Forecaster` defines a strategy contract; `LinearForecaster` and `LastValueForecaster` implement it; `ForecastService` composes a strategy.

## Project files
- `app.py`: Streamlit dashboard
- `src/engine.py`: OOP domain and analytical logic
- `data/synthetic_courts.csv`: invented demonstration records
- `tests/test_engine.py`: 15 offline unit tests
- `docs/CSC8101_Project_Proposal.docx`: proposal draft
- `docs/CSC8101_Project_Report_Draft.docx`: report draft

