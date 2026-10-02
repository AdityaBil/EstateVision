from __future__ import annotations

import pandas as pd


def current_value(price_per_sqft: float, area_sqft: float) -> float:
    if price_per_sqft <= 0 or area_sqft <= 0:
        raise ValueError("Price per square foot and area must be positive.")
    return float(price_per_sqft * area_sqft)


def nominal_future_value(
    current_price: float, years: int, annual_appreciation_pct: float
) -> float:
    """Project the future rupee amount using nominal property appreciation."""
    return float(current_price * (1 + annual_appreciation_pct / 100) ** years)


def todays_money_value(nominal_price: float, years: int, inflation_pct: float) -> float:
    """Express a nominal future price in today's rupees."""
    return float(nominal_price / (1 + inflation_pct / 100) ** years)


def current_value_range(
    low_price_per_sqft: float, high_price_per_sqft: float, area_sqft: float
) -> tuple[float, float]:
    """Convert a source price-per-square-foot range into a property value range."""
    low = current_value(low_price_per_sqft, area_sqft)
    high = current_value(high_price_per_sqft, area_sqft)
    return min(low, high), max(low, high)


def projection_table(
    current_price: float,
    years: list[int],
    annual_appreciation_pct: float,
    inflation_pct: float,
) -> pd.DataFrame:
    rows = []
    for year in years:
        nominal = nominal_future_value(current_price, year, annual_appreciation_pct)
        rows.append(
            {
                "Year": year,
                "Nominal value": nominal,
                "Value in today's money": todays_money_value(nominal, year, inflation_pct),
            }
        )
    return pd.DataFrame(rows)


def projection_range_table(
    low_current_price: float,
    high_current_price: float,
    years: list[int],
    annual_appreciation_pct: float,
    inflation_pct: float,
) -> pd.DataFrame:
    """Project both ends of a valuation range in nominal and real terms."""
    rows = []
    for year in years:
        low_nominal = nominal_future_value(
            low_current_price, year, annual_appreciation_pct
        )
        high_nominal = nominal_future_value(
            high_current_price, year, annual_appreciation_pct
        )
        rows.append(
            {
                "Year": year,
                "Nominal low": low_nominal,
                "Nominal estimate": nominal_future_value(
                    (low_current_price + high_current_price) / 2,
                    year,
                    annual_appreciation_pct,
                ),
                "Nominal high": high_nominal,
                "Today's-money low": todays_money_value(
                    low_nominal, year, inflation_pct
                ),
                "Today's-money high": todays_money_value(
                    high_nominal, year, inflation_pct
                ),
            }
        )
    return pd.DataFrame(rows)


def area_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary = (
        frame.groupby("Areas", as_index=False)
        .agg(
            AveragePrice=("AveragePrice", "mean"),
            PriceRangeLow=("PriceRangeLow", "mean"),
            PriceRangeHigh=("PriceRangeHigh", "mean"),
            Listings=("Areas", "size"),
        )
        .sort_values("AveragePrice", ascending=False)
    )
    return summary.reset_index(drop=True)


def comparable_areas(
    frame: pd.DataFrame, target_area: str, limit: int = 5
) -> pd.DataFrame:
    """Find areas with the closest average price per square foot."""
    summary = area_summary(frame)
    target = summary.loc[summary["Areas"] == target_area, "AveragePrice"]
    if target.empty:
        return summary.head(limit)
    summary = summary.loc[summary["Areas"] != target_area].copy()
    summary["Price difference"] = (summary["AveragePrice"] - target.iloc[0]).abs()
    return summary.sort_values("Price difference").head(limit).drop(columns="Price difference")


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"
