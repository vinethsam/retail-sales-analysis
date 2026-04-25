"""
Retail Sales Analysis - End-to-End
====================================
Author : Vineth Samarasinghe
Dataset: Synthetic retail orders (2021-2023), 5 000 rows
Goal   : Surface revenue, profit, and customer-segment insights
         to guide quarterly strategy decisions.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0. Imports & paths
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
DATA  = BASE / "data" / "raw_sales_data.csv"
DB    = BASE / "data" / "sales.db"
OUT   = BASE / "outputs"
OUT.mkdir(exist_ok=True)

# ── Shared style ─────────────────────────────────────────────────────────────
PALETTE = ["#2C3E7A", "#E8613C", "#4CAF8C", "#F4A823", "#8E6DB8"]
sns.set_theme(style="whitegrid", font_scale=1.05)
plt.rcParams.update({
    "figure.dpi": 150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titleweight":  "bold",
    "axes.titlesize":    13,
})

def save(fig, name):
    path = OUT / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔  saved → {path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 1. Loading ──────────────────────────────────────────────────────")
raw = pd.read_csv(DATA)
print(f"   Shape : {raw.shape}")
print(f"   Columns: {list(raw.columns)}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA-QUALITY AUDIT
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 2. Data-Quality Audit ───────────────────────────────────────────")

null_counts = raw.isnull().sum()
null_pct    = (null_counts / len(raw) * 100).round(2)
audit = pd.DataFrame({"null_count": null_counts, "null_%": null_pct})
audit = audit[audit["null_count"] > 0]
print(audit.to_string())

neg_qty = (raw["quantity"] < 0).sum()
dup_orders = raw.duplicated(subset=["order_id"]).sum()
print(f"\n   Negative quantities : {neg_qty}")
print(f"   Duplicate order IDs : {dup_orders}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. DATA CLEANING
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 3. Cleaning ─────────────────────────────────────────────────────")
df = raw.copy()

# 3a. Fix dtypes
df["order_date"] = pd.to_datetime(df["order_date"])
df["ship_date"]  = pd.to_datetime(df["ship_date"])

# 3b. Remove negative quantities (data-entry errors)
before = len(df)
df = df[df["quantity"] > 0]
print(f"   Dropped {before - len(df)} rows with negative quantity")

# 3c. Impute missing revenue from unit_price × quantity × (1 - discount)
missing_rev = df["revenue"].isna()
df.loc[missing_rev, "revenue"] = (
    df.loc[missing_rev, "unit_price"]
    * df.loc[missing_rev, "quantity"]
    * (1 - df.loc[missing_rev, "discount"])
).round(2)
print(f"   Imputed {missing_rev.sum()} missing revenue values")

# 3d. Fill missing ship_mode with mode
mode_ship = df["ship_mode"].mode()[0]
df["ship_mode"] = df["ship_mode"].fillna(mode_ship)
print(f"   Filled {raw['ship_mode'].isna().sum()} missing ship_mode → '{mode_ship}'")

# 3e. Derived columns
df["profit_margin"] = (df["profit"] / df["revenue"].replace(0, np.nan)).round(4)
df["days_to_ship"]  = (df["ship_date"] - df["order_date"]).dt.days
df["year"]          = df["order_date"].dt.year
df["month"]         = df["order_date"].dt.to_period("M").astype(str)
df["year_month"]    = df["order_date"].dt.to_period("M").astype(str)

print(f"\n   Clean dataset shape: {df.shape}")
print(f"   Null values remaining: {df.isnull().sum().sum()}")

# Save clean CSV
clean_path = BASE / "data" / "clean_sales_data.csv"
df.to_csv(clean_path, index=False)
print(f"   Saved → clean_sales_data.csv")


# ─────────────────────────────────────────────────────────────────────────────
# 4. LOAD INTO SQLite
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 4. Loading into SQLite ──────────────────────────────────────────")
conn = sqlite3.connect(DB)
df.to_sql("sales", conn, if_exists="replace", index=False)
print(f"   Written {len(df)} rows → sales.db / table: sales")


# ─────────────────────────────────────────────────────────────────────────────
# 5. SQL ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 5. SQL Queries ──────────────────────────────────────────────────")

def run(label, sql):
    result = pd.read_sql_query(sql, conn)
    print(f"\n  [{label}]")
    print(result.to_string(index=False))
    return result


# Q1 — Revenue & profit by category
q1 = run("Q1 · Revenue & Profit by Category", """
    SELECT
        category,
        COUNT(*)                          AS orders,
        ROUND(SUM(revenue), 2)            AS total_revenue,
        ROUND(SUM(profit),  2)            AS total_profit,
        ROUND(AVG(profit_margin)*100, 1)  AS avg_margin_pct
    FROM sales
    GROUP BY category
    ORDER BY total_revenue DESC;
