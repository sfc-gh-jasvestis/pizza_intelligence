-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 5: Load Inventory, Staffing, and Campaign Performance Data
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- INVENTORY DATA (Daily snapshots for all stores)
-- ============================================================================
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
    TABLE(GENERATOR(ROWCOUNT => 90))  -- 90 days of inventory data
)
SELECT 
    'INV' || LPAD(ROW_NUMBER() OVER (ORDER BY sd.store_id, sd.snapshot_date, i.ingredient_name)::STRING, 10, '0') AS inventory_id,
    sd.store_id,
    i.ingredient_name,
    i.ingredient_category,
    sd.snapshot_date,
    -- Quantity varies by day and ingredient
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
    -- Some wastage
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

-- ============================================================================
-- STAFFING DATA
-- ============================================================================
INSERT INTO FACT_STAFFING
SELECT 
    'STF' || LPAD(ROW_NUMBER() OVER (ORDER BY s.store_id, d.date_key, shift_type)::STRING, 10, '0') AS staffing_id,
    s.store_id,
    d.date_key AS shift_date,
    shift.shift_type,
    -- Scheduled staff varies by day type and shift
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
    -- Actual staff (sometimes short)
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
    -- Overtime on busy days
    CASE 
        WHEN (d.is_weekend OR d.is_game_day) AND shift.shift_type = 'evening' 
        THEN 2.5 + MOD(HASH(s.store_id || d.date_key::STRING), 30) / 10.0
        ELSE 0
    END AS overtime_hours,
    -- Labor cost
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
WHERE d.date_key >= DATEADD(day, -90, CURRENT_DATE())
  AND d.date_key <= CURRENT_DATE();

-- ============================================================================
-- CAMPAIGN PERFORMANCE DATA
-- ============================================================================
INSERT INTO FACT_CAMPAIGN_PERFORMANCE
SELECT 
    'PERF' || LPAD(ROW_NUMBER() OVER (ORDER BY c.campaign_id, s.store_id, d.date_key)::STRING, 10, '0') AS performance_id,
    c.campaign_id,
    s.store_id,
    d.date_key AS performance_date,
    -- Impressions
    1000 + MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 5000) AS impressions,
    -- Clicks (5-15% CTR)
    (1000 + MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 5000)) * 
        (5 + MOD(HASH(d.date_key::STRING), 10)) / 100 AS clicks,
    -- Redemptions
    MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 50) + 10 AS redemptions,
    -- Orders attributed
    MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5 AS orders_attributed,
    -- Revenue
    (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5) * 
        (35 + MOD(HASH(d.date_key::STRING), 25)) AS revenue_attributed,
    -- Discount cost
    (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 50) + 10) * 
        COALESCE(c.discount_amount, c.discount_percent * 0.35) AS discount_cost,
    -- Incremental revenue (attributed - baseline estimate)
    (MOD(HASH(c.campaign_id || s.store_id || d.date_key::STRING), 40) + 5) * 
        (35 + MOD(HASH(d.date_key::STRING), 25)) * 0.3 AS incremental_revenue,
    -- ROI
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
  AND d.date_key <= COALESCE(c.end_date, CURRENT_DATE())
  AND d.date_key <= CURRENT_DATE()
  AND c.status IN ('active', 'completed');

SELECT 'Inventory, staffing, and campaign performance loaded successfully!' AS status;

