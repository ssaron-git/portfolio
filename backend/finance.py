import time
import httpx

_cache: dict[str, dict] = {}
_CACHE_TTL = 3600  # 1 hour


def _get_from_cache(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _set_cache(key: str, data: dict):
    _cache[key] = {"data": data, "ts": time.time()}


async def fetch_chart_data(symbol: str, years: int) -> dict:
    cache_key = f"{symbol}_{years}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    period_map = {1: "1y", 5: "5y", 10: "10y", 15: "15y", 20: "20y"}
    period = period_map.get(years, "10y")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": period, "interval": "1d"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
        raw = resp.json()

    result_data = raw.get("chart", {}).get("result", [])
    if not result_data:
        return {"dates": [], "prices": []}

    item = result_data[0]
    timestamps = item.get("timestamp", [])
    closes = item.get("indicators", {}).get("quote", [{}])[0].get("close", [])

    # Filter out None values and pair with timestamps
    paired = [(t, c) for t, c in zip(timestamps, closes) if c is not None]
    if not paired:
        return {"dates": [], "prices": []}

    dates = [time.strftime("%Y-%m-%d", time.gmtime(t)) for t, _ in paired]
    prices = [round(c, 4) for _, c in paired]

    data = {"dates": dates, "prices": prices}
    _set_cache(cache_key, data)
    return data


async def fetch_multiple(tickers: list[str], years: int) -> dict[str, dict]:
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = await fetch_chart_data(ticker, years)
        except Exception:
            results[ticker] = {"dates": [], "prices": []}
    return results
