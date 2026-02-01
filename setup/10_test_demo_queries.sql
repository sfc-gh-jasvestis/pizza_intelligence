-- ============================================================================
-- PIZZA INTELLIGENCE DEMO - TEST QUERIES
-- Run this script to verify all demo questions will work correctly
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- TEST 1: Verify Views Exist
-- ============================================================================
SELECT '=== TEST 1: Views Existence ===' AS test;
SELECT 'V_ORDERS' AS view_name, COUNT(*) AS records FROM V_ORDERS
UNION ALL
SELECT 'V_DELIVERIES', COUNT(*) FROM V_DELIVERIES
UNION ALL
SELECT 'V_INVENTORY', COUNT(*) FROM V_INVENTORY
UNION ALL
SELECT 'V_STAFFING', COUNT(*) FROM V_STAFFING
UNION ALL
SELECT 'V_CAMPAIGN_PERFORMANCE', COUNT(*) FROM V_CAMPAIGN_PERFORMANCE
UNION ALL
SELECT 'V_ORDER_ITEMS', COUNT(*) FROM V_ORDER_ITEMS;

-- ============================================================================
-- TEST 2: Thin-Crust vs Pan Pizza Performance (KEY DEMO QUERY)
-- ============================================================================
SELECT '=== TEST 2: Thin-Crust vs Pan Performance ===' AS test;
SELECT 
    crust_type,
    COUNT(DISTINCT order_id) AS orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS total_revenue
FROM V_ORDER_ITEMS
WHERE product_category = 'pizza'
  AND order_date >= CURRENT_DATE() - 30
GROUP BY crust_type
ORDER BY total_revenue DESC;

-- ============================================================================
-- TEST 3: Chicago Thin-Crust Decline (Should show lower numbers than other cities)
-- ============================================================================
SELECT '=== TEST 3: Chicago Thin-Crust Sales ===' AS test;
SELECT 
    city,
    crust_type,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS revenue
FROM V_ORDER_ITEMS
WHERE product_category = 'pizza'
  AND crust_type IN ('thin_crust', 'pan')
  AND order_date >= CURRENT_DATE() - 30
GROUP BY city, crust_type
ORDER BY city, crust_type;

-- ============================================================================
-- TEST 4: Last Night's Sales (KEY DEMO QUERY)
-- ============================================================================
SELECT '=== TEST 4: Last Night Sales ===' AS test;
SELECT 
    store_name,
    city,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM V_ORDERS
WHERE order_date = CURRENT_DATE() - 1
GROUP BY store_name, city
ORDER BY total_revenue DESC;

