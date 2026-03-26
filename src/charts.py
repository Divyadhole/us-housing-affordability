"""
src/charts.py — US Housing Affordability charts
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
from pathlib import Path

OUT = Path("outputs/charts")
OUT.mkdir(parents=True, exist_ok=True)

P = {"red":"#E74C3C","blue":"#2E86AB","amber":"#F39C12","green":"#27AE60",
     "purple":"#8E44AD","teal":"#1ABC9C","neutral":"#7F8C8D","dark":"#2C3E50"}

TIER_COLORS = {
    "Crisis":                "#E74C3C",
    "Severely Unaffordable": "#E67E22",
    "Unaffordable":          "#F39C12",
    "Moderate":              "#3498DB",
    "Affordable":            "#27AE60",
}

BASE = {"figure.facecolor":"white","axes.facecolor":"#FAFAF9",
        "axes.spines.top":False,"axes.spines.right":False,
        "axes.spines.left":False,"axes.grid":True,
        "axes.grid.axis":"y","grid.color":"#ECECEC","grid.linewidth":0.6,
        "font.family":"DejaVu Sans","axes.titlesize":12,
        "axes.titleweight":"bold","axes.labelsize":10,
        "xtick.labelsize":8.5,"ytick.labelsize":9,
        "xtick.bottom":False,"ytick.left":False}

def save(fig, name):
    p = OUT / f"{name}.png"
    fig.savefig(p, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  ✓ {name}.png")


def chart_price_to_income_timeline(df: pd.DataFrame):
    """The core chart — when did housing break?"""
    with plt.rc_context({**BASE, "axes.grid.axis":"both"}):
        fig, ax = plt.subplots(figsize=(13, 6))

        ax.plot(df["year"], df["price_to_income"], "o-",
                color=P["red"], lw=2.8, markersize=6, zorder=4)
        ax.fill_between(df["year"], df["price_to_income"], alpha=0.1, color=P["red"])

        # Eras
        ax.axhspan(0, 3.0, alpha=0.04, color=P["green"])
        ax.axhspan(3.0, 4.0, alpha=0.04, color=P["blue"])
        ax.axhspan(4.0, 12, alpha=0.04, color=P["red"])

        ax.axhline(3.0, color=P["green"], lw=1, linestyle="--", alpha=0.6,
                   label="Affordable threshold (3x)")
        ax.axhline(5.0, color=P["red"], lw=1, linestyle="--", alpha=0.6,
                   label="Severely unaffordable (5x)")

        # Key annotations
        ax.annotate("Housing bubble\npeak 2006",
                    xy=(2006, 5.11), xytext=(2003.5, 5.4),
                    fontsize=8.5, color=P["amber"], fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=P["amber"], lw=1.2))
        ax.annotate("COVID surge\n+35% in 2yr",
                    xy=(2022, 6.10), xytext=(2019, 6.3),
                    fontsize=8.5, color=P["red"], fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=P["red"], lw=1.5))
        ax.scatter([2022], [df[df["year"]==2022]["price_to_income"].values[0]],
                   s=120, color=P["red"], zorder=5, edgecolors="white", lw=1.5)

        ax.set_ylabel("Median Home Price / Median Household Income")
        ax.set_title("US Housing Price-to-Income Ratio 2000-2023\n"
                     "Source: FRED MSPUS + Census ACS B19013_001E")
        ax.legend(fontsize=9)
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.set_xticks(df["year"][::2])
        fig.tight_layout()
        save(fig, "01_price_to_income_timeline")


def chart_payment_burden(df: pd.DataFrame):
    """Monthly mortgage payment as % of income — 2019-2023 shock."""
    with plt.rc_context({**BASE, "axes.grid.axis":"both"}):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

        # Full timeline payment burden
        ax1.bar(df["year"], df["payment_to_income_pct"],
                color=[P["red"] if v > 30 else P["amber"] if v > 25
                       else P["blue"] for v in df["payment_to_income_pct"]],
                alpha=0.88, width=0.7)
        ax1.axhline(28, color=P["amber"], lw=1.5, linestyle="--",
                    label="28% affordability guideline (lenders)")
        ax1.set_ylabel("Monthly Payment as % of Gross Income")
        ax1.set_title("Mortgage Payment Burden 2000-2023")
        ax1.legend(fontsize=9)
        ax1.spines["left"].set_visible(True)
        ax1.tick_params(axis="x", rotation=45)

        # 2019-2023 zoom — the shock in detail
        recent = df[df["year"] >= 2019].copy()
        colors = [P["red"] if v > 30 else P["amber"] for v in recent["payment_to_income_pct"]]
        bars = ax2.bar(recent["year"], recent["payment_to_income_pct"],
                       color=colors, alpha=0.9, width=0.5)
        for bar, v in zip(bars, recent["payment_to_income_pct"]):
            ax2.text(bar.get_x()+bar.get_width()/2, v+0.3,
                     f"{v:.1f}%", ha="center", fontsize=11, fontweight="bold")
        ax2.set_title("2019-2023: The Affordability Collapse\n"
                      "Low rates → price surge → rate hike → payment shock")
        ax2.spines["left"].set_visible(True)

        fig.suptitle("Mortgage Payment Burden as % of Median Household Income\n"
                     "Source: FRED MORTGAGE30US + MSPUS + Census ACS",
                     fontsize=12, fontweight="bold")
        fig.tight_layout()
        save(fig, "02_payment_burden")


def chart_state_affordability(df: pd.DataFrame):
    """State price-to-income ratios — most to least affordable."""
    df_sorted = df.sort_values("price_to_income", ascending=True)
    colors = [TIER_COLORS.get(t, P["neutral"]) for t in df_sorted["afford_tier"]]

    with plt.rc_context({**BASE, "axes.grid.axis":"x"}):
        fig, ax = plt.subplots(figsize=(11, 14))
        bars = ax.barh(df_sorted["state_name"], df_sorted["price_to_income"],
                       color=colors, height=0.7, alpha=0.88)
        ax.axvline(3.0, color=P["green"], lw=1.2, linestyle="--", alpha=0.7,
                   label="Affordable ≤3x")
        ax.axvline(5.0, color=P["red"], lw=1.2, linestyle="--", alpha=0.7,
                   label="Severely unaffordable >5x")
        for bar, v in zip(bars, df_sorted["price_to_income"]):
            ax.text(v+0.05, bar.get_y()+bar.get_height()/2,
                    f"{v:.1f}x", va="center", fontsize=8)
        patches = [mpatches.Patch(color=v, alpha=0.88, label=k)
                   for k, v in TIER_COLORS.items()]
        ax.legend(handles=patches, fontsize=8.5, loc="lower right")
        ax.set_xlabel("Median Home Price ÷ Median Household Income (2022)")
        ax.set_title("Housing Affordability by State — Price-to-Income Ratio 2022\n"
                     "Source: Census ACS B19013_001E + Zillow/HUD")
        fig.tight_layout()
        save(fig, "03_state_affordability")


def chart_rent_burden_map(df: pd.DataFrame):
    """Rent burden by state — who can't afford to rent?"""
    df_sorted = df.sort_values("rent_burden_pct", ascending=True).tail(20)
    colors = [P["red"] if v > 30 else P["amber"] if v > 25 else P["blue"]
              for v in df_sorted["rent_burden_pct"]]

    with plt.rc_context({**BASE, "axes.grid.axis":"x"}):
        fig, ax = plt.subplots(figsize=(11, 7))
        bars = ax.barh(df_sorted["state_name"], df_sorted["rent_burden_pct"],
                       color=colors, height=0.65, alpha=0.88)
        ax.axvline(30, color=P["red"], lw=1.5, linestyle="--",
                   label="HUD cost-burdened threshold (30%)")
        for bar, v in zip(bars, df_sorted["rent_burden_pct"]):
            ax.text(v+0.2, bar.get_y()+bar.get_height()/2,
                    f"{v:.1f}%", va="center", fontsize=9, fontweight="bold")
        ax.legend(fontsize=9)
        ax.set_xlabel("Annual 2BR Rent as % of Median Household Income")
        ax.set_title("Top 20 States by Renter Cost Burden 2022\n"
                     "Source: HUD Fair Market Rents + Census ACS")
        fig.tight_layout()
        save(fig, "04_rent_burden_top20")


