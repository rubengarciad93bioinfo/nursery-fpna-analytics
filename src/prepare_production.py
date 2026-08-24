from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT / "data" / "processed" / "faostat_blueberries.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "blueberry_production.csv"


def main() -> None:
    df = pd.read_csv(INPUT_PATH)

    # Keep the original FAOSTAT records intact in faostat_blueberries.csv
    # and create a business-friendly analytical table here.
    wide = (
        df.pivot(
            index=["Area", "Year"],
            columns="Element",
            values="Value",
        )
        .reset_index()
        .rename(
            columns={
                "Area": "Country",
                "Area harvested": "Area_Harvested_ha",
                "Production": "Production_t",
                "Yield": "Yield_kg_ha",
            }
        )
    )

    # Capture whether at least one source observation for the
    # country-year was estimated by FAOSTAT.
    quality = (
        df.groupby(["Area", "Year"])["Flag"]
        .apply(lambda x: "Estimated" if (x == "E").any() else "Reported")
        .reset_index(name="Data_Status")
        .rename(columns={"Area": "Country"})
    )

    wide = wide.merge(
        quality,
        on=["Country", "Year"],
        how="left",
    )

    # Useful operational metrics for later analysis.
    wide["Production_Growth_pct"] = (
        wide.groupby("Country")["Production_t"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    wide["Yield_Growth_pct"] = (
        wide.groupby("Country")["Yield_kg_ha"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    wide = wide.sort_values(["Country", "Year"])

    wide.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(wide):,} rows to:")
    print(OUTPUT_PATH)

    print("\nLatest year by country:")
    latest = (
        wide.sort_values("Year")
        .groupby("Country")
        .tail(1)
        [
            [
                "Country",
                "Year",
                "Area_Harvested_ha",
                "Production_t",
                "Yield_kg_ha",
                "Production_Growth_pct",
            ]
        ]
    )

    print(latest.to_string(index=False))


if __name__ == "__main__":
    main()
