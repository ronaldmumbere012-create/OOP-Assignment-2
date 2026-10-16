"""Read NASA POWER daily rainfall from API or user-downloaded CSV/JSON."""
from pathlib import Path
from io import StringIO
import json
import numpy as np
import pandas as pd
import requests

LOCATIONS={'Kampala':(0.3476,32.5825),'Gulu':(2.7746,32.2990),'Mbarara':(-0.6072,30.6545)}
START,END='20150101','20241231'
API='https://power.larc.nasa.gov/api/temporal/daily/point'

def nasa_url(lat,lon):
    from urllib.parse import urlencode
    return API+'?'+urlencode(dict(parameters='PRECTOTCORR',community='AG',
        longitude=lon,latitude=lat,start=START,end=END,format='JSON'))

def read_power(path):
    path=Path(path)
    if path.suffix.lower()=='.json':
        obj=json.loads(path.read_text(encoding='utf-8'))
        vals=obj['properties']['parameter']['PRECTOTCORR']
        df=pd.DataFrame({'date':pd.to_datetime(list(vals),format='%Y%m%d'),
                         'rainfall_mm':list(vals.values())})
    elif path.suffix.lower()=='.csv':
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        i=next((i for i,line in enumerate(lines) if
                line.replace(' ','').upper().startswith('YEAR,MO,DY,')),None)
        if i is None:
            raise ValueError(f'{path.name}: select NASA POWER DAILY CSV (YEAR, MO, DY, PRECTOTCORR), not monthly CSV.')
        raw=pd.read_csv(StringIO('\n'.join(lines[i:])))
        raw.columns=raw.columns.str.strip().str.upper()
        if 'PRECTOTCORR' not in raw: raise ValueError('PRECTOTCORR not found in CSV')
        df=pd.DataFrame({'date':pd.to_datetime(dict(year=raw.YEAR,month=raw.MO,day=raw.DY)),
                         'rainfall_mm':raw.PRECTOTCORR})
    else: raise ValueError('Use CSV or JSON files only')
    df['rainfall_mm']=pd.to_numeric(df['rainfall_mm'],errors='coerce')
    df.loc[(df.rainfall_mm<0)|(~np.isfinite(df.rainfall_mm)),'rainfall_mm']=np.nan
    return df

def load_all(raw_dir,offline=False):
    raw_dir=Path(raw_dir)
    frames=[]
    for city,(lat,lon) in LOCATIONS.items():
        path=next((raw_dir/f'{city}{ext}' for ext in ['.json','.csv']
                   if (raw_dir/f'{city}{ext}').exists()),None)
        if path is None:
            if offline:
                raise FileNotFoundError(f'Missing {city}.csv or {city}.json in {raw_dir}')
            try:
                response=requests.get(nasa_url(lat,lon),timeout=120)
                response.raise_for_status()
                obj=response.json()
                if 'properties' not in obj: raise ValueError('No NASA rainfall data returned')
                path=raw_dir/f'{city}.json'
                path.write_text(json.dumps(obj),encoding='utf-8')
                print('Downloaded',city)
            except Exception as exc:
                raise RuntimeError(f'NASA API unavailable for {city}. Save daily POWER file as '
                                   f'{city}.csv or {city}.json in data/raw and run --offline. Details: {exc}') from exc
        df=read_power(path)
        df=df[(df.date>='2015-01-01')&(df.date<='2024-12-31')]
        if df.date.duplicated().any(): raise ValueError(f'{city}: duplicate dates')
        dates=pd.date_range('2015-01-01','2024-12-31')
        df=df.set_index('date').reindex(dates).rename_axis('date').reset_index()
        if df.rainfall_mm.isna().any():
            raise ValueError(f'{city}: {df.rainfall_mm.isna().sum()} missing daily values. '
                             'Download full 2015–2024 daily data.')
        df['region']=city
        df['year']=df.date.dt.year
        df['month']=df.date.dt.month
        frames.append(df)
    daily=pd.concat(frames,ignore_index=True)
    monthly=daily.groupby(['region','year','month'],as_index=False).rainfall_mm.sum()
    assert len(monthly)==360
    return daily,monthly
