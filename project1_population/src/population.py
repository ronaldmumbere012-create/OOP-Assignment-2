"""District population analysis and transparent forecasting models."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import statistics
import numpy as np


@dataclass
class DistrictPopulation:
    name: str
    years: np.ndarray
    populations: np.ndarray  # thousands of people

    def __post_init__(self) -> None:
        self.years = np.asarray(self.years, dtype=int)
        self.populations = np.asarray(self.populations, dtype=float)
        if self.years.ndim != 1 or self.populations.ndim != 1:
            raise ValueError('Years and populations must be one-dimensional.')
        if len(self.years) != len(self.populations) or len(self.years) < 2:
            raise ValueError('Years and populations must have equal lengths of at least 2.')
        if not np.all(np.isfinite(self.populations)) or np.any(self.populations < 0):
            raise ValueError('Population must be finite and nonnegative.')
        if not np.all(np.diff(self.years) == 1):
            raise ValueError('Years must be consecutive and increasing.')
        if not self.name.strip():
            raise ValueError('District name cannot be blank.')

    def __len__(self) -> int:
        return len(self.years)

    def __repr__(self) -> str:
        return f'DistrictPopulation(name={self.name!r}, years={self.years[0]}–{self.years[-1]}, n={len(self)})'

    def descriptive_statistics(self) -> dict:
        values = self.populations.tolist()
        return {
            'mean_statistics': statistics.mean(values),
            'median_statistics': statistics.median(values),
            'sample_variance_statistics': statistics.variance(values),
            'sample_std_statistics': statistics.stdev(values),
            'mean_numpy': float(np.mean(self.populations)),
            'median_numpy': float(np.median(self.populations)),
            'population_variance_numpy': float(np.var(self.populations, ddof=0)),
            'sample_variance_numpy': float(np.var(self.populations, ddof=1)),
            'sample_std_numpy': float(np.std(self.populations, ddof=1)),
        }

    def growth_rates(self) -> np.ndarray:
        if np.any(self.populations[:-1] == 0):
            raise ValueError('Growth rate is undefined when a previous population is zero.')
        return np.diff(self.populations) / self.populations[:-1] * 100

    def cagr(self) -> float:
        if self.populations[0] <= 0:
            raise ValueError('CAGR requires positive starting population.')
        return float((self.populations[-1] / self.populations[0]) ** (1 / (len(self)-1)) - 1)


class Forecaster(ABC):
    @abstractmethod
    def fit(self, years: np.ndarray, populations: np.ndarray) -> 'Forecaster':
        ...

    @abstractmethod
    def predict(self, horizon: int) -> np.ndarray:
        ...

    @staticmethod
    def validate_fit(years: np.ndarray, populations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        years = np.asarray(years, dtype=int)
        populations = np.asarray(populations, dtype=float)
        if years.ndim != 1 or populations.ndim != 1 or len(years) != len(populations) or len(years) < 2:
            raise ValueError('At least two matching one-dimensional observations are required.')
        if not np.all(np.diff(years) == 1) or not np.all(np.isfinite(populations)) or np.any(populations < 0):
            raise ValueError('Years must be consecutive and populations finite/nonnegative.')
        return years, populations

    @staticmethod
    def validate_horizon(horizon: int) -> None:
        if not isinstance(horizon, (int, np.integer)) or horizon < 1:
            raise ValueError('Forecast horizon must be a positive integer.')


class LinearForecaster(Forecaster):
    def fit(self, years: np.ndarray, populations: np.ndarray) -> 'LinearForecaster':
        years, populations = self.validate_fit(years, populations)
        self.start_year = int(years[0]); self.last_year = int(years[-1])
        self.coefficients = np.polyfit(years - self.start_year, populations, deg=1)
        return self

    def predict(self, horizon: int) -> np.ndarray:
        self.validate_horizon(horizon)
        future = np.arange(self.last_year + 1, self.last_year + horizon + 1) - self.start_year
        return np.maximum(np.polyval(self.coefficients, future), 0.0)


class CAGRForecaster(Forecaster):
    def fit(self, years: np.ndarray, populations: np.ndarray) -> 'CAGRForecaster':
        years, populations = self.validate_fit(years, populations)
        if populations[0] <= 0:
            raise ValueError('CAGR requires positive starting population.')
        self.rate = (populations[-1] / populations[0]) ** (1 / (len(populations)-1)) - 1
        self.last_value = float(populations[-1])
        return self

    def predict(self, horizon: int) -> np.ndarray:
        self.validate_horizon(horizon)
        return self.last_value * (1 + self.rate) ** np.arange(1, horizon + 1)


class FibonacciForecaster(Forecaster):
    """Exploratory model: multiply last population by successive F[n+1]/F[n].

    Convention: F1=1, F2=1; use ratios F3/F2=2, F4/F3=1.5, ...
    Each step uses the next ratio; not a demographic model.
    """
    def fit(self, years: np.ndarray, populations: np.ndarray) -> 'FibonacciForecaster':
        _, populations = self.validate_fit(years, populations)
        self.last_value = float(populations[-1])
        return self

    def predict(self, horizon: int) -> np.ndarray:
        self.validate_horizon(horizon)
        a, b = 1, 1
        current = self.last_value
        output = []
        for _ in range(horizon):
            a, b = b, a + b
            current *= b / a
            output.append(current)
        return np.array(output, dtype=float)


def error_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.shape != predicted.shape or actual.size == 0:
        raise ValueError('Actual and predicted must have matching nonempty shapes.')
    residuals = actual - predicted
    nonzero = actual != 0
    return {
        'MAE': float(np.mean(np.abs(residuals))),
        'RMSE': float(np.sqrt(np.mean(residuals ** 2))),
        'MAPE (%)': float(np.mean(np.abs(residuals[nonzero] / actual[nonzero])) * 100) if np.all(nonzero) else float('nan'),
    }


def additional_classrooms(pop_2024_thousands: float, pop_2029_thousands: float,
                          school_age_share: float = 0.18, pupils_per_classroom: int = 53) -> dict:
    """Assumes current classroom requirement exactly meets 2024 estimated demand."""
    if min(pop_2024_thousands, pop_2029_thousands) < 0 or not 0 <= school_age_share <= 1 or pupils_per_classroom < 1:
        raise ValueError('Invalid classroom-planning input.')
    baseline = int(np.ceil(pop_2024_thousands * 1000 * school_age_share / pupils_per_classroom))
    future = int(np.ceil(pop_2029_thousands * 1000 * school_age_share / pupils_per_classroom))
    return {'classrooms_2024': baseline, 'classrooms_2029': future,
            'additional_classrooms': max(0, future - baseline)}


def bootstrap_intervals(model_type: type[Forecaster], years: np.ndarray, populations: np.ndarray,
                        horizon: int = 5, n_boot: int = 1000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Residual bootstrap refitting the model, with new future residual draws.

    Exploratory conditional intervals; residual independence/stationarity are assumed.
    """
    if n_boot < 1000:
        raise ValueError('Use at least 1,000 bootstrap resamples.')
    years, populations = Forecaster.validate_fit(years, populations)
    Forecaster.validate_horizon(horizon)
    fitted_model = model_type().fit(years, populations)
    # One-step-ahead in-sample predictions (avoids requiring an in-sample API).
    fitted = np.array([model_type().fit(years[:i], populations[:i]).predict(1)[0]
                       for i in range(2, len(years))])
    residuals = populations[2:] - fitted
    if residuals.size < 2:
        raise ValueError('Bootstrap needs at least four observations.')
    rng = np.random.default_rng(seed)
    simulated = np.empty((n_boot, horizon))
    for j in range(n_boot):
        # Bootstrap future uncertainty conditional on the estimated model.
        future_errors = rng.choice(residuals, size=horizon, replace=True)
        simulated[j] = np.maximum(0, fitted_model.predict(horizon) + future_errors)
    return np.quantile(simulated, 0.025, axis=0), np.quantile(simulated, 0.975, axis=0)
