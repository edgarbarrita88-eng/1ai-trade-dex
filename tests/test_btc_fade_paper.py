"""Targeted btc_fade paper cycle dry-run. No API, mocks only."""
import sys, os, asyncio
sys.path.insert(0, "/home/openclaw/projects/1ai-trade-dex")
os.environ.setdefault("TRADING_MODE", "paper")

from unittest.mock import MagicMock, AsyncMock
from backend.strategies.btc_fade import BtcFadeStrategy
from backend.strategies.base import StrategyContext, CycleResult
from backend.config import settings

async def run():
    strat = BtcFadeStrategy()
    mock_clob = MagicMock()
    mock_clob.get_mid_price = AsyncMock(return_value=0.5)
    mock_clob.get_order_book = AsyncMock(return_value=MagicMock(
        best_bid=0.49, best_ask=0.51, bids=[], asks=[],
    ))
    mock_db = MagicMock()
    mock_db.execute = MagicMock(return_value=[])
    
    # mock market from Gamma
    market = {
        "id": "btc5m-test",
        "condition_id": "btc5m-test",
        "question": "Will BTC be above $100k in 5 min?",
        "title": "Will BTC be above $100k in 5 min?",
        "outcomePrices": "[0.52, 0.48]",
        "volume": "10000",
        "openInterest": "5000",
        "end_date_iso": "2030-01-01T00:00:00Z",  # far future
        "category": "crypto",
        "active": True,
        "clob_token_ids": '{"YES":"tok_yes","NO":"tok_no"}',
    }
    from backend.data.shared_client import get_shared_client
    shared = MagicMock()
    shared.fetch_markets = AsyncMock(return_value=[market])
    
    from loguru import logger
    ctx = StrategyContext(
        db=mock_db,
        clob=mock_clob,
        settings=settings,
        logger=logger,
        params={"bankroll_pct": 0.02},
        mode="paper",
        bankroll=1000.0,
    )
    result = await strat.run_cycle(ctx)
    print("CycleResult:", result.decisions_recorded, "decisions,", result.trades_attempted, "attempted,", result.trades_placed, "placed")
    for d in result.decisions[:2]:
        print("  decision:", d.get("market_ticker"), "edge=", d.get("edge"), "price=", d.get("entry_price"), "end_date=", d.get("market_end_date"))
    return result

if __name__ == "__main__":
    asyncio.run(run())