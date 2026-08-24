from pathlib import Path
from urllib.request import urlretrieve
import zipfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ZIP_PATH = RAW_DIR / "faostat_qcl.zip"
OUTPUT_PATH = PROCESSED_DIR / "faostat_blueberries.csv"


# Official FAOSTAT bulk-download server.
# Split into host/path simply to keep configuration readable.
FAOSTAT_HOST = "bulks-faostat.fao.org"
FAOSTAT_RESOURCE = (
    "production/"
    "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
)

FAOSTAT_URL = f"https://{FAOSTAT_HOST}/{FAOSTAT_RESOURCE}"


COUNTRIES = [
    "Spain",
    "Netherlands",
    "Mexico",
    "Peru",
    "Chile",
    "South Africa",
]

ELEMENTS = [
    "Area harvested",
    "Production",
    "Yield",
]

START_YEAR = 2010


def download_file() -> None:
    if ZIP_PATH.exists():
        print(f"Using cached file: {ZIP_PATH}")
        return

    print("Downloading FAOSTAT crop-production dataset...")
    urlretrieve(FAOSTAT_URL, ZIP_PATH)
    print(f"Saved to: {ZIP_PATH}")


def load_blueberry_data() -> pd.DataFrame:
    parts = []

    with zipfile.ZipFile(ZIP_PATH) as archive:
        csv_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv")
            and "normalized" in name.lower()
        ]

        if not csv_files:
            csv_files = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv")
            ]

        if not csv_files:
            raise RuntimeError("No CSV file found inside FAOSTAT archive.")

        csv_name = csv_files[0]
        print(f"Reading: {csv_name}")

        with archive.open(csv_name) as file:
            for chunk in pd.read_csv(
                file,
                encoding="utf-8-sig",
                chunksize=200_000,
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

                    existing_columns = [
                        col for col in columns if col in chunk.columns
                    ]

                    parts.append(
                        chunk.loc[mask, existing_columns].copy()
                    )

    if not parts:
        raise RuntimeError(
            "No blueberry records were found for the selected countries."
        )

    data = pd.concat(parts, ignore_index=True)

    data = data.sort_values(
        ["Area", "Year", "Element"]
    ).reset_index(drop=True)

    return data


def main() -> None:
    download_file()

    data = load_blueberry_data()

    data.to_csv(OUTPUT_PATH, index=False)

    print()
    print(f"Saved {len(data):,} rows to:")
    print(OUTPUT_PATH)

    print()
    print("Coverage by country and metric:")
    print(
        data.groupby(["Area", "Element"])["Year"]
        .agg(["min", "max", "count"])
        .to_string()
    )


if __name__ == "__main__":
    main()
