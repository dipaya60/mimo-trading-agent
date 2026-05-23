"""
Market Regime Detector — identifies current market conditions.
Regimes: TRENDING_UP, TRENDING_DOWN, RANGING, HIGH_VOLATILITY, LOW_VOLATILITY.
"""
from enum import Enum
from dataclasses import dataclass


class MarketRegime(Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


@dataclass
class RegimeReport:
    regime: MarketRegime
    confidence: float
    recommended_strategy: str
    position_size_modifier: float  # multiply by this (0.5 = half size)
    reasoning: str


class RegimeDetector:
    """Detect market regime using price action + volatility analysis."""

    def detect(self, market_data: dict) -> RegimeReport:
        change_24h = market_data.get("change_24h", 0)
        rsi = market_data.get("rsi", 50)
        volume = market_data.get("volume_24h", 0)
        bb_pos = market_data.get("bb_position", 0.5)
        vol_24h_pct = abs(change_24h)

        # High volatility
        if vol_24h_pct > 6:
            return RegimeReport(
                regime=MarketRegime.HIGH_VOLATILITY,
                confidence=min(90, 60 + vol_24h_pct * 3),
                recommended_strategy="Breakout",
                position_size_modifier=0.5,
                reasoning=f"Extreme volatility: {change_24h:+.1f}% in 24h. Reduce position sizes, widen stops.",
            )

        # Low volatility
        if vol_24h_pct < 1.5 and volume < 5e8:
            return RegimeReport(
                regime=MarketRegime.LOW_VOLATILITY,
                confidence=min(80, 50 + (1.5 - vol_24h_pct) * 20),
                recommended_strategy="Mean Reversion",
                position_size_modifier=0.7,
                reasoning=f"Low volatility: {change_24h:+.1f}% with low volume. Range-bound conditions.",
            )

        # Trending up
        if change_24h > 2 and rsi > 50 and rsi < 70:
            return RegimeReport(
                regime=MarketRegime.TRENDING_UP,
                confidence=min(85, 55 + change_24h * 5),
                recommended_strategy="Momentum",
                position_size_modifier=1.0,
                reasoning=f"Uptrend: +{change_24h:.1f}%, RSI {rsi:.0f}. Momentum strategy preferred.",
            )

        # Trending down
        if change_24h < -2 and rsi < 50 and rsi > 30:
            return RegimeReport(
                regime=MarketRegime.TRENDING_DOWN,
                confidence=min(85, 55 + abs(change_24h) * 5),
                recommended_strategy="Momentum (Short)",
                position_size_modifier=0.8,
                reasoning=f"Downtrend: {change_24h:.1f}%, RSI {rsi:.0f}. Short momentum or reduce exposure.",
            )

        # Ranging
        return RegimeReport(
            regime=MarketRegime.RANGING,
            confidence=45,
            recommended_strategy="Mean Reversion",
            position_size_modifier=0.8,
            reasoning=f"Range-bound: {change_24h:+.1f}%, RSI {rsi:.0f}. Mean reversion preferred.",
        )

    def format_report(self, report: RegimeReport, asset: str = "") -> str:
        emoji = {
            "TRENDING_UP": "📈",
            "TRENDING_DOWN": "📉",
            "RANGING": "↔️",
            "HIGH_VOLATILITY": "⚡",
            "LOW_VOLATILITY": "😴",
        }
        return (
            f"\n{emoji.get(report.regime.value, '❓')} Market Regime: {report.regime.value} ({asset})\n"
            f"   Confidence: {report.confidence:.0f}%\n"
            f"   Best Strategy: {report.recommended_strategy}\n"
            f"   Position Size: {report.position_size_modifier:.0%} of normal\n"
            f"   💡 {report.reasoning}"
        )
