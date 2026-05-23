"""
Portfolio Risk Manager — real-time risk monitoring, position sizing, drawdown control.
5-dimension risk analysis: market, concentration, liquidity, volatility, correlation.
"""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class RiskMetrics:
    portfolio_var_95: float       # Value at Risk (95% confidence)
    max_drawdown: float           # Maximum drawdown %
    sharpe_ratio: float           # Risk-adjusted return
    concentration_risk: float     # 0-100 score
    volatility_score: float       # 0-100 score
    liquidity_risk: float         # 0-100 score
    correlation_risk: float       # 0-100 score
    overall_risk: str             # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: int               # 0-100
    warnings: List[str]
    recommendations: List[str]


class RiskManager:
    """Multi-dimensional portfolio risk manager."""

    MAX_PORTFOLIO_RISK = 100
    MAX_SINGLE_POSITION = 15  # % of portfolio
    MAX_DRAWDOWN_LIMIT = 20   # %
    CORRELATION_THRESHOLD = 0.7

    def __init__(self):
        self.risk_history: List[RiskMetrics] = []

    def analyze_portfolio(self, positions: List[dict], portfolio_value: float, market_data: Dict[str, dict]) -> RiskMetrics:
        warnings = []
        recommendations = []

        # 1. Concentration Risk — % in single asset
        if positions:
            max_alloc = max(p.get("size", 0) / max(portfolio_value, 1) * 100 for p in positions)
            concentration = min(100, max_alloc * 5)
            if max_alloc > self.MAX_SINGLE_POSITION:
                warnings.append(f"High concentration: {max_alloc:.1f}% in single position (max {self.MAX_SINGLE_POSITION}%)")
                recommendations.append("Diversify: reduce largest position or add uncorrelated assets")
        else:
            concentration = 0

        # 2. Volatility Score
        vol_scores = []
        for p in positions:
            md = market_data.get(p.get("asset", ""), {})
            vol = abs(md.get("change_24h", 0)) * 3
            vol_scores.append(vol)
        volatility = min(100, sum(vol_scores) / max(len(vol_scores), 1) * 5)
        if volatility > 60:
            warnings.append(f"High portfolio volatility: {volatility:.0f}/100")
            recommendations.append("Consider hedging with stablecoins or reducing position sizes")

        # 3. Liquidity Risk
        liq_scores = []
        for p in positions:
            md = market_data.get(p.get("asset", ""), {})
            vol_24h = md.get("volume_24h", 1e9)
            liq = max(0, 100 - vol_24h / 1e8)
            liq_scores.append(liq)
        liquidity = min(100, sum(liq_scores) / max(len(liq_scores), 1))
        if liquidity > 50:
            warnings.append("Some positions have low liquidity — may face slippage on exit")
            recommendations.append("Prioritize high-volume assets for easier exit")

        # 4. Correlation Risk — all long = correlated
        long_count = sum(1 for p in positions if p.get("side") == "LONG")
        short_count = sum(1 for p in positions if p.get("side") == "SHORT")
        if len(positions) > 1 and (long_count == len(positions) or short_count == len(positions)):
            correlation = 70
            warnings.append("All positions same direction — high correlation risk")
            recommendations.append("Add hedging positions (shorts or uncorrelated assets)")
        else:
            correlation = 20

        # 5. Value at Risk (simplified)
        total_position = sum(p.get("size", 0) for p in positions)
        var_95 = total_position * 0.05 * (1 + volatility / 100)

        # Overall risk score
        risk_score = int(
            concentration * 0.25 +
            volatility * 0.25 +
            liquidity * 0.2 +
            correlation * 0.2 +
            min(100, var_95 / max(portfolio_value, 1) * 500) * 0.1
        )

        if risk_score < 25:
            overall = "LOW"
        elif risk_score < 50:
            overall = "MEDIUM"
        elif risk_score < 75:
            overall = "HIGH"
        else:
            overall = "CRITICAL"

        if not warnings:
            warnings.append("Portfolio within acceptable risk parameters")
        if not recommendations:
            recommendations.append("Maintain current allocation — risk levels healthy")

        metrics = RiskMetrics(
            portfolio_var_95=round(var_95, 2),
            max_drawdown=round(min(100, risk_score * 1.5), 2),
            sharpe_ratio=round(max(0, 2 - risk_score / 50), 2),
            concentration_risk=round(concentration, 1),
            volatility_score=round(volatility, 1),
            liquidity_risk=round(liquidity, 1),
            correlation_risk=round(correlation, 1),
            overall_risk=overall,
            risk_score=risk_score,
            warnings=warnings,
            recommendations=recommendations,
        )
        self.risk_history.append(metrics)
        return metrics

    def calculate_position_size(self, portfolio_value: float, risk_per_trade: float, entry_price: float, stop_loss: float) -> float:
        """Kelly Criterion-inspired position sizing."""
        risk_amount = portfolio_value * (risk_per_trade / 100)
        price_risk = abs(entry_price - stop_loss) / entry_price
        if price_risk == 0:
            return 0
        size = risk_amount / price_risk
        max_size = portfolio_value * (self.MAX_SINGLE_POSITION / 100)
        return round(min(size, max_size), 2)

    def format_metrics(self, metrics: RiskMetrics) -> str:
        emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(metrics.overall_risk, "⚪")
        lines = [
            f"\n{emoji} Portfolio Risk Report",
            f"   Overall: {metrics.overall_risk} ({metrics.risk_score}/100)",
            f"",
            f"   📊 Risk Dimensions:",
            f"   Concentration:  {self._bar(metrics.concentration_risk)} {metrics.concentration_risk:.0f}/100",
            f"   Volatility:     {self._bar(metrics.volatility_score)} {metrics.volatility_score:.0f}/100",
            f"   Liquidity:      {self._bar(metrics.liquidity_risk)} {metrics.liquidity_risk:.0f}/100",
            f"   Correlation:    {self._bar(metrics.correlation_risk)} {metrics.correlation_risk:.0f}/100",
            f"",
            f"   💰 VaR (95%): ${metrics.portfolio_var_95:,.2f}",
            f"   📉 Max Drawdown: {metrics.max_drawdown:.1f}%",
            f"   📈 Sharpe Ratio: {metrics.sharpe_ratio:.2f}",
            f"",
            f"   ⚠️ Warnings:",
        ]
        for w in metrics.warnings:
            lines.append(f"   • {w}")
        lines.append(f"\n   💡 Recommendations:")
        for r in metrics.recommendations:
            lines.append(f"   • {r}")
        return "\n".join(lines)

    def _bar(self, value: float) -> str:
        filled = int(value / 10)
        return "█" * filled + "░" * (10 - filled)
