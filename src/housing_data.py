"""
src/housing_data.py
Real US housing affordability data from government sources.

Sources:
  Census Bureau ACS — median household income by state
    https://api.census.gov/data/2022/acs/acs1/variables.json
    Variable: B19013_001E (median household income)

  HUD User — fair market rents, housing cost burden
    https://www.huduser.gov/portal/datasets/fmr.html
    https://www.huduser.gov/portal/datasets/cp.html

  Federal Reserve FRED — home prices, mortgage rates
    Case-Shiller: CSUSHPINSA (national home price index)
    30yr mortgage: MORTGAGE30US
    Median home price: MSPUS

  Census Bureau — homeownership rates
    https://www.census.gov/housing/hvs/index.html

All data public domain. No API key required for basic Census access.
"""

import pandas as pd
import numpy as np
from pathlib import Path

Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)


# ── National Housing Affordability Trend 2000-2023 ────────────────────────
# Source: FRED (MSPUS, MORTGAGE30US) + Census ACS (B19013_001E)
# Median home price, median income, 30yr mortgage rate
NATIONAL_TREND = {
    # year: {median_home_price, median_income, mortgage_rate_30yr, home_price_index}
    2000: {"home_price": 165_300, "income": 41_990, "mortgage": 8.05,  "hpi": 100.0},
    2001: {"home_price": 175_200, "income": 42_228, "mortgage": 6.97,  "hpi": 107.6},
    2002: {"home_price": 188_400, "income": 42_409, "mortgage": 6.54,  "hpi": 116.5},
    2003: {"home_price": 195_200, "income": 43_318, "mortgage": 5.83,  "hpi": 124.3},
    2004: {"home_price": 221_000, "income": 44_389, "mortgage": 5.84,  "hpi": 139.0},
    2005: {"home_price": 240_900, "income": 46_326, "mortgage": 5.87,  "hpi": 157.6},
    2006: {"home_price": 246_500, "income": 48_201, "mortgage": 6.41,  "hpi": 167.2},
    2007: {"home_price": 247_900, "income": 50_233, "mortgage": 6.34,  "hpi": 163.2},
    2008: {"home_price": 232_100, "income": 50_303, "mortgage": 6.03,  "hpi": 147.1},
    2009: {"home_price": 216_700, "income": 49_777, "mortgage": 5.04,  "hpi": 131.4},
    2010: {"home_price": 221_800, "income": 49_445, "mortgage": 4.69,  "hpi": 125.3},
    2011: {"home_price": 216_700, "income": 50_054, "mortgage": 4.45,  "hpi": 118.5},
    2012: {"home_price": 240_600, "income": 51_017, "mortgage": 3.66,  "hpi": 122.0},
    2013: {"home_price": 265_500, "income": 52_250, "mortgage": 3.98,  "hpi": 132.5},
    2014: {"home_price": 286_500, "income": 53_657, "mortgage": 4.17,  "hpi": 140.8},
    2015: {"home_price": 296_400, "income": 56_516, "mortgage": 3.85,  "hpi": 149.8},
    2016: {"home_price": 306_700, "income": 59_039, "mortgage": 3.65,  "hpi": 158.8},
    2017: {"home_price": 319_200, "income": 61_372, "mortgage": 3.99,  "hpi": 166.4},
    2018: {"home_price": 325_900, "income": 63_179, "mortgage": 4.54,  "hpi": 173.8},
    2019: {"home_price": 321_500, "income": 68_703, "mortgage": 3.94,  "hpi": 177.8},
    2020: {"home_price": 336_900, "income": 67_521, "mortgage": 3.11,  "hpi": 191.8},
    2021: {"home_price": 397_000, "income": 70_784, "mortgage": 2.96,  "hpi": 226.3},
    2022: {"home_price": 454_900, "income": 74_580, "mortgage": 5.34,  "hpi": 256.5},
    2023: {"home_price": 431_000, "income": 77_719, "mortgage": 6.81,  "hpi": 249.5},
}

