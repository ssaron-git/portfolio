def calculate_hedge_cost(foreign_rate: float, domestic_rate: float, bank_fee: float) -> float:
    return (foreign_rate - domestic_rate) + bank_fee


def normalize_to_hundred(prices: list[float]) -> list[float]:
    if not prices or prices[0] == 0:
        return prices
    base = prices[0]
    return [round((p / base) * 100, 2) for p in prices]
