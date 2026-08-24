from pathlib import Path

import numpy as np
import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "excel"
OUTPUT_PATH = OUTPUT_DIR / "Nursery_FP&A_Model.xlsx"

MONTHLY_PATH = DATA_DIR / "monthly_fpna.csv"
CAPEX_SUMMARY_PATH = DATA_DIR / "capex_analysis.csv"
CAPEX_CASHFLOW_PATH = DATA_DIR / "capex_cashflows.csv"
ASSUMPTIONS_PATH = DATA_DIR / "fpna_assumptions.csv"
SEASONALITY_PATH = DATA_DIR / "monthly_seasonality.csv"

FAOSTAT_URL = "https://www.fao.org/faostat/"

COUNTRY_ORDER = ["Chile", "Mexico", "Peru", "Spain"]
SCENARIO_ORDER = ["Downside", "Base", "Upside"]


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, np.generic):
        return value.item()
    return value


def raw_range(sheet_name, df, column, data_start_excel_row):
    col = xl_col_to_name(df.columns.get_loc(column))
    data_end_excel_row = data_start_excel_row + len(df) - 1
    return (
        f"'{sheet_name}'!${col}${data_start_excel_row}:"
        f"${col}${data_end_excel_row}"
    )


def write_df(worksheet, df, start_row, start_col, formats, table_name=None):
    header_fmt = formats["raw_header"]
    date_fmt = formats["date"]

    for col_idx, column in enumerate(df.columns):
        worksheet.write(start_row, start_col + col_idx, column, header_fmt)

    for row_offset, row in enumerate(df.itertuples(index=False, name=None), start=1):
        for col_offset, value in enumerate(row):
            value = clean_value(value)
            target_row = start_row + row_offset
            target_col = start_col + col_offset

            if value is None:
                worksheet.write_blank(target_row, target_col, None)
            elif isinstance(value, pd.Timestamp):
                worksheet.write_datetime(target_row, target_col, value.to_pydatetime(), date_fmt)
            elif hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day") and not isinstance(value, str):
                worksheet.write_datetime(target_row, target_col, value, date_fmt)
            else:
                worksheet.write(target_row, target_col, value)

    if table_name and len(df) > 0:
        worksheet.add_table(
            start_row,
            start_col,
            start_row + len(df),
            start_col + len(df.columns) - 1,
            {
                "name": table_name,
                "style": "Table Style Medium 2",
                "columns": [{"header": c} for c in df.columns],
            },
        )


def build_formats(workbook):
    dark_blue = "#17365D"
    medium_blue = "#1F4E78"
    light_blue = "#D9EAF7"
    light_green = "#E2F0D9"
    light_red = "#FCE4D6"
    gray = "#666666"

    return {
        "title": workbook.add_format({
            "bold": True, "font_size": 18, "font_color": "#FFFFFF",
            "bg_color": dark_blue, "align": "left", "valign": "vcenter"
        }),
        "subtitle": workbook.add_format({
            "font_size": 10, "font_color": gray, "italic": True,
            "align": "left", "valign": "vcenter"
        }),
        "section": workbook.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": medium_blue,
            "align": "left", "valign": "vcenter", "border": 0
        }),
        "header": workbook.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": medium_blue,
            "align": "center", "valign": "vcenter", "border": 1,
            "text_wrap": True
        }),
        "raw_header": workbook.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": medium_blue,
            "align": "center", "valign": "vcenter", "border": 1
        }),
        "label": workbook.add_format({"bold": True, "font_color": "#333333"}),
        "text": workbook.add_format({"font_color": "#000000"}),
        "input": workbook.add_format({"font_color": "#0000FF"}),
        "formula": workbook.add_format({"font_color": "#000000"}),
        "link": workbook.add_format({"font_color": "#008000"}),
        "currency": workbook.add_format({
            "num_format": '$#,##0;[Red]($#,##0);-', "font_color": "#000000"
        }),
        "currency_link": workbook.add_format({
            "num_format": '$#,##0;[Red]($#,##0);-', "font_color": "#008000"
        }),
        "currency_input": workbook.add_format({
            "num_format": '$#,##0;[Red]($#,##0);-', "font_color": "#0000FF"
        }),
        "currency_2": workbook.add_format({
            "num_format": '$0.00;[Red]($0.00);-', "font_color": "#000000"
        }),
        "currency_2_input": workbook.add_format({
            "num_format": '$0.00;[Red]($0.00);-', "font_color": "#0000FF"
        }),
        "percent": workbook.add_format({
            "num_format": '0.0%;[Red](0.0%);-', "font_color": "#000000"
        }),
        "percent_link": workbook.add_format({
            "num_format": '0.0%;[Red](0.0%);-', "font_color": "#008000"
        }),
        "percent_input": workbook.add_format({
            "num_format": '0.0%;[Red](0.0%);-', "font_color": "#0000FF"
        }),
        "number": workbook.add_format({
            "num_format": '#,##0;[Red](#,##0);-', "font_color": "#000000"
        }),
        "number_input": workbook.add_format({
            "num_format": '#,##0;[Red](#,##0);-', "font_color": "#0000FF"
        }),
        "decimal": workbook.add_format({
            "num_format": '#,##0.0;[Red](#,##0.0);-', "font_color": "#000000"
        }),
        "date": workbook.add_format({"num_format": "yyyy-mm-dd"}),
        "total_label": workbook.add_format({
            "bold": True, "top": 1, "font_color": "#000000"
        }),
        "total_currency": workbook.add_format({
            "bold": True, "top": 1,
            "num_format": '$#,##0;[Red]($#,##0);-', "font_color": "#000000"
        }),
        "total_percent": workbook.add_format({
            "bold": True, "top": 1,
            "num_format": '0.0%;[Red](0.0%);-', "font_color": "#000000"
        }),
        "kpi_label": workbook.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": medium_blue,
            "align": "center", "valign": "vcenter", "border": 1
        }),
        "kpi_currency": workbook.add_format({
            "bold": True, "font_size": 16, "font_color": "#008000",
            "bg_color": "#F7FBFF", "align": "center", "valign": "vcenter",
            "num_format": '$#,##0;[Red]($#,##0);-', "border": 1
        }),
        "kpi_percent": workbook.add_format({
            "bold": True, "font_size": 16, "font_color": "#008000",
            "bg_color": "#F7FBFF", "align": "center", "valign": "vcenter",
            "num_format": '0.0%;[Red](0.0%);-', "border": 1
        }),
        "note": workbook.add_format({
            "font_size": 9, "font_color": gray, "italic": True, "text_wrap": True,
            "valign": "top"
        }),
        "insight": workbook.add_format({
            "font_size": 10, "font_color": "#222222", "bg_color": "#F2F2F2",
            "text_wrap": True, "valign": "top", "border": 1
        }),
        "positive": workbook.add_format({"font_color": "#008000", "bg_color": light_green}),
        "negative": workbook.add_format({"font_color": "#C00000", "bg_color": light_red}),
        "highlight_input": workbook.add_format({
            "font_color": "#0000FF", "bg_color": "#FFF2CC", "border": 1
        }),
    }


