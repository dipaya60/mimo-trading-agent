"""
Telegram Bot Interface — interact with MiMo Trading Agent via Telegram.
Commands:
    /scan BTC ETH SOL   — Multi-asset scan with consensus signals
    /trade BTC 10000    — Auto-trade with position sizing
    /risk 10000         — Portfolio risk analysis
    /backtest BTC 90    — Backtest all strategies
    /montecarlo 10000   — Monte Carlo simulation
    /regime BTC         — Market regime detection
    /dca ETH 100        — Smart DCA order
    /portfolio          — Show open positions
    /market             — Market overview (8 assets)
    /help               — Show all commands
"""
import os
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import MiMoClient
from src.config import Config
from src.trading.engine import TradingEngine
from src.trading.backtester import Backtester
from src.trading.dca import SmartDCA
from src.risk.manager import RiskManager
from src.risk.monte_carlo import MonteCarloSimulator
from src.market.data import MarketDataFeed
from src.market.regime import RegimeDetector


class TradingBot:
    """Telegram bot interface for MiMo Trading Agent."""

    def __init__(self, token: str):
        self.token = token
        self.client = MiMoClient()
        self.engine = TradingEngine(self.client)
        self.feed = MarketDataFeed()
        self.risk_mgr = RiskManager()
        self.regime = RegimeDetector()
        self.bt = Backtester(10000)
        self.mc = MonteCarloSimulator(1000)
        self.dca_map = {}

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "🤖 *MiMo Trading Agent v2.0*
"
            "Automated Trading Bot + Portfolio Risk Manager
"
            "Powered by Xiaomi MiMo-V2.5-Pro

"
            "📋 *Commands:*
"
            "`/scan BTC ETH SOL` — Multi-asset signal scan
"
            "`/trade BTC 10000` — Auto-trade with capital
"
            "`/risk 10000` — Portfolio risk analysis
"
            "`/backtest BTC 90` — Backtest strategies
"
            "`/montecarlo 10000` — Monte Carlo simulation
"
            "`/regime BTC` — Market regime detection
"
            "`/dca ETH 100` — Smart DCA order
"
            "`/portfolio` — Open positions
"
            "`/market` — Market overview
