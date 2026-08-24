from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_PATH = (
    ROOT / "data" / "processed" / "blueberry_production.csv"
)

OUTPUT_PATH = (
    ROOT / "data" / "processed" / "fpna_model.csv"
)

ASSUMPTIONS_PATH = (
    ROOT / "data" / "processed" / "fpna_assumptions.csv"
)


# ------------------------------------------------------------------
# MODEL ASSUMPTIONS
# ------------------------------------------------------------------
#
# All company financial figures below are synthetic assumptions.
# FAOSTAT production data are used only as external market drivers.
#
# The fictional company sells blueberry nursery plants/genetics to
# commercial growers.
# ------------------------------------------------------------------

REGIONAL_ASSUMPTIONS = {
    "Peru": {
        "market_share": 0.055,
        "plants_per_ha": 3300,
        "replacement_rate": 0.085,
        "price_per_plant": 4.10,
        "variable_cost_per_plant": 1.72,
        "annual_opex": 620_000,
        "budget_growth": 0.12,
        "forecast_adjustment": 0.08,
    },
    "Spain": {
        "market_share": 0.090,
        "plants_per_ha": 3200,
        "replacement_rate": 0.075,
        "price_per_plant": 4.55,
        "variable_cost_per_plant": 1.85,
        "annual_opex": 160_000,
        "budget_growth": 0.06,
        "forecast_adjustment": -0.03,
    },
    "Chile": {
        "market_share": 0.070,
        "plants_per_ha": 3000,
        "replacement_rate": 0.065,
        "price_per_plant": 4.30,
        "variable_cost_per_plant": 1.79,
        "annual_opex": 250_000,
        "budget_growth": 0.04,
        "forecast_adjustment": -0.06,
    },
    "Mexico": {
        "market_share": 0.080,
        "plants_per_ha": 3400,
        "replacement_rate": 0.080,
        "price_per_plant": 4.25,
        "variable_cost_per_plant": 1.76,
        "annual_opex": 170_000,
        "budget_growth": 0.08,
        "forecast_adjustment": 0.02,
    },
}


def load_market_data() -> pd.DataFrame:
    production = pd.read_csv(PRODUCTION_PATH)

    market_2024 = production[
        production["Year"] == 2024
    ].copy()

    if len(market_2024) != 4:
        raise RuntimeError(
            "Expected 2024 production data for four countries."
        )

    return market_2024


def build_assumptions_table() -> pd.DataFrame:
    rows = []

    for country, assumptions in REGIONAL_ASSUMPTIONS.items():
        rows.append(
            {
                "Country": country,
                **assumptions,
            }
        )

    return pd.DataFrame(rows)


def calculate_actuals(
    market: pd.DataFrame,
    assumptions: pd.DataFrame,
) -> pd.DataFrame:

    df = market.merge(
        assumptions,
        on="Country",
        how="inner",
    )

    # Addressable nursery demand:
    # existing planted area * replacement/replanting rate.
    df["Addressable_Area_ha"] = (
        df["Area_Harvested_ha"]
        * df["replacement_rate"]
    )

    df["Addressable_Plants"] = (
        df["Addressable_Area_ha"]
        * df["plants_per_ha"]
    )

    df["Units_Sold"] = (
        df["Addressable_Plants"]
        * df["market_share"]
    ).round()

    df["Revenue"] = (
        df["Units_Sold"]
        * df["price_per_plant"]
    )

    df["COGS"] = (
        df["Units_Sold"]
        * df["variable_cost_per_plant"]
    )

    df["Gross_Profit"] = (
        df["Revenue"] - df["COGS"]
    )

    df["Gross_Margin_pct"] = (
        df["Gross_Profit"]
        / df["Revenue"]
        * 100
    )

    df["Operating_Expenses"] = df["annual_opex"]

    df["EBITDA"] = (
        df["Gross_Profit"]
        - df["Operating_Expenses"]
    )

    df["EBITDA_Margin_pct"] = (
        df["EBITDA"]
        / df["Revenue"]
        * 100
    )

    df["Scenario"] = "Actual"
    df["Model_Year"] = 2024

    return df


def build_budget(actual: pd.DataFrame) -> pd.DataFrame:
    budget = actual.copy()

    budget["Model_Year"] = 2025
    budget["Scenario"] = "Budget"

    budget["Units_Sold"] = (
        budget["Units_Sold"]
        * (1 + budget["budget_growth"])
    ).round()

    # Moderate planned annual price increase.
    budget["price_per_plant"] *= 1.025

    # Cost inflation assumption.
    budget["variable_cost_per_plant"] *= 1.035
    budget["Operating_Expenses"] *= 1.04

    recalculate_financials(budget)

    return budget


def build_forecast(budget: pd.DataFrame) -> pd.DataFrame:
    forecast = budget.copy()

    forecast["Scenario"] = "Forecast"

    # Latest operational outlook vs original budget.
    forecast["Units_Sold"] = (
        forecast["Units_Sold"]
        * (1 + forecast["forecast_adjustment"])
    ).round()

    # Small regional pricing realization differences.
    price_realization = {
        "Peru": 1.010,
        "Spain": 0.995,
        "Chile": 0.990,
        "Mexico": 1.005,
    }

    forecast["price_per_plant"] *= (
        forecast["Country"]
        .map(price_realization)
    )

    recalculate_financials(forecast)

    return forecast


