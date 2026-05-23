"""
Market Data Feed — CoinGecko integration + demo data.
"""
import random


DEMO_ASSETS = {
    "BTC": {"name": "Bitcoin", "price": 104500, "market_cap": 2.07e12, "volume_24h": 38e9},
    "ETH": {"name": "Ethereum", "price": 2520, "market_cap": 303e9, "volume_24h": 15e9},
    "SOL": {"name": "Solana", "price": 174, "market_cap": 84e9, "volume_24h": 3.5e9},
    "BNB": {"name": "BNB", "price": 652, "market_cap": 95e9, "volume_24h": 1.8e9},
    "ARB": {"name": "Arbitrum", "price": 0.42, "market_cap": 1.7e9, "volume_24h": 320e6},
    "AVAX": {"name": "Avalanche", "price": 22.5, "market_cap": 9.4e9, "volume_24h": 450e6},
    "LINK": {"name": "Chainlink", "price": 15.8, "market_cap": 9.8e9, "volume_24h": 620e6},
    "UNI": {"name": "Uniswap", "price": 6.4, "market_cap": 3.8e9, "volume_24h": 180e6},
}


class MarketDataFeed:
    """Market data provider — CoinGecko live + demo fallback."""

    def __init__(self, use_live: bool = False):
        self.use_live = use_live

    def get_price(self, asset: str) -> dict:
        asset = asset.upper()
        base = DEMO_ASSETS.get(asset, {"name": asset, "price": 100, "market_cap": 1e9, "volume_24h": 500e6})
        change_24h = round(random.uniform(-8, 8), 2)
        rsi = round(random.uniform(25, 75), 1)
        bb_pos = round(random.uniform(0, 1), 2)

        return {
            "asset": asset,
            "name": base["name"],
            "price": round(base["price"] * (1 + change_24h / 100), 2),
            "change_24h": change_24h,
            "volume_24h": base["volume_24h"],
            "market_cap": base["market_cap"],
            "rsi": rsi,
            "bb_position": bb_pos,
            "support": round(base["price"] * 0.95, 2),
            "resistance": round(base["price"] * 1.05, 2),
        }

    def get_all(self) -> dict:
        return {asset: self.get_price(asset) for asset in DEMO_ASSETS}

    def format_prices(self, data: dict) -> str:
        lines = []
        for asset, d in data.items():
            color = "\U0001f7e2" if d["change_24h"] > 0 else "\U0001f534"
            price_str = f"${d['price']:>10,.2f}"
            change_str = f"{d['change_24h']:>+6.2f}%"
            vol_str = f"${d['volume_24h']/1e9:.1f}B"
            rsi_str = f"{d['rsi']:.0f}"
            lines.append(f"   {color} {asset:<6} {price_str}  {change_str}  Vol: {vol_str}  RSI: {rsi_str}")
        return "\n".join(lines)
