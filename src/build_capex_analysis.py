from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = (
    ROOT / "data" / "processed" / "capex_analysis.csv"
)

CASHFLOW_PATH = (
    ROOT / "data" / "processed" / "capex_cashflows.csv"
)


INITIAL_INVESTMENT = 850_000
DISCOUNT_RATE = 0.10

BASE_UNITS = [
    100_000,
    120_000,
    140_000,
    160_000,
    180_000,
]

BASE_PRICE = 4.25
BASE_VARIABLE_COST = 1.75
BASE_FIXED_OPEX = 80_000

PRICE_GROWTH = 0.02
COST_GROWTH = 0.03


SCENARIOS = {
    "Downside": {
        "unit_multiplier": 0.75,
        "price_multiplier": 0.97,
        "cost_multiplier": 1.08,
        "terminal_value": 70_000,
    },
    "Base": {
        "unit_multiplier": 1.00,
        "price_multiplier": 1.00,
        "cost_multiplier": 1.00,
        "terminal_value": 100_000,
    },
    "Upside": {
        "unit_multiplier": 1.20,
        "price_multiplier": 1.03,
        "cost_multiplier": 0.97,
        "terminal_value": 120_000,
    },
}


def npv(rate, cashflows):
    return sum(
        cashflow / ((1 + rate) ** year)
        for year, cashflow in enumerate(cashflows)
    )


def irr(cashflows, tolerance=1e-7):
    """
    IRR using bisection.

    This works well here because the project has a conventional
    cash-flow pattern: one initial outflow followed by inflows.
    """
    low = -0.99
    high = 10.0

    low_npv = npv(low, cashflows)
    high_npv = npv(high, cashflows)

    if low_npv * high_npv > 0:
        return None

    for _ in range(300):
        midpoint = (low + high) / 2
        midpoint_npv = npv(midpoint, cashflows)

        if abs(midpoint_npv) < tolerance:
            return midpoint

        if low_npv * midpoint_npv <= 0:
            high = midpoint
        else:
            low = midpoint
            low_npv = midpoint_npv

    return (low + high) / 2


def payback_period(cashflows):
    cumulative = cashflows[0]

    for year in range(1, len(cashflows)):
        previous = cumulative
        cumulative += cashflows[year]

        if cumulative >= 0:
            fraction = (-previous) / cashflows[year]
            return (year - 1) + fraction

    return None


def build_scenario(name, assumptions):
    cashflows = [-INITIAL_INVESTMENT]

    rows = [
        {
            "Scenario": name,
            "Year": 0,
            "Units": 0,
            "Price_per_Plant": 0,
            "Variable_Cost_per_Plant": 0,
            "Incremental_Revenue": 0,
            "Incremental_Variable_Cost": 0,
            "Incremental_Fixed_OPEX": 0,
            "Terminal_Value": 0,
            "Net_Cash_Flow": -INITIAL_INVESTMENT,
        }
    ]

    for year, base_units in enumerate(BASE_UNITS, start=1):

        units = (
            base_units
            * assumptions["unit_multiplier"]
        )

        price = (
            BASE_PRICE
            * (1 + PRICE_GROWTH) ** (year - 1)
            * assumptions["price_multiplier"]
        )

        variable_cost = (
            BASE_VARIABLE_COST
            * (1 + COST_GROWTH) ** (year - 1)
            * assumptions["cost_multiplier"]
        )

        fixed_opex = (
            BASE_FIXED_OPEX
            * (1 + COST_GROWTH) ** (year - 1)
        )

        revenue = units * price
        total_variable_cost = units * variable_cost

        terminal_value = (
            assumptions["terminal_value"]
            if year == 5
            else 0
        )

        net_cash_flow = (
            revenue
            - total_variable_cost
            - fixed_opex
            + terminal_value
        )

        cashflows.append(net_cash_flow)

        rows.append(
            {
                "Scenario": name,
                "Year": year,
                "Units": units,
                "Price_per_Plant": price,
                "Variable_Cost_per_Plant": variable_cost,
                "Incremental_Revenue": revenue,
                "Incremental_Variable_Cost": total_variable_cost,
                "Incremental_Fixed_OPEX": fixed_opex,
                "Terminal_Value": terminal_value,
                "Net_Cash_Flow": net_cash_flow,
            }
        )

    project_npv = npv(
        DISCOUNT_RATE,
        cashflows,
    )

    project_irr = irr(cashflows)
    project_payback = payback_period(cashflows)

    summary = {
        "Scenario": name,
        "Initial_Investment": INITIAL_INVESTMENT,
        "Discount_Rate_pct": DISCOUNT_RATE * 100,
        "NPV": project_npv,
        "IRR_pct": (
            project_irr * 100
            if project_irr is not None
            else None
        ),
        "Payback_Years": project_payback,
    }

    return rows, summary


def main():

    all_cashflows = []
    summaries = []

    for scenario, assumptions in SCENARIOS.items():

        rows, summary = build_scenario(
            scenario,
            assumptions,
        )

        all_cashflows.extend(rows)
        summaries.append(summary)

    cashflow_df = pd.DataFrame(all_cashflows)
    summary_df = pd.DataFrame(summaries)

    cashflow_df.to_csv(
        CASHFLOW_PATH,
        index=False,
    )

    summary_df.to_csv(
        SUMMARY_PATH,
        index=False,
    )

    print("CAPEX evaluation:")
    print()

    print(
        summary_df.to_string(
            index=False,
            formatters={
                "Initial_Investment":
                    "${:,.0f}".format,
                "Discount_Rate_pct":
                    "{:.1f}%".format,
                "NPV":
                    "${:,.0f}".format,
                "IRR_pct":
                    lambda x: (
                        f"{x:.1f}%"
                        if pd.notna(x)
                        else "N/A"
                    ),
                "Payback_Years":
                    lambda x: (
                        f"{x:.1f}"
                        if pd.notna(x)
                        else "Not recovered"
                    ),
            },
        )
    )


if __name__ == "__main__":
    main()
