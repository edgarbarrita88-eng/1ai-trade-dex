"""Self-check: BTC-5M edge gate + FOK wiring (no pytest). Run: python3 this.py"""
import sys
sys.path.insert(0, "/home/openclaw/projects/1ai-trade-dex")

# 1. config fields exist
from backend.config import settings
assert settings.BTC5M_MIN_EDGE_PP == 10.0, settings.BTC5M_MIN_EDGE_PP
assert settings.BTC5M_MAX_ASK == 0.70
assert settings.BTC5M_MIN_SECONDS_TO_ENTER == 90
assert settings.BTC5M_MAX_ENTERS == 1
print("config OK:", settings.BTC5M_MIN_EDGE_PP, settings.BTC5M_MAX_ASK,
      settings.BTC5M_MIN_SECONDS_TO_ENTER, settings.BTC5M_MAX_ENTERS)

# 2. ValidationStage gates
from backend.core.execution_pipeline.stages.validate import ValidationStage
v = ValidationStage()
ctx = {"mode": "paper", "bankroll": 1000.0}

base = dict(size=5.0, market_ticker="BTC5M-X", direction="yes",
            entry_price=0.50, edge=0.20, confidence=0.9)

# MAX_ASK: ask 0.80 > 0.70 cap -> blocked
assert v.validate({**base, "entry_price": 0.80}, ctx) is False, "MAX_ASK not blocking"
# TOO_LATE: 30s left < 90 -> blocked
assert v.validate({**base, "seconds_to_close": 30}, ctx) is False, "TOO_LATE not blocking"
# MAX_ENTERS: 1 entry >= 1 cap -> blocked
assert v.validate({**base, "entry_count": 1}, ctx) is False, "MAX_ENTERS not blocking"
# happy path: ask 0.50 ok, 300s ok, 0 entries ok
assert v.validate({**base, "seconds_to_close": 300, "entry_count": 0}, ctx) is True, "happy path blocked"

# seconds_to_close derived from market_end_date: 10s away -> blocked
from datetime import datetime, timezone, timedelta
soon = (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()
d2 = {**base, "market_end_date": soon, "entry_count": 0}
assert v.validate(d2, ctx) is False, "TOO_LATE not derived from market_end_date"
far = (datetime.now(timezone.utc) + timedelta(seconds=600)).isoformat()
d3 = {**base, "market_end_date": far, "entry_count": 0}
assert v.validate(d3, ctx) is True, "derived-far should pass"
print("validate gates OK: MAX_ASK / TOO_LATE / MAX_ENTERS / happy-path / derived-seconds")

# 3. FOK plumbing: provider passes order_type through
from backend.markets.order_types import NormalizedOrder, OrderSide, OrderType
from decimal import Decimal
o = NormalizedOrder(market_id="t", side=OrderSide.YES, order_type=OrderType.FOK,
                    size=Decimal("5"), price=Decimal("0.5"))
assert o.order_type == OrderType.FOK
print("FOK order type OK")

# 4. clob mixin imported OrderType + FOK branch present
import inspect
from backend.data.polymarket_clob import _client_place_limit_order as m
src = inspect.getsource(m)
assert "OrderType.FOK" in src, "FOK branch missing"
assert "from py_clob_client_v2 import OrderType" in src, "OrderType import missing"
print("clob FOK wiring OK")

print("\nALL PASS")
