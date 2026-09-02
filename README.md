# Global Nursery Finance Analytics

A finance analytics portfolio project built around a fictional international blueberry nursery business.

The project combines **Python, automated Excel reporting and Power BI** to analyze regional performance, Budget vs Forecast results and investment decisions.

> Public blueberry market data are used as external drivers. Company-level financial data and assumptions are modeled for portfolio purposes and do not represent any real company.

## Live Portfolio

[**Open the interactive portfolio**](https://rubengarciad93bioinfo.github.io/nursery-fpna-analytics/)

The portfolio provides a visual overview of the project, including an embedded Power BI dashboard, executive KPIs, CAPEX scenario analysis and access to the underlying Excel financial model.

## Interactive Power BI Dashboard

[**Open the Power BI dashboard**](https://app.powerbi.com/view?r=eyJrIjoiNjQwNzdmYWItMDM2MC00MzY3LWFhOGYtMzE3YTZkMmNmMWM4IiwidCI6ImM5YjZjNzVhLTk3MzAtNDkwMC1hMDQ0LTVlNTM3NjhlMTM3OSJ9&pageName=a20dbd2f80ff19abbce0)

The dashboard provides executive and monthly views of financial performance, with interactive country filtering and Budget vs Forecast analysis.

## Excel Financial Model

[**Download the automated Excel model**](excel/Nursery_FP&A_Model.xlsx)

The workbook includes executive reporting, monthly performance, regional Budget vs Forecast analysis and a CAPEX investment case using NPV, IRR and payback calculations.

## 2025 Forecast

| Metric | Result |
|---|---:|
| Revenue | $4.19M |
| Revenue vs Budget | +3.0% |
| EBITDA | $1.19M |
| EBITDA vs Budget | +6.7% |

Peru is the main modeled upside driver, while Chile and Spain remain below revenue plan.

## CAPEX Investment Case

A modeled 5-year nursery expansion was evaluated under Downside, Base and Upside scenarios.

| Base Case Metric | Result |
|---|---:|
| Initial Investment | $850k |
| NPV | +$218k |
| IRR | 18.0% |
| Payback | 3.6 years |
| Discount Rate | 10.0% |

The positive NPV and an IRR above the modeled 10% hurdle rate support the investment under the Base Case assumptions. Full scenario analysis is available in the portfolio and Excel workbook.

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
Automated Excel reporting + Power BI
```

## Tools

**Python · pandas · Excel · XlsxWriter · Power BI · Power Query · DAX · Git**