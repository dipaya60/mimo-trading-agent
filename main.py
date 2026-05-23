#!/usr/bin/env python3
"""
MiMo Trading Agent — Automated Trading Bot + Portfolio Risk Manager
Powered by Xiaomi MiMo-V2.5-Pro

Usage:
    python main.py scan BTC               # Scan + consensus signal
    python main.py scan BTC ETH SOL       # Multi-asset scan
    python main.py trade BTC --capital 10000   # Auto-trade with $10k
    python main.py risk --capital 10000    # Portfolio risk analysis
    python main.py portfolio              # Show open positions
    python main.py demo                   # Full demo
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
from src.risk.manager import RiskManager
from src.market.data import MarketDataFeed

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

    assets = args.assets if args.assets else ["BTC"]
    console.print(f"\n🔍 Scanning {', '.join(assets)}...\n")

    for asset in assets:
        md = feed.get_price(asset)
        result = engine.scan(md)
        console.print(engine.format_scan(result))

    console.print()


def cmd_trade(args):
    client = MiMoClient()
    engine = TradingEngine(client)
    feed = MarketDataFeed()
    risk_mgr = RiskManager()

    md = feed.get_price(args.asset)
    console.print(f"\n⚡ Trading {args.asset.upper()} — Capital: ${args.capital:,.0f}\n")

    # Market data
    console.print(f"   📊 {md['name']}: ${md['price']:,.2f} ({md['change_24h']:+.2f}%)")
    console.print(f"   Volume: ${md['volume_24h']/1e9:.1f}B | RSI: {md['rsi']:.0f}\n")

    # Generate signal
    signal = engine.generate_signal(md)
    emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "HOLD": "⚪", "SELL": "🔴", "STRONG_SELL": "🔴🔴"}
    console.print(f"   {emoji.get(signal.signal.value, '⚪')} Signal: {signal.signal.value} ({signal.confidence}% confidence)")
    console.print(f"   💡 {signal.reasoning}\n")

    if signal.signal.value in ("BUY", "STRONG_BUY", "SELL", "STRONG_SELL"):
        # Position sizing
        size = risk_mgr.calculate_position_size(args.capital, 2, signal.price, signal.stop_loss)
        console.print(f"   📐 Position Size: ${size:,.2f} ({size/args.capital*100:.1f}% of portfolio)")
        console.print(f"   🛑 Stop Loss: ${signal.stop_loss:,.2f}")
        console.print(f"   🎯 Take Profit: ${signal.take_profit:,.2f}")
        console.print(f"   📊 Risk/Reward: {signal.risk_reward_ratio:.1f}x")

        # Open position
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

    # Generate some positions for demo
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
        # Force at least one position for demo
        md = feed.get_price("BTC")
        market_data["BTC"] = md
        signal = engine.generate_signal(md)
        pos = engine.open_position(signal, args.capital)
        positions.append({"asset": pos.asset, "size": pos.size_usd, "side": pos.side})

    metrics = risk_mgr.analyze_portfolio(positions, args.capital, market_data)
    console.print(risk_mgr.format_metrics(metrics))
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

    console.print("1️⃣ Market Data Feed")
    data = feed.get_all()
    console.print(feed.format_prices(data))
    console.print()

    console.print("2️⃣ Multi-Asset Scan (BTC, ETH, SOL)")
    for asset in ["BTC", "ETH", "SOL"]:
        md = feed.get_price(asset)
        result = engine.scan(md)
        console.print(engine.format_scan(result))
    console.print()

    console.print("3️⃣ Automated Trade Execution ($10,000)")
    md = feed.get_price("ETH")
    signal = engine.generate_signal(md)
    pos = engine.open_position(signal, 10000)
    console.print(f"   ✅ Opened: {pos.side} {pos.asset} @ ${pos.entry_price:,.2f} | Size: ${pos.size_usd:,.2f}")
    console.print(f"   🛑 SL: ${pos.stop_loss:,.2f} | 🎯 TP: ${pos.take_profit:,.2f}")
    console.print(f"   💡 {signal.reasoning}")
    console.print()

    console.print("4️⃣ Portfolio Risk Analysis")
    positions = [{"asset": pos.asset, "size": pos.size_usd, "side": pos.side}]
    all_md = feed.get_all()
    metrics = risk_mgr.analyze_portfolio(positions, 10000, all_md)
    console.print(risk_mgr.format_metrics(metrics))
    console.print()

    console.print("5️⃣ Portfolio Summary")
    summary = engine.get_portfolio_summary()
    console.print(f"   Positions: {summary['open_positions']} | Win Rate: {summary['win_rate']}%")
    console.print(f"   Unrealized: ${summary['unrealized_pnl']:+,.2f} | Realized: ${summary['realized_pnl']:+,.2f}")
    console.print()

    console.print("[bold green]✅ Demo complete![/bold green]\n")


def main():
    p = argparse.ArgumentParser(description="MiMo Trading Agent")
    sub = p.add_subparsers(dest="cmd")

    # Scan
    s = sub.add_parser("scan", help="Scan assets for trading signals")
    s.add_argument("assets", nargs="+", help="Assets to scan (BTC, ETH, SOL...)")
    s.set_defaults(func=cmd_scan)

    # Trade
    t = sub.add_parser("trade", help="Auto-execute trade")
    t.add_argument("asset", help="Asset to trade")
    t.add_argument("--capital", type=float, required=True, help="Portfolio capital in USD")
    t.set_defaults(func=cmd_trade)

    # Risk
    r = sub.add_parser("risk", help="Portfolio risk analysis")
    r.add_argument("--capital", type=float, required=True, help="Portfolio capital in USD")
    r.set_defaults(func=cmd_risk)

    # Portfolio
    pr = sub.add_parser("portfolio", help="Show portfolio summary")
    pr.set_defaults(func=cmd_portfolio)

    # Demo
    d = sub.add_parser("demo", help="Full demo")
    d.set_defaults(func=cmd_demo)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
