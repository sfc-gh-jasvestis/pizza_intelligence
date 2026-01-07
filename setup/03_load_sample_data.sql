-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 3: Load Sample Data
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- STORES DATA (15 stores across regions)
-- ============================================================================
INSERT INTO DIM_STORES VALUES
('STR001', 'Downtown Phoenix', 'Phoenix', 'AZ', 'Southwest', 'Phoenix Metro', 'hybrid', 3200, 45, true, '2018-03-15', 'Maria Rodriguez', 33.4484, -112.0740, 'State Farm Stadium', 15.2),
('STR002', 'Scottsdale North', 'Scottsdale', 'AZ', 'Southwest', 'Phoenix Metro', 'hybrid', 2800, 35, true, '2019-06-20', 'James Chen', 33.6225, -111.8580, 'State Farm Stadium', 22.5),
('STR003', 'Tempe University', 'Tempe', 'AZ', 'Southwest', 'Phoenix Metro', 'delivery_only', 1800, 0, false, '2020-08-10', 'Sarah Johnson', 33.4255, -111.9400, 'State Farm Stadium', 18.3),
('STR004', 'Chicago Loop', 'Chicago', 'IL', 'Midwest', 'Chicago Metro', 'hybrid', 4500, 80, false, '2015-04-01', 'Michael Brown', 41.8781, -87.6298, 'Soldier Field', 2.1),
('STR005', 'Chicago Wrigleyville', 'Chicago', 'IL', 'Midwest', 'Chicago Metro', 'dine_in', 3800, 65, false, '2016-07-15', 'Emily Davis', 41.9484, -87.6553, 'Wrigley Field', 0.8),
('STR006', 'Naperville', 'Naperville', 'IL', 'Midwest', 'Chicago Metro', 'hybrid', 2600, 40, true, '2021-02-28', 'David Wilson', 41.7508, -88.1535, 'Soldier Field', 45.2),
('STR007', 'Manhattan Midtown', 'New York', 'NY', 'Northeast', 'NYC Metro', 'delivery_only', 1500, 0, false, '2017-09-12', 'Jessica Lee', 40.7549, -73.9840, 'Madison Square Garden', 1.2),
('STR008', 'Brooklyn Heights', 'Brooklyn', 'NY', 'Northeast', 'NYC Metro', 'hybrid', 2200, 25, false, '2019-11-05', 'Robert Taylor', 40.6958, -73.9936, 'Barclays Center', 2.8),
('STR009', 'Queens Astoria', 'Queens', 'NY', 'Northeast', 'NYC Metro', 'hybrid', 2400, 30, false, '2020-03-20', 'Amanda Martinez', 40.7644, -73.9235, 'Citi Field', 5.5),
('STR010', 'LA Downtown', 'Los Angeles', 'CA', 'West', 'LA Metro', 'hybrid', 3500, 50, true, '2016-01-10', 'Kevin Anderson', 34.0522, -118.2437, 'Crypto.com Arena', 1.5),
('STR011', 'Santa Monica', 'Santa Monica', 'CA', 'West', 'LA Metro', 'dine_in', 4200, 70, false, '2017-05-25', 'Nicole Thompson', 34.0195, -118.4912, 'Crypto.com Arena', 22.3),
('STR012', 'Pasadena', 'Pasadena', 'CA', 'West', 'LA Metro', 'hybrid', 2900, 45, true, '2018-10-08', 'Christopher White', 34.1478, -118.1445, 'Rose Bowl', 3.2),
('STR013', 'Miami Beach', 'Miami', 'FL', 'Southeast', 'Miami Metro', 'hybrid', 3100, 55, false, '2019-04-15', 'Ashley Garcia', 25.7907, -80.1300, 'Hard Rock Stadium', 18.5),
('STR014', 'Coral Gables', 'Coral Gables', 'FL', 'Southeast', 'Miami Metro', 'dine_in', 3600, 60, false, '2020-01-20', 'Daniel Robinson', 25.7215, -80.2684, 'Hard Rock Stadium', 22.1),
('STR015', 'Fort Lauderdale', 'Fort Lauderdale', 'FL', 'Southeast', 'Miami Metro', 'hybrid', 2700, 40, true, '2021-06-30', 'Michelle Clark', 26.1224, -80.1373, 'Hard Rock Stadium', 35.8);

