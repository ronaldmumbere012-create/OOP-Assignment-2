"""Lake Victoria fish stock and export revenue risk mini-project.

Illustrative model, not an estimate of actual Lake Victoria fish stocks.
Run: python project3_fish_stock.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, variance, stdev

import matplotlib.pyplot as plt
import numpy as np


def fibonacci(n: int = 15) -> list[int]:
    """Return n Fibonacci numbers, starting with 0 and 1."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence


@dataclass
class FishStock:
    """Discrete logistic fish-stock model with proportional harvesting."""
    initial_stock: float = 4000.0  # tonnes
    growth_rate: float = 0.4       # per week (assignment assumption)
    carrying_capacity: float = 10000.0  # tonnes

    def __post_init__(self) -> None:
        if not np.isfinite([self.initial_stock, self.growth_rate, self.carrying_capacity]).all():
            raise ValueError("Fish-stock parameters must be finite")
        if self.initial_stock < 0 or self.growth_rate < 0 or self.carrying_capacity <= 0:
            raise ValueError("Invalid fish-stock parameters")

    def simulate(self, harvest_rate: float, weeks: int = 52) -> tuple[np.ndarray, np.ndarray]:
        """Return stock (weeks+1) and weekly harvest (weeks), both in tonnes.

        Harvest at week t is h*N[t], capped at available stock. This is
        the assignment's discrete equation, with a nonnegative-stock safeguard.
        """
        if not np.isfinite(harvest_rate) or not 0 <= harvest_rate <= 1:
            raise ValueError("harvest_rate must be between 0 and 1")
        if not isinstance(weeks, int) or weeks < 0:
            raise ValueError("weeks must be a nonnegative integer")
        stock = np.zeros(weeks + 1, dtype=float)
        harvest = np.zeros(weeks, dtype=float)
        stock[0] = self.initial_stock
        for t in range(weeks):
            current = stock[t]
            harvest[t] = harvest_rate * current
            growth = self.growth_rate * current * (1 - current / self.carrying_capacity)
            stock[t + 1] = max(0.0, current + growth - harvest[t])
        return stock, harvest

    @property
    def theoretical_msy(self) -> float:
        """Maximum of r*N*(1-N/K), in tonnes per week."""
        return self.growth_rate * self.carrying_capacity / 4


@dataclass
class PriceModel:
    """Seeded bounded random-walk price model (UGX/kg)."""
    start_price: float = 12000.0
    min_price: float = 9000.0
    max_price: float = 16000.0
    weekly_step_sd: float = 450.0

    def __post_init__(self) -> None:
        values = [self.start_price, self.min_price, self.max_price, self.weekly_step_sd]
        if not np.isfinite(values).all() or self.min_price <= 0 or self.max_price < self.min_price:
            raise ValueError("Invalid price bounds")
        if not self.min_price <= self.start_price <= self.max_price or self.weekly_step_sd < 0:
            raise ValueError("Invalid starting price or volatility")

    def simulate(self, weeks: int = 52, seed: int = 2026) -> np.ndarray:
        """Return one price per week, with reproducible random innovations."""
        if weeks < 0:
            raise ValueError("weeks must be nonnegative")
        rng = np.random.default_rng(seed)
        prices = np.empty(weeks, dtype=float)
        last = self.start_price
        for t in range(weeks):
            last = float(np.clip(last + rng.normal(0, self.weekly_step_sd),
                                 self.min_price, self.max_price))
            prices[t] = last
        return prices

    def simulate_paths(self, weeks: int = 52, paths: int = 1000,
                       seed: int = 2026) -> np.ndarray:
        """Return an array shaped (paths, weeks) of price simulations."""
        if weeks < 0 or paths < 1:
            raise ValueError("Invalid weeks or paths")
        rng = np.random.default_rng(seed)
        result = np.empty((paths, weeks), dtype=float)
        last = np.full(paths, self.start_price, dtype=float)
        for t in range(weeks):
            last = np.clip(last + rng.normal(0, self.weekly_step_sd, paths),
                           self.min_price, self.max_price)
            result[:, t] = last
        return result


@dataclass
class RiskAssessor:
    """Classify relative revenue variability using declared CV thresholds."""
    low_threshold: float = 0.10
    high_threshold: float = 0.25

    def __post_init__(self) -> None:
        if not 0 <= self.low_threshold < self.high_threshold:
            raise ValueError("Risk thresholds must be ordered and nonnegative")

    @staticmethod
    def coefficient_of_variation(values: np.ndarray) -> float:
        """Sample standard deviation / mean; undefined when mean is zero."""
        a = np.asarray(values, dtype=float)
        if a.size == 0 or not np.isfinite(a).all():
            raise ValueError("Provide finite, nonempty revenue data")
        avg = float(a.mean())
        if avg <= 0:
            return float('nan')
        return float(a.std(ddof=1) / avg) if a.size > 1 else 0.0

    def classify(self, cv: float) -> str:
        if not np.isfinite(cv) or cv < 0:
            return "Undefined"
        if cv < self.low_threshold:
            return "Low"
        if cv < self.high_threshold:
            return "Moderate"
        return "High"

    @staticmethod
    def annual_revenue_var(annual_revenues: np.ndarray,
                           reference_revenue: float) -> tuple[float, float]:
        """Return 5th-percentile revenue and downside VaR against reference.

        Revenue-at-risk (loss relative to reference) = max(0, reference - P5).
        This avoids confusing a revenue quantile with a monetary loss VaR.
        """
        a = np.asarray(annual_revenues, dtype=float)
        if a.size == 0 or not np.isfinite(a).all() or not np.isfinite(reference_revenue):
            raise ValueError("Invalid revenue distribution/reference")
        p5 = float(np.percentile(a, 5))
        return p5, max(0.0, float(reference_revenue) - p5)


