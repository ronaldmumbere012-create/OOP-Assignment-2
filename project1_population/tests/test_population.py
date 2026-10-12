import numpy as np
import pytest
from src.population import (DistrictPopulation, LinearForecaster, CAGRForecaster,
                            FibonacciForecaster, error_metrics, additional_classrooms,
                            bootstrap_intervals)

def test_statistics_sample_variance_matches_numpy():
    d = DistrictPopulation('Test', [2020, 2021, 2022], [10, 20, 30])
    assert d.descriptive_statistics()['sample_variance_statistics'] == pytest.approx(np.var([10,20,30], ddof=1))

def test_negative_population_rejected():
    with pytest.raises(ValueError):
        DistrictPopulation('Bad', [2020, 2021], [10, -1])

def test_linear_forecast_known_trend():
    m = LinearForecaster().fit([2020, 2021, 2022], [10, 20, 30])
    assert m.predict(2) == pytest.approx([40, 50])

def test_cagr_forecast():
    m = CAGRForecaster().fit([2020, 2021, 2022], [100, 110, 121])
    assert m.predict(1)[0] == pytest.approx(133.1)

def test_fibonacci_ratio_convention():
    m = FibonacciForecaster().fit([2020, 2021], [50, 100])
    assert m.predict(3) == pytest.approx([200, 300, 500])

def test_metrics():
    assert error_metrics([10, 20], [12, 18])['MAE'] == pytest.approx(2)

def test_classrooms_no_negative_additional():
    assert additional_classrooms(200, 100)['additional_classrooms'] == 0

def test_bootstrap_reproducible():
    years = np.arange(2015, 2025)
    vals = np.array([100, 110, 123, 137, 150, 163, 178, 190, 208, 225])
    a = bootstrap_intervals(LinearForecaster, years, vals, n_boot=1000, seed=7)
    b = bootstrap_intervals(LinearForecaster, years, vals, n_boot=1000, seed=7)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