-- ============================================================================
-- PRODUCTS DATA
-- ============================================================================
INSERT INTO DIM_PRODUCTS VALUES
('PRD001', 'Classic Pepperoni', 'pizza', 'thin_crust', 'large', 18.99, 5.50, true, false, '2015-01-01', 850, 12),
('PRD002', 'Classic Pepperoni', 'pizza', 'thin_crust', 'medium', 14.99, 4.20, true, false, '2015-01-01', 620, 10),
('PRD003', 'Classic Pepperoni', 'pizza', 'thin_crust', 'family', 24.99, 7.80, true, false, '2015-01-01', 1200, 15),
('PRD004', 'Supreme Deluxe', 'pizza', 'pan', 'large', 22.99, 7.20, true, false, '2015-01-01', 980, 14),
('PRD005', 'Supreme Deluxe', 'pizza', 'pan', 'medium', 17.99, 5.50, true, false, '2015-01-01', 720, 12),
('PRD006', 'Margherita', 'pizza', 'thin_crust', 'large', 16.99, 4.80, false, false, '2015-01-01', 680, 10),
('PRD007', 'Margherita', 'pizza', 'thin_crust', 'medium', 12.99, 3.60, false, false, '2015-01-01', 510, 8),
('PRD008', 'BBQ Chicken', 'pizza', 'stuffed', 'large', 21.99, 6.90, true, false, '2016-03-15', 920, 14),
('PRD009', 'Veggie Garden', 'pizza', 'thin_crust', 'large', 17.99, 5.20, false, false, '2015-01-01', 580, 11),
('PRD010', 'Meat Lovers', 'pizza', 'pan', 'large', 23.99, 8.10, true, false, '2015-01-01', 1150, 15),
('PRD011', 'Hawaiian Paradise', 'pizza', 'thin_crust', 'large', 18.99, 5.60, false, false, '2015-01-01', 780, 11),
('PRD012', 'Garlic Breadsticks', 'sides', 'breadsticks', 'regular', 6.99, 1.80, false, false, '2015-01-01', 320, 5),
('PRD013', 'Buffalo Wings (8pc)', 'sides', 'wings', 'regular', 11.99, 4.20, true, false, '2015-01-01', 580, 12),
('PRD014', 'Caesar Salad', 'sides', 'salad', 'regular', 8.99, 2.50, false, false, '2015-01-01', 220, 3),
('PRD015', 'Coca-Cola (2L)', 'drinks', 'soda', 'large', 3.99, 1.20, false, false, '2015-01-01', 0, 0),
('PRD016', 'Sprite (2L)', 'drinks', 'soda', 'large', 3.99, 1.20, false, false, '2015-01-01', 0, 0),
('PRD017', 'Chocolate Lava Cake', 'desserts', 'cake', 'regular', 7.99, 2.10, true, false, '2017-06-01', 450, 8),
('PRD018', 'Cinnamon Twists', 'desserts', 'pastry', 'regular', 5.99, 1.50, false, false, '2015-01-01', 280, 5),
('PRD019', 'Family Combo Deal', 'pizza', 'combo', 'family', 44.99, 14.50, true, false, '2018-01-01', 2200, 20),
('PRD020', 'Summer Slice Special', 'pizza', 'thin_crust', 'large', 15.99, 4.50, false, true, '2025-06-01', 720, 11);

-- ============================================================================
-- CAMPAIGNS DATA
-- ============================================================================
INSERT INTO DIM_CAMPAIGNS VALUES
('CMP001', 'Game Day Feast', 'bundle', 'app', 15.00, NULL, 30.00, '2025-09-01', '2026-02-28', 'all', 50000.00, 'active'),
('CMP002', 'First Order Free Delivery', 'discount', 'app', NULL, 5.00, 15.00, '2025-01-01', '2026-12-31', 'new_customers', 100000.00, 'active'),
('CMP003', 'Loyalty Double Points', 'loyalty', 'all', NULL, NULL, NULL, '2025-11-01', '2025-12-31', 'vip', 25000.00, 'completed'),
('CMP004', 'Tuesday 2-for-1', 'bogo', 'all', 50.00, NULL, 20.00, '2025-01-01', '2026-12-31', 'all', 75000.00, 'active'),
('CMP005', 'Sun & Slice Summer', 'bundle', 'email', 20.00, NULL, 25.00, '2025-06-15', '2025-08-31', 'all', 40000.00, 'completed'),
('CMP006', 'Back to School Bundle', 'bundle', 'sms', 18.00, NULL, 35.00, '2025-08-15', '2025-09-15', 'regular', 30000.00, 'completed'),
('CMP007', 'Holiday Feast Special', 'bundle', 'all', 25.00, NULL, 50.00, '2025-12-15', '2026-01-05', 'all', 80000.00, 'active'),
('CMP008', 'Thin Crust Thursday', 'discount', 'app', 12.00, NULL, 15.00, '2025-01-01', '2026-12-31', 'all', 35000.00, 'active'),
('CMP009', 'Lapsed Customer Win-Back', 'discount', 'email', 30.00, NULL, 20.00, '2025-10-01', '2025-12-31', 'lapsed', 45000.00, 'active'),
('CMP010', 'Super Bowl Sunday', 'bundle', 'all', 20.00, NULL, 40.00, '2026-02-01', '2026-02-09', 'all', 100000.00, 'planned');

