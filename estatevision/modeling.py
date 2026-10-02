from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


RECOMMENDED_PROPERTY_COLUMNS = {
    "price": "Observed sale or listing price",
    "area_sqft": "Built-up or carpet area",
    "property_type": "Apartment, house, plot, etc.",
    "bedrooms": "Number of bedrooms",
    "bathrooms": "Number of bathrooms",
    "property_age": "Age at the time of observation",
    "transaction_date": "Sale or listing date",
    "latitude": "Property latitude",
    "longitude": "Property longitude",
}


def training_readiness(frame: pd.DataFrame) -> dict[str, object]:
    """Assess whether the available data is ready for a property-level model."""
    columns = {str(column).strip().lower() for column in frame.columns}
    present = [column for column in RECOMMENDED_PROPERTY_COLUMNS if column in columns]
    missing = [column for column in RECOMMENDED_PROPERTY_COLUMNS if column not in columns]

    has_target = "price" in columns or "price_per_sqft" in columns
    enough_rows = len(frame) >= 100
    ready = bool(has_target and enough_rows and "area_sqft" in columns)
    return {
        "ready": ready,
        "row_count": int(len(frame)),
        "target_available": has_target,
        "present_features": present,
        "missing_features": missing,
        "minimum_row_target": 100,
    }


def normalize_columns(columns: Iterable[object]) -> dict[object, str]:
    """Create stable feature names for a future uploaded property dataset."""
    normalized = {}
    for column in columns:
        name = str(column).strip().lower().replace(" ", "_")
        normalized[column] = name
    return normalized

