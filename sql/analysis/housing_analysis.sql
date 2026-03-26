-- ============================================================
-- sql/analysis/housing_analysis.sql
-- US Housing Affordability Analysis
-- Sources: Census ACS + HUD + FRED
-- ============================================================

-- 1. When did housing break? Year-over-year price-to-income ratio
SELECT year, home_price, income, mortgage,
    price_to_income,
    ROUND(price_to_income - LAG(price_to_income) OVER (ORDER BY year), 2) yoy_change,
    payment_to_income_pct,
    CASE WHEN price_to_income > 5.0 THEN 'Unaffordable'
         WHEN price_to_income > 4.0 THEN 'Strained'
         WHEN price_to_income > 3.0 THEN 'Moderate'
         ELSE 'Affordable' END AS affordability_era
FROM national_housing
ORDER BY year;


-- 2. State affordability tiers 2022
SELECT state, state_name, region,
    income, home_price, price_to_income,
    rent_burden_pct, cost_burden,
    afford_tier,
    RANK() OVER (ORDER BY price_to_income DESC) AS least_affordable_rank,
    RANK() OVER (ORDER BY price_to_income ASC)  AS most_affordable_rank
FROM state_housing
ORDER BY price_to_income DESC;


-- 3. Regional affordability comparison
SELECT region,
    COUNT(*) states,
    ROUND(AVG(income), 0)            avg_income,
    ROUND(AVG(home_price), 0)        avg_home_price,
    ROUND(AVG(price_to_income), 2)   avg_price_to_income,
    ROUND(AVG(rent_burden_pct), 1)   avg_rent_burden_pct,
    ROUND(AVG(cost_burden), 1)       avg_cost_burden_pct,
    ROUND(AVG(homeownership_rate), 1) avg_own_rate
FROM state_housing
GROUP BY region
ORDER BY avg_price_to_income DESC;


-- 4. Mortgage rate impact on monthly payment
-- Same $400K house at different rates — the affordability shock
SELECT year, home_price, mortgage AS rate_pct,
    monthly_payment,
    payment_to_income_pct,
    ROUND(monthly_payment - LAG(monthly_payment) OVER (ORDER BY year), 0)
        AS payment_yoy_change
FROM national_housing
WHERE year >= 2019
ORDER BY year;


-- 5. Worst states for renters — rent burden > 30%
-- 30% is the HUD definition of "cost burdened"
SELECT state_name, region,
    income, rent_2br,
    rent_burden_pct,
    cost_burden,
    homeownership_rate,
    CASE WHEN rent_burden_pct > 30 THEN 'Cost Burdened'
         WHEN rent_burden_pct > 25 THEN 'Approaching Burden'
         ELSE 'Manageable' END AS renter_status
FROM state_housing
WHERE rent_burden_pct > 25
ORDER BY rent_burden_pct DESC;


-- 6. Price-to-income by affordability tier count
SELECT afford_tier,
    COUNT(*) states,
    ROUND(AVG(price_to_income), 2) avg_ratio,
    ROUND(AVG(income), 0) avg_income,
    ROUND(AVG(home_price), 0) avg_price,
    ROUND(AVG(homeownership_rate), 1) avg_own_rate
FROM state_housing
GROUP BY afford_tier
ORDER BY avg_ratio DESC;


-- 7. Rolling 5-year average home price (smoothed trend)
SELECT year, home_price, income,
    ROUND(AVG(home_price) OVER (ORDER BY year ROWS 4 PRECEDING), 0) rolling_5yr_price,
    ROUND(AVG(income)     OVER (ORDER BY year ROWS 4 PRECEDING), 0) rolling_5yr_income,
    ROUND(AVG(home_price) OVER (ORDER BY year ROWS 4 PRECEDING) /
          AVG(income)     OVER (ORDER BY year ROWS 4 PRECEDING), 2) rolling_ratio
FROM national_housing
ORDER BY year;
