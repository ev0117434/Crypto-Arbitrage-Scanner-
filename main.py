import time

from arb_spot_futures import scan_spreads
from config_loader import load_config
from exchanges_registry import create_client
from market_types import FUTURES, SPOT
from prices import PriceStore
from symbols_universe import build_symbol_map, normalize_symbol, spot_futures_pairs


def _timestamp(value) -> int:
    if value is None:
        return int(time.time() * 1000)
    return int(value)


def _fetch_tickers(exchange_id: str, market_type: str):
    client = create_client(exchange_id, market_type)
    return client.fetch_tickers()


def update_prices(store: PriceStore, symbol_map):
    for exchange_id, markets in symbol_map.items():
        for market_type, symbols in markets.items():
            if not symbols:
                continue
            try:
                tickers = _fetch_tickers(exchange_id, market_type)
            except Exception as exc:  # noqa: BLE001
                print(f"skip {exchange_id} {market_type}: {exc}")
                continue
            wanted = set(symbols)
            for symbol, ticker in tickers.items():
                norm = normalize_symbol(symbol)
                if norm not in wanted:
                    continue
                bid = ticker.get("bid")
                ask = ticker.get("ask")
                if bid is None or ask is None:
                    continue
                store.update(exchange_id, market_type, norm, float(bid), float(ask), _timestamp(ticker.get("timestamp")))


def main() -> None:
    config = load_config()
    symbol_map = build_symbol_map(config)
    pairs = spot_futures_pairs(symbol_map)
    if not pairs:
        print("Нет общих символов для сравнения")
        return
    store = PriceStore()
    update_prices(store, symbol_map)
    scan_spreads(store, pairs, config.arbitrage.min_spread_percent)


if __name__ == "__main__":
    main()