def describe_revenue(values: np.ndarray) -> dict[str, float]:
    """Summary statistics; variance is measured in squared UGX."""
    a = np.asarray(values, dtype=float)
    if a.size < 2:
        raise ValueError("At least two observations are required")
    seq = a.tolist()
    return {
        "mean": mean(seq), "median": median(seq),
        "variance": variance(seq), "std_dev": stdev(seq),
        "cv": RiskAssessor.coefficient_of_variation(a),
    }


def analyse_scenario(stock_model: FishStock, price_model: PriceModel,
                     assessor: RiskAssessor, h: float, weeks: int = 52,
                     paths: int = 1000, seed: int = 2026) -> dict:
    """Analyse one harvesting scenario with identical seeded price distributions."""
    stock, harvest_tonnes = stock_model.simulate(h, weeks)
    prices = price_model.simulate(weeks, seed)
    weekly_revenue = harvest_tonnes * 1000 * prices  # tonnes -> kg
    price_paths = price_model.simulate_paths(weeks, paths, seed)
    annual_revenues = (price_paths * (harvest_tonnes * 1000)[None, :]).sum(axis=1)
    reference = float(weekly_revenue.sum())
    p5, var = assessor.annual_revenue_var(annual_revenues, reference)
    summary = describe_revenue(weekly_revenue)
    return {
        "harvest_rate": h, "stock": stock, "harvest_tonnes": harvest_tonnes,
        "prices": prices, "weekly_revenue": weekly_revenue,
        "annual_revenues": annual_revenues, "final_stock": float(stock[-1]),
        "total_harvest_tonnes": float(harvest_tonnes.sum()),
        "annual_revenue": reference, "revenue_summary": summary,
        "risk_class": assessor.classify(summary["cv"]),
        "revenue_p5": p5, "downside_var": var,
    }


def make_plots(results: list[dict], output_dir: Path) -> None:
    """Save required stock and annual-revenue risk visualisations."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    for item in results:
        ax.plot(range(len(item["stock"])), item["stock"],
                label=f'h = {item["harvest_rate"]:.0%}')
    ax.set(title="Lake Victoria illustrative fish-stock trajectories",
           xlabel="Week", ylabel="Fish stock (tonnes)")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "fish_stock_trajectories.png", dpi=160)
    plt.close(fig)

    baseline = next(item for item in results if np.isclose(item["harvest_rate"], 0.10))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(baseline["annual_revenues"] / 1e9, bins=35, edgecolor="white")
    ax.axvline(baseline["revenue_p5"] / 1e9, color="red", linestyle="--",
               label="5th-percentile annual revenue")
    ax.set(title="Simulated annual revenue (h = 10%)",
           xlabel="Annual revenue (billion UGX)", ylabel="Frequency")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "annual_revenue_var.png", dpi=160)
    plt.close(fig)


def main() -> None:
    print("Fibonacci baseline (15 values):", fibonacci(15))
    print("Fibonacci growth is unbounded and ignores carrying capacity,\n"
          "competition for food, mortality and harvesting. It is therefore\n"
          "not a realistic long-run model for fish stocks.\n")
    stock_model = FishStock()
    price_model = PriceModel()
    assessor = RiskAssessor(low_threshold=0.10, high_threshold=0.25)
    scenarios = [analyse_scenario(stock_model, price_model, assessor, h)
                 for h in (0.05, 0.10, 0.20, 0.30)]
    print(f"Theoretical MSY = {stock_model.theoretical_msy:,.0f} tonnes/week")
    print("MSY is a benchmark for biological growth, not a guarantee of\n"
          "sustainable harvest under every dynamic harvesting policy.\n")
    print(f'{"h":>5} {"Final stock (t)":>18} {"Harvest (t)":>15} '
          f'{"Revenue (UGX bn)":>19} {"CV":>8} {"Risk":>10} {"P5 (UGX bn)":>14}')
    for item in scenarios:
        print(f'{item["harvest_rate"]:>5.0%} {item["final_stock"]:>18,.1f} '
              f'{item["total_harvest_tonnes"]:>15,.1f} '
              f'{item["annual_revenue"]/1e9:>19,.3f} '
              f'{item["revenue_summary"]["cv"]:>8.3f} '
              f'{item["risk_class"]:>10} {item["revenue_p5"]/1e9:>14.3f}')
    example = scenarios[1]
    print("\nWeekly revenue descriptive statistics for h=10%:")
    for name, value in example["revenue_summary"].items():
        print(f"  {name}: {value:,.4f}")
    print(f"\n5% revenue quantile: UGX {example['revenue_p5']:,.0f}")
    print(f"Downside VaR vs one-path reference: UGX {example['downside_var']:,.0f}")
    print("A fixed variance threshold of 50,000 is meaningless: revenue\n"
          "variance has units UGX² and changes dramatically with scale.\n"
          "CV is unit-free and supports comparison across scenarios.")
    out = Path(__file__).resolve().parent / "figures"
    make_plots(scenarios, out)
    print(f"\nSaved charts in {out}")


if __name__ == "__main__":
    main()
