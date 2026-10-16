# Mini-Project 2: Solar Micro-Grid Dispatch Planner

OOP with Python — Advent 2026. A rural health-centre micro-grid scenario in Kasese, Uganda.

## Setup
From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
jupyter notebook notebooks/project2_microgrid.ipynb
```

Run **Kernel > Restart & Run All**. The notebook imports `src.microgrid`, generates a seeded 30-day CSV, solves 2×2 linear systems by loop and vectorisation, reports energy costs and statistics, produces a chart and runs sensitivity/hybrid extensions.

## Important interpretation
The NNLS method enforces nonnegative source allocations when the exact solution is infeasible, but the resulting allocation may not satisfy both demand equations exactly.

## Findings & Limitations
In this project, I looked at how solar and battery energy could meet electricity demand at a rural health centre in Kasese. The determinant was −5, showing that the equations had a unique solution. I also checked the condition number to see how changes in demand could affect energy allocation.

I compared loop-based and vectorised methods to understand which processed the 30 days of data faster. I examined daily changes in solar and battery usage and how these affected costs. Battery energy was more expensive at UGX 450 per kWh compared to UGX 150 for solar.

One challenge was that some demand values produced negative energy allocations, which would not work in practice. I used NNLS to address this, although some differences between demand and supply remained.

The main limitation is that I used simulated data rather than actual health-centre electricity consumption. The model also leaves out weather changes, battery storage limits and energy losses.