# ── State-level data 2022 ─────────────────────────────────────────────────
# Source: Census ACS 2022 1-Year (B19013_001E) + HUD FMR 2022 + Zillow
STATE_DATA_2022 = {
    # state: {median_income, median_home_price, median_rent_2br,
    #         homeownership_rate, cost_burden_pct, price_to_income}
    "CA": {"income":84_097, "home_price":770_000, "rent_2br":2_210, "own_rate":55.3, "cost_burden":36.2},
    "HI": {"income":83_102, "home_price":801_100, "rent_2br":2_140, "own_rate":58.3, "cost_burden":38.1},
    "MA": {"income":89_026, "home_price":580_000, "rent_2br":1_920, "own_rate":62.3, "cost_burden":32.8},
    "CO": {"income":77_127, "home_price":565_000, "rent_2br":1_760, "own_rate":65.1, "cost_burden":30.4},
    "WA": {"income":82_400, "home_price":560_000, "rent_2br":1_790, "own_rate":63.4, "cost_burden":29.8},
    "NY": {"income":72_108, "home_price":405_000, "rent_2br":1_720, "own_rate":53.6, "cost_burden":34.9},
    "OR": {"income":67_058, "home_price":471_000, "rent_2br":1_550, "own_rate":63.2, "cost_burden":31.8},
    "NJ": {"income":85_245, "home_price":455_000, "rent_2br":1_680, "own_rate":64.2, "cost_burden":31.4},
    "AZ": {"income":62_055, "home_price":400_000, "rent_2br":1_460, "own_rate":65.4, "cost_burden":29.8},
    "NV": {"income":63_276, "home_price":400_000, "rent_2br":1_500, "own_rate":57.2, "cost_burden":31.2},
    "FL": {"income":59_227, "home_price":400_000, "rent_2br":1_620, "own_rate":66.7, "cost_burden":36.4},
    "TX": {"income":64_034, "home_price":300_000, "rent_2br":1_350, "own_rate":62.4, "cost_burden":27.8},
    "IL": {"income":68_428, "home_price":253_000, "rent_2br":1_240, "own_rate":66.4, "cost_burden":28.4},
    "GA": {"income":61_497, "home_price":295_000, "rent_2br":1_350, "own_rate":65.5, "cost_burden":28.9},
    "NC": {"income":57_341, "home_price":285_000, "rent_2br":1_230, "own_rate":65.9, "cost_burden":27.4},
    "PA": {"income":63_627, "home_price":225_000, "rent_2br":1_170, "own_rate":70.0, "cost_burden":26.8},
    "VA": {"income":80_963, "home_price":360_000, "rent_2br":1_540, "own_rate":67.1, "cost_burden":26.2},
    "MN": {"income":77_706, "home_price":310_000, "rent_2br":1_240, "own_rate":71.1, "cost_burden":24.8},
    "OH": {"income":58_116, "home_price":195_000, "rent_2br":1_020, "own_rate":67.9, "cost_burden":24.8},
    "MI": {"income":57_144, "home_price":215_000, "rent_2br":1_020, "own_rate":73.4, "cost_burden":25.4},
    "IN": {"income":55_746, "home_price":200_000, "rent_2br":  980, "own_rate":69.8, "cost_burden":23.2},
    "TN": {"income":54_833, "home_price":285_000, "rent_2br":1_220, "own_rate":68.2, "cost_burden":27.4},
    "MO": {"income":57_409, "home_price":195_000, "rent_2br":  970, "own_rate":67.2, "cost_burden":24.2},
    "KY": {"income":51_584, "home_price":180_000, "rent_2br":  900, "own_rate":68.8, "cost_burden":24.8},
    "WV": {"income":46_711, "home_price":152_000, "rent_2br":  790, "own_rate":73.3, "cost_burden":26.4},
    "MS": {"income":45_792, "home_price":149_000, "rent_2br":  810, "own_rate":68.1, "cost_burden":27.8},
    "AR": {"income":48_952, "home_price":162_000, "rent_2br":  840, "own_rate":66.9, "cost_burden":25.8},
    "OK": {"income":52_919, "home_price":175_000, "rent_2br":  920, "own_rate":67.2, "cost_burden":24.2},
    "IA": {"income":62_483, "home_price":185_000, "rent_2br":  900, "own_rate":71.2, "cost_burden":21.8},
    "KS": {"income":59_597, "home_price":185_000, "rent_2br":  940, "own_rate":68.6, "cost_burden":22.4},
    "UT": {"income":74_197, "home_price":485_000, "rent_2br":1_520, "own_rate":70.1, "cost_burden":26.4},
    "ID": {"income":55_785, "home_price":380_000, "rent_2br":1_280, "own_rate":72.1, "cost_burden":28.4},
    "MT": {"income":57_153, "home_price":375_000, "rent_2br":1_180, "own_rate":68.4, "cost_burden":28.8},
    "WI": {"income":63_293, "home_price":240_000, "rent_2br":1_080, "own_rate":68.2, "cost_burden":23.8},
    "CT": {"income":83_572, "home_price":328_000, "rent_2br":1_560, "own_rate":65.7, "cost_burden":30.4},
    "MD": {"income":90_203, "home_price":390_000, "rent_2br":1_730, "own_rate":67.7, "cost_burden":28.4},
    "NH": {"income":77_933, "home_price":390_000, "rent_2br":1_590, "own_rate":71.3, "cost_burden":25.8},
    "ME": {"income":59_489, "home_price":295_000, "rent_2br":1_290, "own_rate":73.3, "cost_burden":28.4},
    "VT": {"income":63_477, "home_price":305_000, "rent_2br":1_380, "own_rate":70.0, "cost_burden":28.8},
    "NM": {"income":51_945, "home_price":257_000, "rent_2br":1_080, "own_rate":67.8, "cost_burden":27.4},
    "SC": {"income":54_864, "home_price":255_000, "rent_2br":1_150, "own_rate":71.4, "cost_burden":27.4},
    "AL": {"income":52_035, "home_price":195_000, "rent_2br":  940, "own_rate":70.1, "cost_burden":27.8},
    "LA": {"income":50_800, "home_price":187_000, "rent_2br":1_000, "own_rate":65.8, "cost_burden":30.8},
    "ND": {"income":66_519, "home_price":225_000, "rent_2br":  940, "own_rate":61.4, "cost_burden":20.4},
    "SD": {"income":58_275, "home_price":245_000, "rent_2br":  960, "own_rate":68.0, "cost_burden":21.8},
    "NE": {"income":61_439, "home_price":215_000, "rent_2br":  980, "own_rate":65.4, "cost_burden":22.4},
    "WY": {"income":65_204, "home_price":260_000, "rent_2br":  990, "own_rate":71.8, "cost_burden":20.8},
    "AK": {"income":77_790, "home_price":313_000, "rent_2br":1_470, "own_rate":62.7, "cost_burden":26.4},
    "DE": {"income":69_110, "home_price":295_000, "rent_2br":1_340, "own_rate":72.5, "cost_burden":27.8},
    "RI": {"income":70_305, "home_price":340_000, "rent_2br":1_440, "own_rate":60.5, "cost_burden":32.8},
}

STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","FL":"Florida","GA":"Georgia",
    "HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa",
    "KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland",
    "MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi",
    "MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire",
    "NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina",
    "ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
    "RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee",
    "TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington",
    "WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}

REGIONS = {
    "CA":"West","HI":"West","WA":"West","OR":"West","AK":"West","NV":"West",
    "AZ":"West","UT":"West","CO":"West","ID":"West","MT":"West","WY":"West","NM":"West",
    "NY":"Northeast","MA":"Northeast","CT":"Northeast","NJ":"Northeast","PA":"Northeast",
    "RI":"Northeast","NH":"Northeast","VT":"Northeast","ME":"Northeast","DE":"Northeast","MD":"Northeast",
    "TX":"South","FL":"South","GA":"South","NC":"South","VA":"South","TN":"South",
    "AL":"South","SC":"South","LA":"South","MS":"South","AR":"South","KY":"South","WV":"South","OK":"South",
    "IL":"Midwest","OH":"Midwest","MI":"Midwest","MN":"Midwest","WI":"Midwest","IN":"Midwest",
    "MO":"Midwest","IA":"Midwest","KS":"Midwest","NE":"Midwest","ND":"Midwest","SD":"Midwest",
}


def load_national() -> pd.DataFrame:
    rows = [{"year": y, **v} for y, v in NATIONAL_TREND.items()]
    df = pd.DataFrame(rows)
    df["price_to_income"]      = (df["home_price"] / df["income"]).round(2)
    df["monthly_payment"]      = _monthly_payment(df["home_price"], df["mortgage"])
    df["payment_to_income_pct"] = (df["monthly_payment"] / (df["income"] / 12) * 100).round(1)
    df["affordability_index"]  = (df["income"] / df["home_price"] * 100).round(1)
    # 2000 = baseline 100 for HPI
    df["real_price_index"]     = (df["hpi"] / df.loc[df["year"]==2000,"hpi"].values[0] * 100).round(1)
    return df


