SPOT = "spot"
FUTURES = "futures"


def futures_default_type(exchange_id: str) -> str:
    if exchange_id in {"binance", "mexc", "bingx"}:
        return "swap"
    if exchange_id == "okx":
        return "swap"
    return "future"
