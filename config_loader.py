import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class MarketToggle:
    spot: bool
    futures: bool


@dataclass
class ExchangeConfig:
    name: str
    id: str
    markets: MarketToggle


@dataclass
class FilterConfig:
    quote: str
    only_active: bool


@dataclass
class ArbitrageConfig:
    min_spread_percent: float


@dataclass
class AppConfig:
    exchanges: List[ExchangeConfig]
    filters: FilterConfig
    arbitrage: ArbitrageConfig


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path: str = "config.yaml") -> AppConfig:
    raw = _load_yaml(Path(path))
    exchanges = [
        ExchangeConfig(
            name=item["name"],
            id=item["id"],
            markets=MarketToggle(**item.get("markets", {})),
        )
        for item in raw.get("exchanges", [])
    ]
    filters = FilterConfig(**raw.get("filters", {}))
    arbitrage = ArbitrageConfig(**raw.get("arbitrage", {}))
    return AppConfig(exchanges=exchanges, filters=filters, arbitrage=arbitrage)
