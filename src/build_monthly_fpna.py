from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    ROOT / "data" / "processed" / "fpna_model.csv"
)

OUTPUT_PATH = (
    ROOT / "data" / "processed" / "monthly_fpna.csv"
)

SEASONALITY_PATH = (
    ROOT / "data" / "processed" / "monthly_seasonality.csv"
)


# ---------------------------------------------------------
# Synthetic seasonality assumptions.
# Each country's monthly weights must sum to 1.00.
#
# These are modeled commercial patterns for portfolio use,
# not observed Fall Creek data.
# ---------------------------------------------------------

SEASONALITY = {
    "Chile": [
        0.06, 0.07, 0.09, 0.11, 0.12, 0.11,
        0.09, 0.08, 0.07, 0.07, 0.07, 0.06,
    ],
    "Mexico": [
        0.07, 0.08, 0.09, 0.10, 0.11, 0.10,
        0.09, 0.08, 0.07, 0.07, 0.07, 0.07,
    ],
    "Peru": [
        0.05, 0.06, 0.07, 0.08, 0.09, 0.10,
        0.11, 0.11, 0.10, 0.09, 0.08, 0.06,
    ],
    "Spain": [
        0.06, 0.07, 0.10, 0.12, 0.13, 0.11,
        0.09, 0.07, 0.06, 0.06, 0.07, 0.06,
    ],
}


MONTH_NAMES = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


def validate_seasonality() -> None:
    for country, weights in SEASONALITY.items():
        if len(weights) != 12:
            raise ValueError(
                f"{country}: expected 12 monthly weights."
            )

        total = sum(weights)

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"{country}: seasonality sums to {total:.4f}, not 1."
            )


def save_seasonality() -> None:
    rows = []

    for country, weights in SEASONALITY.items():
        for month_num, weight in enumerate(weights, start=1):
            rows.append(
                {
                    "Country": country,
                    "Month_Num": month_num,
                    "Month": MONTH_NAMES[month_num],
                    "Sales_Weight": weight,
                }
            )

    pd.DataFrame(rows).to_csv(
        SEASONALITY_PATH,
        index=False,
    )


