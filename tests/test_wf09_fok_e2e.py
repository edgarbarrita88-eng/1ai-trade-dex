"""WF09 FOK end-to-end: real PolymarketCLOB paper mixin + HFT retry path. No network/funds."""
import sys, os, asyncio
sys.path.insert(0, "/home/openclaw/projects/1ai-trade-dex")
os.environ.setdefault("TRADING_MODE", "paper")

from unittest.mock import MagicMock, AsyncMock

async def run():
    from backend.data.polymarket_clob.client import PolymarketCLOB
    from backend.core.hft_executor import _place_order_with_retry

    clob = PolymarketCLOB(mode="paper")
    r = await clob.place_limit_order(
        token_id="tok_test", side="BUY", price=0.50, size=5.0, order_type="FOK")
    print("FOK paper:", r.success, r.order_id, r.fill_price, r.fill_size)
    assert r.success is True, r.error
    assert r.idempotency_key, "idempotency key must be derived"

    # HFT retry path propagates FOK
    mock = MagicMock()
    mock.place_limit_order = AsyncMock(return_value=r)
    oid = await _place_order_with_retry(mock, "tok_test", "BUY", 0.50, 5.0, "sig1")
    print("HFT order_id:", oid, "| kwargs:", mock.place_limit_order.call_args.kwargs)
    assert oid == r.order_id
    assert mock.place_limit_order.call_args.kwargs.get("order_type") == "FOK"

    # GTC fallback when disabled
    import backend.core.hft_executor as hx
    orig = hx.settings.BTC5M_FOK
    hx.settings.BTC5M_FOK = False
    mock2 = MagicMock()
    mock2.place_limit_order = AsyncMock(return_value=r)
    await _place_order_with_retry(mock2, "tok_test", "BUY", 0.50, 5.0, "sig2")
    assert mock2.place_limit_order.call_args.kwargs.get("order_type") == "GTC"
    hx.settings.BTC5M_FOK = orig
    print("GTC fallback OK")
    print("E2E FOK PASS")

if __name__ == "__main__":
    asyncio.run(run())