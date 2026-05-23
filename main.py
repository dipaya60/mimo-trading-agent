#!/usr/bin/env python3
"""
MiMo Trading Agent — Automated Trading Bot + Portfolio Risk Manager
Powered by Xiaomi MiMo-V2.5-Pro

Usage:
    python main.py scan BTC                    # Multi-strategy consensus signal
    python main.py scan BTC ETH SOL            # Multi-asset scan
    python main.py trade BTC --capital 10000   # Auto-trade with $10k
    python main.py risk --capital 10000        # Portfolio risk analysis
    python main.py backtest BTC --days 90      # Backtest all strategies
    python main.py montecarlo --capital 10000  # Monte Carlo simulation
    python main.py regime BTC                  # Detect market regime
    python main.py dca ETH --amount 100        # Smart DCA order
    python main.py portfolio                   # Show open positions
    python main.py demo                        # Full demo
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent))

from src.client import MiMoClient
from src.config import Config
from src.trading.engine import TradingEngine
from src.trading.backtester import Backtester
from src.trading.dca import SmartDCA
from src.risk.manager import RiskManager
from src.risk.monte_carlo import MonteCarloSimulator
from src.market.data import MarketDataFeed
from src.market.regime import RegimeDetector

console = Console()


def banner():
    console.print(Panel.fit(
        "[bold cyan]MiMo Trading Agent v2.0[/bold cyan]\n"
        "[dim]Automated Trading Bot + Portfolio Risk Manager | Xiaomi MiMo-V2.5-Pro[/dim]",
        border_style="cyan"
    ))


def cmd_scan(args):
    client = MiMoClient()
    engine = TradingEngine(client)
    feed = MarketDataFeed()
    regime = RegimeDetector()

    assets = args.assets if args.assets else ["BTC"]
    console.print(f"\n🔍 Scanning {', '.join(assets)}...\n")

    for asset in assets:
        md = feed.get_price(asset)
        result = engine.scan(md)
        console.print(engine.format_scan(result))

        # Show regime
        rr = regime.detect(md)
        console.print(regime.format_report(rr, asset))

    console.print()


def cmd_trade(args):
    client = MiMoClient()
    engine = TradingEngine(client)
    feed = MarketDataFeed()
    risk_mgr = RiskManager()

    md = feed.get_price(args.asset)
    console.print(f"\n⚡ Trading {args.asset.upper()} — Capital: ${args.capital:,.0f}\n")

    console.print(f"   📊 {md['name']}: ${md['price']:,.2f} ({md['change_24h']:+.2f}%)")
    console.print(f"   Volume: ${md['volume_24h']/1e9:.1f}B | RSI: {md['rsi']:.0f}\n")

    signal = engine.generate_signal(md)
    emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}
    console.print(f"   {emoji.get(signal.signal.value, '⚪')} Signal: {signal.signal.value} ({signal.confidence}% confidence)")
    console.print(f"   💡 {signal.reasoning}\n")

    if signal.signal.value in ("BUY", "STRONG_BUY", "SELL", "STRONG_SELL"):
        size = risk_mgr.calculate_position_size(args.capital, 2, signal.price, signal.stop_loss)
        console.print(f"   📐 Position Size: ${size:,.2f} ({size/args.capital*100:.1f}% of portfolio)")
        console.print(f"   🛑 Stop Loss: ${signal.stop_loss:,.2f}")
        console.print(f"   🎯 Take Profit: ${signal.take_profit:,.2f}")
        console.print(f"   📊 Risk/Reward: {signal.risk_reward_ratio:.1f}x")

        pos = engine.open_position(signal, args.capital)
        console.print(f"\n   ✅ Position opened: {pos.side} {pos.asset} @ ${pos.entry_price:,.2f}")
        console.print(f"   Size: ${pos.size_usd:,.2f}\n")
    else:
        console.print("   ⏸️ No trade — signal is HOLD\n")


def cmd_risk(args):
    client = MiMoClient()
    engine = TradingEngine(client)
    risk_mgr = RiskManager()
    feed = MarketDataFeed()

    console.print(f"\n🛡️ Portfolio Risk Analysis — Capital: ${args.capital:,.0f}\n")

    assets = ["BTC", "ETH", "SOL"]
    positions = []
    market_data = {}

    for asset in assets:
        md = feed.get_price(asset)
        market_data[asset] = md
        signal = engine.generate_signal(md)
        if signal.signal.value in ("BUY", "STRONG_BUY"):
            pos = engine.open_position(signal, args.capital)
            positions.append({"asset": pos.asset, "size": pos.size_usd, "side": pos.side})

    if not positions:
        md = feed.get_price("BTC")
        market_data["BTC"] = md
        signal = engine.generate_signal(md)
        pos = engine.open_position(signal, args.capital)
        positions.append({"asset": pos.asset, "size": pos.size_usd, "side": pos.side})

    metrics = risk_mgr.analyze_portfolio(positions, args.capital, market_data)
    console.print(risk_mgr.format_metrics(metrics))
    console.print()


def cmd_backtest(args):
    bt = Backtester(initial_capital=args.capital)
    strategies = ["Momentum", "Mean Reversion", "Breakout", "Consensus"]

    console.print(f"\n📊 Backtesting all strategies on {args.asset.upper()} ({args.days} days, ${args.capital:,.0f})\n")

    t = Table(title="Backtest Results")
    t.add_column("Strategy", style="cyan")
    t.add_column("Trades", style="white")
    t.add_column("Win Rate", style="green")
    t.add_column("Return", style="green")
    t.add_column("Max DD", style="red")
    t.add_column("Sharpe", style="yellow")
    t.add_column("Profit Factor", style="green")
    t.add_column("Expectancy", style="cyan")

    for strat in strategies:
        result = bt.run(strat, args.asset, days=args.days)
        ret_color = "green" if result.total_return_pct > 0 else "red"
        t.add_row(
            strat, str(result.total_trades),
            f"{result.win_rate:.1f}%",
            f"[{ret_color}]{result.total_return_pct:+.2f}%[/{ret_color}]",
            f"{result.max_drawdown_pct:.2f}%",
            f"{result.sharpe_ratio:.2f}",
            f"{result.profit_factor:.2f}",
            f"{result.expectancy:+.2f}%",
        )

    console.print(t)
    console.print()


def cmd_montecarlo(args):
    mc = MonteCarloSimulator(num_simulations=1000)
    console.print(f"\n🎲 Monte Carlo Portfolio Simulation — ${args.capital:,.0f}\n")

    result = mc.simulate(
        initial_capital=args.capital,
        expected_return_pct=args.return_pct,
        volatility_pct=args.volatility,
        days=args.days,
    )
    console.print(mc.format_result(result))
    console.print()


def cmd_regime(args):
    feed = MarketDataFeed()
    regime = RegimeDetector()
    md = feed.get_price(args.asset)
    report = regime.detect(md)
    console.print(regime.format_report(report, args.asset))
    console.print()


def cmd_dca(args):
    feed = MarketDataFeed()
    dca = SmartDCA(base_amount_usd=args.amount)
    md = feed.get_price(args.asset)

    order = dca.evaluate(md)
    console.print(dca.format_order(order))
    console.print()


def cmd_portfolio(args):
    client = MiMoClient()
    engine = TradingEngine(client)
    summary = engine.get_portfolio_summary()

    console.print(f"\n📋 Portfolio Summary\n")
    console.print(f"   Open Positions: {summary['open_positions']}")
    console.print(f"   Total Trades: {summary['total_trades']}")
    console.print(f"   Win Rate: {summary['win_rate']}%")
    console.print(f"   Unrealized PnL: ${summary['unrealized_pnl']:+,.2f}")
    console.print(f"   Realized PnL: ${summary['realized_pnl']:+,.2f}")
    console.print()


def cmd_demo(args):
    banner()
    client = MiMoClient()
    engine = TradingEngine(client)
    risk_mgr = RiskManager()
    feed = MarketDataFeed()
    regime = RegimeDetector()
    bt = Backtester(10000)
    mc = MonteCarloSimulator(1000)
    dca = SmartDCA(100)

    console.print("1️⃣ Market Data Feed (8 assets)")
    data = feed.get_all()
    console.print(feed.format_prices(data))
    console.print()

    console.print("2️⃣ Market Regime Detection")
    md_btc = feed.get_price("BTC")
    report = regime.detect(md_btc)
    console.print(regime.format_report(report, "BTC"))
    console.print()

    console.print("3️⃣ Multi-Strategy Consensus Scan")
    for asset in ["BTC", "ETH", "SOL"]:
        md = feed.get_price(asset)
        result = engine.scan(md)
        console.print(engine.format_scan(result))
    console.print()

    console.print("4️⃣ Automated Trade Execution ($10,000)")
    md = feed.get_price("ETH")
    signal = engine.generate_signal(md)
    pos = engine.open_position(signal, 10000)
    console.print(f"   ✅ Opened: {pos.side} {pos.asset} @ ${pos.entry_price:,.2f} | Size: ${pos.size_usd:,.2f}")
    console.print(f"   🛑 SL: ${pos.stop_loss:,.2f} | 🎯 TP: ${pos.take_profit:,.2f}")
    console.print(f"   💡 {signal.reasoning}")
    console.print()

    console.print("5️⃣ Portfolio Risk Analysis")
    positions = [{"asset": pos.asset, "size": pos.size_usd, "side": pos.side}]
    all_md = feed.get_all()
    metrics = risk_mgr.analyze_portfolio(positions, 10000, all_md)
    console.print(risk_mgr.format_metrics(metrics))
    console.print()

    console.print("6️⃣ Backtest: All Strategies (90 days)")
    t = Table(title="Backtest Summary")
    t.add_column("Strategy", style="cyan")
    t.add_column("Win Rate", style="green")
    t.add_column("Return", style="green")
    t.add_column("Sharpe", style="yellow")
    for strat in ["Momentum", "Mean Reversion", "Breakout", "Consensus"]:
        r = bt.run(strat, "BTC", days=90)
        ret_c = "green" if r.total_return_pct > 0 else "red"
        t.add_row(strat, f"{r.win_rate:.1f}%", f"[{ret_c}]{r.total_return_pct:+.2f}%[/{ret_c}]", f"{r.sharpe_ratio:.2f}")
    console.print(t)
    console.print()

    console.print("7️⃣ Monte Carlo Simulation ($10,000, 365 days)")
    mc_result = mc.simulate(10000, expected_return_pct=30, volatility_pct=60, days=365)
    console.print(mc.format_result(mc_result))
    console.print()

    console.print("8️⃣ Smart DCA Order")
    dca_order = dca.evaluate(feed.get_price("ETH"))
    console.print(dca.format_order(dca_order))
    console.print()

    console.print("[bold green]✅ Demo complete![/bold green]\n")


def cmd_bot(args):
    """Launch Telegram bot."""
    import os
    from src.telegram.bot import TradingBot
    token = os.getenv("TELEGRAM_BOT_TOKEN", args.token)
    if not token:
        print("❌ Set TELEGRAM_BOT_TOKEN or use --token")
        return
    bot = TradingBot(token)
    bot.run()


def main():
    p = argparse.ArgumentParser(description="MiMo Trading Agent")
    sub = p.add_subparsers(dest="cmd")

    # Scan
    s = sub.add_parser("scan", help="Scan assets for trading signals")
    s.add_argument("assets", nargs="+", help="Assets to scan")
    s.set_defaults(func=cmd_scan)

    # Trade
    t = sub.add_parser("trade", help="Auto-execute trade")
    t.add_argument("asset", help="Asset to trade")
    t.add_argument("--capital", type=float, required=True)
    t.set_defaults(func=cmd_trade)

    # Risk
    r = sub.add_parser("risk", help="Portfolio risk analysis")
    r.add_argument("--capital", type=float, required=True)
    r.set_defaults(func=cmd_risk)

    # Backtest
    bt = sub.add_parser("backtest", help="Backtest strategies")
    bt.add_argument("asset", help="Asset to backtest")
    bt.add_argument("--capital", type=float, default=10000)
    bt.add_argument("--days", type=int, default=90)
    bt.set_defaults(func=cmd_backtest)

    # Monte Carlo
    mc = sub.add_parser("montecarlo", help="Monte Carlo simulation")
    mc.add_argument("--capital", type=float, default=10000)
    mc.add_argument("--return-pct", type=float, default=30, help="Expected annual return %%")
    mc.add_argument("--volatility", type=float, default=60, help="Annual volatility %%")
    mc.add_argument("--days", type=int, default=365)
    mc.set_defaults(func=cmd_montecarlo)

    # Regime
    rg = sub.add_parser("regime", help="Detect market regime")
    rg.add_argument("asset", help="Asset to analyze")
    rg.set_defaults(func=cmd_regime)

    # DCA
    dc = sub.add_parser("dca", help="Smart DCA order")
    dc.add_argument("asset", help="Asset to DCA")
    dc.add_argument("--amount", type=float, default=100, help="Base amount USD")
    dc.set_defaults(func=cmd_dca)

    # Portfolio
    pr = sub.add_parser("portfolio", help="Show portfolio")
    pr.set_defaults(func=cmd_portfolio)

    # Demo
    d = sub.add_parser("demo", help="Full demo")
    d.set_defaults(func=cmd_demo)

    # Bot
    bt_cmd = sub.add_parser("bot", help="Launch Telegram bot")
    bt_cmd.add_argument("--token", default="", help="Telegram bot token")
    bt_cmd.set_defaults(func=cmd_bot)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
