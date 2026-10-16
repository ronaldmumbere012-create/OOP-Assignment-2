# Project 4 — Uganda Rainfall Pattern and Crop Suitability Analyser

## Contents
- `src/rainfall.py`: OOP `Region` and `CropRule` classes, cosine, Pearson, Euclidean, rainy peaks.
- `src/data_io.py`: NASA POWER API + offline daily CSV/JSON loading and validation.
- `run_analysis.py`: full analysis and figures.
- `notebooks/project4_rainfall.ipynb`: results and assignment interpretation.
- `data/raw`: put NASA downloads here.
- `data/processed`: generated results.
- `figures`: generated plots.

## Installation (Windows / Jupyter)
From a terminal opened **inside this project folder**:
```
py -m pip install -r requirements.txt
py run_analysis.py
```
If using Jupyter, first run `%pip install -r ../requirements.txt` if your notebook's current directory is `notebooks`.

## Manual NASA POWER downloads when API fails
Open https://power.larc.nasa.gov/data-access-viewer/ and select:
- **Community**: Agroclimatology (AG)
- **Temporal**: Daily (NOT Monthly)
- **Parameter**: PRECTOTCORR (precipitation, mm/day)
- **Date range**: 2015-01-01 to 2024-12-31
- **Output**: CSV or JSON
- **Locations** (one download each):
  - Kampala: latitude 0.3476, longitude 32.5825
  - Gulu: latitude 2.7746, longitude 32.2990
  - Mbarara: latitude -0.6072, longitude 30.6545

Rename the downloaded files EXACTLY `Kampala.csv`, `Gulu.csv`, `Mbarara.csv`
(or `.json`) and put them in `data/raw/`. Then run:
```
py run_analysis.py --offline
```
Open `notebooks/project4_rainfall.ipynb` and Run All. The notebook uses offline mode by default.
**Do not put the files in the notebooks folder.** The loader will reject incomplete
downloads and missing daily values rather than quietly substituting invented data.

If the API is available, `py run_analysis.py` downloads missing files only, saves
them locally, and uses the same calculations. The source is gridded NASA POWER
rainfall, not Uganda rain-gauge measurements.

## Crop threshold sources and cautions
- **Maize:** 500–600 mm well-distributed rainfall during the growing season,
  Uganda MAAIF maize extension manual:
  https://agriculture.go.ug/wp-content/uploads/2023/06/Maize-training-manual-for-extension-workers-in-Uganda_Reduced.pdf
- **Beans:** 300–500 mm seasonal *crop water need*, FAO:
  https://www.fao.org/4/S2022E/s2022e07.htm
  MAAIF emphasizes drainage and moderate/lighter rain towards maturity:
  https://www.agriculture.go.ug/wp-content/uploads/2023/06/Beans-training-manual-for-extension-workers-in-Uganda_Reduced-1.pdf
- **Groundnuts:** 500–700 mm seasonal *crop water need*, FAO, same source.

Model durations: maize 4 months, beans 3 months, groundnuts 4 months.
These are **illustrative duration assumptions** requiring local variety verification.
The monthly thresholds are derived by dividing seasonal needs by assumed
months and are **not official monthly Ugandan crop thresholds**.
The more meaningful seasonal classification compares accumulated rainfall over
each crop's assumed growing months to its seasonal range. It remains a
**rainfall-only screening model**, not a planting recommendation: rainfall is
not the same as crop evapotranspiration, and no soil drainage, temperature,
effective rainfall or daily dry spells are included. An 'Above reference'
classification does not establish waterlogging.

## Interpretation
- Cosine compares seasonal shape, not absolute wetness.
- Pearson compares the timing of above/below-average rainfall.
- Euclidean distance retains differences in rainfall magnitude (mm).
- `find_peaks` counts local peaks; its prominence threshold is a modelling
  choice and results should be checked against Uganda's climate zones.
- 2015–2024 monthly boxplots show interannual variability.
- A Nov/Dec planting window wraps into Jan/Feb of the *average climatology*;
  it does not calculate individual cross-year seasonal outcomes.

## Outputs
`regional_summary.csv`, `monthly_rainfall_2015_2024.csv`,
`monthly_climatology.csv`, `monthly_crop_classification.csv`,
`seasonal_crop_suitability.csv`, three similarity matrices, and
`rainfall_lines.png`, `rainfall_boxplots.png`, `crop_heatmap.png`.

No real NASA observations are bundled in the ZIP. Supply your downloaded files
or run the API to populate the dataset. Do not report numerical results until
the program has processed those observations.
