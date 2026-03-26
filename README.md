# US Housing Affordability Crisis

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Dashboard](https://img.shields.io/badge/🌐%20Live%20Dashboard-Click%20Here-2E86AB)](https://divyadhole.github.io/us-housing-affordability/)
[![Census](https://img.shields.io/badge/Data-Census%20ACS%202022-orange)](https://api.census.gov/data/2022/acs/acs1/)
[![FRED](https://img.shields.io/badge/Data-FRED%20Home%20Prices-blue)](https://fred.stlouisfed.org/)
[![HUD](https://img.shields.io/badge/Data-HUD%20Fair%20Market%20Rents-green)](https://www.huduser.gov/)
[![CI](https://github.com/Divyadhole/us-housing-affordability/workflows/Housing%20Analysis%20Validation/badge.svg)](https://github.com/Divyadhole/us-housing-affordability/actions)

## Live Dashboard

**[divyadhole.github.io/us-housing-affordability](https://divyadhole.github.io/us-housing-affordability/)**

---

## What This Shows

In 2000, the median US home cost 3.9x the median household income.
By 2022 it cost 6.1x. The traditional affordability threshold is 3x.
That line was crossed in 2003 and has never come back.

In 2023 the average family buying a median-priced home was spending
**34.7% of gross income** on the mortgage payment. The lender guideline is 28%.
We are 6 points over and showing no signs of returning.

This project tracks how that happened using real government data from
Census, FRED, and HUD — year by year, state by state.

---

## Data Sources

**Census Bureau ACS 2022 — Median Household Income by State**
```python
url = "https://api.census.gov/data/2022/acs/acs1/"
# Variable: B19013_001E — median household income
# No API key required for basic access
```

**Federal Reserve FRED — Home Prices and Mortgage Rates**
```python
# MSPUS       — Median Sales Price of Existing Homes
# MORTGAGE30US — 30-Year Fixed Mortgage Rate
# CSUSHPINSA  — Case-Shiller National Home Price Index
# https://fred.stlouisfed.org/
```

**HUD User — Fair Market Rents 2022**
```
https://www.huduser.gov/portal/datasets/fmr.html
# 2BR fair market rents by state, used for rent burden analysis
```

---

## The Numbers

| Metric | 2000 | 2010 | 2020 | 2023 |
|---|---|---|---|---|
| Median home price | $165,300 | $221,800 | $336,900 | $431,000 |
| Median income | $41,990 | $49,445 | $67,521 | $77,719 |
| Price-to-income ratio | **3.9x** | **4.5x** | **5.0x** | **5.5x** |
| 30yr mortgage rate | 8.05% | 4.69% | 3.11% | 6.81% |
| Monthly payment burden | 22.8% | 22.1% | 21.8% | **34.7%** |

The payment burden jump from 21.8% in 2020 to 34.7% in 2023 is the
compounding effect of prices rising AND rates nearly tripling.

---

## State Rankings (Most to Least Affordable)

| Most Unaffordable | Ratio | Most Affordable | Ratio |
|---|---|---|---|
| Hawaii | 9.6x | Iowa | 3.0x |
| California | 9.2x | Indiana | 3.6x |
| Colorado | 7.3x | Ohio | 3.4x |
| Oregon | 7.0x | Michigan | 3.8x |
| Washington | 6.8x | West Virginia | 3.3x |

12 states are at 5x or higher — the OECD "severely unaffordable" threshold.

---

## SQL Examples

```sql
-- When did housing break? Year-over-year price-to-income with LAG()
SELECT year, price_to_income,
    ROUND(price_to_income - LAG(price_to_income) OVER (ORDER BY year), 2) AS yoy_change,
    CASE WHEN price_to_income > 5 THEN 'Unaffordable'
         WHEN price_to_income > 4 THEN 'Strained'
         ELSE 'Moderate' END AS era
FROM national_housing ORDER BY year;

-- States where renting is also unaffordable
SELECT state_name, rent_2br, income,
    rent_burden_pct,
    CASE WHEN rent_burden_pct > 30 THEN 'Cost Burdened' ELSE 'OK' END AS status
FROM state_housing
WHERE rent_burden_pct > 28
ORDER BY rent_burden_pct DESC;

-- Regional affordability comparison
SELECT region, ROUND(AVG(price_to_income), 2) avg_pti,
    ROUND(AVG(rent_burden_pct), 1) avg_rent_burden
FROM state_housing
GROUP BY region ORDER BY avg_pti DESC;
```

---

## Project Layout

```
us-housing-affordability/
├── src/
│   ├── housing_data.py    # National + state data (Census ACS + HUD + FRED)
│   ├── charts.py          # 6 analysis charts
│   └── build_website.py   # GitHub Pages generator
├── sql/analysis/
│   └── housing_analysis.sql   # 7 queries with LAG, RANK, rolling AVG
├── .github/workflows/
│   └── validate.yml       # CI validation
├── data/
│   ├── processed/         # national_housing.csv, state_housing.csv
│   └── housing.db         # SQLite
├── docs/index.html        # Live dashboard
├── outputs/
│   ├── charts/            # 6 PNGs
│   └── excel/             # 6-sheet workbook
├── FINDINGS.md            # Why housing broke and hasn't fixed itself
└── run_analysis.py
```

---

## Run Locally

```bash
git clone https://github.com/Divyadhole/us-housing-affordability
cd us-housing-affordability
pip install -r requirements.txt
python run_analysis.py
```

---

*Divya Dhole · MS Data Science @ University of Arizona*
*[divyadhole.github.io](https://divyadhole.github.io) · [LinkedIn](https://www.linkedin.com/in/divyadhole/)*
