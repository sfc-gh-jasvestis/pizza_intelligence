-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Data Refresh Script
-- This script refreshes all data to ensure 12 months of historical data
-- and 3 months of future calendar data for forecasting
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- STEP 1: Refresh Calendar Data (12 months back, 3 months forward)
-- ============================================================================
TRUNCATE TABLE DIM_CALENDAR;

INSERT INTO DIM_CALENDAR
WITH date_series AS (
    SELECT DATEADD(day, seq4() - 365, CURRENT_DATE()) AS date_key
    FROM TABLE(GENERATOR(ROWCOUNT => 460))  -- ~12 months back + 3 months forward
)
SELECT 
    date_key,
    DAYNAME(date_key) AS day_of_week,
    DAYOFWEEK(date_key) AS day_of_week_num,
    DAYOFWEEK(date_key) IN (0, 6) AS is_weekend,
    WEEKOFYEAR(date_key) AS week_of_year,
    MONTHNAME(date_key) AS month_name,
    MONTH(date_key) AS month_num,
    QUARTER(date_key) AS quarter,
    YEAR(date_key) AS year,
    -- Holidays
    CASE 
        WHEN MONTH(date_key) = 1 AND DAY(date_key) = 1 THEN true
        WHEN MONTH(date_key) = 7 AND DAY(date_key) = 4 THEN true
        WHEN MONTH(date_key) = 12 AND DAY(date_key) = 25 THEN true
        WHEN MONTH(date_key) = 11 AND DAYOFWEEK(date_key) = 4 AND DAY(date_key) BETWEEN 22 AND 28 THEN true
        ELSE false
    END AS is_holiday,
    CASE 
        WHEN MONTH(date_key) = 1 AND DAY(date_key) = 1 THEN 'New Year''s Day'
        WHEN MONTH(date_key) = 7 AND DAY(date_key) = 4 THEN 'Independence Day'
        WHEN MONTH(date_key) = 12 AND DAY(date_key) = 25 THEN 'Christmas'
        WHEN MONTH(date_key) = 11 AND DAYOFWEEK(date_key) = 4 AND DAY(date_key) BETWEEN 22 AND 28 THEN 'Thanksgiving'
        ELSE NULL
    END AS holiday_name,
    -- Game days (Fridays and Sundays in fall/winter = NFL, plus some events)
    CASE 
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) BETWEEN 9 AND 12 THEN true  -- NFL Sunday
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) IN (1, 2) THEN true         -- NFL Playoffs
        WHEN DAYOFWEEK(date_key) = 5 AND MONTH(date_key) BETWEEN 9 AND 12 THEN true  -- Friday night games
        WHEN MONTH(date_key) = 2 AND DAY(date_key) BETWEEN 7 AND 14 AND DAYOFWEEK(date_key) = 0 THEN true  -- Super Bowl
        ELSE false
    END AS is_game_day,
    CASE 
        WHEN MONTH(date_key) = 2 AND DAY(date_key) BETWEEN 7 AND 14 AND DAYOFWEEK(date_key) = 0 THEN 'Super Bowl'
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) BETWEEN 9 AND 12 THEN 'NFL Sunday'
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) IN (1, 2) THEN 'NFL Playoffs'
        WHEN DAYOFWEEK(date_key) = 5 AND MONTH(date_key) BETWEEN 9 AND 12 THEN 'Friday Night Lights'
        ELSE NULL
    END AS game_event,
    -- Weather patterns (seasonal)
    CASE 
        WHEN MONTH(date_key) IN (6, 7, 8) THEN 'hot'
        WHEN MONTH(date_key) IN (12, 1, 2) THEN 'cold'
        WHEN MOD(DAY(date_key), 7) = 0 THEN 'rainy'
        ELSE 'sunny'
    END AS weather_condition,
    -- Temperatures (vary by season)
    CASE 
        WHEN MONTH(date_key) IN (6, 7, 8) THEN 85 + MOD(DAY(date_key), 20)
        WHEN MONTH(date_key) IN (12, 1, 2) THEN 35 + MOD(DAY(date_key), 15)
        ELSE 60 + MOD(DAY(date_key), 20)
    END AS high_temp_f,
    CASE 
        WHEN MONTH(date_key) IN (6, 7, 8) THEN 70 + MOD(DAY(date_key), 15)
        WHEN MONTH(date_key) IN (12, 1, 2) THEN 20 + MOD(DAY(date_key), 15)
        ELSE 45 + MOD(DAY(date_key), 15)
    END AS low_temp_f
