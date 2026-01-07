-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 8: Create Pre-Joined Views for Semantic Model
-- ============================================================================
-- These views pre-join fact tables with dimension tables so the semantic model
-- doesn't need to define complex relationships.
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- Orders View (with store details)
-- ============================================================================
CREATE OR REPLACE VIEW V_ORDERS AS
SELECT 
    o.order_id,
    o.order_date,
    o.order_timestamp,
    o.store_id,
    s.store_name,
    s.city,
    s.state,
    s.region,
    s.district,
    o.customer_id,
    o.campaign_id,
    o.order_channel,
    o.order_type,
    o.subtotal,
    o.discount_amount,
    o.tax_amount,
    o.delivery_fee,
    o.tip_amount,
    o.total_amount,
    o.item_count,
    o.is_first_order,
    o.payment_method,
    -- Calendar fields for easy filtering
    c.day_of_week,
    c.is_weekend,
    c.is_holiday,
    c.holiday_name,
    c.is_game_day,
    c.game_event,
    c.weather_condition,
    c.high_temp_f
FROM FACT_ORDERS o
LEFT JOIN DIM_STORES s ON o.store_id = s.store_id
LEFT JOIN DIM_CALENDAR c ON o.order_date = c.date_key;

-- ============================================================================
-- Deliveries View (with store details)
-- ============================================================================
CREATE OR REPLACE VIEW V_DELIVERIES AS
SELECT 
    d.delivery_id,
    d.order_id,
    d.store_id,
    s.store_name,
    s.city,
    s.state,
    s.region,
    d.rider_id,
    d.delivery_date,
    d.promised_time,
    d.actual_delivery_time,
    d.prep_start_time,
    d.prep_end_time,
    d.dispatch_time,
    d.delivery_distance_km,
    d.delivery_duration_min,
    d.is_late,
    d.late_minutes,
    d.late_reason,
    d.customer_rating,
    d.delivery_notes,
    -- Calendar fields
    c.day_of_week,
    c.is_weekend,
    c.is_game_day,
    c.weather_condition
FROM FACT_DELIVERIES d
LEFT JOIN DIM_STORES s ON d.store_id = s.store_id
LEFT JOIN DIM_CALENDAR c ON d.delivery_date = c.date_key;

-- ============================================================================
-- Inventory View (with store details)
-- ============================================================================
CREATE OR REPLACE VIEW V_INVENTORY AS
SELECT 
    i.inventory_id,
    i.store_id,
    s.store_name,
    s.city,
    s.region,
    i.ingredient_name,
    i.ingredient_category,
    i.snapshot_date,
    i.quantity_on_hand,
    i.unit_of_measure,
    i.reorder_point,
    i.reorder_quantity,
    i.unit_cost,
    i.days_until_expiry,
    i.wastage_units,
    i.wastage_reason
FROM FACT_INVENTORY i
LEFT JOIN DIM_STORES s ON i.store_id = s.store_id;

-- ============================================================================
-- Staffing View (with store details)
-- ============================================================================
CREATE OR REPLACE VIEW V_STAFFING AS
SELECT 
    f.staffing_id,
    f.store_id,
    s.store_name,
    s.city,
    s.region,
    f.shift_date,
    f.shift_type,
    f.scheduled_staff,
    f.actual_staff,
    f.kitchen_staff,
    f.counter_staff,
    f.riders_available,
    f.overtime_hours,
    f.labor_cost,
    -- Calendar fields
    c.day_of_week,
    c.is_weekend,
    c.is_game_day
FROM FACT_STAFFING f
LEFT JOIN DIM_STORES s ON f.store_id = s.store_id
LEFT JOIN DIM_CALENDAR c ON f.shift_date = c.date_key;

-- ============================================================================
-- Campaign Performance View (with campaign and store details)
-- ============================================================================
CREATE OR REPLACE VIEW V_CAMPAIGN_PERFORMANCE AS
SELECT 
    cp.performance_id,
    cp.campaign_id,
    ca.campaign_name,
    ca.campaign_type,
    ca.channel,
    ca.target_segment,
    cp.store_id,
    s.store_name,
    s.city,
    s.region,
    cp.performance_date,
    cp.impressions,
    cp.clicks,
    cp.redemptions,
    cp.orders_attributed,
    cp.revenue_attributed,
    cp.discount_cost,
    cp.incremental_revenue,
    cp.roi_percent
FROM FACT_CAMPAIGN_PERFORMANCE cp
LEFT JOIN DIM_CAMPAIGNS ca ON cp.campaign_id = ca.campaign_id
LEFT JOIN DIM_STORES s ON cp.store_id = s.store_id;

-- Verify views
SELECT 'Views created successfully!' AS status;
SELECT 'V_ORDERS' AS view_name, COUNT(*) AS row_count FROM V_ORDERS
UNION ALL
SELECT 'V_DELIVERIES', COUNT(*) FROM V_DELIVERIES
UNION ALL
SELECT 'V_INVENTORY', COUNT(*) FROM V_INVENTORY
UNION ALL
SELECT 'V_STAFFING', COUNT(*) FROM V_STAFFING
UNION ALL
SELECT 'V_CAMPAIGN_PERFORMANCE', COUNT(*) FROM V_CAMPAIGN_PERFORMANCE;