def chart_price_vs_income_scatter(df: pd.DataFrame):
    """Home price vs income — who's priced out?"""
    region_colors = {
        "West":"#E74C3C","Northeast":"#3498DB",
        "South":"#F39C12","Midwest":"#27AE60","Other":"#95A5A6",
    }
    with plt.rc_context({**BASE, "axes.grid":False}):
        fig, ax = plt.subplots(figsize=(12, 7))
        for _, row in df.iterrows():
            c = region_colors.get(row["region"], "#95A5A6")
            ax.scatter(row["income"]/1000, row["home_price"]/1000,
                       color=c, s=80, alpha=0.85, zorder=4,
                       edgecolors="white", linewidths=0.7)
            if row["price_to_income"] > 7 or row["home_price"] > 550_000 or \
               row["home_price"] < 170_000:
                ax.annotate(row["state"],
                            (row["income"]/1000, row["home_price"]/1000),
                            fontsize=8, color="#333",
                            xytext=(4, 4), textcoords="offset points")

        # Reference lines
        x_range = np.linspace(df["income"].min()/1000, df["income"].max()/1000, 100)
        for multiple, color, label in [(3, P["green"], "3x income"),
                                       (5, P["amber"], "5x income"),
                                       (8, P["red"],   "8x income (crisis)")]:
            ax.plot(x_range, x_range * multiple,
                    "--", color=color, lw=1.2, alpha=0.7, label=label)

        patches = [mpatches.Patch(color=v, alpha=0.85, label=k)
                   for k, v in region_colors.items() if k != "Other"]
        ax.legend(handles=patches+[
            plt.Line2D([0],[0], color=P["green"],lw=1.2,linestyle="--",label="3x income"),
            plt.Line2D([0],[0], color=P["amber"],lw=1.2,linestyle="--",label="5x income"),
            plt.Line2D([0],[0], color=P["red"],  lw=1.2,linestyle="--",label="8x income"),
        ], fontsize=8.5, ncol=2)

        ax.set_xlabel("Median Household Income ($K)")
        ax.set_ylabel("Median Home Price ($K)")
        ax.set_title("Home Price vs Income by State 2022\n"
                     "Points above red line = crisis-level unaffordability")
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, "05_price_vs_income_scatter")


