"""
Trading Strategies — multiple strategy implementations with MiMo reasoning.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class TradeSignal:
    signal: SignalType
    asset: str
    price: float
    confidence: float  # 0-100
    reasoning: str
    stop_loss: float
    take_profit: float
    position_size_pct: float
    timeframe: str
    risk_reward_ratio: float


@dataclass
class Position:
    asset: str
    entry_price: float
    size_usd: float
    side: str  # LONG or SHORT
    stop_loss: float
    take_profit: float
    entry_time: str
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0


class Strategy:
    """Base strategy with MiMo reasoning integration."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.signals_history: List[TradeSignal] = []

    def evaluate(self, market_data: dict) -> TradeSignal:
        raise NotImplementedError


class MomentumStrategy(Strategy):
    """Trend-following momentum strategy."""

    def __init__(self):
        super().__init__("Momentum", "Trend-following: buy strength, sell weakness")

    def evaluate(self, market_data: dict) -> TradeSignal:
        price = market_data.get("price", 0)
        change_24h = market_data.get("change_24h", 0)
        volume = market_data.get("volume_24h", 0)
        rsi = market_data.get("rsi", 50)

        if change_24h > 5 and rsi < 70 and volume > 1e9:
            signal = SignalType.STRONG_BUY
            confidence = min(90, 60 + change_24h * 3)
            reasoning = f"Strong momentum: +{change_24h:.1f}% with high volume (${volume/1e9:.1f}B). RSI {rsi:.0f} not overbought."
        elif change_24h > 2 and rsi < 65:
            signal = SignalType.BUY
            confidence = min(75, 50 + change_24h * 5)
            reasoning = f"Positive momentum: +{change_24h:.1f}%. RSI {rsi:.0f} supports upside."
        elif change_24h < -5 and rsi > 30:
            signal = SignalType.STRONG_SELL
            confidence = min(85, 55 + abs(change_24h) * 3)
            reasoning = f"Strong reversal: {change_24h:.1f}% with RSI {rsi:.0f}. Momentum fading."
        elif change_24h < -2 and rsi > 35:
            signal = SignalType.SELL
            confidence = min(70, 45 + abs(change_24h) * 5)
            reasoning = f"Negative momentum: {change_24h:.1f}%. RSI {rsi:.0f} declining."
        else:
            signal = SignalType.HOLD
            confidence = 40
            reasoning = f"Neutral: {change_24h:+.1f}% change, RSI {rsi:.0f}. Wait for clearer trend."

        sl = price * (0.95 if signal in (SignalType.BUY, SignalType.STRONG_BUY) else 1.05)
        tp = price * (1.10 if signal in (SignalType.BUY, SignalType.STRONG_BUY) else 0.90)

        return TradeSignal(
            signal=signal, asset=market_data.get("asset", "BTC"),
            price=price, confidence=confidence, reasoning=reasoning,
            stop_loss=round(sl, 2), take_profit=round(tp, 2),
            position_size_pct=min(10, confidence / 10),
            timeframe="4h", risk_reward_ratio=2.0,
        )