FROM date_series;

SELECT 'Calendar refreshed: ' || COUNT(*) || ' days' AS status FROM DIM_CALENDAR;

-- ============================================================================
-- STEP 2: Refresh Orders Data (12 months)
-- ============================================================================
TRUNCATE TABLE FACT_ORDERS;

INSERT INTO FACT_ORDERS
WITH order_gen AS (
    SELECT 
        seq4() AS row_num,
        DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE()) AS order_date
    FROM TABLE(GENERATOR(ROWCOUNT => 60000))
)
SELECT 
    'ORD' || LPAD(row_num::STRING, 8, '0') AS order_id,
    order_date,
    DATEADD(hour, 10 + MOD(row_num * 7, 12), order_date::TIMESTAMP_NTZ) AS order_timestamp,
    CASE MOD(row_num, 15)
        WHEN 0 THEN 'STR001' WHEN 1 THEN 'STR002' WHEN 2 THEN 'STR003'
        WHEN 3 THEN 'STR004' WHEN 4 THEN 'STR004' WHEN 5 THEN 'STR005'
        WHEN 6 THEN 'STR006' WHEN 7 THEN 'STR007' WHEN 8 THEN 'STR008'
        WHEN 9 THEN 'STR009' WHEN 10 THEN 'STR010' WHEN 11 THEN 'STR011'
        WHEN 12 THEN 'STR012' WHEN 13 THEN 'STR013' ELSE 'STR014'
    END AS store_id,
    'CUST' || LPAD(MOD(row_num * 17, 500)::STRING, 6, '0') AS customer_id,
    CASE 
        WHEN MOD(row_num, 5) = 0 THEN 'CMP00' || (MOD(row_num, 10) + 1)::STRING
        ELSE NULL 
    END AS campaign_id,
    CASE MOD(row_num, 5)
        WHEN 0 THEN 'app'
        WHEN 1 THEN 'web'
        WHEN 2 THEN 'phone'
        WHEN 3 THEN 'in_store'
        ELSE 'third_party'
    END AS order_channel,
    CASE MOD(row_num, 3)
        WHEN 0 THEN 'delivery'
        WHEN 1 THEN 'pickup'
        ELSE 'dine_in'
    END AS order_type,
    25.00 + MOD(row_num * 13, 75) AS subtotal,
    CASE WHEN MOD(row_num, 5) = 0 THEN 3.00 + MOD(row_num, 8) ELSE 0 END AS discount_amount,
    (25.00 + MOD(row_num * 13, 75)) * 0.08 AS tax_amount,
    CASE WHEN MOD(row_num, 3) = 0 THEN 4.99 ELSE 0 END AS delivery_fee,
    CASE WHEN MOD(row_num, 3) = 0 THEN MOD(row_num, 8) + 2 ELSE 0 END AS tip_amount,
    (25.00 + MOD(row_num * 13, 75)) * 1.08 
        + CASE WHEN MOD(row_num, 3) = 0 THEN 4.99 + MOD(row_num, 8) + 2 ELSE 0 END
        - CASE WHEN MOD(row_num, 5) = 0 THEN 3.00 + MOD(row_num, 8) ELSE 0 END AS total_amount,
    MOD(row_num, 5) + 1 AS item_count,
    MOD(row_num, 20) = 0 AS is_first_order,
    CASE MOD(row_num, 4)
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'debit_card'
        WHEN 2 THEN 'apple_pay'
        ELSE 'cash'
    END AS payment_method
FROM order_gen;

SELECT 'Orders refreshed: ' || COUNT(*) || ' orders' AS status FROM FACT_ORDERS;

-- ============================================================================
-- STEP 3: Refresh Deliveries Data
-- ============================================================================
TRUNCATE TABLE FACT_DELIVERIES;

