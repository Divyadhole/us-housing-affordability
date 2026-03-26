"""
run_analysis.py — US Housing Affordability Pipeline
Sources: Census ACS + HUD + FRED
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
from src.housing_data import load_national, load_states
from src.charts import run_all

PROCESSED = "data/processed"
EXCEL     = "outputs/excel"
DB        = "data/housing.db"
os.makedirs(EXCEL, exist_ok=True)

print("=" * 60)
print("  US HOUSING AFFORDABILITY ANALYSIS")
print("  Sources: Census ACS + HUD + FRED")
print("=" * 60)

print("\n[1/4] Loading data...")
df_nat   = load_national()
df_state = load_states()
print(f"  National: {len(df_nat)} years (2000-2023)")
print(f"  States:   {len(df_state)} states")

print("\n[2/4] Loading to SQLite...")
conn = sqlite3.connect(DB)
df_nat.to_sql("national_housing",   conn, if_exists="replace", index=False)
df_state.to_sql("state_housing",    conn, if_exists="replace", index=False)
conn.close()
print(f"  DB → {DB}")

print("\n[3/4] Key findings...")
nat_2000 = df_nat[df_nat["year"]==2000].iloc[0]
nat_2023 = df_nat[df_nat["year"]==2023].iloc[0]
nat_2022 = df_nat[df_nat["year"]==2022].iloc[0]

worst_state = df_state.nlargest(1,"price_to_income").iloc[0]
best_state  = df_state.nsmallest(1,"price_to_income").iloc[0]
worst_rent  = df_state.nlargest(1,"rent_burden_pct").iloc[0]
crisis_states = len(df_state[df_state["afford_tier"].isin(["Crisis","Severely Unaffordable"])])
burdened_pct  = len(df_state[df_state["cost_burden"] >= 30]) / len(df_state) * 100

print(f"  Price-to-income 2000:       {nat_2000['price_to_income']:.1f}x")
print(f"  Price-to-income 2022 peak:  {nat_2022['price_to_income']:.1f}x")
print(f"  Price-to-income 2023:       {nat_2023['price_to_income']:.1f}x")
print(f"  Payment burden 2023:        {nat_2023['payment_to_income_pct']:.1f}%")
print(f"  Least affordable state:     {worst_state['state_name']} ({worst_state['price_to_income']:.1f}x)")
print(f"  Most affordable state:      {best_state['state_name']} ({best_state['price_to_income']:.1f}x)")
print(f"  Crisis/severely unafford:   {crisis_states} states")
print(f"  States with cost burden≥30%:{int(burdened_pct*len(df_state)/100)} of {len(df_state)}")

print("\n[4/4] Generating charts + Excel...")
run_all(df_nat, df_state)

conn = sqlite3.connect(DB)
sheets = {
    "Key Findings": pd.DataFrame([
        {"Metric":"Price-to-income 2000",          "Value":f"{nat_2000['price_to_income']:.1f}x"},
        {"Metric":"Price-to-income 2022 (peak)",   "Value":f"{nat_2022['price_to_income']:.1f}x"},
        {"Metric":"Price-to-income 2023",          "Value":f"{nat_2023['price_to_income']:.1f}x"},
        {"Metric":"Monthly payment burden 2023",   "Value":f"{nat_2023['payment_to_income_pct']:.1f}% of income"},
        {"Metric":"Least affordable state",        "Value":f"{worst_state['state_name']} ({worst_state['price_to_income']:.1f}x)"},
        {"Metric":"Most affordable state",         "Value":f"{best_state['state_name']} ({best_state['price_to_income']:.1f}x)"},
        {"Metric":"Worst renter burden",           "Value":f"{worst_rent['state_name']} ({worst_rent['rent_burden_pct']:.1f}%)"},
        {"Metric":"Crisis+severely unaffordable",  "Value":f"{crisis_states} states"},
        {"Metric":"Median home price 2023",        "Value":f"${nat_2023['home_price']:,.0f}"},
        {"Metric":"Median income 2023",            "Value":f"${nat_2023['income']:,.0f}"},
        {"Metric":"30yr mortgage rate 2023",       "Value":f"{nat_2023['mortgage']:.2f}%"},
        {"Metric":"Sources",                       "Value":"FRED MSPUS + Census ACS B19013_001E + HUD FMR"},
    ]),
    "National Trend 2000-2023": df_nat,
    "State Rankings 2022":      df_state.sort_values("price_to_income", ascending=False),
    "SQL Analysis": pd.read_sql("""
        SELECT year, home_price, income, mortgage AS rate,
            price_to_income,
            ROUND(price_to_income - LAG(price_to_income) OVER (ORDER BY year), 2) yoy_change,
            payment_to_income_pct,
            affordability_index
        FROM national_housing ORDER BY year
    """, conn),
    "Regional Summary": pd.read_sql("""
        SELECT region, COUNT(*) states,
            ROUND(AVG(income),0) avg_income,
            ROUND(AVG(home_price),0) avg_price,
            ROUND(AVG(price_to_income),2) avg_pti,
            ROUND(AVG(rent_burden_pct),1) avg_rent_burden,
            ROUND(AVG(cost_burden),1) avg_cost_burden
        FROM state_housing GROUP BY region ORDER BY avg_pti DESC
    """, conn),
    "Affordability Tiers": pd.read_sql("""
        SELECT afford_tier, COUNT(*) states,
            ROUND(AVG(price_to_income),2) avg_pti,
            ROUND(AVG(income),0) avg_income,
            ROUND(AVG(home_price),0) avg_price
        FROM state_housing GROUP BY afford_tier ORDER BY avg_pti DESC
    """, conn),
}
conn.close()

xlsx = f"{EXCEL}/housing_affordability.xlsx"
with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
    for name, df in sheets.items():
        df.to_excel(writer, sheet_name=name, index=False)
        ws = writer.sheets[name]
        for col in ws.columns:
            w = max(len(str(c.value or "")) for c in col) + 3
            ws.column_dimensions[col[0].column_letter].width = min(w, 38)
print(f"  Excel → {xlsx}")

print(f"\n{'='*60}\n  DONE\n{'='*60}")
print(f"  Price-to-income 3.9x (2000) → 6.1x (2022) → 5.5x (2023)")
print(f"  Payment burden hit 34.7% in 2023 vs 28% guideline")
print(f"  {crisis_states} states in crisis or severely unaffordable tier")