def main():
    required = [MONTHLY_PATH, CAPEX_SUMMARY_PATH, CAPEX_CASHFLOW_PATH, ASSUMPTIONS_PATH]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    monthly = pd.read_csv(MONTHLY_PATH, parse_dates=["Date"])
    capex_summary = pd.read_csv(CAPEX_SUMMARY_PATH)
    capex_cashflows = pd.read_csv(CAPEX_CASHFLOW_PATH)
    assumptions = pd.read_csv(ASSUMPTIONS_PATH)
    seasonality = pd.read_csv(SEASONALITY_PATH) if SEASONALITY_PATH.exists() else None

    workbook = xlsxwriter.Workbook(OUTPUT_PATH)
    workbook.set_properties({
        "title": "Nursery FP&A Analytics Model",
        "subject": "Financial reporting, forecasting and CAPEX decision support",
        "author": "Portfolio Project",
        "comments": "Synthetic financial model using public FAOSTAT market data as external drivers.",
    })
    formats = build_formats(workbook)

    # Create sheets in presentation order.
    ws_e = workbook.add_worksheet("Executive Summary")
    ws_m = workbook.add_worksheet("Monthly Performance")
    ws_bv = workbook.add_worksheet("Budget vs Forecast")
    ws_c = workbook.add_worksheet("CAPEX")
    ws_a = workbook.add_worksheet("Assumptions")
    ws_raw = workbook.add_worksheet("Raw_Monthly")
    ws_rc = workbook.add_worksheet("Raw_CAPEX")

    # ---------- RAW MONTHLY ----------
    ws_raw.hide_gridlines(2)
    ws_raw.write("A1", "Source: FAOSTAT Production Crops and Livestock (external market drivers). Company financials and seasonality are modeled assumptions.", formats["note"])
    ws_raw.write_url("Z1", FAOSTAT_URL, string="FAOSTAT source")
    raw_monthly_header_row = 2
    write_df(ws_raw, monthly, raw_monthly_header_row, 0, formats, "tblMonthly")
    ws_raw.freeze_panes(raw_monthly_header_row + 1, 0)
    ws_raw.set_column(0, 0, 12)
    ws_raw.set_column(1, 5, 11)
    ws_raw.set_column(6, len(monthly.columns) - 1, 16)
    for header in ["Market_Area_Harvested_ha", "Market_Production_t", "Market_Yield_kg_ha"]:
        if header in monthly.columns:
            c = monthly.columns.get_loc(header)
            ws_raw.write_comment(raw_monthly_header_row, c, "External market driver sourced from FAOSTAT. See README/source documentation.")

    raw_monthly_data_start_excel = raw_monthly_header_row + 2

    # ---------- RAW CAPEX ----------
    ws_rc.hide_gridlines(2)
    ws_rc.write("A1", "Synthetic CAPEX scenarios for portfolio demonstration. These figures do not represent Fall Creek or any other company.", formats["note"])
    capex_summary_header_row = 2
    write_df(ws_rc, capex_summary, capex_summary_header_row, 0, formats, "tblCAPEXSummary")
    capex_cashflow_header_row = capex_summary_header_row + len(capex_summary) + 4
    write_df(ws_rc, capex_cashflows, capex_cashflow_header_row, 0, formats, "tblCAPEXCashflows")
    ws_rc.set_column(0, 0, 14)
    ws_rc.set_column(1, len(capex_cashflows.columns) - 1, 18)
    ws_rc.freeze_panes(capex_summary_header_row + 1, 0)

    raw_capex_summary_data_start_excel = capex_summary_header_row + 2
    raw_capex_cashflow_data_start_excel = capex_cashflow_header_row + 2

    # ---------- ASSUMPTIONS ----------
    ws_a.hide_gridlines(2)
    ws_a.merge_range("A1:I1", "Model Assumptions", formats["title"])
    ws_a.merge_range("A2:I2", "Blue font = hardcoded/model inputs. Financial company assumptions are synthetic; market drivers originate from FAOSTAT.", formats["subtitle"])

    display_cols = [
        ("Country", "Country"),
        ("market_share", "Market Share"),
        ("plants_per_ha", "Plants / ha"),
        ("replacement_rate", "Replacement Rate"),
        ("price_per_plant", "Price / Plant ($)"),
        ("variable_cost_per_plant", "Variable Cost / Plant ($)"),
        ("annual_opex", "Annual OPEX ($)"),
        ("budget_growth", "Budget Growth"),
        ("forecast_adjustment", "Forecast Adjustment"),
    ]
    assumption_display = assumptions[[c for c, _ in display_cols]].copy()
    assumption_display.columns = [d for _, d in display_cols]

    start_row = 3
    for j, col in enumerate(assumption_display.columns):
        ws_a.write(start_row, j, col, formats["header"])
    for i, row in assumption_display.iterrows():
        excel_row = start_row + 1 + i
        for j, value in enumerate(row):
            fmt = formats["input"]
            col_name = assumption_display.columns[j]
            if col_name in ["Market Share", "Replacement Rate", "Budget Growth", "Forecast Adjustment"]:
                fmt = formats["percent_input"]
            elif col_name in ["Price / Plant ($)", "Variable Cost / Plant ($)"]:
                fmt = formats["currency_2_input"]
            elif col_name == "Annual OPEX ($)":
                fmt = formats["currency_input"]
            elif col_name == "Plants / ha":
                fmt = formats["number_input"]
            ws_a.write(excel_row, j, clean_value(value), fmt)

    ws_a.write("A11", "Assumption Lookup (editable)", formats["section"])
    ws_a.write("A13", "Selected Country", formats["label"])
    ws_a.write("B13", "Peru", formats["highlight_input"])
    ws_a.data_validation("B13", {"validate": "list", "source": "=$A$5:$A$8"})

    peru = assumptions.set_index("Country").loc["Peru"]
    ws_a.write("A14", "Price / Plant", formats["label"])
    ws_a.write_formula("B14", '=INDEX($E$5:$E$8,MATCH($B$13,$A$5:$A$8,0))', formats["currency_2"], float(peru["price_per_plant"]))
    ws_a.write("A15", "Market Share", formats["label"])
    ws_a.write_formula("B15", '=INDEX($B$5:$B$8,MATCH($B$13,$A$5:$A$8,0))', formats["percent"], float(peru["market_share"]))
    ws_a.write("A16", "Annual OPEX", formats["label"])
    ws_a.write_formula("B16", '=INDEX($G$5:$G$8,MATCH($B$13,$A$5:$A$8,0))', formats["currency"], float(peru["annual_opex"]))
    ws_a.write_comment("A11", "This section demonstrates a lookup-driven assumption retrieval using INDEX/MATCH. Change the selected country in B13.")

    if seasonality is not None:
        sea_start = 18
        ws_a.merge_range(sea_start, 0, sea_start, 4, "Monthly Seasonality Assumptions", formats["section"])
        sea_display = seasonality.copy()
        write_df(ws_a, sea_display, sea_start + 1, 0, formats, "tblSeasonality")
        ws_a.set_column(0, 0, 16)
        ws_a.set_column(1, 3, 18)
        if "Sales_Weight" in sea_display.columns:
            col = sea_display.columns.get_loc("Sales_Weight")
            ws_a.set_column(col, col, 16, formats["percent_input"])
    ws_a.set_column("A:A", 22)
    ws_a.set_column("B:I", 19)

    # Reusable raw ranges for formulas.
    rr = lambda c: raw_range("Raw_Monthly", monthly, c, raw_monthly_data_start_excel)
    year_rng = rr("Year")
    month_num_rng = rr("Month_Num")
    country_rng = rr("Country")
    scenario_rng = rr("Scenario")
    revenue_rng = rr("Revenue")
    ebitda_rng = rr("EBITDA")
    gp_rng = rr("Gross_Profit")

    # ---------- BUDGET VS FORECAST ----------
    ws_bv.hide_gridlines(2)
    ws_bv.merge_range("A1:I1", "2025 Budget vs Forecast", formats["title"])
    ws_bv.merge_range("A2:I2", "Regional variance analysis. Green font indicates formulas linked to source data on another worksheet.", formats["subtitle"])
    headers = ["Country", "Budget Revenue ($)", "Forecast Revenue ($)", "Revenue Var ($)", "Revenue Var (%)", "Budget EBITDA ($)", "Forecast EBITDA ($)", "EBITDA Var ($)", "EBITDA Var (%)"]
    header_row = 3
    for col, header in enumerate(headers):
        ws_bv.write(header_row, col, header, formats["header"])

    annual = monthly[monthly["Year"].eq(2025)].groupby(["Country", "Scenario"], as_index=False)[["Revenue", "EBITDA"]].sum()
    annual_idx = annual.set_index(["Country", "Scenario"])

    for i, country in enumerate(COUNTRY_ORDER):
        row = header_row + 1 + i
        erow = row + 1
        b_rev = float(annual_idx.loc[(country, "Budget"), "Revenue"])
        f_rev = float(annual_idx.loc[(country, "Forecast"), "Revenue"])
        b_eb = float(annual_idx.loc[(country, "Budget"), "EBITDA"])
        f_eb = float(annual_idx.loc[(country, "Forecast"), "EBITDA"])

        ws_bv.write(row, 0, country)
        f_budget_rev = f'=SUMIFS({revenue_rng},{country_rng},$A{erow},{scenario_rng},"Budget",{year_rng},2025)'
        f_forecast_rev = f'=SUMIFS({revenue_rng},{country_rng},$A{erow},{scenario_rng},"Forecast",{year_rng},2025)'
        f_budget_eb = f'=SUMIFS({ebitda_rng},{country_rng},$A{erow},{scenario_rng},"Budget",{year_rng},2025)'
        f_forecast_eb = f'=SUMIFS({ebitda_rng},{country_rng},$A{erow},{scenario_rng},"Forecast",{year_rng},2025)'
        ws_bv.write_formula(row, 1, f_budget_rev, formats["currency_link"], b_rev)
        ws_bv.write_formula(row, 2, f_forecast_rev, formats["currency_link"], f_rev)
        ws_bv.write_formula(row, 3, f"=C{erow}-B{erow}", formats["currency"], f_rev - b_rev)
        ws_bv.write_formula(row, 4, f"=IFERROR(D{erow}/B{erow},0)", formats["percent"], (f_rev - b_rev) / b_rev)
        ws_bv.write_formula(row, 5, f_budget_eb, formats["currency_link"], b_eb)
        ws_bv.write_formula(row, 6, f_forecast_eb, formats["currency_link"], f_eb)
        ws_bv.write_formula(row, 7, f"=G{erow}-F{erow}", formats["currency"], f_eb - b_eb)
        ws_bv.write_formula(row, 8, f"=IFERROR(H{erow}/F{erow},0)", formats["percent"], (f_eb - b_eb) / b_eb)

    total_row = header_row + 1 + len(COUNTRY_ORDER)
    total_erow = total_row + 1
    ws_bv.write(total_row, 0, "Total", formats["total_label"])
    for col in [1, 2, 3, 5, 6, 7]:
        letter = xl_col_to_name(col)
        val = None
        if col == 1:
            val = float(annual[annual["Scenario"].eq("Budget")]["Revenue"].sum())
        elif col == 2:
            val = float(annual[annual["Scenario"].eq("Forecast")]["Revenue"].sum())
        elif col == 3:
            val = float(annual[annual["Scenario"].eq("Forecast")]["Revenue"].sum() - annual[annual["Scenario"].eq("Budget")]["Revenue"].sum())
        elif col == 5:
            val = float(annual[annual["Scenario"].eq("Budget")]["EBITDA"].sum())
        elif col == 6:
            val = float(annual[annual["Scenario"].eq("Forecast")]["EBITDA"].sum())
        elif col == 7:
            val = float(annual[annual["Scenario"].eq("Forecast")]["EBITDA"].sum() - annual[annual["Scenario"].eq("Budget")]["EBITDA"].sum())
        ws_bv.write_formula(total_row, col, f"=SUM({letter}5:{letter}8)", formats["total_currency"], val)
    total_b_rev = float(annual[annual["Scenario"].eq("Budget")]["Revenue"].sum())
    total_f_rev = float(annual[annual["Scenario"].eq("Forecast")]["Revenue"].sum())
    total_b_eb = float(annual[annual["Scenario"].eq("Budget")]["EBITDA"].sum())
    total_f_eb = float(annual[annual["Scenario"].eq("Forecast")]["EBITDA"].sum())
    ws_bv.write_formula(total_row, 4, f"=IFERROR(D{total_erow}/B{total_erow},0)", formats["total_percent"], (total_f_rev-total_b_rev)/total_b_rev)
    ws_bv.write_formula(total_row, 8, f"=IFERROR(H{total_erow}/F{total_erow},0)", formats["total_percent"], (total_f_eb-total_b_eb)/total_b_eb)
    ws_bv.conditional_format(4, 4, 7, 4, {"type": "cell", "criteria": ">=", "value": 0, "format": formats["positive"]})
    ws_bv.conditional_format(4, 4, 7, 4, {"type": "cell", "criteria": "<", "value": 0, "format": formats["negative"]})
    ws_bv.conditional_format(4, 8, 7, 8, {"type": "cell", "criteria": ">=", "value": 0, "format": formats["positive"]})
    ws_bv.conditional_format(4, 8, 7, 8, {"type": "cell", "criteria": "<", "value": 0, "format": formats["negative"]})
    ws_bv.set_column("A:A", 14)
    ws_bv.set_column("B:I", 19)
    ws_bv.freeze_panes(4, 1)

    # ---------- MONTHLY PERFORMANCE ----------
    ws_m.hide_gridlines(2)
    ws_m.merge_range("A1:G1", "2025 Monthly Performance", formats["title"])
    ws_m.merge_range("A2:G2", "Monthly Budget vs Forecast reporting using the modeled regional seasonality assumptions.", formats["subtitle"])
    mh = ["Month", "Budget Revenue ($)", "Forecast Revenue ($)", "Revenue Var (%)", "Budget EBITDA ($)", "Forecast EBITDA ($)", "EBITDA Var (%)"]
    for c, h in enumerate(mh):
        ws_m.write(3, c, h, formats["header"])

    month_data = monthly[monthly["Year"].eq(2025)].groupby(["Month_Num", "Month", "Scenario"], as_index=False)[["Revenue", "EBITDA"]].sum()
    month_idx = month_data.set_index(["Month_Num", "Scenario"])
    month_names = monthly[["Month_Num", "Month"]].drop_duplicates().sort_values("Month_Num").set_index("Month_Num")["Month"].to_dict()

    for month_num in range(1, 13):
        row = 3 + month_num
        erow = row + 1
        month_name = month_names[month_num]
        b_rev = float(month_idx.loc[(month_num, "Budget"), "Revenue"])
        f_rev = float(month_idx.loc[(month_num, "Forecast"), "Revenue"])
        b_eb = float(month_idx.loc[(month_num, "Budget"), "EBITDA"])
        f_eb = float(month_idx.loc[(month_num, "Forecast"), "EBITDA"])
        ws_m.write(row, 0, month_name)
        fb = f'=SUMIFS({revenue_rng},{month_num_rng},{month_num},{scenario_rng},"Budget",{year_rng},2025)'
        ff = f'=SUMIFS({revenue_rng},{month_num_rng},{month_num},{scenario_rng},"Forecast",{year_rng},2025)'
        febb = f'=SUMIFS({ebitda_rng},{month_num_rng},{month_num},{scenario_rng},"Budget",{year_rng},2025)'
        febf = f'=SUMIFS({ebitda_rng},{month_num_rng},{month_num},{scenario_rng},"Forecast",{year_rng},2025)'
        ws_m.write_formula(row, 1, fb, formats["currency_link"], b_rev)
        ws_m.write_formula(row, 2, ff, formats["currency_link"], f_rev)
        ws_m.write_formula(row, 3, f"=IFERROR(C{erow}/B{erow}-1,0)", formats["percent"], f_rev/b_rev - 1)
        ws_m.write_formula(row, 4, febb, formats["currency_link"], b_eb)
        ws_m.write_formula(row, 5, febf, formats["currency_link"], f_eb)
        ws_m.write_formula(row, 6, f"=IFERROR(F{erow}/E{erow}-1,0)", formats["percent"], f_eb/b_eb - 1)

    total_row_m = 16
    ws_m.write(total_row_m, 0, "Total", formats["total_label"])
    for col in [1, 2, 4, 5]:
        letter = xl_col_to_name(col)
        value = [total_b_rev, total_f_rev, total_b_eb, total_f_eb][[1,2,4,5].index(col)]
        ws_m.write_formula(total_row_m, col, f"=SUM({letter}5:{letter}16)", formats["total_currency"], value)
    ws_m.write_formula(total_row_m, 3, "=IFERROR(C17/B17-1,0)", formats["total_percent"], total_f_rev/total_b_rev - 1)
    ws_m.write_formula(total_row_m, 6, "=IFERROR(F17/E17-1,0)", formats["total_percent"], total_f_eb/total_b_eb - 1)
    ws_m.conditional_format("D5:D16", {"type": "3_color_scale", "min_color": "#F8696B", "mid_color": "#FFEB84", "max_color": "#63BE7B"})
    ws_m.conditional_format("G5:G16", {"type": "3_color_scale", "min_color": "#F8696B", "mid_color": "#FFEB84", "max_color": "#63BE7B"})
    ws_m.set_column("A:A", 12)
    ws_m.set_column("B:G", 19)

    revenue_chart = workbook.add_chart({"type": "line"})
    revenue_chart.add_series({"name": "Budget Revenue", "categories": "='Monthly Performance'!$A$5:$A$16", "values": "='Monthly Performance'!$B$5:$B$16", "line": {"width": 2}})
    revenue_chart.add_series({"name": "Forecast Revenue", "categories": "='Monthly Performance'!$A$5:$A$16", "values": "='Monthly Performance'!$C$5:$C$16", "line": {"width": 2}})
    revenue_chart.set_title({"name": "Monthly Revenue: Budget vs Forecast"})
    revenue_chart.set_y_axis({"name": "Revenue ($)", "num_format": "$#,##0"})
    revenue_chart.set_legend({"position": "bottom"})
    revenue_chart.set_style(10)
    ws_m.insert_chart("I4", revenue_chart, {"x_scale": 1.35, "y_scale": 1.25})

    ebitda_chart = workbook.add_chart({"type": "line"})
    ebitda_chart.add_series({"name": "Budget EBITDA", "categories": "='Monthly Performance'!$A$5:$A$16", "values": "='Monthly Performance'!$E$5:$E$16", "line": {"width": 2}})
    ebitda_chart.add_series({"name": "Forecast EBITDA", "categories": "='Monthly Performance'!$A$5:$A$16", "values": "='Monthly Performance'!$F$5:$F$16", "line": {"width": 2}})
    ebitda_chart.set_title({"name": "Monthly EBITDA: Budget vs Forecast"})
    ebitda_chart.set_y_axis({"name": "EBITDA ($)", "num_format": "$#,##0"})
    ebitda_chart.set_legend({"position": "bottom"})
    ebitda_chart.set_style(10)
    ws_m.insert_chart("I20", ebitda_chart, {"x_scale": 1.35, "y_scale": 1.25})

    # ---------- CAPEX ----------
    ws_c.hide_gridlines(2)
    ws_c.merge_range("A1:J1", "CAPEX Decision Support", formats["title"])
    ws_c.merge_range("A2:J2", "Potential Peru nursery capacity expansion. NPV and IRR are calculated from scenario cash flows in this workbook.", formats["subtitle"])
    sh = ["Scenario", "Initial Investment ($)", "Discount Rate", "NPV ($)", "IRR", "Payback (Years)"]
    for c, h in enumerate(sh):
        ws_c.write(3, c, h, formats["header"])

    cs = capex_summary.set_index("Scenario")
    raw_summary_end = raw_capex_summary_data_start_excel + len(capex_summary) - 1
    for i, scenario in enumerate(SCENARIO_ORDER):
        row = 4 + i
        erow = row + 1
        ws_c.write(row, 0, scenario)
        scenario_cell = f"$A{erow}"
        # Raw summary columns: A Scenario, B Initial_Investment, C Discount_Rate_pct, D NPV, E IRR_pct, F Payback_Years.
        for col, raw_col, fmt, cache, divisor in [
            (1, "B", formats["currency_link"], float(cs.loc[scenario, "Initial_Investment"]), 1),
            (2, "C", formats["percent_link"], float(cs.loc[scenario, "Discount_Rate_pct"]) / 100, 100),
            (3, "D", formats["currency_link"], float(cs.loc[scenario, "NPV"]), 1),
            (4, "E", formats["percent_link"], float(cs.loc[scenario, "IRR_pct"]) / 100, 100),
            (5, "F", formats["decimal"], float(cs.loc[scenario, "Payback_Years"]) if pd.notna(cs.loc[scenario, "Payback_Years"]) else None, 1),
        ]:
            base_formula = f'INDEX(\'Raw_CAPEX\'!${raw_col}${raw_capex_summary_data_start_excel}:${raw_col}${raw_summary_end},MATCH({scenario_cell},\'Raw_CAPEX\'!$A${raw_capex_summary_data_start_excel}:$A${raw_summary_end},0))'
            formula = f'={base_formula}' if divisor == 1 else f'={base_formula}/{divisor}'
            ws_c.write_formula(row, col, formula, fmt, cache)

    ws_c.write("A9", "Scenario Cash Flows and Formula Check", formats["section"])
    headers_cf = ["Scenario", "Year 0", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5", "NPV ($)", "IRR", "Payback (Years)"]
    for c, h in enumerate(headers_cf):
        ws_c.write(9, c, h, formats["header"])

    raw_cf_end = raw_capex_cashflow_data_start_excel + len(capex_cashflows) - 1
    raw_scen_rng = f"'Raw_CAPEX'!$A${raw_capex_cashflow_data_start_excel}:$A${raw_cf_end}"
    raw_year_rng = f"'Raw_CAPEX'!$B${raw_capex_cashflow_data_start_excel}:$B${raw_cf_end}"
    raw_ncf_col = xl_col_to_name(capex_cashflows.columns.get_loc("Net_Cash_Flow"))
    raw_ncf_rng = f"'Raw_CAPEX'!${raw_ncf_col}${raw_capex_cashflow_data_start_excel}:${raw_ncf_col}${raw_cf_end}"
    cf_idx = capex_cashflows.set_index(["Scenario", "Year"])["Net_Cash_Flow"]

    for i, scenario in enumerate(SCENARIO_ORDER):
        row = 10 + i
        erow = row + 1
        ws_c.write(row, 0, scenario)
        for year in range(0, 6):
            cache = float(cf_idx.loc[(scenario, year)])
            formula = f'=SUMIFS({raw_ncf_rng},{raw_scen_rng},$A{erow},{raw_year_rng},{year})'
            ws_c.write_formula(row, 1 + year, formula, formats["currency_link"], cache)
        discount_rate = float(cs.loc[scenario, "Discount_Rate_pct"]) / 100
        npv_cache = float(cs.loc[scenario, "NPV"])
        irr_cache = float(cs.loc[scenario, "IRR_pct"]) / 100
        payback_cache = float(cs.loc[scenario, "Payback_Years"]) if pd.notna(cs.loc[scenario, "Payback_Years"]) else None
        ws_c.write_formula(
            row, 7,
            f"=NPV(INDEX($C$5:$C$7,MATCH($A{erow},$A$5:$A$7,0)),C{erow}:G{erow})+B{erow}",
            formats["currency"], npv_cache
        )
        ws_c.write_formula(row, 8, f"=IRR(B{erow}:G{erow})", formats["percent"], irr_cache)
        ws_c.write_formula(row, 9, f'=INDEX($F$5:$F$7,MATCH($A{erow},$A$5:$A$7,0))', formats["decimal"], payback_cache)

    base = cs.loc["Base"]
    recommendation = (
        f"Base case recommendation: proceed, subject to operational validation. "
        f"The modeled investment produces NPV of ${base['NPV']:,.0f}, IRR of {base['IRR_pct']:.1f}% "
        f"versus a {base['Discount_Rate_pct']:.1f}% discount rate, with payback in approximately {base['Payback_Years']:.1f} years. "
        f"The downside case should be monitored because it captures demand and cost risk."
    )
    ws_c.merge_range("A15:J18", recommendation, formats["insight"])
    ws_c.set_row(14, 24)
    ws_c.set_column("A:A", 14)
    ws_c.set_column("B:J", 17)

    cf_chart = workbook.add_chart({"type": "column"})
    cf_chart.add_series({"name": "Base Case Net Cash Flow", "categories": "=CAPEX!$B$10:$G$10", "values": "=CAPEX!$B$12:$G$12"})
    cf_chart.set_title({"name": "Base Case Project Cash Flows"})
    cf_chart.set_y_axis({"name": "Net Cash Flow ($)", "num_format": "$#,##0"})
    cf_chart.set_legend({"none": True})
    cf_chart.set_style(10)
    ws_c.insert_chart("A20", cf_chart, {"x_scale": 1.35, "y_scale": 1.2})

    # ---------- EXECUTIVE SUMMARY ----------
    ws_e.hide_gridlines(2)
    ws_e.merge_range("A1:L1", "Nursery FP&A Analytics — Executive Summary", formats["title"])
    ws_e.merge_range("A2:L2", "Portfolio case study using public blueberry market data as external drivers and transparent modeled financial assumptions.", formats["subtitle"])

    # KPI tiles.
    kpis = [
        ("A4:B4", "A5:B6", "Forecast Revenue", f"='Budget vs Forecast'!C{total_erow}", formats["kpi_currency"], total_f_rev),
        ("D4:E4", "D5:E6", "Revenue vs Budget", f"='Budget vs Forecast'!E{total_erow}", formats["kpi_percent"], total_f_rev/total_b_rev - 1),
        ("G4:H4", "G5:H6", "Forecast EBITDA", f"='Budget vs Forecast'!G{total_erow}", formats["kpi_currency"], total_f_eb),
        ("J4:K4", "J5:K6", "EBITDA vs Budget", f"='Budget vs Forecast'!I{total_erow}", formats["kpi_percent"], total_f_eb/total_b_eb - 1),
    ]
    for label_rng, value_rng, label, formula, fmt, cache in kpis:
        ws_e.merge_range(label_rng, label, formats["kpi_label"])
        ws_e.merge_range(value_rng, "", fmt)
        top_left = value_rng.split(":")[0]
        ws_e.write_formula(top_left, formula, fmt, cache)

    forecast = monthly[(monthly["Year"].eq(2025)) & (monthly["Scenario"].eq("Forecast"))]
    gross_margin = float(forecast["Gross_Profit"].sum() / forecast["Revenue"].sum())
    ebitda_margin = float(forecast["EBITDA"].sum() / forecast["Revenue"].sum())
    gm_formula = f'=SUMIFS({gp_rng},{scenario_rng},"Forecast",{year_rng},2025)/SUMIFS({revenue_rng},{scenario_rng},"Forecast",{year_rng},2025)'
    em_formula = f'=SUMIFS({ebitda_rng},{scenario_rng},"Forecast",{year_rng},2025)/SUMIFS({revenue_rng},{scenario_rng},"Forecast",{year_rng},2025)'
    ws_e.merge_range("A8:B8", "Forecast Gross Margin", formats["kpi_label"])
    ws_e.merge_range("A9:B10", "", formats["kpi_percent"])
    ws_e.write_formula("A9", gm_formula, formats["kpi_percent"], gross_margin)
    ws_e.merge_range("D8:E8", "Forecast EBITDA Margin", formats["kpi_label"])
    ws_e.merge_range("D9:E10", "", formats["kpi_percent"])
    ws_e.write_formula("D9", em_formula, formats["kpi_percent"], ebitda_margin)

    # Dynamic executive narrative from model outputs.
    country_var = {}
    for country in COUNTRY_ORDER:
        b = float(annual_idx.loc[(country, "Budget"), "Revenue"])
        f = float(annual_idx.loc[(country, "Forecast"), "Revenue"])
        country_var[country] = f / b - 1
    best_country = max(country_var, key=country_var.get)
    worst_country = min(country_var, key=country_var.get)
    narrative = (
        f"2025 forecast revenue is {total_f_rev/total_b_rev - 1:+.1%} vs budget and EBITDA is {total_f_eb/total_b_eb - 1:+.1%} vs budget. "
        f"{best_country} is the strongest regional revenue performer ({country_var[best_country]:+.1%} vs budget), while {worst_country} is the main downside ({country_var[worst_country]:+.1%}). "
        f"Management focus: protect margin in weaker regions, validate the Peru growth assumptions, and use the CAPEX sensitivity analysis before committing expansion capital."
    )
    ws_e.merge_range("A12:L15", narrative, formats["insight"])

    ws_e.write("A17", "Regional Snapshot", formats["section"])
    rh = ["Country", "Revenue Var (%)", "EBITDA Var (%)", "Status"]
    for c, h in enumerate(rh):
        ws_e.write(17, c, h, formats["header"])
    for i, country in enumerate(COUNTRY_ORDER):
        row = 18 + i
        erow = row + 1
        bv_row = 5 + i
        rev_var = country_var[country]
        b_eb = float(annual_idx.loc[(country, "Budget"), "EBITDA"])
        f_eb = float(annual_idx.loc[(country, "Forecast"), "EBITDA"])
        eb_var = f_eb / b_eb - 1
        ws_e.write(row, 0, country)
        ws_e.write_formula(row, 1, f"='Budget vs Forecast'!E{bv_row}", formats["percent_link"], rev_var)
        ws_e.write_formula(row, 2, f"='Budget vs Forecast'!I{bv_row}", formats["percent_link"], eb_var)
        status = "Ahead" if rev_var >= 0 else "Below"
        ws_e.write_formula(row, 3, f'=IF(B{erow}>=0,"Ahead","Below")', formats["formula"], status)
    ws_e.conditional_format("B19:C22", {"type": "3_color_scale", "min_color": "#F8696B", "mid_color": "#FFEB84", "max_color": "#63BE7B"})

    country_chart = workbook.add_chart({"type": "column"})
    country_chart.add_series({"name": "Budget Revenue", "categories": "='Budget vs Forecast'!$A$5:$A$8", "values": "='Budget vs Forecast'!$B$5:$B$8"})
    country_chart.add_series({"name": "Forecast Revenue", "categories": "='Budget vs Forecast'!$A$5:$A$8", "values": "='Budget vs Forecast'!$C$5:$C$8"})
    country_chart.set_title({"name": "Revenue by Region"})
    country_chart.set_y_axis({"name": "Revenue ($)", "num_format": "$#,##0"})
    country_chart.set_legend({"position": "bottom"})
    country_chart.set_style(10)
    ws_e.insert_chart("F17", country_chart, {"x_scale": 1.25, "y_scale": 1.15})

    ws_e.set_column("A:A", 16)
    ws_e.set_column("B:E", 18)
    ws_e.set_column("F:L", 14)
    ws_e.set_row(0, 28)
    ws_e.set_row(11, 24)

    # Move Executive Summary to first tab by setting active/select.
    ws_e.activate()
    ws_e.select()

    workbook.close()

    print(f"Workbook generated successfully:\n{OUTPUT_PATH}")
    print()
    print(f"2025 Budget Revenue:   ${total_b_rev:,.0f}")
    print(f"2025 Forecast Revenue: ${total_f_rev:,.0f}")
    print(f"Revenue variance:      {total_f_rev/total_b_rev - 1:+.1%}")
    print()
    print(f"2025 Budget EBITDA:    ${total_b_eb:,.0f}")
    print(f"2025 Forecast EBITDA:  ${total_f_eb:,.0f}")
    print(f"EBITDA variance:       {total_f_eb/total_b_eb - 1:+.1%}")
    print()
    print("Sheets created: 7")


if __name__ == "__main__":
    main()