INSERT INTO FACT_DELIVERIES
SELECT 
    'DEL' || LPAD(seq4()::STRING, 8, '0') AS delivery_id,
    'ORD' || LPAD((seq4() * 3)::STRING, 8, '0') AS order_id,
    CASE MOD(seq4(), 15)
        WHEN 0 THEN 'STR001' WHEN 1 THEN 'STR002' WHEN 2 THEN 'STR003'
        WHEN 3 THEN 'STR004' WHEN 4 THEN 'STR004' WHEN 5 THEN 'STR005'
        WHEN 6 THEN 'STR006' WHEN 7 THEN 'STR007' WHEN 8 THEN 'STR008'
        WHEN 9 THEN 'STR009' WHEN 10 THEN 'STR010' WHEN 11 THEN 'STR011'
        WHEN 12 THEN 'STR012' WHEN 13 THEN 'STR013' ELSE 'STR014'
    END AS store_id,
    'RDR' || LPAD(MOD(seq4(), 200)::STRING, 4, '0') AS rider_id,
    DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE()) AS delivery_date,
    DATEADD(minute, 30, DATEADD(hour, 11 + MOD(seq4() * 7, 10), 
        DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE())::TIMESTAMP_NTZ)) AS promised_time,
    DATEADD(minute, 
        30 + CASE 
            WHEN MOD(seq4(), 8) = 0 THEN 15 + MOD(seq4(), 20)
            ELSE MOD(seq4(), 10) - 5
        END,
        DATEADD(hour, 11 + MOD(seq4() * 7, 10), 
            DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE())::TIMESTAMP_NTZ)
    ) AS actual_delivery_time,
    DATEADD(hour, 11 + MOD(seq4() * 7, 10), 
        DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE())::TIMESTAMP_NTZ) AS prep_start_time,
    DATEADD(minute, 15 + MOD(seq4(), 10), 
        DATEADD(hour, 11 + MOD(seq4() * 7, 10), 
            DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE())::TIMESTAMP_NTZ)) AS prep_end_time,
    DATEADD(minute, 20 + MOD(seq4(), 5), 
        DATEADD(hour, 11 + MOD(seq4() * 7, 10), 
            DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE())::TIMESTAMP_NTZ)) AS dispatch_time,
    2.5 + MOD(seq4(), 80) / 10.0 AS delivery_distance_km,
    15 + MOD(seq4(), 25) AS delivery_duration_min,
    MOD(seq4(), 8) = 0 AS is_late,
    CASE WHEN MOD(seq4(), 8) = 0 THEN 5 + MOD(seq4(), 20) ELSE 0 END AS late_minutes,
    CASE 
        WHEN MOD(seq4(), 8) = 0 THEN 
            CASE MOD(seq4(), 4)
                WHEN 0 THEN 'traffic'
                WHEN 1 THEN 'kitchen_delay'
                WHEN 2 THEN 'rider_shortage'
                ELSE 'weather'
            END
        ELSE NULL
    END AS late_reason,
    3.5 + MOD(seq4(), 15) / 10.0 AS customer_rating,
    CASE MOD(seq4(), 10)
        WHEN 0 THEN 'Left at door as requested'
        WHEN 1 THEN 'Customer not available, left with neighbor'
        WHEN 2 THEN 'Delivered to office reception'
        ELSE NULL
    END AS delivery_notes
FROM TABLE(GENERATOR(ROWCOUNT => 20000));

SELECT 'Deliveries refreshed: ' || COUNT(*) || ' deliveries' AS status FROM FACT_DELIVERIES;

-- ============================================================================
-- STEP 4: Refresh Order Items Data
-- ============================================================================
TRUNCATE TABLE FACT_ORDER_ITEMS;