""")

# Q2 — Monthly revenue trend
q2 = run("Q2 · Monthly Revenue Trend", """
    SELECT
        month,
        ROUND(SUM(revenue), 2)  AS monthly_revenue,
        ROUND(SUM(profit),  2)  AS monthly_profit
    FROM sales
    GROUP BY month
    ORDER BY month;
""")

# Q3 — Top 10 sub-categories by profit
q3 = run("Q3 · Top 10 Sub-Categories by Profit", """
    SELECT
        sub_category,
        category,
        ROUND(SUM(profit), 2)            AS total_profit,
        ROUND(AVG(profit_margin)*100, 1) AS avg_margin_pct
    FROM sales
    GROUP BY sub_category, category
    ORDER BY total_profit DESC
    LIMIT 10;
""")

# Q4 — Performance by region & segment
q4 = run("Q4 · Revenue by Region and Customer Segment", """
    SELECT
        region,
        segment,
        ROUND(SUM(revenue), 2)  AS total_revenue,
        ROUND(SUM(profit),  2)  AS total_profit,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM sales
    GROUP BY region, segment
    ORDER BY region, total_revenue DESC;
""")

# Q5 — Discount impact on profit margin
q5 = run("Q5 · Discount Bands vs Average Margin", """
    SELECT
        CASE
            WHEN discount = 0          THEN '0%'
            WHEN discount <= 0.10      THEN '1–10%'
            WHEN discount <= 0.20      THEN '11–20%'
            WHEN discount <= 0.30      THEN '21–30%'
            ELSE '31%+'
        END                                    AS discount_band,
        COUNT(*)                               AS num_orders,
        ROUND(AVG(profit_margin)*100, 1)       AS avg_margin_pct,
        ROUND(SUM(revenue), 2)                 AS total_revenue
    FROM sales
    GROUP BY discount_band
    ORDER BY avg_margin_pct DESC;
""")

# Q6 — Shipping mode breakdown
q6 = run("Q6 · Ship Mode: Volume, Speed & Profit", """
    SELECT
        ship_mode,
        COUNT(*)                      AS orders,
        ROUND(AVG(days_to_ship), 1)   AS avg_days_to_ship,
        ROUND(SUM(profit), 2)         AS total_profit,
        ROUND(AVG(profit_margin)*100,1) AS avg_margin_pct
    FROM sales
    GROUP BY ship_mode
    ORDER BY orders DESC;
""")

# Q7 — YoY revenue growth
q7 = run("Q7 · Year-over-Year Revenue Growth", """
    WITH yearly AS (
        SELECT
            year,
            ROUND(SUM(revenue), 2) AS total_revenue,
            ROUND(SUM(profit),  2) AS total_profit
        FROM sales
        GROUP BY year
    )
    SELECT
        year,
        total_revenue,
        total_profit,
        ROUND(
            (total_revenue - LAG(total_revenue) OVER (ORDER BY year))
            / LAG(total_revenue) OVER (ORDER BY year) * 100, 1
        ) AS yoy_growth_pct
    FROM yearly
    ORDER BY year;
