"""Direct HTTP weather APIs for MSDS Mini-Project 1."""
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json, time
import requests
import pandas as pd

GEO='https://geocoding-api.open-meteo.com/v1/search'
FORECAST='https://api.open-meteo.com/v1/forecast'
NORWAY='https://api.met.no/weatherapi/locationforecast/2.0/compact'

class WeatherError(Exception): pass
class WeatherAPIError(WeatherError): pass
class InvalidLocationError(WeatherError): pass
class NoLocationsError(WeatherError): pass
class InvalidForecastError(WeatherError): pass

@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    country: str = ''
    admin1: str = ''
    timezone: str = 'UTC'
    @property
    def label(self):
        return ', '.join(x for x in (self.name,self.admin1,self.country) if x)

CODES={0:'Clear sky',1:'Mainly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Rime fog',51:'Light drizzle',53:'Moderate drizzle',55:'Dense drizzle',56:'Light freezing drizzle',57:'Dense freezing drizzle',61:'Slight rain',63:'Moderate rain',65:'Heavy rain',66:'Light freezing rain',67:'Heavy freezing rain',71:'Slight snow',73:'Moderate snow',75:'Heavy snow',77:'Snow grains',80:'Slight rain showers',81:'Moderate rain showers',82:'Violent rain showers',85:'Slight snow showers',86:'Heavy snow showers',95:'Thunderstorm',96:'Thunderstorm with slight hail',99:'Thunderstorm with heavy hail'}
def describe_weather(code:int)->str:
    """Decode the Open-Meteo WMO weather code."""
    return CODES.get(int(code),f'Unknown weather code ({code})')

def validate_coordinates(lat,lon):
    """Reject out-of-range or nonnumeric geographic coordinates."""
    try:
        if isinstance(lat,bool) or isinstance(lon,bool): raise ValueError('bool')
        a,b=float(lat),float(lon)
        if not (-90<=a<=90 and -180<=b<=180): raise ValueError('range')
    except (ValueError,TypeError) as e:
        raise InvalidLocationError('Latitude must be -90 to 90; longitude -180 to 180.') from e

def request_json(url:str,*,params=None,headers=None,timeout=12,retries=2,backoff=.25,session=None):
    """Request JSON with timeout, raise_for_status, retry cap and exponential backoff."""
    if timeout<=0 or retries<0: raise ValueError('Invalid timeout/retry count')
    client=session if session is not None else requests
    last=None
    for attempt in range(retries+1):
        try:
            start=time.perf_counter()
            response=client.get(url,params=params,headers=headers,timeout=timeout)
            elapsed=time.perf_counter()-start
            response.raise_for_status()
            data=response.json()
            if not isinstance(data,dict): raise InvalidForecastError('Expected a JSON object')
            return data,{'status_code':response.status_code,'content_type':response.headers.get('Content-Type',''),'response_seconds':round(elapsed,3),'url':response.url}
        except (requests.ConnectionError,requests.Timeout) as e: last=e
        except requests.HTTPError as e:
            last=e
            status=getattr(e.response,'status_code',None)
            if status not in (429,500,502,503,504): raise WeatherAPIError(f'HTTP {status}: {e}') from e
        except ValueError as e: raise WeatherAPIError(f'Invalid JSON: {e}') from e
        if attempt<retries: time.sleep(backoff*2**attempt)
    raise WeatherAPIError(f'Failed after {retries+1} attempt(s): {last}') from last

def parse_locations(data:dict)->list[Location]:
    """Parse zero or more candidate cities, including missing results key."""
    results=data.get('results') or []
    if not isinstance(results,list): raise InvalidLocationError('Invalid results list')
    output=[]
    for item in results:
        try:
            loc=Location(str(item['name']),float(item['latitude']),float(item['longitude']),str(item.get('country','')),str(item.get('admin1','')),str(item.get('timezone') or 'UTC'))
            validate_coordinates(loc.latitude,loc.longitude)
            output.append(loc)
        except (KeyError,ValueError,TypeError,InvalidLocationError) as e: raise InvalidLocationError('Malformed location result') from e
    return output

def geocode(name:str,*,timeout=12)->list[Location]:
    """Search city names; caller can choose from multiple matches."""
    return geocode_requests(name,timeout=timeout)[0]

def _name(name):
    if not isinstance(name,str) or len(name.strip())<2: raise InvalidLocationError('Enter at least two letters')
    return name.strip()

def geocode_requests(name:str,*,timeout=12):
    """Part A: geocode with requests params and a timeout."""
    data,meta=request_json(GEO,params={'name':_name(name),'count':10,'language':'en','format':'json'},timeout=timeout)
    return parse_locations(data),meta

def geocode_urllib(name:str,*,timeout=12):
    """Part A: geocode with urllib.request, urllib.parse and json."""
    url=GEO+'?'+urlencode({'name':_name(name),'count':10,'language':'en','format':'json'})
    start=time.perf_counter()
    try:
        with urlopen(Request(url,headers={'Accept':'application/json'}),timeout=timeout) as response:
            data=json.loads(response.read().decode('utf-8'))
            meta={'status_code':response.status,'content_type':response.headers.get('Content-Type',''),'response_seconds':round(time.perf_counter()-start,3),'url':url}
    except Exception as e: raise WeatherAPIError(f'urllib request failed: {e}') from e
    return parse_locations(data),meta

