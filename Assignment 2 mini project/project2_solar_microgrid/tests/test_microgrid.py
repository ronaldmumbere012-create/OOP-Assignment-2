import numpy as np
import pytest
from src.microgrid import MicroGrid, HybridMicroGrid, generate_demands, validated_demand_input

def test_exact_solution():
    result = MicroGrid().solve_day(90, 100)
    assert result["solar"] == pytest.approx(22)
    assert result["battery"] == pytest.approx(12)
    assert result["cost"] == pytest.approx(8700)

def test_diagnostics():
    assert MicroGrid().diagnostics()["determinant"] == pytest.approx(-5)

def test_vectorized_matches_loop():
    grid = MicroGrid()
    demands = generate_demands(30, seed=2026)
    assert np.allclose(grid.solve_many(demands), np.array([[grid.solve_day(*row)["solar"], grid.solve_day(*row)["battery"]] for row in demands]))

def test_invalid_demand():
    with pytest.raises(ValueError):
        MicroGrid().solve_day(-1, 5)

def test_infeasible_nnls():
    result = MicroGrid().solve_day(10, 100)
    assert result["infeasible"]
    assert result["solar"] >= 0 and result["battery"] >= 0
    assert result["residual_norm"] > 0

def test_reproducibility():
    assert np.array_equal(generate_demands(seed=42), generate_demands(seed=42))

def test_singular_hybrid():
    with pytest.raises(ValueError):
        HybridMicroGrid(matrix=np.array([[1,2,3],[2,4,6],[3,6,9]])).solve_hybrid(np.array([1.,2.,3.]))
