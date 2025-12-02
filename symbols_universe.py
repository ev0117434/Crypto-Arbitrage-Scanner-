from typing import Dict, Iterable, List, Set, Tuple

import ccxt

from config_loader import AppConfig, ExchangeConfig
from exchanges_registry import create_client
from market_types import FUTURES, SPOT, futures_default_type

SymbolMap = Dict[str, Dict[str, List[str]]]


def normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace("-", "").upper()


def _load_markets(exchange: ccxt.Exchange) -> Dict:
    return exchange.load_markets()


def _filter_symbols(markets: Dict, quote: str, only_active: bool) -> List[str]:
    symbols = []
    for symbol, meta in markets.items():
        if only_active and not meta.get("active", True):
            continue
        if meta.get("quote", "").upper() != quote.upper():
            continue
        symbols.append(normalize_symbol(symbol))
    return symbols


def _symbols_for_exchange(cfg: ExchangeConfig, filters) -> Dict[str, List[str]]:
    results: Dict[str, List[str]] = {}
    if cfg.markets.spot:
        spot = create_client(cfg.id, SPOT)
        results[SPOT] = _filter_symbols(_load_markets(spot), filters.quote, filters.only_active)
    if cfg.markets.futures:
        futures_client = create_client(cfg.id, FUTURES)
        futures_client.options = {"defaultType": futures_default_type(cfg.id)}
        results[FUTURES] = _filter_symbols(_load_markets(futures_client), filters.quote, filters.only_active)
    return results


def build_symbol_map(app_config: AppConfig) -> SymbolMap:
    all_symbols: SymbolMap = {}
    for exchange_cfg in app_config.exchanges:
        all_symbols[exchange_cfg.id] = _symbols_for_exchange(exchange_cfg, app_config.filters)
    return all_symbols


def common_tradables(symbol_map: SymbolMap) -> Set[str]:
    spot_sets: List[Set[str]] = []
    futures_sets: List[Set[str]] = []
    for markets in symbol_map.values():
        if SPOT in markets:
            spot_sets.append(set(markets[SPOT]))
        if FUTURES in markets:
            futures_sets.append(set(markets[FUTURES]))
    if not spot_sets or not futures_sets:
        return set()
    common_spot = set.intersection(*spot_sets)
    common_futures = set.intersection(*futures_sets)
    return common_spot & common_futures


def spot_futures_pairs(symbol_map: SymbolMap) -> List[Tuple[str, str, str]]:
    symbols = common_tradables(symbol_map)
    pairs: List[Tuple[str, str, str]] = []
    exchanges = list(symbol_map.keys())
    for symbol in symbols:
        for spot_exchange in exchanges:
            if SPOT not in symbol_map[spot_exchange]:
                continue
            if symbol not in symbol_map[spot_exchange][SPOT]:
                continue
            for futures_exchange in exchanges:
                if FUTURES not in symbol_map[futures_exchange]:
                    continue
                if symbol not in symbol_map[futures_exchange][FUTURES]:
                    continue
                pairs.append((symbol, spot_exchange, futures_exchange))
    return pairs
