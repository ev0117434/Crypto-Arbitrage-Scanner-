import ccxt
from typing import Dict

from market_types import FUTURES, SPOT, futures_default_type


DEFAULT_OPTIONS: Dict[str, Dict] = {
    "binance": {"options": {"defaultType": "spot"}},
    "bybit": {"options": {"defaultType": "spot"}},
    "okx": {"options": {"defaultType": "spot"}},
    "mexc": {"options": {"defaultType": "spot"}},
    "bingx": {"options": {"defaultType": "spot"}},
}


def create_client(exchange_id: str, market_type: str):
    options = DEFAULT_OPTIONS.get(exchange_id, {}).copy()
    if market_type == FUTURES:
        options.setdefault("options", {})["defaultType"] = futures_default_type(exchange_id)
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class(options)


def client_label(exchange_id: str, market_type: str) -> str:
    return f"{exchange_id}-{market_type}"