class MeanReversionStrategy(Strategy):
    """Buy dips, sell rallies — mean reversion."""

    def __init__(self):
        super().__init__("Mean Reversion", "Buy oversold dips, sell overbought rallies")

    def evaluate(self, market_data: dict) -> TradeSignal:
        price = market_data.get("price", 0)
        change_24h = market_data.get("change_24h", 0)
        rsi = market_data.get("rsi", 50)
        bb_position = market_data.get("bb_position", 0.5)

        if rsi < 30 and bb_position < 0.1:
            signal = SignalType.STRONG_BUY
            confidence = min(85, 60 + (30 - rsi) * 2)
            reasoning = f"Oversold: RSI {rsi:.0f}, BB position {bb_position:.2f}. High reversal probability."
        elif rsi < 40 and change_24h < -3:
            signal = SignalType.BUY
            confidence = min(70, 45 + (40 - rsi) * 1.5)
            reasoning = f"Pullback: RSI {rsi:.0f}, {change_24h:.1f}% dip. Good entry for mean reversion."
        elif rsi > 70 and bb_position > 0.9:
            signal = SignalType.STRONG_SELL
            confidence = min(80, 55 + (rsi - 70) * 2)
            reasoning = f"Overbought: RSI {rsi:.0f}, BB position {bb_position:.2f}. Expect pullback."
        elif rsi > 60 and change_24h > 5:
            signal = SignalType.SELL
            confidence = min(65, 40 + (rsi - 60) * 1.5)
            reasoning = f"Extended: RSI {rsi:.0f}, +{change_24h:.1f}%. Taking profits."
        else:
            signal = SignalType.HOLD
            confidence = 35
            reasoning = f"Neutral zone: RSI {rsi:.0f}. No clear mean reversion setup."

        sl = price * (0.97 if signal in (SignalType.BUY, SignalType.STRONG_BUY) else 1.03)
        tp = price * (1.05 if signal in (SignalType.BUY, SignalType.STRONG_BUY) else 0.95)

        return TradeSignal(
            signal=signal, asset=market_data.get("asset", "BTC"),
            price=price, confidence=confidence, reasoning=reasoning,
            stop_loss=round(sl, 2), take_profit=round(tp, 2),
            position_size_pct=min(8, confidence / 12),
            timeframe="1d", risk_reward_ratio=1.7,
        )


class BreakoutStrategy(Strategy):
    """Trade breakouts from consolidation ranges."""

    def __init__(self):
        super().__init__("Breakout", "Trade breakouts from key support/resistance levels")

    def evaluate(self, market_data: dict) -> TradeSignal:
        price = market_data.get("price", 0)
        change_24h = market_data.get("change_24h", 0)
        volume = market_data.get("volume_24h", 0)
        resistance = market_data.get("resistance", price * 1.05)
        support = market_data.get("support", price * 0.95)

        if price > resistance * 0.99 and volume > 2e9:
            signal = SignalType.STRONG_BUY
            confidence = min(80, 55 + volume / 1e9 * 5)
            reasoning = f"Breakout above resistance ${resistance:,.0f} with ${volume/1e9:.1f}B volume. Strong continuation likely."
        elif price > resistance * 0.97 and change_24h > 3:
            signal = SignalType.BUY
            confidence = min(65, 45 + change_24h * 3)
            reasoning = f"Approaching resistance ${resistance:,.0f}. +{change_24h:.1f}% momentum supports breakout."
        elif price < support * 1.01 and volume > 2e9:
            signal = SignalType.STRONG_SELL
            confidence = min(75, 50 + volume / 1e9 * 5)
            reasoning = f"Breakdown below support ${support:,.0f} with ${volume/1e9:.1f}B volume. Further downside."
        elif price < support * 1.03 and change_24h < -3:
            signal = SignalType.SELL
            confidence = min(60, 40 + abs(change_24h) * 3)
            reasoning = f"Approaching support ${support:,.0f}. {change_24h:.1f}% decline risks breakdown."
        else:
            signal = SignalType.HOLD
            confidence = 30
            reasoning = f"Consolidating between ${support:,.0f}-${resistance:,.0f}. Wait for breakout."

        sl = price * (0.96 if signal in (SignalType.BUY, SignalType.STRONG_BUY) else 1.04)
        tp = price * (1.12 if signal in (SignalType.BUY, SignalType.STRONG_BUY) else 0.88)

        return TradeSignal(
            signal=signal, asset=market_data.get("asset", "BTC"),
            price=price, confidence=confidence, reasoning=reasoning,
            stop_loss=round(sl, 2), take_profit=round(tp, 2),
            position_size_pct=min(12, confidence / 8),
            timeframe="1h", risk_reward_ratio=3.0,
        )
