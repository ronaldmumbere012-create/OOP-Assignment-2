
"""Kasese micro-grid dispatch: constrained linear systems and costing. """
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.linalg import solve
from scipy.optimize import nnls

@dataclass
class MicroGrid:
    """Dispatch solar and battery energy for a two-equation demand system."""
    matrix: np.ndarray | None = None
    solar_cost: float = 150.0
    battery_cost: float = 450.0

    def __post_init__(self) -> None:
        self.matrix = np.asarray(self.matrix if self.matrix is not None else [[3., 2.], [4., 1.]], dtype=float)
        if self.matrix.shape != (2, 2):
            raise ValueError('The coefficient matrix must be 2x2')
        if self.solar_cost < 0 or self.battery_cost < 0:
            raise ValueError('Energy prices must be nonnegative')

    def diagnostics(self) -> dict[str, float]:
        """Return determinant and 2-norm condition number."""
        return {'determinant': float(np.linalg.det(self.matrix)), 'condition_number': float(np.linalg.cond(self.matrix))}

    def solve_day(self, d1: float, d2: float, strategy: str = 'nnls') -> dict:
        """Solve dispatch; replace infeasible negative solution with NNLS if requested."""
        demand = np.asarray([d1, d2], dtype=float)
        if not np.isfinite(demand).all() or np.any(demand < 0):
            raise ValueError('Demand must be finite and nonnegative')
        if abs(np.linalg.det(self.matrix)) < 1e-10 or np.linalg.cond(self.matrix) > 1e12:
            raise ValueError('Matrix is singular or too ill-conditioned')
        raw = solve(self.matrix, demand)
        infeasible = bool(np.any(raw < -1e-10))
        if strategy not in {'nnls', 'flag'}:
            raise ValueError('strategy must be nnls or flag')
        solution = nnls(self.matrix, demand)[0] if infeasible and strategy == 'nnls' else raw
        cost = float(np.dot(solution, [self.solar_cost, self.battery_cost])) if np.all(solution >= 0) else float('nan')
        return {'solar': float(solution[0]), 'battery': float(solution[1]), 'raw_solar': float(raw[0]), 'raw_battery': float(raw[1]), 'infeasible': infeasible, 'residual_norm': float(np.linalg.norm(self.matrix @ solution - demand)), 'cost': cost}

    def solve_many(self, demands: np.ndarray) -> np.ndarray:
        """Vectorised unconstrained solve, input shape (days,2), output (days,2)."""
        d = np.asarray(demands, dtype=float)
        if d.ndim != 2 or d.shape[1] != 2 or not np.isfinite(d).all() or (d < 0).any():
            raise ValueError('demands must have shape (days,2) and be nonnegative')
        if abs(np.linalg.det(self.matrix)) < 1e-10:
            raise ValueError('Singular matrix')
        return solve(self.matrix, d.T).T

class HybridMicroGrid(MicroGrid):
    """Three-source dispatch with a third independent equation."""
    def __init__(self, matrix: np.ndarray | None = None, costs=(150.,450.,800.)) -> None:
        super().__init__()
        self.matrix3 = np.asarray(matrix if matrix is not None else [[3.,2.,1.],[4.,1.,2.],[1.,1.,3.]], dtype=float)
        self.costs3 = np.asarray(costs, dtype=float)
        if self.matrix3.shape != (3,3) or self.costs3.shape != (3,) or (self.costs3 < 0).any():
            raise ValueError('Expected 3x3 matrix and three nonnegative costs')

    def solve_hybrid(self, demands: np.ndarray) -> dict:
        d = np.asarray(demands, dtype=float)
        if d.shape != (3,) or (d < 0).any() or not np.isfinite(d).all():
            raise ValueError('Three nonnegative demands required')
        if abs(np.linalg.det(self.matrix3)) < 1e-10:
            raise ValueError('Linearly dependent constraints')
        raw = solve(self.matrix3, d)
        feasible = bool((raw >= -1e-10).all())
        sol = raw if feasible else nnls(self.matrix3, d)[0]
        return {'sources': sol, 'raw_feasible': feasible, 'cost': float(sol @ self.costs3), 'residual_norm': float(np.linalg.norm(self.matrix3 @ sol-d))}

def generate_demands(days: int = 30, seed: int = 2026) -> np.ndarray:
    """Synthetic weekly-pattern demands built from feasible source allocations."""
    if days < 1:
        raise ValueError('days must be positive')
    rng = np.random.default_rng(seed)
    t = np.arange(days)
    solar = np.maximum(3, 22 + 4 * np.sin(2*np.pi*t/7) + rng.normal(0, 2, days))
    battery = np.maximum(2, 12 + 2 * np.cos(2*np.pi*t/7) + rng.normal(0, 1.5, days))
    demand = np.column_stack([solar,battery]) @ np.array([[3.,4.],[2.,1.]])
    return demand

def validated_demand_input(input_fn=input) -> tuple[float,float]:
    """Interactive input with re-prompts for empty, invalid and negative entries."""
    result=[]
    for label in ('D1 (kWh)', 'D2 (kWh)'):
        while True:
            try:
                value=float(input_fn(f'Enter {label}: '))
                if not np.isfinite(value) or value < 0:
                    raise ValueError
                result.append(value)
                break
            except (ValueError, TypeError):
                print('Enter a finite nonnegative number.')
    return tuple(result)
