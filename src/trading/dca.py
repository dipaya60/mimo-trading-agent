"""
Smart DCA (Dollar Cost Averaging) — AI-enhanced DCA with buy-the-dip logic.
Instead of fixed intervals, MiMo decides when to buy based on market conditions.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class DCAOrder:
    asset: str
    amount_usd: float
    price: float
    reasoning: str
    is_dip_buy: bool
    discount_from_avg: float


class SmartDCA:
    """AI-enhanced DCA strategy — buy more on dips, less on rallies."""

    def __init__(self, base_amount_usd: float = 100, dip_multiplier: float = 2.0, rally_divisor: float = 2.0):
        self.base_amount = base_amount_usd
        self.dip_multiplier = dip_multiplier
        self.rally_divisor = rally_divisor
        self.orders: List[DCAOrder] = []
        self.avg_price = 0
        self.total_invested = 0
        self.total_units = 0

    def evaluate(self, market_data: dict) -> DCAOrder:
        """Decide how much to buy based on current conditions."""
        asset = market_data.get("asset", "BTC")
        price = market_data.get("price", 0)
        change_24h = market_data.get("change_24h", 0)
        rsi = market_data.get("rsi", 50)

        # Calculate discount from average price
        if self.avg_price > 0:
            discount = (self.avg_price - price) / self.avg_price * 100
        else:
            discount = 0

        # Smart sizing
        if change_24h < -5 or rsi < 30:
            # Deep dip — aggressive buy
            amount = self.base_amount * self.dip_multiplier * 2
            reasoning = f"Deep dip ({change_24h:+.1f}%, RSI {rsi:.0f}) — aggressive DCA at ${price:,.0f}"
            is_dip = True
        elif change_24h < -3 or rsi < 40:
            # Moderate dip
            amount = self.base_amount * self.dip_multiplier
            reasoning = f"Moderate dip ({change_24h:+.1f}%) — increased DCA at ${price:,.0f}"
            is_dip = True
        elif change_24h > 5 or rsi > 70:
            # Rally — reduce buy
            amount = self.base_amount / self.rally_divisor
            reasoning = f"Rally ({change_24h:+.1f}%, RSI {rsi:.0f}) — reduced DCA at ${price:,.0f}"
            is_dip = False
        else:
            # Normal — base amount
            amount = self.base_amount
            reasoning = f"Standard DCA at ${price:,.0f} (RSI {rsi:.0f})"
            is_dip = False

        order = DCAOrder(
            asset=asset,
            amount_usd=round(amount, 2),
            price=price,
            reasoning=reasoning,
            is_dip_buy=is_dip,
            discount_from_avg=round(discount, 2),
        )

        # Update running average
        units = amount / price
        self.total_invested += amount
        self.total_units += units
        self.avg_price = self.total_invested / self.total_units if self.total_units > 0 else price

        self.orders.append(order)
        return order

    def get_summary(self) -> dict:
        return {
            "total_orders": len(self.orders),
            "total_invested": round(self.total_invested, 2),
            "avg_price": round(self.avg_price, 2),
            "dip_buys": sum(1 for o in self.orders if o.is_dip_buy),
            "total_units": round(self.total_units, 6),
        }

    def format_order(self, order: DCAOrder) -> str:
        emoji = "🟢🟢" if order.is_dip_buy else "🟢"
        return (
            f"{emoji} DCA Order: {order.asset}\n"
            f"   Amount: ${order.amount_usd:,.2f} @ ${order.price:,.2f}\n"
            f"   {order.reasoning}"
        )