INSERT INTO FACT_ORDER_ITEMS
WITH item_gen AS (
    SELECT 
        'ORD' || LPAD(o.row_num::STRING, 8, '0') AS order_id,
        seq4() AS item_num,
        o.row_num
    FROM (
        SELECT seq4() AS row_num FROM TABLE(GENERATOR(ROWCOUNT => 60000))
    ) o,
    TABLE(GENERATOR(ROWCOUNT => 3))
    WHERE seq4() < MOD(o.row_num, 5) + 1
)
SELECT 
    order_id || '-' || item_num AS order_item_id,
    order_id,
    'PRD' || LPAD((MOD(row_num * 7 + item_num, 20) + 1)::STRING, 3, '0') AS product_id,
    MOD(item_num, 3) + 1 AS quantity,
    12.99 + MOD(row_num * 3, 15) AS unit_price,
    (MOD(item_num, 3) + 1) * (12.99 + MOD(row_num * 3, 15)) AS line_total,
    CASE MOD(item_num, 4)
        WHEN 0 THEN '{"extra_cheese": true}'
        WHEN 1 THEN '{"no_onions": true, "extra_pepperoni": true}'
        WHEN 2 THEN '{"gluten_free_crust": true}'
        ELSE NULL
    END AS customizations
FROM item_gen;

SELECT 'Order items refreshed: ' || COUNT(*) || ' items' AS status FROM FACT_ORDER_ITEMS;

-- ============================================================================
-- STEP 5: Refresh Inventory Data (last 90 days)
-- ============================================================================
TRUNCATE TABLE FACT_INVENTORY;

INSERT INTO FACT_INVENTORY
WITH ingredients AS (
    SELECT * FROM (VALUES 
        ('Pepperoni', 'toppings'),
        ('Mozzarella', 'cheese'),
        ('Parmesan', 'cheese'),
        ('Pizza Dough', 'dough'),
        ('Thin Crust Dough', 'dough'),
        ('Pan Dough', 'dough'),
        ('Tomato Sauce', 'sauces'),
        ('BBQ Sauce', 'sauces'),
        ('Mushrooms', 'toppings'),
        ('Bell Peppers', 'toppings'),
        ('Onions', 'toppings'),
        ('Italian Sausage', 'toppings'),
        ('Chicken', 'toppings'),
        ('Pineapple', 'toppings'),
        ('Olives', 'toppings'),
        ('Pizza Boxes (Large)', 'packaging'),
        ('Pizza Boxes (Medium)', 'packaging'),
        ('Napkins', 'packaging')
    ) AS t(ingredient_name, ingredient_category)
),
store_dates AS (
    SELECT 
        s.store_id,
        DATEADD(day, -seq4(), CURRENT_DATE()) AS snapshot_date
    FROM DIM_STORES s,
    TABLE(GENERATOR(ROWCOUNT => 90))
)
SELECT 
    'INV' || LPAD(ROW_NUMBER() OVER (ORDER BY sd.store_id, sd.snapshot_date, i.ingredient_name)::STRING, 10, '0') AS inventory_id,
    sd.store_id,
    i.ingredient_name,
    i.ingredient_category,
    sd.snapshot_date,
    CASE i.ingredient_category
        WHEN 'dough' THEN 50 + MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 100)
        WHEN 'cheese' THEN 30 + MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 50)
        WHEN 'toppings' THEN 20 + MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 40)
        WHEN 'sauces' THEN 15 + MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 30)
        ELSE 100 + MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 200)
    END AS quantity_on_hand,
    CASE i.ingredient_category
        WHEN 'dough' THEN 'kg'
        WHEN 'cheese' THEN 'kg'
        WHEN 'toppings' THEN 'kg'
        WHEN 'sauces' THEN 'liters'
        ELSE 'units'
    END AS unit_of_measure,
    CASE i.ingredient_category
        WHEN 'dough' THEN 20
        WHEN 'cheese' THEN 15
        WHEN 'toppings' THEN 10
        WHEN 'sauces' THEN 8
        ELSE 50
    END AS reorder_point,
    CASE i.ingredient_category
        WHEN 'dough' THEN 100
        WHEN 'cheese' THEN 50
        WHEN 'toppings' THEN 30
        WHEN 'sauces' THEN 25
        ELSE 200
    END AS reorder_quantity,
    CASE i.ingredient_category
        WHEN 'dough' THEN 2.50
        WHEN 'cheese' THEN 8.00
        WHEN 'toppings' THEN 5.00
        WHEN 'sauces' THEN 3.00
        ELSE 0.50
    END AS unit_cost,
    CASE i.ingredient_category
        WHEN 'dough' THEN 3 + MOD(HASH(sd.snapshot_date::STRING), 4)
        WHEN 'cheese' THEN 7 + MOD(HASH(sd.snapshot_date::STRING), 7)
        WHEN 'toppings' THEN 5 + MOD(HASH(sd.snapshot_date::STRING), 5)
        WHEN 'sauces' THEN 14 + MOD(HASH(sd.snapshot_date::STRING), 14)
        ELSE 365
    END AS days_until_expiry,
    CASE 
        WHEN MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 10) = 0 
        THEN 1 + MOD(HASH(sd.snapshot_date::STRING), 5)
        ELSE 0
    END AS wastage_units,
    CASE 
        WHEN MOD(HASH(sd.store_id || i.ingredient_name || sd.snapshot_date::STRING), 10) = 0 
        THEN CASE MOD(HASH(sd.snapshot_date::STRING), 4)
            WHEN 0 THEN 'expired'
            WHEN 1 THEN 'damaged'
            WHEN 2 THEN 'quality'
            ELSE 'overproduction'
        END
        ELSE NULL
    END AS wastage_reason
