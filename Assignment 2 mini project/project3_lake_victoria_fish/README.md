# Mini-Project 3: Lake Victoria Fish Stock and Export Risk

This is an illustrative OOP implementation of the Advent 2026 mini-project.

## Run

```bash
pip install -r requirements.txt
python project3_fish_stock.py
pytest -q
```

## Model notes

- The weekly growth rate r=0.4 and capacity K=10,000 tonnes are assignment assumptions, not observed Lake Victoria parameters.
- Harvest is h times beginning-of-week stock. Revenue converts tonnes to kilograms using 1 tonne = 1,000 kg.
- Risk categories use illustrative CV cutoffs: low <0.10, moderate 0.10–<0.25, high >=0.25. Justify these for the case study.
- Annual revenue 5th percentile is reported separately from downside Value-at-Risk relative to the selected one-path reference.
- The stochastic price process is bounded and illustrative. The Monte Carlo experiment varies prices, not biological parameters.
- Charts are saved to figures/.

## Required student work

Interpret the computed results in 150–300 words under **Findings & Limitations**, discuss the sustainability of each harvest scenario, explain the interpretation and units of variance, and declare AI assistance in the repository README.
