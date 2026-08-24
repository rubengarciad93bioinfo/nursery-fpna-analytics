from pathlib import Path
from urllib.request import urlretrieve
import zipfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

ZIP_PATH = RAW_DIR / "faostat_trade.zip"
SOURCE_PATH = PROCESSED_DIR / "faostat_blueberry_trade.csv"
OUTPUT_PATH = PROCESSED_DIR / "blueberry_trade.csv"

FAOSTAT_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Trade_CropsLivestock_E_All_Data_(Normalized).zip"
)

COUNTRIES = [
    "Chile",
    "Mexico",
    "Peru",
    "Spain",
]

ELEMENTS = [
    "Export quantity",
    "Export value",
    "Import quantity",
    "Import value",
]

START_YEAR = 2010


def download() -> None:
    if ZIP_PATH.exists():
        print(f"Using cached file: {ZIP_PATH}")
        return

    print("Downloading FAOSTAT trade dataset...")
    urlretrieve(FAOSTAT_URL, ZIP_PATH)
    print(f"Saved to: {ZIP_PATH}")


def extract_blueberry_trade() -> pd.DataFrame:
    parts = []

    with zipfile.ZipFile(ZIP_PATH) as archive:
        csv_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv")
            and "normalized" in name.lower()
        ]

        if not csv_files:
            raise RuntimeError("Normalized CSV not found in archive.")

        csv_name = csv_files[0]
        print(f"Reading: {csv_name}")

        with archive.open(csv_name) as file:
            for chunk in pd.read_csv(
                file,
                encoding="latin-1",
                chunksize=250_000,
                low_memory=False,
            ):
                mask = (
                    chunk["Item"].eq("Blueberries")
                    & chunk["Area"].isin(COUNTRIES)
                    & chunk["Element"].isin(ELEMENTS)
                    & chunk["Year"].ge(START_YEAR)
                )

                if mask.any():
                    columns = [
                        "Area",
                        "Item",
                        "Element",
                        "Year",
                        "Unit",
                        "Value",
                        "Flag",
                    ]

                    parts.append(
                        chunk.loc[mask, columns].copy()
                    )

    if not parts:
        raise RuntimeError(
            "No blueberry trade records found."
        )

    return pd.concat(parts, ignore_index=True)


def build_analytical_table(df: pd.DataFrame) -> pd.DataFrame:
    trade = (
        df.pivot_table(
            index=["Area", "Year"],
            columns="Element",
            values="Value",
            aggfunc="sum",
        )
        .reset_index()
        .rename(
            columns={
                "Area": "Country",
                "Export quantity": "Export_Quantity_t",
                "Export value": "Export_Value_1000USD",
                "Import quantity": "Import_Quantity_t",
                "Import value": "Import_Value_1000USD",
            }
        )
    )

    numeric_columns = [
        "Export_Quantity_t",
        "Export_Value_1000USD",
        "Import_Quantity_t",
        "Import_Value_1000USD",
    ]

    for column in numeric_columns:
        if column not in trade.columns:
            trade[column] = 0

        trade[column] = trade[column].fillna(0)

    # Convert FAOSTAT values from thousands of USD to USD.
    trade["Export_Value_USD"] = (
        trade["Export_Value_1000USD"] * 1000
    )

    trade["Import_Value_USD"] = (
        trade["Import_Value_1000USD"] * 1000
    )

    # Approximate unit value, useful as a market price proxy.
    trade["Export_Value_USD_per_kg"] = (
        trade["Export_Value_USD"]
        / (trade["Export_Quantity_t"] * 1000)
    )

    trade["Import_Value_USD_per_kg"] = (
        trade["Import_Value_USD"]
        / (trade["Import_Quantity_t"] * 1000)
    )

    trade.loc[
        trade["Export_Quantity_t"] == 0,
        "Export_Value_USD_per_kg",
    ] = pd.NA

    trade.loc[
        trade["Import_Quantity_t"] == 0,
        "Import_Value_USD_per_kg",
    ] = pd.NA

    trade["Trade_Balance_USD"] = (
        trade["Export_Value_USD"]
        - trade["Import_Value_USD"]
    )

    trade["Export_Value_Growth_pct"] = (
        trade.groupby("Country")["Export_Value_USD"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    trade["Export_Volume_Growth_pct"] = (
        trade.groupby("Country")["Export_Quantity_t"]
        .pct_change(fill_method=None)
        .mul(100)
    )

    return trade.sort_values(
        ["Country", "Year"]
    ).reset_index(drop=True)


def main() -> None:
    download()

    source = extract_blueberry_trade()
    source.to_csv(SOURCE_PATH, index=False)

    trade = build_analytical_table(source)
    trade.to_csv(OUTPUT_PATH, index=False)

    print()
    print(f"Filtered source rows: {len(source):,}")
    print(f"Analytical rows: {len(trade):,}")
    print(f"Saved to: {OUTPUT_PATH}")

    print("\nLatest year by country:")

    latest = (
        trade.sort_values("Year")
        .groupby("Country")
        .tail(1)
        [
            [
                "Country",
                "Year",
                "Export_Quantity_t",
                "Export_Value_USD",
                "Export_Value_USD_per_kg",
                "Trade_Balance_USD",
            ]
        ]
    )

    print(latest.to_string(index=False))


if __name__ == "__main__":
    main()