FROM store_dates sd
CROSS JOIN ingredients i;

SELECT 'Inventory refreshed: ' || COUNT(*) || ' records' AS status FROM FACT_INVENTORY;

-- ============================================================================
-- STEP 6: Refresh Staffing Data (uses calendar, so includes future dates)
-- ============================================================================
TRUNCATE TABLE FACT_STAFFING;

INSERT INTO FACT_STAFFING
SELECT 
    'STF' || LPAD(ROW_NUMBER() OVER (ORDER BY s.store_id, d.date_key, shift_type)::STRING, 10, '0') AS staffing_id,
    s.store_id,
    d.date_key AS shift_date,
    shift.shift_type,
    CASE 
        WHEN d.is_weekend OR d.is_game_day THEN 
            CASE shift.shift_type
                WHEN 'evening' THEN 12
                WHEN 'afternoon' THEN 10
                ELSE 6
            END
        ELSE 
            CASE shift.shift_type
                WHEN 'evening' THEN 8
                WHEN 'afternoon' THEN 7
                ELSE 5
            END
    END AS scheduled_staff,
    CASE 
        WHEN d.is_weekend OR d.is_game_day THEN 
            CASE shift.shift_type
                WHEN 'evening' THEN 12 - MOD(HASH(s.store_id || d.date_key::STRING), 3)
                WHEN 'afternoon' THEN 10 - MOD(HASH(s.store_id || d.date_key::STRING), 2)
                ELSE 6
            END
        ELSE 
            CASE shift.shift_type
                WHEN 'evening' THEN 8 - MOD(HASH(s.store_id || d.date_key::STRING), 2)
                WHEN 'afternoon' THEN 7
                ELSE 5
            END
    END AS actual_staff,
    CASE shift.shift_type
        WHEN 'evening' THEN 4
        WHEN 'afternoon' THEN 3
        ELSE 2
    END AS kitchen_staff,
    CASE shift.shift_type
        WHEN 'evening' THEN 3
        WHEN 'afternoon' THEN 2
        ELSE 2
    END AS counter_staff,
    CASE shift.shift_type
        WHEN 'evening' THEN 5
        WHEN 'afternoon' THEN 4
        ELSE 2
    END AS riders_available,
    CASE 
        WHEN (d.is_weekend OR d.is_game_day) AND shift.shift_type = 'evening' 
        THEN 2.5 + MOD(HASH(s.store_id || d.date_key::STRING), 30) / 10.0
        ELSE 0
    END AS overtime_hours,
    CASE 
        WHEN d.is_weekend OR d.is_game_day THEN 
            CASE shift.shift_type
                WHEN 'evening' THEN 850 + MOD(HASH(s.store_id || d.date_key::STRING), 200)
                WHEN 'afternoon' THEN 650 + MOD(HASH(s.store_id || d.date_key::STRING), 150)
                ELSE 400 + MOD(HASH(s.store_id || d.date_key::STRING), 100)
            END
        ELSE 
            CASE shift.shift_type
                WHEN 'evening' THEN 550 + MOD(HASH(s.store_id || d.date_key::STRING), 150)
                WHEN 'afternoon' THEN 450 + MOD(HASH(s.store_id || d.date_key::STRING), 100)
                ELSE 300 + MOD(HASH(s.store_id || d.date_key::STRING), 80)
            END
    END AS labor_cost
