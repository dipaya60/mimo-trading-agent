"""
Trading Engine — orchestrates strategies, manages positions, executes trades.
"""
import json
from datetime import datetime
from typing import List, Dict, Optional
from .strategy import Strategy, TradeSignal, SignalType, Position, MomentumStrategy, MeanReversionStrategy, BreakoutStrategy


class TradingEngine:
    """Automated trading engine with multi-strategy consensus."""

    def __init__(self, mimo_client=None):
        self.client = mimo_client
        self.strategies: List[Strategy] = [
            MomentumStrategy(),
            MeanReversionStrategy(),
            BreakoutStrategy(),
        ]
        self.positions: List[Position] = []
        self.trade_history: List[dict] = []
        self.portfolio_value = 0

    def scan(self, market_data: dict) -> dict:
        """Run all strategies and generate consensus signal."""
        signals = []
        for strat in self.strategies:
            sig = strat.evaluate(market_data)
            signals.append({"strategy": strat.name, "signal": sig})

        # Consensus scoring
        buy_score = 0
        sell_score = 0
        for s in signals:
            sig = s["signal"]
            weight = sig.confidence / 100
            if sig.signal in (SignalType.BUY, SignalType.STRONG_BUY):
                buy_score += weight * (2 if sig.signal == SignalType.STRONG_BUY else 1)
            elif sig.signal in (SignalType.SELL, SignalType.STRONG_SELL):
                sell_score += weight * (2 if sig.signal == SignalType.STRONG_SELL else 1)

        if buy_score > sell_score * 1.5:
            consensus = "STRONG_BUY" if buy_score > sell_score * 2.5 else "BUY"
        elif sell_score > buy_score * 1.5:
            consensus = "STRONG_SELL" if sell_score > buy_score * 2.5 else "SELL"
        else:
            consensus = "HOLD"

        return {
            "asset": market_data.get("asset", "BTC"),
            "consensus": consensus,
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "strategies": [
                {
                    "name": s["strategy"],
                    "signal": s["signal"].signal.value,
                    "confidence": s["signal"].confidence,
                    "reasoning": s["signal"].reasoning,
                }
                for s in signals
            ],
        }

    def generate_signal(self, market_data: dict) -> TradeSignal:
        """Generate best trade signal from strategy consensus."""
        consensus = self.scan(market_data)
        best = max(consensus["strategies"], key=lambda s: s["confidence"])

        # Find the actual TradeSignal object
        for strat in self.strategies:
            sig = strat.evaluate(market_data)
            if strat.name == best["name"]:
                return sig

        return self.strategies[0].evaluate(market_data)

    def open_position(self, signal: TradeSignal, portfolio_value: float) -> Position:
        """Open a new position based on signal."""
        size_usd = portfolio_value * (signal.position_size_pct / 100)
        side = "LONG" if signal.signal in (SignalType.BUY, SignalType.STRONG_BUY) else "SHORT"

        pos = Position(
            asset=signal.asset,
            entry_price=signal.price,
            size_usd=size_usd,
            side=side,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            entry_time=datetime.now().isoformat(),
        )
        self.positions.append(pos)

        self.trade_history.append({
            "action": "OPEN",
            "asset": pos.asset,
            "side": side,
            "price": signal.price,
            "size_usd": size_usd,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "time": pos.entry_time,
            "reasoning": signal.reasoning,
        })

        return pos

    def check_exits(self, current_prices: Dict[str, float]) -> List[dict]:
        """Check all positions for stop-loss or take-profit hits."""
        exits = []
        remaining = []
        for pos in self.positions:
            price = current_prices.get(pos.asset, pos.entry_price)
            pnl_pct = ((price - pos.entry_price) / pos.entry_price * 100) if pos.side == "LONG" else ((pos.entry_price - price) / pos.entry_price * 100)

            should_exit = False
            reason = ""

            if pos.side == "LONG":
                if price <= pos.stop_loss:
                    should_exit = True
                    reason = "Stop-loss hit"
                elif price >= pos.take_profit:
                    should_exit = True
                    reason = "Take-profit hit"
            else:
                if price >= pos.stop_loss:
                    should_exit = True
                    reason = "Stop-loss hit"
                elif price <= pos.take_profit:
                    should_exit = True
                    reason = "Take-profit hit"

            if should_exit:
                pnl_usd = pos.size_usd * (pnl_pct / 100)
                exits.append({
                    "action": "CLOSE",
                    "asset": pos.asset,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "exit_price": price,
                    "pnl_pct": round(pnl_pct, 2),
                    "pnl_usd": round(pnl_usd, 2),
                    "reason": reason,
                })
                self.trade_history.append({
                    "action": "CLOSE",
                    "asset": pos.asset,
                    "pnl_usd": round(pnl_usd, 2),
                    "reason": reason,
                    "time": datetime.now().isoformat(),
                })
            else:
                pos.unrealized_pnl_pct = round(pnl_pct, 2)
                pos.unrealized_pnl = round(pos.size_usd * (pnl_pct / 100), 2)
                remaining.append(pos)

        self.positions = remaining
        return exits

    def get_portfolio_summary(self) -> dict:
        total_unrealized = sum(p.unrealized_pnl for p in self.positions)
        total_realized = sum(t.get("pnl_usd", 0) for t in self.trade_history if t["action"] == "CLOSE")
        wins = sum(1 for t in self.trade_history if t["action"] == "CLOSE" and t.get("pnl_usd", 0) > 0)
        losses = sum(1 for t in self.trade_history if t["action"] == "CLOSE" and t.get("pnl_usd", 0) <= 0)
        total_trades = wins + losses

        return {
            "open_positions": len(self.positions),
            "total_trades": total_trades,
            "win_rate": round(wins / max(total_trades, 1) * 100, 1),
            "unrealized_pnl": round(total_unrealized, 2),
            "realized_pnl": round(total_realized, 2),
            "positions": [
                {
                    "asset": p.asset,
                    "side": p.side,
                    "entry": p.entry_price,
                    "size": p.size_usd,
                    "pnl": f"{p.unrealized_pnl_pct:+.2f}%",
                }
                for p in self.positions
            ],
        }

    def format_scan(self, result: dict) -> str:
        emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}
        lines = [
            f"\n🎯 {result['asset']} — {emoji.get(result['consensus'], '⚪')} {result['consensus']}",
            f"   Buy Score: {result['buy_score']:.2f} | Sell Score: {result['sell_score']:.2f}",
            f"\n   Strategy Breakdown:",
        ]
        for s in result["strategies"]:
            sig_emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}
            lines.append(f"   {s['name']:<18} {sig_emoji.get(s['signal'], '⚪')} {s['signal']:<12} {s['confidence']}%  {s['reasoning'][:60]}")
        return "\n".join(lines)
