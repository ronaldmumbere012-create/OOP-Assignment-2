# Project 6 – Weather Forecast Using Python APIs

**OOP with Python – Assignment 2 (2026)**  
**Programme:** MSc Data Science and Analytics

I developed a weather forecast program using Open-Meteo and MET Norway. It searches for a city, retrieves weather information and shows the results in a table and chart. The assignment calls this Mini-Project 1; I use Project 6 to match my own project numbering.

## Project files

- `project6_weather_forecast.ipynb` – complete notebook with code, results and short explanations
- `src/weather.py` – reusable weather functions and `Location` class
- `tests/test_weather.py` – offline tests
- `samples/` – invented JSON data for offline demonstrations
- `requirements.txt` – required Python packages
- `pyproject.toml` – pytest project configuration

## How I run it

1. Open a terminal in the extracted Project 6 folder.
2. Install packages: `python -m pip install -r requirements.txt`
3. Run tests: `python -m pytest -v`
4. Open `project6_weather_forecast.ipynb` in VS Code or run `python -m notebook`.
5. Change the city and forecast settings in the notebook configuration cell.
6. Select **Restart Kernel and Run All Cells**.

I run tests through `python -m pytest`, not by opening `tests/test_weather.py` as a standalone Python script.

## Live and offline data

The notebook tries live weather requests first. If they fail, it uses invented sample JSON and clearly labels the results as **not current weather**. The MET Norway live call needs my real university email in the local notebook configuration. I do not publish my email in the shared code.

## What I found

I found that one city name can match several places. Open-Meteo provides daily temperatures, rainfall and wind data. MET Norway provides data at different time intervals, so direct comparisons need care. I also tested invalid inputs, missing data and network errors.

## Data sources

- Open-Meteo: https://open-meteo.com/en/docs
- Open-Meteo terms: https://open-meteo.com/en/terms
- Open-Meteo geocoding: https://open-meteo.com/en/docs/geocoding-api
- MET Norway: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- MET Norway terms: https://api.met.no/doc/TermsOfService
- MET Norway licence: https://api.met.no/doc/License

I would check the latest API terms before using the program for commercial purposes.

## AI assistance

I used AI assistance to help organise the project, improve the code and tests and shorten the explanations. I can review and test the code before submission.
