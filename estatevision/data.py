from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


AREA_ALIASES = {
    "Mahalakshmi Nagarties": "Mahalakshmi Nagar",
    "Bengali Squareperties": "Bengali Square",
    "Scheme No 114es": "Scheme No 114",
    "Silicon Cityies": "Silicon City",
    "Tukoganjes": "Tukoganj",
    "Scheme 78s": "Scheme 78",
    "Manishpurierties": "Manishpuri",
    "Sudama NagarProperties": "Sudama Nagar",
    "Scheme No 71erties": "Scheme No 71",
    "Balya Khedaerties": "Balya Kheda",
}


def _parse_price_range(value: object) -> tuple[float | None, float | None]:
    numbers = re.findall(r"\d[\d,]*", str(value))
    if len(numbers) < 2:
        return None, None
    return tuple(float(number.replace(",", "")) for number in numbers[:2])


def load_property_data(path: str | Path) -> pd.DataFrame:
    """Load and normalize the source workbook used by the app."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Property data file not found: {source}")

    frame = pd.read_excel(source)
    required = {"Areas", "AveragePrice", "Price Range"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    frame = frame.copy()
    frame["Areas"] = (
        frame["Areas"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    )
    frame["Areas"] = frame["Areas"].replace(AREA_ALIASES)
    frame["AveragePrice"] = pd.to_numeric(frame["AveragePrice"], errors="coerce")

    parsed_ranges = frame["Price Range"].map(_parse_price_range)
    frame["PriceRangeLow"] = parsed_ranges.map(lambda item: item[0])
    frame["PriceRangeHigh"] = parsed_ranges.map(lambda item: item[1])
    frame["PriceRangeSpread"] = frame["PriceRangeHigh"] - frame["PriceRangeLow"]

    frame = frame.dropna(subset=["Areas", "AveragePrice"]).copy()
    frame = frame[frame["AveragePrice"] > 0].reset_index(drop=True)
    return frame


def validate_property_data(frame: pd.DataFrame) -> dict[str, int]:
    """Return simple data-quality indicators for display in the dashboard."""
    return {
        "rows": int(len(frame)),
        "areas": int(frame["Areas"].nunique()),
        "missing_values": int(frame.isna().sum().sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
        "invalid_prices": int((frame["AveragePrice"] <= 0).sum()),
    }

