-- ============================================================
-- Retail Sales Analysis — SQL Queries
-- Database : sales.db  (SQLite)
-- Table    : sales
-- Author   : Vineth Samarasinghe
-- ============================================================


-- ──────────────────────────────────────────────────────────────
-- Q1 · Revenue & Profit by Category
--     Which product category drives the most revenue and profit?
-- ──────────────────────────────────────────────────────────────
SELECT
    category,
    COUNT(*)                          AS orders,
    ROUND(SUM(revenue), 2)            AS total_revenue,
    ROUND(SUM(profit),  2)            AS total_profit,
    ROUND(AVG(profit_margin)*100, 1)  AS avg_margin_pct
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────────
-- Q2 · Monthly Revenue Trend
--     How does revenue fluctuate month-to-month?
-- ──────────────────────────────────────────────────────────────
SELECT
    month,
    ROUND(SUM(revenue), 2)  AS monthly_revenue,
    ROUND(SUM(profit),  2)  AS monthly_profit
FROM sales
GROUP BY month
ORDER BY month;


-- ──────────────────────────────────────────────────────────────
-- Q3 · Top 10 Sub-Categories by Profit
--     Which specific product lines are most profitable?
-- ──────────────────────────────────────────────────────────────
SELECT
    sub_category,
    category,
    ROUND(SUM(profit), 2)            AS total_profit,
    ROUND(AVG(profit_margin)*100, 1) AS avg_margin_pct
FROM sales
GROUP BY sub_category, category
ORDER BY total_profit DESC
LIMIT 10;


-- ──────────────────────────────────────────────────────────────
-- Q4 · Revenue by Region and Customer Segment
--     Which region + segment combinations generate the most value?
-- ──────────────────────────────────────────────────────────────
SELECT
    region,
    segment,
    ROUND(SUM(revenue), 2)       AS total_revenue,
    ROUND(SUM(profit),  2)       AS total_profit,
    COUNT(DISTINCT customer_id)  AS unique_customers
FROM sales
GROUP BY region, segment
ORDER BY region, total_revenue DESC;


-- ──────────────────────────────────────────────────────────────
-- Q5 · Discount Depth vs Profit Margin
--     Are heavy discounts destroying margin?
-- ──────────────────────────────────────────────────────────────
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


-- ──────────────────────────────────────────────────────────────
-- Q6 · Ship Mode: Volume, Speed & Profitability
--     Does faster shipping affect profitability?
-- ──────────────────────────────────────────────────────────────
SELECT
    ship_mode,
    COUNT(*)                        AS orders,
    ROUND(AVG(days_to_ship), 1)     AS avg_days_to_ship,
    ROUND(SUM(profit), 2)           AS total_profit,
    ROUND(AVG(profit_margin)*100,1) AS avg_margin_pct
FROM sales
GROUP BY ship_mode
ORDER BY orders DESC;


-- ──────────────────────────────────────────────────────────────
-- Q7 · Year-over-Year Revenue Growth
--     Is the business growing year on year?
-- ──────────────────────────────────────────────────────────────
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
