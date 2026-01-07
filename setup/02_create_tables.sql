-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 2: Create Analytics Tables (QSR Master Schema)
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Stores dimension
CREATE OR REPLACE TABLE DIM_STORES (
    store_id            VARCHAR(10) PRIMARY KEY,
    store_name          VARCHAR(100),
    city                VARCHAR(50),
    state               VARCHAR(2),
    region              VARCHAR(20),
    district            VARCHAR(50),
    store_type          VARCHAR(20),      -- 'dine_in', 'delivery_only', 'hybrid'
    square_feet         INT,
    seating_capacity    INT,
    has_drive_thru      BOOLEAN,
    open_date           DATE,
    manager_name        VARCHAR(100),
    latitude            FLOAT,
    longitude           FLOAT,
    nearby_stadium      VARCHAR(100),     -- For event-based forecasting
    stadium_distance_km FLOAT
);

-- Products dimension
CREATE OR REPLACE TABLE DIM_PRODUCTS (
    product_id          VARCHAR(10) PRIMARY KEY,
    product_name        VARCHAR(100),
    category            VARCHAR(30),      -- 'pizza', 'sides', 'drinks', 'desserts'
    subcategory         VARCHAR(30),      -- 'thin_crust', 'pan', 'stuffed', etc.
    size                VARCHAR(10),      -- 'small', 'medium', 'large', 'family'
    base_price          DECIMAL(8,2),
    cost                DECIMAL(8,2),
    is_signature        BOOLEAN,
    is_seasonal         BOOLEAN,
    launch_date         DATE,
    calories            INT,
    prep_time_minutes   INT
);

-- Campaigns/Promotions dimension
CREATE OR REPLACE TABLE DIM_CAMPAIGNS (
    campaign_id         VARCHAR(10) PRIMARY KEY,
    campaign_name       VARCHAR(100),
    campaign_type       VARCHAR(30),      -- 'discount', 'bogo', 'bundle', 'loyalty'
    channel             VARCHAR(30),      -- 'app', 'email', 'sms', 'in_store', 'social'
    discount_percent    DECIMAL(5,2),
    discount_amount     DECIMAL(8,2),
    min_order_value     DECIMAL(8,2),
    start_date          DATE,
    end_date            DATE,
    target_segment      VARCHAR(50),      -- 'new_customers', 'lapsed', 'vip', 'all'
    budget              DECIMAL(12,2),
    status              VARCHAR(20)
);

-- Customers dimension
CREATE OR REPLACE TABLE DIM_CUSTOMERS (
    customer_id         VARCHAR(20) PRIMARY KEY,
    customer_segment    VARCHAR(30),      -- 'new', 'regular', 'vip', 'lapsed'
    loyalty_tier        VARCHAR(20),      -- 'bronze', 'silver', 'gold', 'platinum'
    loyalty_points      INT,
    signup_date         DATE,
    city                VARCHAR(50),
    state               VARCHAR(2),
    preferred_channel   VARCHAR(20),      -- 'app', 'web', 'phone', 'in_store'
    lifetime_orders     INT,
    lifetime_value      DECIMAL(12,2),
    avg_order_value     DECIMAL(8,2),
    last_order_date     DATE
);

-- Calendar dimension (for time-series analysis)
CREATE OR REPLACE TABLE DIM_CALENDAR (
    date_key            DATE PRIMARY KEY,
    day_of_week         VARCHAR(10),
    day_of_week_num     INT,
    is_weekend          BOOLEAN,
    week_of_year        INT,
    month_name          VARCHAR(10),
    month_num           INT,
    quarter             INT,
    year                INT,
    is_holiday          BOOLEAN,
    holiday_name        VARCHAR(50),
    is_game_day         BOOLEAN,          -- Local sports events
    game_event          VARCHAR(100),
    weather_condition   VARCHAR(30),      -- 'sunny', 'rainy', 'hot', 'cold'
    high_temp_f         INT,
    low_temp_f          INT
);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Orders fact table
CREATE OR REPLACE TABLE FACT_ORDERS (
    order_id            VARCHAR(20) PRIMARY KEY,
    order_date          DATE,
    order_timestamp     TIMESTAMP_NTZ,
    store_id            VARCHAR(10),
    customer_id         VARCHAR(20),
    campaign_id         VARCHAR(10),
    order_channel       VARCHAR(20),      -- 'app', 'web', 'phone', 'in_store', 'third_party'
    order_type          VARCHAR(20),      -- 'delivery', 'pickup', 'dine_in'
    subtotal            DECIMAL(10,2),
    discount_amount     DECIMAL(10,2),
    tax_amount          DECIMAL(10,2),
    delivery_fee        DECIMAL(8,2),
    tip_amount          DECIMAL(8,2),
    total_amount        DECIMAL(10,2),
    item_count          INT,
    is_first_order      BOOLEAN,
    payment_method      VARCHAR(20)
);

