from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from market_types import FUTURES, SPOT

Key = Tuple[str, str, str]


@dataclass
class Price:
    bid: float
    ask: float
    ts: int


class PriceStore:
    def __init__(self) -> None:
        self._store: Dict[Key, Price] = {}

    def update(self, exchange: str, market: str, symbol: str, bid: float, ask: float, ts: int) -> None:
        self._store[(exchange, market, symbol)] = Price(bid=bid, ask=ask, ts=ts)

    def get(self, exchange: str, market: str, symbol: str) -> Optional[Price]:
        return self._store.get((exchange, market, symbol))
