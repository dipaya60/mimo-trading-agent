# MiMo Trading Agent

> **v2.0** — Automated Trading Bot + Portfolio Risk Manager  
> Powered by **Xiaomi MiMo-V2.5-Pro** · Multi-Strategy Consensus · 8 Assets

Built for the [100T Token Creator Incentive Program](https://100t.xiaomimimo.com/)

---

## The Problem

Crypto trading bots are either too simple (single strategy, no risk management) or too complex (require quant PhDs to configure). Most retail traders use basic DCA or grid bots that ignore market regime changes, have no stop-loss logic, and zero portfolio risk monitoring. They make money in bull markets and give it all back in crashes.

## The Solution

MiMo Trading Agent combines **3 proven trading strategies** with **5-dimension portfolio risk management**, all powered by MiMo-V2.5-Pro's reasoning engine. It doesn't just generate signals — it explains *why*, sizes positions correctly, monitors risk in real-time, and automatically exits when stop-losses or take-profits hit.

**Trading + Risk in one agent.** Not two separate tools.

---

## 🎯 Multi-Strategy Consensus Engine

3 strategies vote on every trade. Consensus reduces false signals:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL GENERATION PIPELINE                    │
├──────────────┬──────────────────────────────────────────────────┤
│  MOMENTUM    │  Trend-following: buy strength, sell weakness    │
│              │  RSI + Volume + 24h change → directional signal  │
├──────────────┼──────────────────────────────────────────────────┤
│  MEAN REV.   │  Buy oversold dips, sell overbought rallies     │
│              │  RSI + Bollinger Bands → reversal signals        │
├──────────────┼──────────────────────────────────────────────────┤
│  BREAKOUT    │  Trade breakouts from support/resistance        │
│              │  Price vs S/R levels + Volume → breakout signals │
├──────────────┼──────────────────────────────────────────────────┤
│  CONSENSUS   │  Weighted vote: buy_score vs sell_score          │
│              │  Strong consensus (>1.5x) → actionable trade     │
└──────────────┴──────────────────────────────────────────────────┘
```

| Strategy | Timeframe | Best For | Risk/Reward |
|----------|-----------|----------|-------------|
| 🏃 Momentum | 4h | Trending markets | 2.0x |
| 🔄 Mean Reversion | 1d | Range-bound markets | 1.7x |
| 💥 Breakout | 1h | Volatility expansion | 3.0x |

---

## 🛡️ Portfolio Risk Manager

5-dimension real-time risk monitoring:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Concentration | 25% | Single position % of portfolio |
| Volatility | 25% | 24h price movement magnitude |
| Liquidity | 20% | Trading volume depth |
| Correlation | 20% | All-long or all-short bias |
| Value at Risk | 10% | 95% confidence maximum loss |

**Risk levels:** 🟢 LOW (0-25) · 🟡 MEDIUM (26-50) · 🟠 HIGH (51-75) · 🔴 CRITICAL (76-100)

**Features:**
- **Kelly Criterion position sizing** — optimal bet size based on edge and risk
- **Automatic stop-loss/take-profit** — exits positions when targets hit
- **Drawdown monitoring** — alerts when portfolio drops below threshold
- **Correlation detection** — warns when all positions move together

---

## ⚡ Quick Start

```bash
git clone https://github.com/dipaya60/mimo-trading-agent.git
cd mimo-trading-agent
pip install -r requirements.txt
cp .env.example .env   # add your MiMo API key

# Scan a single asset
python main.py scan BTC

# Scan multiple assets
python main.py scan BTC ETH SOL BNB ARB

# Auto-trade with $10,000 capital
python main.py trade BTC --capital 10000
python main.py trade ETH --capital 50000

# Portfolio risk analysis
python main.py risk --capital 10000

# Show open positions
python main.py portfolio

# Full demo
python main.py demo
```

### Docker

```bash
docker-compose up -d
docker-compose run mimo-trader demo
```

---

## 🏗️ Architecture

```
mimo-trading-agent/
├── src/
│   ├── client.py              # MiMo API client (async, retry)
│   ├── config.py              # Configuration
│   │
│   ├── trading/
│   │   ├── engine.py          # Trading engine + position manager
│   │   └── strategy.py        # 3 strategies: Momentum, Mean Rev, Breakout
│   │
│   ├── risk/
│   │   └── manager.py         # 5-dimension risk analyzer + position sizing
│   │
│   ├── market/
│   │   └── data.py            # Market data feed (CoinGecko + demo)
│   │
│   └── utils/
│       └── logger.py          # Structured logging
│
├── main.py                    # CLI entry (Rich-powered)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 🧠 Why MiMo-V2.5-Pro?

1. **Reasoning** — Explains *why* each trade signal is generated across 3 strategies
2. **Risk Assessment** — Multi-dimensional portfolio risk with actionable recommendations
3. **Structured Output** — Reliable JSON for programmatic execution
4. **Cost Efficiency** — 100T program makes heavy daily scanning accessible

---

## 🛣️ Roadmap

- [x] 3 trading strategies with consensus engine
- [x] 5-dimension portfolio risk manager
- [x] Kelly Criterion position sizing
- [x] Auto stop-loss/take-profit
- [x] CLI + Docker deployment
- [ ] Real-time price feeds (CoinGecko API)
- [ ] Backtesting framework (historical data)
- [ ] Telegram/Discord trade alerts
- [ ] Web dashboard (React)
- [ ] Exchange integration (Binance, Bybit)

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**Powered by Xiaomi MiMo-V2.5-Pro**

[🌐 MiMo](https://mimo.xiaomi.com) · [📚 API Docs](https://platform.xiaomimimo.com/#/docs/welcome) · [🎮 Studio](https://aistudio.xiaomimimo.com)

*100T Token Creator Incentive Program*

</div>