def choose_location(locations:list[Location],index:int=0)->Location:
    """Choose a candidate explicitly using its displayed index."""
    if not locations: raise NoLocationsError('No matching locations')
    if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(locations): raise InvalidLocationError('Invalid candidate index')
    return locations[index]

def get_forecast(lat:float,lon:float,days:int=7,*,timezone_name='auto',timeout=12):
    """Request daily temperatures, rainfall, wind and weather codes."""
    validate_coordinates(lat,lon)
    if isinstance(days,bool) or not isinstance(days,int) or not 1<=days<=16: raise ValueError('Days must be 1..16')
    return request_json(FORECAST,params={'latitude':lat,'longitude':lon,'forecast_days':days,'timezone':timezone_name,'daily':'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code'},timeout=timeout)

def parse_forecast(data:dict)->pd.DataFrame:
    """Convert aligned daily arrays to labelled pandas DataFrame."""
    daily=data.get('daily')
    if not isinstance(daily,dict): raise InvalidForecastError('Missing daily data')
    cols={'time':'Date','temperature_2m_max':'Max temperature (°C)','temperature_2m_min':'Min temperature (°C)','precipitation_sum':'Precipitation (mm)','wind_speed_10m_max':'Max wind (km/h)','weather_code':'Weather code'}
    try: lengths=[len(daily[k]) for k in cols]
    except (KeyError,TypeError) as e: raise InvalidForecastError('Missing daily variable') from e
    if not lengths[0] or len(set(lengths))!=1: raise InvalidForecastError('Daily arrays have inconsistent lengths')
    try:
        df=pd.DataFrame({v:daily[k] for k,v in cols.items()})
        df['Date']=pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        for col in list(cols.values())[1:-1]: df[col]=pd.to_numeric(df[col],errors='raise')
        df['Weather']=df['Weather code'].map(describe_weather)
        return df.drop(columns='Weather code')
    except (ValueError,TypeError,KeyError) as e: raise InvalidForecastError(f'Invalid forecast values: {e}') from e

def summary(df, loc, live=False):
    """Summarise the weather forecast and identify its source."""

    if df.empty:
        raise InvalidForecastError("Empty forecast")

    source = (
        "Live Open-Meteo forecast"
        if live
        else "Invented sample data - not current weather"
    )

    min_temp = df["Max temperature (°C)"].min()
    max_temp = df["Max temperature (°C)"].max()
    rainfall = df["Precipitation (mm)"].sum()

    return (
        f"{loc.label}: {len(df)}-day forecast. "
        f"Maximum temperatures {min_temp:.1f}–{max_temp:.1f} °C; "
        f"total precipitation {rainfall:.1f} mm. "
        f"Source: {source}."
    )

def plot_forecast(df:pd.DataFrame):
    """Chart daily min/max temperatures and rainfall on separate axes."""
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,5)); x=pd.to_datetime(df['Date'])
    ax.plot(x,df['Max temperature (°C)'],marker='o',label='Maximum temperature')
    ax.plot(x,df['Min temperature (°C)'],marker='o',label='Minimum temperature')
    ax.fill_between(x,df['Min temperature (°C)'].to_numpy(),df['Max temperature (°C)'].to_numpy(),alpha=.15)
    ax.set(xlabel='Local forecast date',ylabel='Temperature (°C)',title='Daily temperature range and precipitation — Open-Meteo')
    ax2=ax.twinx(); ax2.bar(x,df['Precipitation (mm)'],alpha=.25,width=.65,label='Precipitation')
    ax2.set_ylabel('Precipitation (mm)')
    a,b=ax.get_legend_handles_labels(); c,d=ax2.get_legend_handles_labels(); ax.legend(a+c,b+d,loc='upper left')
    fig.autofmt_xdate(); fig.tight_layout(); return fig

def get_norway_forecast(lat:float,lon:float,*,contact_email:str,timeout=12):
    """Fetch MET Norway forecast using the student's actual contact in User-Agent."""
    validate_coordinates(lat,lon)
    if not contact_email or '@' not in contact_email or contact_email.endswith('@example.com'):
        raise ValueError('Set your real university email to use MET Norway')
    return request_json(NORWAY,params={'lat':round(float(lat),4),'lon':round(float(lon),4)},headers={'User-Agent':f'MSDSWeatherMiniProject/1.0 ({contact_email})','Accept':'application/json'},timeout=timeout)

def parse_norway(data:dict)->pd.DataFrame:
    """Read MET Norway instant temperature/wind and next-hour precipitation."""
    try:
        rows=[]
        for item in data['properties']['timeseries']:
            instant=item['data']['instant']['details']; nxt=item['data'].get('next_1_hours',{})
            rows.append({'Time (UTC)':item['time'],'Temperature (°C)':instant.get('air_temperature'),'Wind speed (m/s)':instant.get('wind_speed'),'Next-hour precipitation (mm)':nxt.get('details',{}).get('precipitation_amount')})
        if not rows: raise ValueError('Empty timeseries')
        return pd.DataFrame(rows)
    except (KeyError,TypeError,ValueError) as e: raise InvalidForecastError(f'Malformed MET Norway forecast: {e}') from e
