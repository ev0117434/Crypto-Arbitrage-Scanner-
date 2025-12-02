from typing import Iterable, Tuple

from market_types import FUTURES, SPOT
from prices import PriceStore


def _calc_spread(spot_price: float, futures_price: float) -> float:
    return (futures_price - spot_price) / spot_price * 100


def scan_spreads(
    price_store: PriceStore,
    pairs: Iterable[Tuple[str, str, str]],
    min_spread_percent: float,
) -> None:
    for symbol, spot_exchange, futures_exchange in pairs:
        spot = price_store.get(spot_exchange, SPOT, symbol)
        futures = price_store.get(futures_exchange, FUTURES, symbol)
        if not spot or not futures:
            continue
        spread = _calc_spread(spot.ask, futures.bid)
        if spread >= min_spread_percent:
            print(
                f"{symbol} | spot {spot_exchange} {spot.ask:.4f} < futures {futures_exchange} {futures.bid:.4f} | spread {spread:.2f}%"
            )
