"""
Monte Carlo Simulation — portfolio risk modeling.
Runs 1000+ simulations to estimate probability of outcomes.
"""
import random
import math
from dataclasses import dataclass


@dataclass
class MonteCarloResult:
    simulations: int
    days: int
    initial_capital: float
    median_final: float
    mean_final: float
    best_case: float
    worst_case: float
    p5: float   # 5th percentile (VaR)
    p25: float
    p75: float
    p95: float
    prob_profit: float
    prob_double: float
    prob_ruin: float  # lose >50%
    expected_cagr: float
    max_simulated_drawdown: float


class MonteCarloSimulator:
    """Run Monte Carlo simulations for portfolio risk modeling."""

    def __init__(self, num_simulations: int = 1000):
        self.num_simulations = num_simulations

    def simulate(self, initial_capital: float, expected_return_pct: float, volatility_pct: float, days: int = 365) -> MonteCarloResult:
        """Run Monte Carlo simulation with geometric Brownian motion."""
        daily_return = expected_return_pct / 365 / 100
        daily_vol = volatility_pct / (365 ** 0.5) / 100

        final_values = []
        max_drawdowns = []

        for _ in range(self.num_simulations):
            capital = initial_capital
            peak = capital
            max_dd = 0

            for _ in range(days):
                shock = random.gauss(0, 1)
                daily_r = daily_return + daily_vol * shock
                capital *= (1 + daily_r)

                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak
                if dd > max_dd:
                    max_dd = dd

            final_values.append(capital)
            max_drawdowns.append(max_dd)

        final_values.sort()
        n = len(final_values)

        return MonteCarloResult(
            simulations=self.num_simulations,
            days=days,
            initial_capital=initial_capital,
            median_final=round(final_values[n // 2], 2),
            mean_final=round(sum(final_values) / n, 2),
            best_case=round(final_values[-1], 2),
            worst_case=round(final_values[0], 2),
            p5=round(final_values[int(n * 0.05)], 2),
            p25=round(final_values[int(n * 0.25)], 2),
            p75=round(final_values[int(n * 0.75)], 2),
            p95=round(final_values[int(n * 0.95)], 2),
            prob_profit=round(sum(1 for v in final_values if v > initial_capital) / n * 100, 1),
            prob_double=round(sum(1 for v in final_values if v > initial_capital * 2) / n * 100, 1),
            prob_ruin=round(sum(1 for v in final_values if v < initial_capital * 0.5) / n * 100, 1),
            expected_cagr=round(((sum(final_values) / n / initial_capital) ** (365 / days) - 1) * 100, 2),
            max_simulated_drawdown=round(max(max_drawdowns) * 100, 2),
        )

    def format_result(self, result: MonteCarloResult) -> str:
        lines = [
            f"\n🎲 Monte Carlo Simulation ({result.simulations} runs, {result.days} days)",
            f"   Initial Capital: ${result.initial_capital:,.0f}",
            f"",
            f"   📊 Distribution:",
            f"   Worst Case (P5):  ${result.p5:>12,.0f}",
            f"   P25:              ${result.p25:>12,.0f}",
            f"   Median:           ${result.median_final:>12,.0f}",
            f"   P75:              ${result.p75:>12,.0f}",
            f"   Best Case (P95):  ${result.p95:>12,.0f}",
            f"",
            f"   📈 Probabilities:",
            f"   Profit:           {result.prob_profit:.1f}%",
            f"   Double capital:   {result.prob_double:.1f}%",
            f"   Ruin (>50% loss): {result.prob_ruin:.1f}%",
            f"",
            f"   📉 Max Simulated Drawdown: {result.max_simulated_drawdown:.1f}%",
            f"   📊 Expected CAGR: {result.expected_cagr:+.2f}%",
        ]
        return "\n".join(lines)