"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/scan BTC ETH SOL`", parse_mode=ParseMode.MARKDOWN)
            return

        await update.message.reply_text(f"🔍 Scanning {', '.join(args)}...")

        lines = []
        for asset in args:
            md = self.feed.get_price(asset.upper())
            result = self.engine.scan(md)
            emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}
            lines.append(
                f"{emoji.get(result['consensus'], '⚪')} *{asset.upper()}*: {result['consensus']}
"
                f"   Buy: {result['buy_score']:.2f} | Sell: {result['sell_score']:.2f}
"
                f"   Price: ${md['price']:,.2f} ({md['change_24h']:+.2f}%) | RSI: {md['rsi']:.0f}
"
            )
            for s in result["strategies"]:
                sig_e = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}
                lines.append(f"   {s['name']}: {sig_e.get(s['signal'], '⚪')} {s['signal']} ({s['confidence']}%)
")

            # Regime
            rr = self.regime.detect(md)
            regime_e = {"TRENDING_UP": "📈", "TRENDING_DOWN": "📉", "RANGING": "↔️", "HIGH_VOLATILITY": "⚡", "LOW_VOLATILITY": "😴"}
            lines.append(f"   {regime_e.get(rr.regime.value, '❓')} Regime: {rr.regime.value} → Best: {rr.recommended_strategy}

")

        await update.message.reply_text("".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def cmd_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: `/trade BTC 10000`", parse_mode=ParseMode.MARKDOWN)
            return

        asset = args[0].upper()
        capital = float(args[1])
        md = self.feed.get_price(asset)
        signal = self.engine.generate_signal(md)
        emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}

        msg = f"📊 *{asset}*
${md['price']:,.2f} ({md['change_24h']:+.2f}%) | RSI: {md['rsi']:.0f}

"

        if signal.signal.value in ("BUY", "STRONG_BUY", "SELL", "STRONG_SELL"):
            size = self.risk_mgr.calculate_position_size(capital, 2, signal.price, signal.stop_loss)
            pos = self.engine.open_position(signal, capital)
            msg += (
                f"{emoji.get(signal.signal.value, '⚪')} *{signal.signal.value}* ({signal.confidence}%)
"
                f"💡 {signal.reasoning}

"
                f"📐 Size: ${size:,.2f} ({size/capital*100:.1f}%)
"
                f"🛑 SL: ${signal.stop_loss:,.2f}
"
                f"🎯 TP: ${signal.take_profit:,.2f}
"
                f"📊 R:R: {signal.risk_reward_ratio}x

"
                f"✅ *{pos.side} {pos.asset}* opened"
            )
        else:
            msg += f"{emoji.get(signal.signal.value, '⚪')} *HOLD* — No trade
💡 {signal.reasoning}"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/risk 10000`", parse_mode=ParseMode.MARKDOWN)
            return

        capital = float(args[0])
        positions = []
        market_data = {}

        for asset in ["BTC", "ETH", "SOL"]:
            md = self.feed.get_price(asset)
            market_data[asset] = md
            signal = self.engine.generate_signal(md)
            if signal.signal.value in ("BUY", "STRONG_BUY"):
                pos = self.engine.open_position(signal, capital)
                positions.append({"asset": pos.asset, "size": pos.size_usd, "side": pos.side})

        if not positions:
            md = self.feed.get_price("BTC")
            market_data["BTC"] = md
            signal = self.engine.generate_signal(md)
            pos = self.engine.open_position(signal, capital)
            positions.append({"asset": pos.asset, "size": pos.size_usd, "side": pos.side})

        metrics = self.risk_mgr.analyze_portfolio(positions, capital, market_data)
        emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}

        msg = (
            f"{emoji.get(metrics.overall_risk, '⚪')} *Portfolio Risk: {metrics.overall_risk}* ({metrics.risk_score}/100)

"
            f"📊 Concentration: {metrics.concentration_risk:.0f}/100
"
            f"📊 Volatility: {metrics.volatility_score:.0f}/100
"
            f"📊 Liquidity: {metrics.liquidity_risk:.0f}/100
"
            f"📊 Correlation: {metrics.correlation_risk:.0f}/100

"
            f"💰 VaR (95%): ${metrics.portfolio_var_95:,.2f}
"
            f"📉 Max DD: {metrics.max_drawdown:.1f}%
"
            f"📈 Sharpe: {metrics.sharpe_ratio:.2f}

"
            f"⚠️ {' | '.join(metrics.warnings[:2])}
"
            f"💡 {' | '.join(metrics.recommendations[:2])}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_backtest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        asset = args[0].upper() if args else "BTC"
        days = int(args[1]) if len(args) > 1 else 90

        await update.message.reply_text(f"📊 Backtesting on {asset} ({days} days)...")

        lines = [f"📊 *Backtest: {asset} ({days} days)*

"]
        for strat in ["Momentum", "Mean Reversion", "Breakout", "Consensus"]:
            r = self.bt.run(strat, asset, days=days)
            ret_e = "🟢" if r.total_return_pct > 0 else "🔴"
            lines.append(
                f"*{strat}*: {r.win_rate:.1f}% WR | {ret_e} {r.total_return_pct:+.2f}% | "
                f"Sharpe {r.sharpe_ratio:.2f} | DD {r.max_drawdown_pct:.1f}%
"
            )

        await update.message.reply_text("".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def cmd_montecarlo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        capital = float(args[0]) if args else 10000

        result = self.mc.simulate(capital, expected_return_pct=30, volatility_pct=60, days=365)

        msg = (
            f"🎲 *Monte Carlo: ${capital:,.0f} (365 days, 1000 runs)*

"
            f"Median: ${result.median_final:,.0f}
"
            f"P5 (worst): ${result.p5:,.0f}
"
            f"P95 (best): ${result.p95:,.0f}

"
            f"🟢 Profit: {result.prob_profit}%
"
            f"🟢 Double: {result.prob_double}%
"
            f"🔴 Ruin: {result.prob_ruin}%

"
            f"CAGR: {result.expected_cagr:+.2f}%"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_regime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        asset = args[0].upper() if args else "BTC"

        md = self.feed.get_price(asset)
        report = self.regime.detect(md)
        emoji = {"TRENDING_UP": "📈", "TRENDING_DOWN": "📉", "RANGING": "↔️", "HIGH_VOLATILITY": "⚡", "LOW_VOLATILITY": "😴"}

        msg = (
            f"{emoji.get(report.regime.value, '❓')} *{asset}: {report.regime.value}*

"
            f"Confidence: {report.confidence:.0f}%
"
            f"Best Strategy: {report.recommended_strategy}
"
            f"Position Size: {report.position_size_modifier:.0%}

"
            f"💡 {report.reasoning}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_dca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: `/dca ETH 100`", parse_mode=ParseMode.MARKDOWN)
            return

        asset = args[0].upper()
        amount = float(args[1])
        md = self.feed.get_price(asset)

        dca = SmartDCA(base_amount_usd=amount)
        order = dca.evaluate(md)

        emoji = "🟢🟢" if order.is_dip_buy else "🟢"
        msg = (
            f"{emoji} *Smart DCA: {asset}*

"
            f"Amount: ${order.amount_usd:,.2f} @ ${order.price:,.2f}
"
            f"💡 {order.reasoning}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        summary = self.engine.get_portfolio_summary()
        msg = (
            f"📋 *Portfolio Summary*

"
            f"Open: {summary['open_positions']} positions
"
            f"Trades: {summary['total_trades']}
"
            f"Win Rate: {summary['win_rate']}%
"
            f"Unrealized: ${summary['unrealized_pnl']:+,.2f}
"
            f"Realized: ${summary['realized_pnl']:+,.2f}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_market(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        data = self.feed.get_all()
        lines = ["📊 *Market Overview*

"]
        for asset, d in data.items():
            emoji = "🟢" if d["change_24h"] > 0 else "🔴"
            lines.append(f"{emoji} *{asset}*: ${d['price']:,.2f} ({d['change_24h']:+.2f}%) | Vol: ${d['volume_24h']/1e9:.1f}B | RSI: {d['rsi']:.0f}
")
        await update.message.reply_text("".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "🤖 *MiMo Trading Agent v2.0*

"
            "📋 *Commands:*
"
            "`/scan BTC ETH` — Signal scan
"
            "`/trade BTC 10000` — Auto-trade
"
            "`/risk 10000` — Risk analysis
"
            "`/backtest BTC 90` — Backtest
"
            "`/montecarlo 10000` — Monte Carlo
"
            "`/regime BTC` — Market regime
"
            "`/dca ETH 100` — Smart DCA
"
            "`/portfolio` — Positions
"
            "`/market` — Market data
"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        app = Application.builder().token(self.token).build()

        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("scan", self.cmd_scan))
        app.add_handler(CommandHandler("trade", self.cmd_trade))
        app.add_handler(CommandHandler("risk", self.cmd_risk))
        app.add_handler(CommandHandler("backtest", self.cmd_backtest))
        app.add_handler(CommandHandler("montecarlo", self.cmd_montecarlo))
        app.add_handler(CommandHandler("regime", self.cmd_regime))
        app.add_handler(CommandHandler("dca", self.cmd_dca))
        app.add_handler(CommandHandler("portfolio", self.cmd_portfolio))
        app.add_handler(CommandHandler("market", self.cmd_market))

        print("🤖 MiMo Trading Bot started!")
        app.run_polling()


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ Set TELEGRAM_BOT_TOKEN environment variable")
        sys.exit(1)
    bot = TradingBot(token)
    bot.run()
