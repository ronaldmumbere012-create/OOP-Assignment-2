"""Rainfall analysis for Project 4."""
from dataclasses import dataclass
import numpy as np
from scipy.signal import find_peaks
from scipy.spatial.distance import cosine as scipy_cosine

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

@dataclass
class Region:
    name: str
    rainfall: np.ndarray
    def __post_init__(self):
        self.rainfall=np.asarray(self.rainfall,dtype=float)
        if self.rainfall.shape!=(12,) or not np.isfinite(self.rainfall).all() or (self.rainfall<0).any():
            raise ValueError("Region needs 12 nonnegative, finite monthly rainfall values")
    def annual_total(self): return float(self.rainfall.sum())
    def mean(self): return float(self.rainfall.mean())
    def wettest_month(self): return MONTHS[int(self.rainfall.argmax())]
    def driest_month(self): return MONTHS[int(self.rainfall.argmin())]
    def cv(self): return float(self.rainfall.std(ddof=1)/self.mean()) if self.mean() else float('nan')
    def rainy_peaks(self, prominence=25):
        ext=np.r_[self.rainfall[-2:],self.rainfall,self.rainfall[:2]]
        peaks,_=find_peaks(ext,prominence=prominence,distance=2)
        return sorted({int(i-2) for i in peaks if 2<=i<14})
    def season_pattern(self):
        n=len(self.rainy_peaks())
        return 'unimodal' if n==1 else 'bimodal' if n==2 else f'{n} peaks (review manually)'

@dataclass(frozen=True)
class CropRule:
    name: str
    min_mm: float
    max_mm: float
    growing_months: int
    source: str
    def classify(self, rainfall_mm):
        if rainfall_mm < self.min_mm: return 'Below reference'
        if rainfall_mm <= self.max_mm: return 'Within reference'
        return 'Above reference'

def cosine_similarity(a,b):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/den) if den else np.nan

def comparison_matrices(regions):
    names=list(regions)
    mats={key:np.zeros((len(names),len(names))) for key in ['cosine','pearson','euclidean']}
    for i,a in enumerate(names):
        for j,b in enumerate(names):
            x,y=regions[a].rainfall,regions[b].rainfall
            mats['cosine'][i,j]=cosine_similarity(x,y)
            mats['pearson'][i,j]=np.corrcoef(x,y)[0,1] if x.std() and y.std() else np.nan
            mats['euclidean'][i,j]=np.linalg.norm(x-y)
            if np.isfinite(mats['cosine'][i,j]):
                assert np.isclose(mats['cosine'][i,j],1-scipy_cosine(x,y))
    return names,mats
