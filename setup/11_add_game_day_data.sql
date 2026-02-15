-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Add Game Day Variation Data
-- This script adds more orders on game day Fridays to show meaningful demand forecasts
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- UPDATE CALENDAR: Add Bulls/Blackhawks Friday game days
-- day_of_week column stores text like 'Fri', 'Sat', etc.
-- ============================================================================
UPDATE DIM_CALENDAR
SET 
    is_game_day = TRUE,
    game_event = 'Bulls/Blackhawks Friday'
WHERE day_of_week = 'Fri'  -- Friday
  AND MONTH(date_key) IN (10, 11, 12, 1, 2, 3)  -- NBA/NHL season
  AND is_game_day = FALSE;

-- ============================================================================
-- ADD EXTRA ORDERS ON GAME DAY FRIDAYS (40% more orders)
-- This creates a clear difference between game day Fridays and regular Fridays
-- ============================================================================
INSERT INTO FACT_ORDERS
WITH game_fridays AS (
    SELECT date_key
    FROM DIM_CALENDAR
    WHERE is_game_day = TRUE 
      AND day_of_week = 'Fri'  -- Fridays
      AND date_key >= DATEADD(month, -12, CURRENT_DATE())
      AND date_key < CURRENT_DATE()
),
extra_orders AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY gf.date_key, seq4()) AS row_num,
        gf.date_key AS order_date
    FROM game_fridays gf,
    TABLE(GENERATOR(ROWCOUNT => 35))  -- ~35 extra orders per game Friday
)
SELECT 
    'ORD' || LPAD((100000 + row_num)::STRING, 8, '0') AS order_id,
    order_date,
    DATEADD(hour, 17 + MOD(row_num, 5), order_date::TIMESTAMP_NTZ) AS order_timestamp,  -- Evening orders (5-9pm)
    -- Chicago stores get the game day bump
    CASE MOD(row_num, 5)
        WHEN 0 THEN 'STR004'
        WHEN 1 THEN 'STR005'
        WHEN 2 THEN 'STR006'
        WHEN 3 THEN 'STR004'
        ELSE 'STR005'
    END AS store_id,
    'CUST' || LPAD(MOD(row_num * 17, 500)::STRING, 6, '0') AS customer_id,
    NULL AS campaign_id,
    CASE MOD(row_num, 3)
        WHEN 0 THEN 'app'
        WHEN 1 THEN 'web'
        ELSE 'phone'
    END AS order_channel,
    'delivery' AS order_type,  -- Game day = lots of deliveries
    -- Game day orders tend to be larger (group orders)
    45.00 + MOD(row_num * 13, 55) AS subtotal,
    0 AS discount_amount,
    (45.00 + MOD(row_num * 13, 55)) * 0.08 AS tax_amount,
    4.99 AS delivery_fee,
    MOD(row_num, 10) + 3 AS tip_amount,
    (45.00 + MOD(row_num * 13, 55)) * 1.08 + 4.99 + MOD(row_num, 10) + 3 AS total_amount,
    MOD(row_num, 4) + 2 AS item_count,  -- More items per order
    FALSE AS is_first_order,
    CASE MOD(row_num, 3)
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'apple_pay'
        ELSE 'debit_card'
    END AS payment_method
FROM extra_orders;

-- ============================================================================
-- VERIFY THE DIFFERENCE
-- ============================================================================
SELECT 
    CASE WHEN c.is_game_day THEN 'Game Day Friday' ELSE 'Regular Friday' END AS day_type,
    COUNT(DISTINCT o.order_date) AS num_fridays,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) / COUNT(DISTINCT o.order_date), 0) AS avg_orders_per_friday,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM FACT_ORDERS o
JOIN DIM_CALENDAR c ON o.order_date = c.date_key
WHERE c.day_of_week = 'Fri'  -- Fridays
  AND o.order_date >= DATEADD(month, -6, CURRENT_DATE())
GROUP BY c.is_game_day
ORDER BY c.is_game_day DESC;

SELECT 'Game day variation data added successfully!' AS status;
