# Global Nursery Finance Analytics

A finance analytics portfolio project built around a fictional international blueberry nursery business.

The project combines **Python, automated Excel reporting and Power BI** to analyze regional performance, Budget vs Forecast results and investment decisions.

> Public blueberry market data are used as external drivers. Company-level financial data and assumptions are modeled for portfolio purposes and do not represent any real company.

## Interactive Power BI Dashboard

[**Open the interactive dashboard**](https://app.powerbi.com/view?r=eyJrIjoiNjQwNzdmYWItMDM2MC00MzY3LWFhOGYtMzE3YTZkMmNmMWM4IiwidCI6ImM5YjZjNzVhLTk3MzAtNDkwMC1hMDQ0LTVlNTM3NjhlMTM3OSJ9&pageName=a20dbd2f80ff19abbce0)

The dashboard provides an executive and monthly view of financial performance, with interactive country filtering and Budget vs Forecast analysis.

## Excel Financial Model

[**Download the automated Excel model**](excel/Nursery_FP&A_Model.xlsx)

The workbook includes executive reporting, monthly performance, regional Budget vs Forecast analysis and a CAPEX investment case with NPV, IRR and payback calculations.

## 2025 Forecast

| Metric | Result |
|---|---:|
| Revenue | $4.19M |
| Revenue vs Budget | +3.0% |
| EBITDA | $1.19M |
| EBITDA vs Budget | +6.7% |

Peru is the main modeled upside driver, while Chile and Spain remain below revenue plan.

## Workflow

```text
FAOSTAT market data
        ↓
Python data pipeline
        ↓
Financial & operational model
        ↓
Budget / Forecast / CAPEX analysis
        ↓
Excel reporting + Power BI