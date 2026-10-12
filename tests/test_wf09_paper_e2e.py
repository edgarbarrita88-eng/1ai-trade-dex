"""WF09 paper e2e: decision -> ValidationStage gates -> paper place_order. No live funds."""
import sys, os, asyncio
sys.path.insert(0, "/home/openclaw/projects/1ai-trade-dex")
os.environ.setdefault("TRADING_MODE", "paper")

from datetime import datetime, timezone, timedelta
from decimal import Decimal

async def run():
    from backend.core.execution_pipeline.stages.validate import ValidationStage
    from backend.markets.providers.polymarket_provider import PolymarketProvider
    from backend.markets.order_types import NormalizedOrder, OrderSide, OrderType

    v = ValidationStage()
    ctx = {"mode": "paper", "bankroll": 1000.0}
    far = (datetime.now(timezone.utc) + timedelta(seconds=600)).isoformat()

    # pWin 0.61 vs ask 0.50 -> edge 11pp > 10 cap; ask ok; 600s left; 0 entries
    decision = dict(size=5.0, market_ticker="BTC-15m-test", direction="yes",
                    entry_price=0.50, edge=0.11, confidence=0.9,
                    market_end_date=far, entry_count=0, seconds_to_close=600)
    ok = v.validate(decision, ctx)
    print("validate:", "PASS" if ok else "BLOCKED")

    provider = PolymarketProvider(paper_mode=True)
    order = NormalizedOrder(market_id="tok_yes_test", side=OrderSide.BUY,
                            order_type=OrderType.FOK,
                            size=Decimal("5"), price=Decimal("0.50"))
    result = await provider.place_order(order)
    print("place_order:", result.status, "venue_order_id=", result.venue_order_id,
          "filled=", result.filled_size, "@", result.filled_avg_price)
    assert ok is True, "validate must pass for happy path"
    assert str(result.status.value).lower() == "filled", result.status
    assert result.venue_order_id.startswith("paper_"), result.venue_order_id
    print("E2E PAPER PASS")

if __name__ == "__main__":
    asyncio.run(run())