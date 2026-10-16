# Project 1 — UBOS District Population Forecaster

Course: MSCS & MSDS OOP with Python, Advent 2026.

## Run

From this directory:

```bash
python -m pip install -r requirements.txt
jupyter notebook notebooks/project1_population.ipynb
python -m pytest -q
```

Notebook imports from `src/population.py`. Launch Jupyter from the project root.

## Data and assumptions

- Kampala, Wakiso and Gulu observations for 2015–2024 are figures provided in thousands.
- Mbarara and Arua are official UBOS statistics.
- Training period: 2015–2021. Holdout: 2022–2024. Best model chosen by smallest RMSE, with MAE/MAPE also reported. Refit on 2015–2024 before 2025–2029 forecasts.
- The Fibonacci ratio model is an exploratory mathematical benchmark. Its ratios are F3/F2, F4/F3, etc.; long-run growth approaches the golden ratio, an implausibly large annual rate.
- Forecast variance is not uncertainty variance: a deterministic forecast's across-year variance reflects trend, not confidence. Bootstrap intervals are exploratory and rely on stable, independent residuals.
- Additional classrooms compare estimated 2029 requirements with estimated 2024 requirements, assuming the latter are already supplied; they are NOT an estimate of actual classroom deficits.
- Population unit conversion: thousands to persons ×1,000.

## Files

- `src/population.py`: classes, forecasting models, evaluation, bootstrap and classroom functions.
- `notebooks/project1_population.ipynb`: analysis, tables, figures and findings.
- `tests/test_population.py`: pytest checks.