def expand_monthly(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, annual in df.iterrows():

        country = annual["Country"]
        weights = SEASONALITY[country]

        for month_num, sales_weight in enumerate(
            weights,
            start=1,
        ):
            year = int(annual["Model_Year"])

            # Sales-driven metrics follow regional seasonality.
            monthly_units = (
                annual["Units_Sold"]
                * sales_weight
            )

            monthly_revenue = (
                annual["Revenue"]
                * sales_weight
            )

            monthly_cogs = (
                annual["COGS"]
                * sales_weight
            )

            monthly_gross_profit = (
                monthly_revenue
                - monthly_cogs
            )

            # OPEX is treated as relatively fixed and spread evenly.
            monthly_opex = (
                annual["Operating_Expenses"]
                / 12
            )

            monthly_ebitda = (
                monthly_gross_profit
                - monthly_opex
            )

            gross_margin = (
                monthly_gross_profit
                / monthly_revenue
                * 100
                if monthly_revenue
                else None
            )

            ebitda_margin = (
                monthly_ebitda
                / monthly_revenue
                * 100
                if monthly_revenue
                else None
            )

            rows.append(
                {
                    "Date": f"{year}-{month_num:02d}-01",
                    "Year": year,
                    "Month_Num": month_num,
                    "Month": MONTH_NAMES[month_num],
                    "Country": country,
                    "Scenario": annual["Scenario"],
                    "Units_Sold": monthly_units,
                    "Price_per_Plant": annual["price_per_plant"],
                    "Revenue": monthly_revenue,
                    "COGS": monthly_cogs,
                    "Gross_Profit": monthly_gross_profit,
                    "Gross_Margin_pct": gross_margin,
                    "Operating_Expenses": monthly_opex,
                    "EBITDA": monthly_ebitda,
                    "EBITDA_Margin_pct": ebitda_margin,
                    "Market_Area_Harvested_ha":
                        annual["Area_Harvested_ha"],
                    "Market_Production_t":
                        annual["Production_t"],
                    "Market_Yield_kg_ha":
                        annual["Yield_kg_ha"],
                }
            )

    monthly = pd.DataFrame(rows)

    monthly["Date"] = pd.to_datetime(
        monthly["Date"]
    )

    return monthly


def add_forecast_variances(
    monthly: pd.DataFrame,
) -> pd.DataFrame:

    budget = (
        monthly[
            (monthly["Year"] == 2025)
            & (monthly["Scenario"] == "Budget")
        ][
            [
                "Country",
                "Month_Num",
                "Revenue",
                "EBITDA",
                "Units_Sold",
            ]
        ]
        .rename(
            columns={
                "Revenue": "Budget_Revenue",
                "EBITDA": "Budget_EBITDA",
                "Units_Sold": "Budget_Units_Sold",
            }
        )
    )

    monthly = monthly.merge(
        budget,
        on=["Country", "Month_Num"],
        how="left",
    )

    forecast_mask = (
        (monthly["Year"] == 2025)
        & (monthly["Scenario"] == "Forecast")
    )

    monthly.loc[
        forecast_mask,
        "Revenue_Variance_vs_Budget"
    ] = (
        monthly.loc[forecast_mask, "Revenue"]
        - monthly.loc[forecast_mask, "Budget_Revenue"]
    )

    monthly.loc[
        forecast_mask,
        "Revenue_Variance_vs_Budget_pct"
    ] = (
        monthly.loc[
            forecast_mask,
            "Revenue_Variance_vs_Budget"
        ]
        / monthly.loc[
            forecast_mask,
            "Budget_Revenue"
        ]
        * 100
    )

    monthly.loc[
        forecast_mask,
        "EBITDA_Variance_vs_Budget"
    ] = (
        monthly.loc[forecast_mask, "EBITDA"]
        - monthly.loc[forecast_mask, "Budget_EBITDA"]
    )

    monthly.loc[
        forecast_mask,
        "EBITDA_Variance_vs_Budget_pct"
    ] = (
        monthly.loc[
            forecast_mask,
            "EBITDA_Variance_vs_Budget"
        ]
        / monthly.loc[
            forecast_mask,
            "Budget_EBITDA"
        ]
        * 100
    )

    monthly.loc[
        forecast_mask,
        "Units_Variance_vs_Budget_pct"
    ] = (
        (
            monthly.loc[
                forecast_mask,
                "Units_Sold"
            ]
            / monthly.loc[
                forecast_mask,
                "Budget_Units_Sold"
            ]
        )
        - 1
    ) * 100

    return monthly


def validate_annual_totals(
    annual: pd.DataFrame,
    monthly: pd.DataFrame,
) -> None:

    metrics = [
        "Units_Sold",
        "Revenue",
        "COGS",
        "Gross_Profit",
        "Operating_Expenses",
        "EBITDA",
    ]

    monthly_totals = (
        monthly.groupby(
            ["Country", "Year", "Scenario"]
        )[metrics]
        .sum()
        .reset_index()
    )

    annual_check = annual.rename(
        columns={"Model_Year": "Year"}
    )[
        ["Country", "Year", "Scenario"] + metrics
    ]

    check = annual_check.merge(
        monthly_totals,
        on=["Country", "Year", "Scenario"],
        suffixes=("_Annual", "_Monthly"),
    )

    for metric in metrics:
        difference = (
            check[f"{metric}_Annual"]
            - check[f"{metric}_Monthly"]
        ).abs().max()

        if difference > 0.01:
            raise RuntimeError(
                f"Monthly totals do not reconcile for {metric}: "
                f"max difference = {difference}"
            )


def main() -> None:

    validate_seasonality()
    save_seasonality()

    annual = pd.read_csv(INPUT_PATH)

    monthly = expand_monthly(annual)

    monthly = add_forecast_variances(
        monthly
    )

    validate_annual_totals(
        annual,
        monthly,
    )

    monthly.to_csv(
        OUTPUT_PATH,
        index=False,
        date_format="%Y-%m-%d",
    )

    print(f"Saved {len(monthly):,} monthly rows to:")
    print(OUTPUT_PATH)

    print("\nReconciliation passed:")
    print("Monthly values reproduce annual model totals.")

    print("\n2025 Forecast monthly company summary:")

    summary = (
        monthly[
            (monthly["Year"] == 2025)
            & (monthly["Scenario"] == "Forecast")
        ]
        .groupby(["Month_Num", "Month"], as_index=False)
        [["Revenue", "EBITDA"]]
        .sum()
        .sort_values("Month_Num")
    )

    print(
        summary.to_string(
            index=False,
            formatters={
                "Revenue": "${:,.0f}".format,
                "EBITDA": "${:,.0f}".format,
            },
        )
    )


if __name__ == "__main__":
    main()