-- ============================================================================
-- CALENDAR DATA (2025-2026)
-- ============================================================================
-- Generate calendar with events and weather patterns
INSERT INTO DIM_CALENDAR
WITH date_series AS (
    SELECT DATEADD(day, seq4(), '2025-01-01'::DATE) AS date_key
    FROM TABLE(GENERATOR(ROWCOUNT => 730))  -- ~2 years
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
    -- Game days (Sundays in fall = NFL, plus some random events)
    CASE 
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) BETWEEN 9 AND 12 THEN true
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) IN (1, 2) THEN true
        WHEN MONTH(date_key) = 2 AND DAY(date_key) BETWEEN 7 AND 14 AND DAYOFWEEK(date_key) = 0 THEN true  -- Super Bowl
        ELSE false
    END AS is_game_day,
    CASE 
        WHEN MONTH(date_key) = 2 AND DAY(date_key) BETWEEN 7 AND 14 AND DAYOFWEEK(date_key) = 0 THEN 'Super Bowl'
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) BETWEEN 9 AND 12 THEN 'NFL Sunday'
        WHEN DAYOFWEEK(date_key) = 0 AND MONTH(date_key) IN (1, 2) THEN 'NFL Playoffs'
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
FROM date_series
WHERE date_key < '2027-01-01';

-- ============================================================================
-- CUSTOMERS DATA (sample of 500 customers)
-- ============================================================================
INSERT INTO DIM_CUSTOMERS
SELECT 
    'CUST' || LPAD(seq4()::STRING, 6, '0') AS customer_id,
    CASE MOD(seq4(), 4)
        WHEN 0 THEN 'new'
        WHEN 1 THEN 'regular'
        WHEN 2 THEN 'vip'
        ELSE 'lapsed'
    END AS customer_segment,
    CASE MOD(seq4(), 4)
        WHEN 0 THEN 'bronze'
        WHEN 1 THEN 'silver'
        WHEN 2 THEN 'gold'
        ELSE 'platinum'
    END AS loyalty_tier,
    MOD(seq4() * 127, 50000) AS loyalty_points,
    DATEADD(day, -MOD(seq4() * 17, 1000), CURRENT_DATE()) AS signup_date,
    CASE MOD(seq4(), 5)
        WHEN 0 THEN 'Phoenix'
        WHEN 1 THEN 'Chicago'
        WHEN 2 THEN 'New York'
        WHEN 3 THEN 'Los Angeles'
        ELSE 'Miami'
    END AS city,
    CASE MOD(seq4(), 5)
        WHEN 0 THEN 'AZ'
        WHEN 1 THEN 'IL'
        WHEN 2 THEN 'NY'
        WHEN 3 THEN 'CA'
        ELSE 'FL'
    END AS state,
    CASE MOD(seq4(), 4)
        WHEN 0 THEN 'app'
        WHEN 1 THEN 'web'
        WHEN 2 THEN 'phone'
        ELSE 'in_store'
    END AS preferred_channel,
    MOD(seq4() * 13, 150) + 1 AS lifetime_orders,
    (MOD(seq4() * 13, 150) + 1) * (25 + MOD(seq4(), 30)) AS lifetime_value,
    25 + MOD(seq4(), 30) AS avg_order_value,
    DATEADD(day, -MOD(seq4() * 7, 90), CURRENT_DATE()) AS last_order_date
FROM TABLE(GENERATOR(ROWCOUNT => 500));

SELECT 'Dimension tables loaded successfully!' AS status;

