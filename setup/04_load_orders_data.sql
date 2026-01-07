-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 4: Load Orders and Transaction Data
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- ORDERS FACT DATA (Generate ~50,000 orders over past 12 months)
-- ============================================================================
INSERT INTO FACT_ORDERS
WITH order_gen AS (
    SELECT 
        seq4() AS row_num,
        DATEADD(day, -MOD(seq4(), 365), CURRENT_DATE()) AS order_date
    FROM TABLE(GENERATOR(ROWCOUNT => 50000))
)
SELECT 
    'ORD' || LPAD(row_num::STRING, 8, '0') AS order_id,
    order_date,
    DATEADD(hour, 10 + MOD(row_num * 7, 12), order_date::TIMESTAMP_NTZ) AS order_timestamp,
    -- Distribute across stores with some stores busier
    CASE MOD(row_num, 15)
        WHEN 0 THEN 'STR001' WHEN 1 THEN 'STR002' WHEN 2 THEN 'STR003'
        WHEN 3 THEN 'STR004' WHEN 4 THEN 'STR004' WHEN 5 THEN 'STR005'  -- Chicago stores busier
        WHEN 6 THEN 'STR006' WHEN 7 THEN 'STR007' WHEN 8 THEN 'STR008'
        WHEN 9 THEN 'STR009' WHEN 10 THEN 'STR010' WHEN 11 THEN 'STR011'
        WHEN 12 THEN 'STR012' WHEN 13 THEN 'STR013' ELSE 'STR014'
    END AS store_id,
    'CUST' || LPAD(MOD(row_num * 17, 500)::STRING, 6, '0') AS customer_id,
    -- Some orders have campaigns
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
    -- Order values with realistic distribution
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

-- ============================================================================
-- ORDER ITEMS DATA
-- ============================================================================
INSERT INTO FACT_ORDER_ITEMS
WITH item_gen AS (
    SELECT 
        'ORD' || LPAD(o.row_num::STRING, 8, '0') AS order_id,
        seq4() AS item_num,
        o.row_num
    FROM (
        SELECT seq4() AS row_num FROM TABLE(GENERATOR(ROWCOUNT => 50000))
    ) o,
    TABLE(GENERATOR(ROWCOUNT => 3))  -- avg 3 items per order
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

-- ============================================================================
-- DELIVERIES DATA
-- ============================================================================
INSERT INTO FACT_DELIVERIES
SELECT 
    'DEL' || LPAD(seq4()::STRING, 8, '0') AS delivery_id,
    'ORD' || LPAD((seq4() * 3)::STRING, 8, '0') AS order_id,  -- ~1/3 of orders are delivery
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
    -- Actual delivery time with some late ones
    DATEADD(minute, 
        30 + CASE 
            WHEN MOD(seq4(), 8) = 0 THEN 15 + MOD(seq4(), 20)  -- ~12.5% late
            ELSE MOD(seq4(), 10) - 5  -- Some early, some on time
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
FROM TABLE(GENERATOR(ROWCOUNT => 17000));

-- Add specific late deliveries in Chicago for the demo scenario
-- "Why did thin-crust sales dip in Chicago last night?"
UPDATE FACT_DELIVERIES 
SET 
    is_late = true,
    late_minutes = 12,
    late_reason = 'traffic'
WHERE delivery_date = CURRENT_DATE() - 1 
  AND store_id IN ('STR004', 'STR005', 'STR006');

SELECT 'Orders and deliveries loaded successfully!' AS status;