FROM DIM_STORES s
CROSS JOIN DIM_CALENDAR d
CROSS JOIN (SELECT 'morning' AS shift_type UNION ALL SELECT 'afternoon' UNION ALL SELECT 'evening') shift
WHERE d.date_key >= DATEADD(day, -365, CURRENT_DATE())
  AND d.date_key <= DATEADD(day, 90, CURRENT_DATE());

SELECT 'Staffing refreshed: ' || COUNT(*) || ' records' AS status FROM FACT_STAFFING;

-- ============================================================================
-- STEP 7: Refresh Campaign Performance Data
-- ============================================================================
TRUNCATE TABLE FACT_CAMPAIGN_PERFORMANCE;

-- First update campaign dates to be current
UPDATE DIM_CAMPAIGNS SET 
    start_date = DATEADD(month, -6, CURRENT_DATE()),
    end_date = DATEADD(month, 6, CURRENT_DATE())
WHERE status = 'active';

UPDATE DIM_CAMPAIGNS SET 
    start_date = DATEADD(month, -9, CURRENT_DATE()),
    end_date = DATEADD(month, -3, CURRENT_DATE())
WHERE status = 'completed';

INSERT INTO FACT_CAMPAIGN_PERFORMANCE
SELECT 
    'PERF' || LPAD(ROW_NUMBER() OVER (ORDER BY c.campaign_id, s.store_id, d.date_key)::STRING, 10, '0') AS performance_id,
    c.campaign_id,
    s.store_id,
    d.date_key AS performance_date,
    1000 + MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 5000) AS impressions,
    (1000 + MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 5000)) * 
        (5 + MOD(HASH(d.date_key::STRING), 10)) / 100 AS clicks,
    MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 50) + 10 AS redemptions,
    MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5 AS orders_attributed,
    (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5) * 
        (35 + MOD(HASH(d.date_key::STRING), 25)) AS revenue_attributed,
    (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 50) + 10) * 
        COALESCE(c.discount_amount, c.discount_percent * 0.35) AS discount_cost,
    (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5) * 
        (35 + MOD(HASH(d.date_key::STRING), 25)) * 0.3 AS incremental_revenue,
    ((MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5) * 
        (35 + MOD(HASH(d.date_key::STRING), 25)) * 0.3 - 
        (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 50) + 10) * 
        COALESCE(c.discount_amount, c.discount_percent * 0.35)) /
    NULLIF((MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 50) + 10) * 
        COALESCE(c.discount_amount, c.discount_percent * 0.35), 0) * 100 AS roi_percent
FROM DIM_CAMPAIGNS c
CROSS JOIN DIM_STORES s
CROSS JOIN DIM_CALENDAR d
WHERE d.date_key >= c.start_date
  AND d.date_key <= LEAST(COALESCE(c.end_date, CURRENT_DATE()), CURRENT_DATE())
  AND c.status IN ('active', 'completed');

SELECT 'Campaign performance refreshed: ' || COUNT(*) || ' records' AS status FROM FACT_CAMPAIGN_PERFORMANCE;

-- ============================================================================
-- STEP 8: Recreate Views
-- ============================================================================
CREATE OR REPLACE VIEW V_ORDERS AS
SELECT 
    o.order_id, o.order_date, o.order_timestamp, o.store_id,
    s.store_name, s.city, s.state, s.region, s.district,
    o.customer_id, o.campaign_id, o.order_channel, o.order_type,
    o.subtotal, o.discount_amount, o.tax_amount, o.delivery_fee,
    o.tip_amount, o.total_amount, o.item_count, o.is_first_order, o.payment_method,
    c.day_of_week, c.is_weekend, c.is_holiday, c.holiday_name,
    c.is_game_day, c.game_event, c.weather_condition, c.high_temp_f
FROM FACT_ORDERS o
LEFT JOIN DIM_STORES s ON o.store_id = s.store_id
LEFT JOIN DIM_CALENDAR c ON o.order_date = c.date_key;