def chart_affordability_index_trend(df: pd.DataFrame):
    """Affordability index 2000-2023 — 100 = perfectly affordable."""
    with plt.rc_context({**BASE, "axes.grid.axis":"both"}):
        fig, ax = plt.subplots(figsize=(13, 5.5))

        ax.plot(df["year"], df["affordability_index"], "o-",
                color=P["blue"], lw=2.5, markersize=6, zorder=4)
        ax.fill_between(df["year"], df["affordability_index"],
                        alpha=0.1, color=P["blue"])

        ax.axhline(100, color=P["green"], lw=1.5, linestyle="--",
                   alpha=0.7, label="Index = 100 (income = home price)")

        # Highlight the collapse
        ax.axvspan(2020, 2023, alpha=0.08, color=P["red"])
        ax.text(2021.2, df["affordability_index"].max()*0.95,
                "COVID era\naffordability collapse",
                ha="center", fontsize=9, color=P["red"], fontweight="bold")

        current = df[df["year"]==2023]["affordability_index"].values[0]
        ax.scatter([2023], [current], s=120, color=P["red"],
                   zorder=5, edgecolors="white", lw=1.5)
        ax.annotate(f"2023: {current:.0f}",
                    xy=(2023, current), xytext=(2021, current-4),
                    fontsize=9, color=P["red"], fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=P["red"], lw=1.2))

        ax.set_ylabel("Affordability Index (Income / Price × 100)")
        ax.set_title("National Housing Affordability Index 2000-2023\n"
                     "Lower = less affordable. Sources: FRED MSPUS + Census ACS")
        ax.legend(fontsize=9)
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.set_xticks(df["year"][::2])
        fig.tight_layout()
        save(fig, "06_affordability_index")


def run_all(df_nat: pd.DataFrame, df_state: pd.DataFrame):
    print("\nGenerating charts...")
    chart_price_to_income_timeline(df_nat)
    chart_payment_burden(df_nat)
    chart_state_affordability(df_state)
    chart_rent_burden_map(df_state)
    chart_price_vs_income_scatter(df_state)
    chart_affordability_index_trend(df_nat)
    print("  All charts saved to outputs/charts/")
