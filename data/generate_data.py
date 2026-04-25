"""
Script to generate a realistic retail sales dataset.
Run once to create raw_sales_data.csv in this folder.
"""

import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker()
np.random.seed(42)
random.seed(42)

# ── Config ──────────────────────────────────────────────────────────────────
N_ROWS = 5000

REGIONS   = ["North", "South", "East", "West"]
SEGMENTS  = ["Consumer", "Corporate", "Home Office"]

CATEGORIES = {
    "Technology":   ["Laptops", "Monitors", "Printers", "Phones", "Tablets", "Accessories"],
    "Office Supplies": ["Paper", "Binders", "Pens & Pencils", "Storage", "Labels", "Envelopes"],
    "Furniture":    ["Chairs", "Desks", "Bookcases", "Tables", "Shelving"],
}

SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]

# Base price ranges per sub-category
PRICE_MAP = {
    "Laptops": (600, 2000), "Monitors": (150, 900), "Printers": (80, 600),
    "Phones": (200, 1200), "Tablets": (150, 800), "Accessories": (10, 150),
    "Paper": (5, 60), "Binders": (3, 40), "Pens & Pencils": (2, 25),
    "Storage": (10, 80), "Labels": (2, 20), "Envelopes": (3, 30),
    "Chairs": (80, 900), "Desks": (100, 1200), "Bookcases": (60, 500),
    "Tables": (120, 1500), "Shelving": (40, 300),
}

DISCOUNT_MAP = {
    "Technology": 0.08, "Office Supplies": 0.20, "Furniture": 0.15
}

rows = []
start_date = pd.Timestamp("2021-01-01")
end_date   = pd.Timestamp("2023-12-31")

for i in range(N_ROWS):
    category    = random.choice(list(CATEGORIES.keys()))
    sub_cat     = random.choice(CATEGORIES[category])
    low, high   = PRICE_MAP[sub_cat]
    unit_price  = round(random.uniform(low, high), 2)
    quantity    = random.randint(1, 10)
    discount    = round(random.choices(
                      [0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50],
                      weights=[50, 15, 12, 10, 7, 4, 2])[0], 2)

    # introduce realistic noise / messiness
    if random.random() < 0.03:        # 3% nulls in ship mode
        ship_mode = np.nan
    else:
        ship_mode = random.choice(SHIP_MODES)

    if random.random() < 0.02:        # 2% duplicate-ish order IDs
        order_id = f"ORD-{random.randint(1000, 1999):04d}"
    else:
        order_id = f"ORD-{i+10000}"

    revenue = round(unit_price * quantity * (1 - discount), 2)
    cost    = round(unit_price * quantity * random.uniform(0.45, 0.70), 2)
    profit  = round(revenue - cost, 2)

    order_date = start_date + pd.Timedelta(
        days=random.randint(0, (end_date - start_date).days))
    ship_date  = order_date + pd.Timedelta(days=random.randint(1, 7))

    # inject a handful of obvious errors for cleaning demo
    if random.random() < 0.015:
        quantity = -quantity          # negative quantity
    if random.random() < 0.01:
        revenue = np.nan              # missing revenue

    rows.append({
        "order_id":    order_id,
        "order_date":  order_date.strftime("%Y-%m-%d"),
        "ship_date":   ship_date.strftime("%Y-%m-%d"),
        "ship_mode":   ship_mode,
        "customer_id": f"CUST-{random.randint(1000, 3000):04d}",
        "customer_name": fake.name(),
        "segment":     random.choice(SEGMENTS),
        "region":      random.choice(REGIONS),
        "state":       fake.state(),
        "category":    category,
        "sub_category": sub_cat,
        "product_name": f"{fake.company()} {sub_cat}",
        "quantity":    quantity,
        "unit_price":  unit_price,
        "discount":    discount,
        "revenue":     revenue,
        "cost":        cost,
        "profit":      profit,
    })

df = pd.DataFrame(rows)
df.to_csv("raw_sales_data.csv", index=False)
print(f"Generated {len(df)} rows → raw_sales_data.csv")
print(f"Nulls injected: ship_mode={df['ship_mode'].isna().sum()}, revenue={df['revenue'].isna().sum()}")
print(f"Negative quantities: {(df['quantity'] < 0).sum()}")
