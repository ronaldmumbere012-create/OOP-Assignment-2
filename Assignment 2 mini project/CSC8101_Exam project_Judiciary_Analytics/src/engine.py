"""Object-oriented court performance analytics and simple forecasting."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

COLUMNS = ['court','region','year','opening','registered','disposed','backlog_opening','backlog_closing']

class DataValidationError(ValueError):
    """Raised when court data are missing, invalid or inconsistent."""

@dataclass(frozen=True)
class CourtRecord:
    """Annual caseload and backlog information for one court."""
    court: str
    region: str
    year: int
    opening: int
    registered: int
    disposed: int
    backlog_opening: int
    backlog_closing: int

    def __post_init__(self):
        if not self.court.strip() or not self.region.strip():
            raise DataValidationError('Court and region are required')
        if self.year < 2000 or self.year > 2100:
            raise DataValidationError('Year must be between 2000 and 2100')
        values = (self.opening,self.registered,self.disposed,self.backlog_opening,self.backlog_closing)
        if any(type(v) is not int or v < 0 for v in values):
            raise DataValidationError('All counts must be non-negative integers')
        if self.disposed > self.opening + self.registered:
            raise DataValidationError('Disposed cannot exceed available caseload')
        if self.backlog_opening > self.opening or self.backlog_closing > self.closing:
            raise DataValidationError('Backlog cannot exceed pending cases')

    @property
    def caseload(self) -> int:
        return self.opening + self.registered

    @property
    def closing(self) -> int:
        return self.caseload - self.disposed

    @property
    def clearance_rate(self) -> float | None:
        return self.disposed / self.registered * 100 if self.registered else None

    @property
    def disposal_rate(self) -> float | None:
        return self.disposed / self.caseload * 100 if self.caseload else None

    @property
    def backlog_share(self) -> float | None:
        return self.backlog_closing / self.closing * 100 if self.closing else None

class CourtRepository:
    """Validated in-memory collection of court records with CSV persistence."""
    def __init__(self, records: list[CourtRecord]):
        self._records = list(records)
        keys = [(r.court.casefold(),r.year) for r in records]
        if len(keys) != len(set(keys)):
            raise DataValidationError('Duplicate court/year records')

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> 'CourtRepository':
        missing = set(COLUMNS) - set(frame.columns)
        if missing:
            raise DataValidationError(f'Missing columns: {sorted(missing)}')
        records=[]
        for i,row in frame.iterrows():
            try:
                numeric = {k: int(row[k]) for k in COLUMNS[2:]}
                for k,v in numeric.items():
                    if pd.isna(row[k]) or float(row[k]) != v:
                        raise ValueError(f'{k} is not an integer')
                records.append(CourtRecord(str(row['court']),str(row['region']),**numeric))
            except (ValueError,TypeError,DataValidationError) as exc:
                raise DataValidationError(f'Row {i}: {exc}') from exc
        return cls(records)

    @classmethod
    def from_csv(cls,path: str | Path) -> 'CourtRepository':
        return cls.from_frame(pd.read_csv(path))

    @property
    def records(self) -> tuple[CourtRecord,...]:
        return tuple(self._records)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([r.__dict__ for r in self._records],columns=COLUMNS)

class PerformanceAnalyzer:
    """Calculate court performance from validated records."""
    def __init__(self,repository: CourtRepository):
        self.repository = repository

    def detailed(self) -> pd.DataFrame:
        rows=[]
        for r in self.repository.records:
            rows.append({**r.__dict__,'caseload':r.caseload,'closing':r.closing,
                         'clearance_rate':r.clearance_rate,'disposal_rate':r.disposal_rate,
                         'backlog_share':r.backlog_share})
        return pd.DataFrame(rows)

    def aggregate(self, by: list[str] | None = None) -> pd.DataFrame:
        """Aggregate counts before calculating rates (avoids averaging percentages)."""
        by = by or []
        allowed={'court','region','year'}
        if any(col not in allowed for col in by):
            raise DataValidationError('Invalid grouping column')
        df=self.repository.to_frame()
        numeric=['opening','registered','disposed','backlog_opening','backlog_closing']
        if df.empty:
            return pd.DataFrame(columns=by+numeric+['caseload','closing','clearance_rate','disposal_rate','backlog_share'])
        if by:
            out=df.groupby(by,as_index=False)[numeric].sum()
        else:
            out=pd.DataFrame([df[numeric].sum().to_dict()])
        out['caseload']=out.opening+out.registered
        out['closing']=out.caseload-out.disposed
        out['clearance_rate']=out.disposed.div(out.registered.where(out.registered.ne(0)))*100
        out['disposal_rate']=out.disposed.div(out.caseload.where(out.caseload.ne(0)))*100
        out['backlog_share']=out.backlog_closing.div(out.closing.where(out.closing.ne(0)))*100
        return out

class Forecaster(ABC):
    """Abstraction for interchangeable prediction strategies."""
    @abstractmethod
    def predict(self, years: list[int], values: list[float], horizon: int) -> pd.DataFrame:
        """Forecast future values from a chronological series."""

    @staticmethod
    def _check(years,values,horizon):
        if len(years) != len(values) or len(years) < 2:
            raise DataValidationError('At least two paired observations are needed')
        if len(set(years)) != len(years) or years != sorted(years):
            raise DataValidationError('Years must be sorted and unique')
        if not isinstance(horizon,int) or not 1 <= horizon <= 10:
            raise DataValidationError('Horizon must be 1–10 years')
        if any(v < 0 for v in values):
            raise DataValidationError('Forecast values must be non-negative')

class LinearForecaster(Forecaster):
    """Ordinary least-squares trend extrapolation without extra ML dependencies."""
    def predict(self,years: list[int],values: list[float],horizon: int) -> pd.DataFrame:
        self._check(years,values,horizon)
        xs=[y-years[0] for y in years]
        mx=sum(xs)/len(xs); my=sum(values)/len(values)
        den=sum((x-mx)**2 for x in xs)
        slope=sum((x-mx)*(v-my) for x,v in zip(xs,values))/den
        intercept=my-slope*mx
        future=list(range(years[-1]+1,years[-1]+horizon+1))
        return pd.DataFrame({'year':future,'forecast':[max(0,round(intercept+slope*(y-years[0]))) for y in future]})

class LastValueForecaster(Forecaster):
    """Simple persistence benchmark: future equals last observed value."""
    def predict(self,years: list[int],values: list[float],horizon:int) -> pd.DataFrame:
        self._check(years,values,horizon)
        future=list(range(years[-1]+1,years[-1]+horizon+1))
        return pd.DataFrame({'year':future,'forecast':[round(values[-1])]*horizon})

class ForecastService:
    """Composition: selects a Forecaster without inheriting from it."""
    def __init__(self,model: Forecaster):
        self.model=model

    def forecast(self, frame: pd.DataFrame, metric: str='closing',horizon:int=3) -> pd.DataFrame:
        if metric not in ('closing','registered','disposed','backlog_closing'):
            raise DataValidationError('Unsupported forecasting metric')
        if frame.empty or 'year' not in frame or metric not in frame:
            raise DataValidationError('Forecast input must include year and metric')
        yearly=frame.groupby('year',as_index=False)[metric].sum().sort_values('year')
        return self.model.predict(yearly.year.astype(int).tolist(),yearly[metric].astype(float).tolist(),horizon)