""")

conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# 6. VISUALISATIONS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── 6. Visualisations ───────────────────────────────────────────────")

# ── Fig 1: Revenue & Profit by Category ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(q1))
w = 0.38
bars_r = ax.bar(x - w/2, q1["total_revenue"]/1e6, w, label="Revenue", color=PALETTE[0])
bars_p = ax.bar(x + w/2, q1["total_profit"]/1e6,  w, label="Profit",  color=PALETTE[1])
ax.set_xticks(x); ax.set_xticklabels(q1["category"])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.1f}M"))
ax.set_title("Revenue & Profit by Category")
ax.set_ylabel("USD (millions)")
ax.legend()
for b in [*bars_r, *bars_p]:
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.005,
            f"${b.get_height():.2f}M", ha="center", va="bottom", fontsize=8)
save(fig, "fig1_category_revenue_profit.png")

# ── Fig 2: Monthly Revenue Trend ────────────────────────────────────────────
q2["month_dt"] = pd.to_datetime(q2["month"])
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.fill_between(q2["month_dt"], q2["monthly_revenue"]/1e3,
                alpha=0.18, color=PALETTE[0])
ax.plot(q2["month_dt"], q2["monthly_revenue"]/1e3,
        color=PALETTE[0], linewidth=2.2, label="Revenue")
ax.plot(q2["month_dt"], q2["monthly_profit"]/1e3,
        color=PALETTE[1], linewidth=2.0, linestyle="--", label="Profit")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}K"))
ax.set_title("Monthly Revenue & Profit Trend (2021–2023)")
ax.set_xlabel("Month")
ax.legend()
save(fig, "fig2_monthly_trend.png")

# ── Fig 3: Top 10 Sub-Categories by Profit ──────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = [PALETTE[0] if c == "Technology" else PALETTE[2] if c == "Furniture"
          else PALETTE[3] for c in q3["category"]]
bars = ax.barh(q3["sub_category"][::-1], q3["total_profit"][::-1]/1e3, color=colors[::-1])
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}K"))
ax.set_title("Top 10 Sub-Categories by Total Profit")
ax.set_xlabel("Total Profit (USD thousands)")
for b in bars:
    ax.text(b.get_width() + 0.3, b.get_y() + b.get_height()/2,
            f"${b.get_width():.1f}K", va="center", fontsize=8.5)
save(fig, "fig3_top_subcategories.png")

# ── Fig 4: Region × Segment Heatmap ─────────────────────────────────────────
pivot = q4.pivot_table(index="region", columns="segment",
                       values="total_revenue", aggfunc="sum")
fig, ax = plt.subplots(figsize=(7, 4))
sns.heatmap(pivot/1e3, annot=True, fmt=".1f", cmap="Blues",
            linewidths=0.5, ax=ax,
            annot_kws={"size": 10},
            cbar_kws={"label": "Revenue ($K)"})
ax.set_title("Revenue by Region & Customer Segment ($K)")
ax.set_xlabel("Segment"); ax.set_ylabel("Region")
save(fig, "fig4_region_segment_heatmap.png")

# ── Fig 5: Discount Band vs Margin ──────────────────────────────────────────
order = ["0%", "1–10%", "11–20%", "21–30%", "31%+"]
q5_s = q5.set_index("discount_band").reindex(order).reset_index()
fig, ax1 = plt.subplots(figsize=(8, 4.5))
ax2 = ax1.twinx()
bars = ax1.bar(q5_s["discount_band"], q5_s["total_revenue"]/1e3,
               color=PALETTE[0], alpha=0.7, label="Revenue ($K)")
ax2.plot(q5_s["discount_band"], q5_s["avg_margin_pct"],
         color=PALETTE[1], linewidth=2.5, marker="o", label="Avg Margin %")
ax1.set_title("Discount Depth vs Revenue & Profit Margin")
ax1.set_xlabel("Discount Band")
ax1.set_ylabel("Revenue ($K)", color=PALETTE[0])
ax2.set_ylabel("Avg Profit Margin %", color=PALETTE[1])
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}K"))
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
save(fig, "fig5_discount_impact.png")

# ── Fig 6: YoY Growth ───────────────────────────────────────────────────────
q7_clean = q7.dropna(subset=["yoy_growth_pct"])
fig, ax = plt.subplots(figsize=(6, 4))
bar_colors = [PALETTE[2] if v >= 0 else PALETTE[1]
              for v in q7_clean["yoy_growth_pct"]]
ax.bar(q7_clean["year"].astype(str), q7_clean["yoy_growth_pct"],
       color=bar_colors, width=0.45)
ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
ax.set_title("Year-over-Year Revenue Growth (%)")
ax.set_ylabel("Growth %")
for i, v in enumerate(q7_clean["yoy_growth_pct"]):
    ax.text(i, v + 0.3, f"{v:+.1f}%", ha="center", fontsize=11, fontweight="bold")
save(fig, "fig6_yoy_growth.png")

print("\n── All done! ──────────────────────────────────────────────────────")
print(f"   Output files → {OUT}")
