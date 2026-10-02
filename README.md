# EstateVision

EstateVision is a Streamlit property-intelligence prototype for area-level valuation, market comparison, and future-value scenarios.

## Current capabilities

- Loads and validates the property workbook.
- Cleans known locality-name issues and parses price ranges.
- Estimates current property value from area and average price per square foot.
- Separates nominal future value from value expressed in today's money.
- Provides interactive market charts and diagnostic views.
- Keeps the legacy inflation artifact available for inspection, but does not use it as the primary property-price model.

## Run locally

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

The application expects `pythonproj.xlsx` in the project root. The legacy `.pkl` files are optional and are only shown in the Diagnostics page when present.

## Project structure

```text
app.py                    Streamlit UI and page routing
estatevision/data.py      Data loading, normalization, and validation
estatevision/valuation.py Valuation and scenario calculations
estatevision/modeling.py  Property-model data readiness checks
tests/test_core.py        Core calculation and data-loading tests
pythonproj.xlsx           Current area-level source data
```

## Important modelling note

The current workbook contains area averages rather than individual property transactions. The application therefore presents scenario-based estimates, not production-grade property predictions. The next modelling milestone is to add property-level historical data, then train and validate a model using time- and geography-aware splits.