CREATE OR REPLACE VIEW V_STAFFING AS
SELECT 
    f.staffing_id, f.store_id, s.store_name, s.city, s.region,
    f.shift_date, f.shift_type, f.scheduled_staff, f.actual_staff,
    f.kitchen_staff, f.counter_staff, f.riders_available,
    f.overtime_hours, f.labor_cost,
    c.day_of_week, c.is_weekend, c.is_game_day
FROM FACT_STAFFING f
LEFT JOIN DIM_STORES s ON f.store_id = s.store_id
LEFT JOIN DIM_CALENDAR c ON f.shift_date = c.date_key;

-- V_ORDER_ITEMS - CRITICAL for thin-crust vs pan pizza analysis
CREATE OR REPLACE VIEW V_ORDER_ITEMS AS
SELECT 
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    p.product_name,
    p.category AS product_category,
    p.subcategory AS crust_type,
    p.size AS product_size,
    p.base_price,
    p.is_signature,
    oi.quantity,
    oi.unit_price,
    oi.line_total,
    oi.customizations,
    o.order_date,
    o.order_timestamp,
    o.store_id,
    s.store_name,
    s.city,
    s.state,
    s.region,
    o.order_channel,
    o.order_type,
    o.customer_id,
    c.day_of_week,
    c.is_weekend,
    c.is_game_day,
    c.weather_condition
FROM FACT_ORDER_ITEMS oi
LEFT JOIN DIM_PRODUCTS p ON oi.product_id = p.product_id
LEFT JOIN FACT_ORDERS o ON oi.order_id = o.order_id
LEFT JOIN DIM_STORES s ON o.store_id = s.store_id
LEFT JOIN DIM_CALENDAR c ON o.order_date = c.date_key;

-- ============================================================================
-- STEP 9: Add Chicago Thin-Crust Decline Story Data
-- This creates the data pattern for "Why did thin-crust sales dip in Chicago?"
-- ============================================================================

-- Reduce thin-crust orders in Chicago stores for the past 30 days
-- (Delete some thin-crust items from Chicago orders to simulate decline)
DELETE FROM FACT_ORDER_ITEMS
WHERE order_item_id IN (
    SELECT oi.order_item_id
    FROM FACT_ORDER_ITEMS oi
    JOIN FACT_ORDERS o ON oi.order_id = o.order_id
    JOIN DIM_PRODUCTS p ON oi.product_id = p.product_id
    WHERE o.store_id IN ('STR004', 'STR005', 'STR006')  -- Chicago stores
      AND p.subcategory = 'thin_crust'
      AND o.order_date >= CURRENT_DATE() - 30
      AND MOD(HASH(oi.order_item_id), 4) = 0  -- Remove ~25% of thin-crust items
);

-- Also mark more deliveries as late in Chicago stores for "last night"
UPDATE FACT_DELIVERIES 
SET 
    is_late = true,
    late_minutes = 15 + MOD(HASH(delivery_id), 20),
    late_reason = 'traffic'
WHERE delivery_date = CURRENT_DATE() - 1 
  AND store_id IN ('STR004', 'STR005', 'STR006');

SELECT 'Chicago thin-crust decline story data created' AS status;

-- ============================================================================
-- FINAL SUMMARY
-- ============================================================================
SELECT '=== DATA REFRESH COMPLETE ===' AS status;
SELECT 'Calendar' AS table_name, COUNT(*) AS records, MIN(date_key) AS min_date, MAX(date_key) AS max_date FROM DIM_CALENDAR
UNION ALL
SELECT 'Orders', COUNT(*), MIN(order_date), MAX(order_date) FROM FACT_ORDERS
UNION ALL
SELECT 'Deliveries', COUNT(*), MIN(delivery_date), MAX(delivery_date) FROM FACT_DELIVERIES
UNION ALL
SELECT 'Staffing', COUNT(*), MIN(shift_date), MAX(shift_date) FROM FACT_STAFFING
UNION ALL
SELECT 'Inventory', COUNT(*), MIN(snapshot_date), MAX(snapshot_date) FROM FACT_INVENTORY;