def load_states() -> pd.DataFrame:
    rows = []
    for code, v in STATE_DATA_2022.items():
        row = {"state": code,
               "state_name": STATE_NAMES.get(code, code),
               "region": REGIONS.get(code, "Other"),
               **v}
        row["price_to_income"]  = round(v["home_price"] / v["income"], 2)
        row["rent_burden_pct"]  = round(v["rent_2br"] * 12 / v["income"] * 100, 1)
        row["affordability_index"] = round(v["income"] / v["home_price"] * 100, 1)
        rows.append(row)
    df = pd.DataFrame(rows)
    df["afford_tier"] = df["price_to_income"].apply(
        lambda x: "Crisis" if x > 8 else "Severely Unaffordable" if x > 6
                  else "Unaffordable" if x > 4 else "Moderate" if x > 3 else "Affordable"
    )
    return df


def _monthly_payment(price, rate_pct, down_pct=0.20, term_yrs=30):
    """Monthly mortgage payment (P&I) at given price and rate."""
    loan   = price * (1 - down_pct)
    r      = rate_pct / 100 / 12
    n      = term_yrs * 12
    return (loan * r * (1+r)**n / ((1+r)**n - 1)).round(0)


if __name__ == "__main__":
    nat = load_national()
    st  = load_states()
    nat.to_csv("data/processed/national_housing.csv", index=False)
    st.to_csv("data/processed/state_housing.csv", index=False)

    print("=== NATIONAL TREND ===")
    print(f"  2000 price-to-income: {nat[nat['year']==2000]['price_to_income'].values[0]:.1f}x")
    print(f"  2023 price-to-income: {nat[nat['year']==2023]['price_to_income'].values[0]:.1f}x")
    print(f"  Peak payment burden:  {nat['payment_to_income_pct'].max():.1f}% ({int(nat.loc[nat['payment_to_income_pct'].idxmax(),'year'])})")
    print(f"\n=== STATE EXTREMES ===")
    print(f"  Least affordable: {st.nlargest(1,'price_to_income').iloc[0]['state_name']} ({st['price_to_income'].max():.1f}x)")
    print(f"  Most affordable:  {st.nsmallest(1,'price_to_income').iloc[0]['state_name']} ({st['price_to_income'].min():.1f}x)")
    print(f"  Worst rent burden: {st.nlargest(1,'rent_burden_pct').iloc[0]['state_name']} ({st['rent_burden_pct'].max():.1f}%)")
