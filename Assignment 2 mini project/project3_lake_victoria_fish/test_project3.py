import numpy as np
import pytest
from project3_fish_stock import FishStock, PriceModel, RiskAssessor, fibonacci, analyse_scenario

def test_fibonacci():
    assert fibonacci(7) == [0, 1, 1, 2, 3, 5, 8]

def test_stock_one_week():
    stocks, harvests = FishStock().simulate(0.10, weeks=1)
    assert harvests[0] == pytest.approx(400)
    assert stocks[1] == pytest.approx(4560)

def test_invalid_harvest():
    with pytest.raises(ValueError):
        FishStock().simulate(-0.1)

def test_seed_reproducibility_and_bounds():
    p = PriceModel()
    a, b = p.simulate(seed=7), p.simulate(seed=7)
    assert np.array_equal(a, b)
    assert np.all((a >= 9000) & (a <= 16000))

def test_zero_harvest():
    r = analyse_scenario(FishStock(), PriceModel(), RiskAssessor(), 0.0)
    assert r['annual_revenue'] == 0
    assert r['risk_class'] == 'Undefined'

def test_revenue_var():
    q, loss = RiskAssessor.annual_revenue_var(np.array([10.,20.,30.,40.,50.]), 40)
    assert q == pytest.approx(12)
    assert loss == pytest.approx(28)
