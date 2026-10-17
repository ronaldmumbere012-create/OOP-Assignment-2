import json
from pathlib import Path
import pytest
from src.weather import *
ROOT=Path(__file__).resolve().parents[1]
def sample(name): return json.loads((ROOT/'samples'/name).read_text())
def test_locations(): assert len(parse_locations(sample('geocoding_sample.json')))==2
def test_missing_results(): assert parse_locations({})==[]
def test_ambiguous_selection(): assert choose_location(parse_locations(sample('geocoding_sample.json')),1).country=='Sampleland'
def test_weather_code(): assert describe_weather(61)=='Slight rain'
def test_unknown_code(): assert 'Unknown' in describe_weather(999)
def test_forecast(): assert len(parse_forecast(sample('open_meteo_sample.json')))==3
def test_rainfall(): assert parse_forecast(sample('open_meteo_sample.json'))['Precipitation (mm)'].sum()==pytest.approx(10.6)
def test_norway(): assert len(parse_norway(sample('met_norway_sample.json')))==1
def test_invalid_coordinates():
    with pytest.raises(InvalidLocationError): validate_coordinates(91,30)
def test_no_locations():
    with pytest.raises(NoLocationsError): choose_location([])
def test_missing_forecast():
    with pytest.raises(InvalidForecastError): parse_forecast({})
def test_bad_day_count():
    with pytest.raises(ValueError): get_forecast(0,32,17)
def test_no_network():
    class Offline:
        def get(self,*args,**kwargs): raise __import__('requests').ConnectionError('offline')
    with pytest.raises(WeatherAPIError): request_json('https://example.invalid',session=Offline(),retries=1,backoff=0)
def test_retry_transient():
    import requests
    class Response:
        status_code=200; headers={'Content-Type':'application/json'}; url='https://example.invalid'
        def raise_for_status(self): pass
        def json(self): return {'results':[]}
    class Flaky:
        def __init__(self): self.calls=0
        def get(self,*args,**kwargs):
            self.calls+=1
            if self.calls==1: raise requests.Timeout('temporary')
            return Response()
    client=Flaky()
    data,meta=request_json('https://example.invalid',session=client,retries=1,backoff=0)
    assert client.calls==2 and meta['status_code']==200