def recalculate_financials(df: pd.DataFrame) -> None:
    df["Revenue"] = (
        df["Units_Sold"]
        * df["price_per_plant"]
    )

    df["COGS"] = (
        df["Units_Sold"]
        * df["variable_cost_per_plant"]
    )

    df["Gross_Profit"] = (
        df["Revenue"] - df["COGS"]
    )

    df["Gross_Margin_pct"] = (
        df["Gross_Profit"]
        / df["Revenue"]
        * 100
    )

    df["EBITDA"] = (
        df["Gross_Profit"]
        - df["Operating_Expenses"]
    )

    df["EBITDA_Margin_pct"] = (
        df["EBITDA"]
        / df["Revenue"]
        * 100
    )


def add_variances(
    model: pd.DataFrame,
) -> pd.DataFrame:

    budget = (
        model[
            (model["Model_Year"] == 2025)
            & (model["Scenario"] == "Budget")
        ]
        .set_index("Country")
    )

    forecast_mask = (
        (model["Model_Year"] == 2025)
        & (model["Scenario"] == "Forecast")
    )

    for metric in [
        "Revenue",
        "Gross_Profit",
        "EBITDA",
        "Units_Sold",
    ]:
        model.loc[
            forecast_mask,
            f"{metric}_Variance_vs_Budget",
        ] = (
            model.loc[forecast_mask, metric].values
            - budget.loc[
                model.loc[forecast_mask, "Country"],
                metric,
            ].values
        )

        model.loc[
            forecast_mask,
            f"{metric}_Variance_vs_Budget_pct",
        ] = (
            model.loc[
                forecast_mask,
                f"{metric}_Variance_vs_Budget",
            ].values
            / budget.loc[
                model.loc[forecast_mask, "Country"],
                metric,
            ].values
            * 100
        )

    return model


def main() -> None:
    market = load_market_data()

    assumptions = build_assumptions_table()
    assumptions.to_csv(
        ASSUMPTIONS_PATH,
        index=False,
    )

    actual = calculate_actuals(
        market,
        assumptions,
    )

    budget = build_budget(actual)
    forecast = build_forecast(budget)

    model = pd.concat(
        [actual, budget, forecast],
        ignore_index=True,
    )

    model = add_variances(model)

    columns = [
        "Country",
        "Model_Year",
        "Scenario",
        "Area_Harvested_ha",
        "Production_t",
        "Yield_kg_ha",
        "Units_Sold",
        "price_per_plant",
        "Revenue",
        "COGS",
        "Gross_Profit",
        "Gross_Margin_pct",
        "Operating_Expenses",
        "EBITDA",
        "EBITDA_Margin_pct",
        "Revenue_Variance_vs_Budget",
        "Revenue_Variance_vs_Budget_pct",
        "Gross_Profit_Variance_vs_Budget",
        "Gross_Profit_Variance_vs_Budget_pct",
        "EBITDA_Variance_vs_Budget",
        "EBITDA_Variance_vs_Budget_pct",
        "Units_Sold_Variance_vs_Budget",
        "Units_Sold_Variance_vs_Budget_pct",
    ]

    model = model[columns]

    model.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Saved model to:\n{OUTPUT_PATH}")

    print("\n2025 Forecast vs Budget:")
    summary = model[
        model["Scenario"] == "Forecast"
    ][
        [
            "Country",
            "Revenue",
            "Revenue_Variance_vs_Budget_pct",
            "EBITDA",
            "EBITDA_Variance_vs_Budget_pct",
        ]
    ]

    print(
        summary.to_string(
            index=False,
            formatters={
                "Revenue": "{:,.0f}".format,
                "Revenue_Variance_vs_Budget_pct":
                    "{:+.1f}%".format,
                "EBITDA": "{:,.0f}".format,
                "EBITDA_Variance_vs_Budget_pct":
                    "{:+.1f}%".format,
            },
        )
    )

    forecast = model[
        model["Scenario"] == "Forecast"
    ]

    budget = model[
        model["Scenario"] == "Budget"
    ]

    total_forecast_revenue = forecast["Revenue"].sum()
    total_budget_revenue = budget["Revenue"].sum()

    total_forecast_ebitda = forecast["EBITDA"].sum()
    total_budget_ebitda = budget["EBITDA"].sum()

    print("\nCOMPANY TOTAL")
    print(
        f"Forecast Revenue: "
        f"${total_forecast_revenue:,.0f}"
    )
    print(
        f"Revenue vs Budget: "
        f"{(
            total_forecast_revenue
            / total_budget_revenue
            - 1
        ) * 100:+.1f}%"
    )
    print(
        f"Forecast EBITDA: "
        f"${total_forecast_ebitda:,.0f}"
    )
    print(
        f"EBITDA vs Budget: "
        f"{(
            total_forecast_ebitda
            / total_budget_ebitda
            - 1
        ) * 100:+.1f}%"
    )


if __name__ == "__main__":
    main()