-- ============================================================================
-- TEST 5: Late Deliveries Analysis
-- ============================================================================
SELECT '=== TEST 5: Late Delivery Rate by City ===' AS test;
SELECT 
    city,
    COUNT(*) AS total_deliveries,
    SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_deliveries,
    ROUND(100.0 * SUM(CASE WHEN is_late THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_rate_pct
FROM V_DELIVERIES
WHERE delivery_date >= CURRENT_DATE() - 7
GROUP BY city
ORDER BY late_rate_pct DESC;

-- ============================================================================
-- TEST 6: Friday Night Prep Data
-- ============================================================================
SELECT '=== TEST 6: Upcoming Friday Night Data ===' AS test;
SELECT 
    date_key AS friday_date,
    day_of_week,
    is_game_day,
    game_event
FROM DIM_CALENDAR
WHERE day_of_week = 'Fri'
  AND date_key >= CURRENT_DATE()
  AND date_key <= CURRENT_DATE() + 14
ORDER BY date_key;

-- Show historical Friday performance
SELECT 
    'Historical Friday Average' AS metric,
    ROUND(AVG(total_revenue), 2) AS avg_revenue,
    ROUND(AVG(order_count), 0) AS avg_orders
FROM (
    SELECT 
        order_date,
        SUM(total_amount) AS total_revenue,
        COUNT(DISTINCT order_id) AS order_count
    FROM V_ORDERS
    WHERE day_of_week = 'Fri'
      AND order_date >= CURRENT_DATE() - 90
    GROUP BY order_date
);

-- ============================================================================
-- TEST 7: Cortex Search Documents
-- ============================================================================
USE SCHEMA DOCUMENTS;
SELECT '=== TEST 7: Cortex Search Documents ===' AS test;
SELECT 
    document_id,
    document_type,
    document_title,
    LEFT(summary, 80) AS summary_preview
FROM PIZZA_DOCUMENTS
ORDER BY document_type, document_date DESC;

-- Test thin-crust related document search
SELECT '=== Documents mentioning thin-crust or competitor ===' AS test;
SELECT 
    document_id,
    document_type,
    document_title
FROM PIZZA_DOCUMENTS
WHERE LOWER(content) LIKE '%thin%crust%'
   OR LOWER(content) LIKE '%crispy crust%';

-- ============================================================================
-- TEST 8: Semantic Model Stage
-- ============================================================================
USE SCHEMA SEMANTIC_MODELS;
SELECT '=== TEST 8: Semantic Model Stage ===' AS test;
LIST @SEMANTIC_MODEL_STAGE;

-- ============================================================================
-- TEST 9: Game Day Impact Analysis
-- ============================================================================
USE SCHEMA ANALYTICS;
SELECT '=== TEST 9: Game Day Impact ===' AS test;
SELECT 
    CASE WHEN is_game_day THEN 'Game Day' ELSE 'Regular Day' END AS day_type,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM V_ORDERS
WHERE order_date >= CURRENT_DATE() - 90
GROUP BY is_game_day
ORDER BY is_game_day DESC;

-- ============================================================================
-- TEST 10: Product Mix Analysis
-- ============================================================================
SELECT '=== TEST 10: Top Selling Products ===' AS test;
SELECT 
    product_name,
    crust_type,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS revenue
FROM V_ORDER_ITEMS
WHERE order_date >= CURRENT_DATE() - 30
GROUP BY product_name, crust_type
ORDER BY revenue DESC
LIMIT 10;

-- ============================================================================
-- SUMMARY
-- ============================================================================
SELECT '=== DEMO READINESS SUMMARY ===' AS status;
SELECT 
    'Data Coverage' AS check_item,
    CASE WHEN MIN(order_date) <= CURRENT_DATE() - 300 THEN 'PASS' ELSE 'FAIL' END AS status,
    MIN(order_date)::STRING || ' to ' || MAX(order_date)::STRING AS details
FROM V_ORDERS
UNION ALL
SELECT 
    'Thin-Crust Data',
    CASE WHEN COUNT(*) > 1000 THEN 'PASS' ELSE 'FAIL' END,
    COUNT(*)::STRING || ' thin-crust items'
FROM V_ORDER_ITEMS WHERE crust_type = 'thin_crust'
UNION ALL
SELECT 
    'Chicago Stores',
    CASE WHEN COUNT(*) > 5000 THEN 'PASS' ELSE 'FAIL' END,
    COUNT(*)::STRING || ' Chicago orders'
FROM V_ORDERS WHERE city = 'Chicago'
UNION ALL
SELECT 
    'Documents Loaded',
    CASE WHEN (SELECT COUNT(*) FROM PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS) >= 6 THEN 'PASS' ELSE 'FAIL' END,
    (SELECT COUNT(*)::STRING FROM PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS) || ' documents'
UNION ALL
SELECT 
    'Future Dates (Friday Prep)',
    CASE WHEN MAX(date_key) >= CURRENT_DATE() + 7 THEN 'PASS' ELSE 'FAIL' END,
    'Calendar goes to ' || MAX(date_key)::STRING
FROM DIM_CALENDAR;

SELECT '=== ALL TESTS COMPLETE ===' AS status;