-- Order line items
CREATE OR REPLACE TABLE FACT_ORDER_ITEMS (
    order_item_id       VARCHAR(30) PRIMARY KEY,
    order_id            VARCHAR(20),
    product_id          VARCHAR(10),
    quantity            INT,
    unit_price          DECIMAL(8,2),
    line_total          DECIMAL(10,2),
    customizations      VARCHAR(500)      -- JSON-like string for toppings, etc.
);

-- Deliveries fact table
CREATE OR REPLACE TABLE FACT_DELIVERIES (
    delivery_id         VARCHAR(20) PRIMARY KEY,
    order_id            VARCHAR(20),
    store_id            VARCHAR(10),
    rider_id            VARCHAR(10),
    delivery_date       DATE,
    promised_time       TIMESTAMP_NTZ,
    actual_delivery_time TIMESTAMP_NTZ,
    prep_start_time     TIMESTAMP_NTZ,
    prep_end_time       TIMESTAMP_NTZ,
    dispatch_time       TIMESTAMP_NTZ,
    delivery_distance_km DECIMAL(6,2),
    delivery_duration_min INT,
    is_late             BOOLEAN,
    late_minutes        INT,
    late_reason         VARCHAR(100),     -- 'traffic', 'kitchen_delay', 'rider_shortage', etc.
    customer_rating     DECIMAL(2,1),
    delivery_notes      VARCHAR(500)
);

-- Inventory fact table
CREATE OR REPLACE TABLE FACT_INVENTORY (
    inventory_id        VARCHAR(20) PRIMARY KEY,
    store_id            VARCHAR(10),
    ingredient_name     VARCHAR(50),
    ingredient_category VARCHAR(30),      -- 'dough', 'cheese', 'toppings', 'sauces', 'packaging'
    snapshot_date       DATE,
    quantity_on_hand    DECIMAL(12,2),
    unit_of_measure     VARCHAR(20),
    reorder_point       DECIMAL(12,2),
    reorder_quantity    DECIMAL(12,2),
    unit_cost           DECIMAL(8,2),
    days_until_expiry   INT,
    wastage_units       DECIMAL(10,2),
    wastage_reason      VARCHAR(50)       -- 'expired', 'damaged', 'quality', 'overproduction'
);

-- Staffing fact table
CREATE OR REPLACE TABLE FACT_STAFFING (
    staffing_id         VARCHAR(20) PRIMARY KEY,
    store_id            VARCHAR(10),
    shift_date          DATE,
    shift_type          VARCHAR(20),      -- 'morning', 'afternoon', 'evening', 'night'
    scheduled_staff     INT,
    actual_staff        INT,
    kitchen_staff       INT,
    counter_staff       INT,
    riders_available    INT,
    overtime_hours      DECIMAL(6,2),
    labor_cost          DECIMAL(10,2)
);

-- Campaign performance fact table
CREATE OR REPLACE TABLE FACT_CAMPAIGN_PERFORMANCE (
    performance_id      VARCHAR(20) PRIMARY KEY,
    campaign_id         VARCHAR(10),
    store_id            VARCHAR(10),
    performance_date    DATE,
    impressions         INT,
    clicks              INT,
    redemptions         INT,
    orders_attributed   INT,
    revenue_attributed  DECIMAL(12,2),
    discount_cost       DECIMAL(12,2),
    incremental_revenue DECIMAL(12,2),
    roi_percent         DECIMAL(8,2)
);

SELECT 'All tables created successfully!' AS status;

