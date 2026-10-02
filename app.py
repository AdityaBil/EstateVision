from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from estatevision.data import load_property_data, validate_property_data
from estatevision.modeling import training_readiness
from estatevision.valuation import (
    area_summary,
    comparable_areas,
    current_value,
    current_value_range,
    format_inr,
    projection_range_table,
    projection_table,
)


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "pythonproj.xlsx"

st.set_page_config(
    page_title="EstateVision | Property Intelligence",
    page_icon="🏠",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(214, 168, 95, 0.13), transparent 26rem),
            radial-gradient(circle at 94% 18%, rgba(68, 129, 119, 0.13), transparent 25rem),
            #0B1117;
    }
    .block-container { max-width: 1450px; padding-top: 2.5rem; padding-bottom: 4rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101923 0%, #0B1117 100%);
        border-right: 1px solid rgba(214, 168, 95, 0.16);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #AEB9C4; }
    [data-testid="stSidebar"] .stRadio label { padding: 0.35rem 0; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.075), rgba(255, 255, 255, 0.025));
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
    }
    [data-testid="stMetricLabel"] { color: #AEB9C4; }
    [data-testid="stMetricValue"] {
        color: #F4F0E8;
        font-size: 1.35rem;
        line-height: 1.15;
        white-space: normal;
        overflow-wrap: anywhere;
    }
    .ev-brand { margin: 0 0 2.3rem 0; }
    .ev-brand-mark { color: #D6A85F; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.22em; }
    .ev-brand-name { color: #F4F0E8; font-size: 1.45rem; font-weight: 700; letter-spacing: -0.03em; margin-top: 0.35rem; }
    .ev-hero {
        background: linear-gradient(120deg, rgba(22, 34, 43, 0.96), rgba(18, 28, 35, 0.72));
        border: 1px solid rgba(214, 168, 95, 0.23);
        border-radius: 22px;
        padding: 2rem 2.2rem 2.1rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.2);
    }
    .ev-kicker { color: #D6A85F; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; }
    .ev-hero h1 { color: #F4F0E8; font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1.05; letter-spacing: -0.055em; margin: 0.55rem 0 0.7rem; }
    .ev-hero p { color: #AEB9C4; font-size: 1rem; margin: 0; max-width: 48rem; }
    .ev-section { color: #F4F0E8; font-size: 1.15rem; font-weight: 650; letter-spacing: -0.02em; margin: 1.7rem 0 0.45rem; }
    .ev-note { color: #93A2AE; font-size: 0.82rem; margin-bottom: 0.85rem; }
    .stButton > button, .stDownloadButton > button {
        border: 1px solid rgba(214, 168, 95, 0.45);
        border-radius: 10px;
        background: rgba(214, 168, 95, 0.12);
        color: #F4F0E8;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color: #D6A85F; color: #FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_property_data() -> pd.DataFrame:
    return load_property_data(DATA_PATH)


@st.cache_data(show_spinner=False)
def get_experimental_macro_forecast() -> tuple[float | None, dict]:
    """Read the legacy inflation artifact without making it the price model."""
    try:
        with (ROOT / "y_pred.pkl").open("rb") as handle:
            predictions = pd.Series(pickle.load(handle), dtype="float64")
        with (ROOT / "metrics.pkl").open("rb") as handle:
            metrics = pickle.load(handle)
        if predictions.empty or not predictions.notna().all():
            return None, metrics
        return float(predictions.mean()), metrics
    except (FileNotFoundError, EOFError, pickle.UnpicklingError, ValueError, TypeError):
        return None, {}


def render_sidebar(frame: pd.DataFrame) -> tuple[str, float, float, float, int]:
    st.sidebar.markdown(
        """
        <div class="ev-brand">
            <div class="ev-brand-mark">ESTATE / VISION</div>
            <div class="ev-brand-name">Property intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    locations = sorted(frame["Areas"].unique().tolist())
    location = st.sidebar.selectbox("Location", locations)
    area_sqft = st.sidebar.number_input(
        "Property area (sq ft)", min_value=100, max_value=100_000, value=1_000, step=50
    )
    appreciation = st.sidebar.slider(
        "Annual property appreciation (%)", 0.0, 25.0, 8.0, 0.5
    )
    macro_forecast, _ = get_experimental_macro_forecast()
    default_inflation = round(macro_forecast, 1) if macro_forecast is not None else 5.0
    inflation = st.sidebar.slider(
        "Annual inflation scenario (%)", 0.0, 20.0, float(min(default_inflation, 20.0)), 0.5
    )
    horizon = st.sidebar.slider("Projection horizon (years)", 1, 20, 10)
    return location, float(area_sqft), appreciation, inflation, horizon


def render_valuation(frame: pd.DataFrame) -> None:
    location, area_sqft, appreciation, inflation, horizon = render_sidebar(frame)
    selected = frame.loc[frame["Areas"] == location].iloc[0]
    price_per_sqft = float(selected["AveragePrice"])
    current_price = current_value(price_per_sqft, area_sqft)
    source_low = float(selected["PriceRangeLow"])
    source_high = float(selected["PriceRangeHigh"])
    current_low, current_high = current_value_range(source_low, source_high, area_sqft)

    st.markdown(
        """
        <div class="ev-hero">
            <div class="ev-kicker">Valuation workspace · Indore market</div>
            <h1>See the value of<br>where you live.</h1>
            <p>Explore a current estimate, compare nearby markets, and understand how appreciation and inflation reshape the future value of a property.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first, second, third, fourth = st.columns(4)
    first.metric("Selected area", location)
    second.metric("Average price / sq ft", format_inr(price_per_sqft))
    third.metric("Estimated current value", format_inr(current_price))
    fourth.metric("Source range / sq ft", f"{format_inr(source_low)} – {format_inr(source_high)}")

    st.info(
        "This is currently a scenario engine, not a production-grade property-price model. "
        "The dataset contains area averages rather than individual property transactions."
    )

    years = sorted(set([1, 3, 5, 7, 10, horizon]))
    projection = projection_table(current_price, years, appreciation, inflation)
    projection_range = projection_range_table(
        current_low, current_high, years, appreciation, inflation
    )
    st.markdown('<div class="ev-section">Projection outlook</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class=\"ev-note\">Nominal appreciation: {appreciation:.1f}% &nbsp;·&nbsp; Inflation scenario: {inflation:.1f}%<br>Adjust the assumptions in the sidebar to explore different market conditions.</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1.4])
    with left:
        st.dataframe(
            projection_range[
                [
                    "Year",
                    "Nominal low",
                    "Nominal estimate",
                    "Nominal high",
                    "Today's-money low",
                    "Today's-money high",
                ]
            ].style.format(
                {
                    "Nominal low": "₹{:,.0f}",
                    "Nominal estimate": "₹{:,.0f}",
                    "Nominal high": "₹{:,.0f}",
                    "Today's-money low": "₹{:,.0f}",
                    "Today's-money high": "₹{:,.0f}",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    with right:
        chart_data = projection.melt(
            id_vars="Year", var_name="Measure", value_name="Value"
        )
        chart = px.line(
            chart_data,
            x="Year",
            y="Value",
            color="Measure",
            markers=True,
            labels={"Value": "Property value (INR)"},
        )
        chart.update_layout(legend_title_text="", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(chart, use_container_width=True)

    st.caption(
        "The displayed range comes from the source workbook's reported price range. "
        "It is a market-data range, not a statistically calibrated confidence interval."
    )

    similar = comparable_areas(frame, location)
    st.markdown('<div class="ev-section">Comparable areas</div>', unsafe_allow_html=True)
    st.dataframe(
        similar[["Areas", "AveragePrice", "PriceRangeLow", "PriceRangeHigh"]].style.format(
            {
                "AveragePrice": "₹{:,.0f}",
                "PriceRangeLow": "₹{:,.0f}",
                "PriceRangeHigh": "₹{:,.0f}",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.download_button(
        "Download projection CSV",
        data=projection_range.to_csv(index=False).encode("utf-8"),
        file_name=f"{location.lower().replace(' ', '_')}_projection.csv",
        mime="text/csv",
    )

    st.markdown('<div class="ev-section">Selected area details</div>', unsafe_allow_html=True)
    st.json(
        {
            "Area": location,
            "Price range in source": (
                f"{format_inr(source_low)} – {format_inr(source_high)} per sq ft"
            ),
            "Current valuation range": f"{format_inr(current_low)} – {format_inr(current_high)}",
            "Selected property size": f"{area_sqft:,.0f} sq ft",
            "Current estimate": format_inr(current_price),
        }
    )


def render_market_overview(frame: pd.DataFrame) -> None:
    st.header("Market overview")
    summary = area_summary(frame)
    left, right = st.columns([1.35, 1])
    with left:
        chart = px.bar(
            summary.sort_values("AveragePrice").tail(15),
            x="AveragePrice",
            y="Areas",
            orientation="h",
            color="AveragePrice",
            color_continuous_scale="Viridis",
            labels={"AveragePrice": "Average price / sq ft"},
        )
        chart.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(chart, use_container_width=True)
    with right:
        st.dataframe(
            summary[["Areas", "AveragePrice", "PriceRangeLow", "PriceRangeHigh"]]
            .head(15)
            .style.format(
                {
                    "AveragePrice": "₹{:,.0f}",
                    "PriceRangeLow": "₹{:,.0f}",
                    "PriceRangeHigh": "₹{:,.0f}",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )


def render_diagnostics(frame: pd.DataFrame) -> None:
    st.header("Data and model diagnostics")
    quality = validate_property_data(frame)
    cols = st.columns(len(quality))
    for column, (label, value) in zip(cols, quality.items()):
        column.metric(label.replace("_", " ").title(), value)

    readiness = training_readiness(frame)
    st.subheader("Property-model readiness")
    if readiness["ready"]:
        st.success("The dataset has enough property-level fields for a first model.")
    else:
        st.warning(
            "The current dataset is not ready for a reliable property-level model. "
            "Add transaction-level records, a price target, and property area first."
        )
    ready_cols = st.columns(3)
    ready_cols[0].metric("Rows available", readiness["row_count"])
    ready_cols[1].metric("Minimum recommended", readiness["minimum_row_target"])
    ready_cols[2].metric("Price target found", "Yes" if readiness["target_available"] else "No")
    st.caption(
        "Recommended fields: price, area_sqft, property_type, bedrooms, bathrooms, "
        "property_age, transaction_date, latitude, and longitude."
    )

    forecast, metrics = get_experimental_macro_forecast()
    st.subheader("Legacy inflation artifact")
    if metrics:
        st.warning(
            "The existing inflation model is retained for inspection only. It is trained on a "
            "small synthetic-looking dataset and is not used as the property valuation model."
        )
        metric_cols = st.columns(3)
        metric_cols[0].metric("Test R²", f"{metrics.get('r2_test', 0):.3f}")
        metric_cols[1].metric("Test RMSE", f"{metrics.get('rmse_test', 0):.3f}")
        metric_cols[2].metric(
            "Average forecast", f"{forecast:.2f}%" if forecast else "Unavailable"
        )
    else:
        st.info("No legacy inflation artifacts were found. The app still works with manual scenarios.")

    st.subheader("Source data")
    st.dataframe(frame, hide_index=True, use_container_width=True)


def main() -> None:
    try:
        frame = get_property_data()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    page = st.sidebar.radio("Workspace", ["Valuation", "Market overview", "Diagnostics"])
    if page == "Valuation":
        render_valuation(frame)
    elif page == "Market overview":
        render_market_overview(frame)
    else:
        render_diagnostics(frame)


if __name__ == "__main__":
    main()
