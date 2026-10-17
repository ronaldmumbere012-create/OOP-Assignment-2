# Mini-Project 1 — Fetching and Displaying a Weather Forecast with Python Web APIs

Complete submission package for MSCS/MSDS OOP with Python Assignment 2, Advent 2026.

## Run
1. Extract the ZIP and open a terminal **inside** `mini_project_1_weather`.
2. Create a virtual environment if desired: `python -m venv .venv` and activate it.
3. Install dependencies: `python -m pip install -r requirements.txt`.
4. Start Jupyter: `jupyter notebook project1_weather_forecast.ipynb` (install `notebook` if needed) or open the notebook in VS Code.
5. In the first configuration cell set `CITY`, `CANDIDATE_INDEX`, `FORECAST_DAYS` and **your own** `UNIVERSITY_EMAIL`.
6. Select **Kernel > Restart & Run All**.
7. Run tests from the project root: `python -m pytest -q`.

Offline behaviour: The program first tries to get live weather data from the APIs. If the internet is unavailable or the request fails, it uses saved sample data to display the tables and charts. This sample data was created for demonstration and does not represent current weather conditions. The tests also use saved data, so they can run without an internet connection.

## Files
- `project1_weather_forecast.ipynb`: Part A–D, 1,000–1,500-word report, chart and tests.
- `src/weather.py`: reusable typed functions, Location class, request retry logic and parsers.
- `samples/`: invented sample JSON for reproducible offline tests.
- `tests/test_weather.py`: offline unit tests and simulated connection failure.

## Summary of findings
When searching for a location, the program may find several places with the same name, so the user needs to select the correct one. Open-Meteo provides daily weather forecasts that are displayed in tables and charts showing temperature and rainfall. MET Norway provides similar weather information, but the data is recorded at different times and uses different units, making direct comparison difficult. The program also checks for errors, limits the time spent on failed requests, identifies the data sources and avoids sharing personal contact information in the code.

## Provider references and usage
- Open-Meteo: https://open-meteo.com/en/docs and https://open-meteo.com/en/terms
- Geocoding: https://open-meteo.com/en/docs/geocoding-api
- MET Norway: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Terms: https://api.met.no/doc/TermsOfService and https://api.met.no/doc/License
