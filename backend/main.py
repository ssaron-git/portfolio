from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.finance import fetch_multiple
from backend.calculations import calculate_hedge_cost, normalize_to_hundred

app = FastAPI(title="Swiss Investor Pro")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/api/market-data")
async def market_data(
    tickers: str = Query(default="CSSP.SW,SWDA.SW,EIMI.SW,IWDC.SW,IUSE.SW"),
    years: int = Query(default=10, ge=1, le=20),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    all_tickers = list(set(ticker_list + ["CHF=X", "EURCHF=X"]))

    raw = await fetch_multiple(all_tickers, years)

    # Normalize stock data to 100
    stocks_normalized = {}
    for t in ticker_list:
        if t in raw and raw[t]["prices"]:
            stocks_normalized[t] = {
                "dates": raw[t]["dates"],
                "prices": normalize_to_hundred(raw[t]["prices"]),
            }

    # Currency data normalized
    currencies = {}
    for c in ["CHF=X", "EURCHF=X"]:
        if c in raw and raw[c]["prices"]:
            prices = raw[c]["prices"]
            currencies[c] = {
                "dates": raw[c]["dates"],
                "prices": normalize_to_hundred(prices),
                "current": prices[-1],
                "pct_change": round((prices[-1] / prices[0] - 1) * 100, 2) if prices[0] else 0,
            }

    return {
        "stocks": stocks_normalized,
        "currencies": currencies,
        "years": years,
    }


@app.get("/api/hedge-cost")
async def hedge_cost(
    snb: float = Query(default=0.0),
    fed: float = Query(default=3.75),
    ecb: float = Query(default=2.0),
    bank_fee: float = Query(default=0.15),
):
    return {
        "usd_hedge": round(calculate_hedge_cost(fed, snb, bank_fee), 2),
        "eur_hedge": round(calculate_hedge_cost(ecb, snb, bank_fee), 2),
    }


# Serve frontend static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
