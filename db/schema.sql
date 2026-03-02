-- =============================================================================
-- PIZZA OPERATIONS DATABASE SCHEMA
-- OLTP (Transactional) + OLAP (Analytics) Tables
-- =============================================================================

-- Use your own database (replace with your database name)
USE DATABASE PIZZA_INTELLIGENCE;

-- =============================================================================
-- SCHEMA: OLTP - Operational/Transactional Data
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS OLTP;
USE SCHEMA OLTP;

-- Customers table
CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(20),
    address VARCHAR(255),
    address_lat FLOAT,
    address_lon FLOAT,
    zone VARCHAR(50),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Drivers table
CREATE OR REPLACE TABLE DRIVERS (
    driver_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    vehicle_type VARCHAR(20) DEFAULT 'car', -- car, bike, scooter
    status VARCHAR(20) DEFAULT 'available', -- available, on_delivery, off_duty
    current_lat FLOAT,
    current_lon FLOAT,
    current_order_id VARCHAR(20),
    shift_start TIMESTAMP_NTZ,
    shift_end TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Menu items table
CREATE OR REPLACE TABLE MENU_ITEMS (
    item_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- pizza, sides, drinks, dessert
    price DECIMAL(10,2) NOT NULL,
    prep_time_min INT DEFAULT 10,
    is_available BOOLEAN DEFAULT TRUE
);

-- Orders table (main OLTP table)
CREATE OR REPLACE TABLE ORDERS (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES CUSTOMERS(customer_id),
    driver_id VARCHAR(20) REFERENCES DRIVERS(driver_id),
    
    -- Order details
    total_amount DECIMAL(10,2),
    item_count INT,
    
    -- Status tracking
    status VARCHAR(30) DEFAULT 'received', 
    -- received, preparing, ready, out_for_delivery, delivered, cancelled
    
    -- Timestamps
    order_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    kitchen_start_time TIMESTAMP_NTZ,
    ready_time TIMESTAMP_NTZ,
    dispatch_time TIMESTAMP_NTZ,
    delivery_time TIMESTAMP_NTZ,
    
    -- Delivery details
    delivery_address VARCHAR(255),
    delivery_lat FLOAT,
    delivery_lon FLOAT,
    delivery_zone VARCHAR(50),
    estimated_delivery_min INT,
    actual_delivery_min INT,
    
    -- Conditions at time of order
    weather_condition VARCHAR(30),
    traffic_condition VARCHAR(30), -- light, moderate, heavy
    
    -- Route optimization
    selected_route VARCHAR(500),
    route_distance_km DECIMAL(5,2),
    
    -- Delay tracking
    is_delayed BOOLEAN DEFAULT FALSE,
    delay_reason VARCHAR(100),
    delay_minutes INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Order items (line items)
CREATE OR REPLACE TABLE ORDER_ITEMS (
    order_item_id VARCHAR(30) PRIMARY KEY,
    order_id VARCHAR(20) REFERENCES ORDERS(order_id),
    item_id VARCHAR(20) REFERENCES MENU_ITEMS(item_id),
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    special_instructions VARCHAR(255),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Kitchen queue for processing
CREATE OR REPLACE TABLE KITCHEN_QUEUE (
    queue_id VARCHAR(30) PRIMARY KEY,
    order_id VARCHAR(20) REFERENCES ORDERS(order_id),
    priority INT DEFAULT 5, -- 1=highest, 10=lowest
    status VARCHAR(20) DEFAULT 'queued', -- queued, in_progress, completed
    station VARCHAR(20), -- prep, oven, packaging
    estimated_completion TIMESTAMP_NTZ,
    started_at TIMESTAMP_NTZ,
    completed_at TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- SCHEMA: ANALYTICS - OLAP/Analytical Data
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS ANALYTICS;
USE SCHEMA ANALYTICS;

-- Fact table: Completed deliveries
CREATE OR REPLACE TABLE FACT_DELIVERIES (
    delivery_id VARCHAR(30) PRIMARY KEY,
    order_id VARCHAR(20),
    customer_id VARCHAR(20),
    driver_id VARCHAR(20),
    
    -- Time dimensions
    delivery_date DATE,
    delivery_hour INT,
    day_of_week VARCHAR(10),
    is_weekend BOOLEAN,
    is_peak_hour BOOLEAN,
    
    -- Metrics
    order_amount DECIMAL(10,2),
    item_count INT,
    prep_time_min INT,
    delivery_time_min INT,
    total_time_min INT,
    
    -- Performance
    promised_time_min INT DEFAULT 35,
    is_on_time BOOLEAN,
    delay_minutes INT DEFAULT 0,
    delay_reason VARCHAR(100),
    
    -- Conditions
    weather_condition VARCHAR(30),
    traffic_condition VARCHAR(30),
    
    -- Route
    delivery_zone VARCHAR(50),
    route_distance_km DECIMAL(5,2),
    
    -- Points awarded
    points_earned INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension: Customers with loyalty info
CREATE OR REPLACE TABLE DIM_CUSTOMERS (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150),
    zone VARCHAR(50),
    
    -- Loyalty metrics
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0,
    total_points INT DEFAULT 0,
    loyalty_tier VARCHAR(20) DEFAULT 'Bronze', -- Bronze, Silver, Gold, Platinum
    
    -- Behavior
    avg_order_value DECIMAL(10,2),
    favorite_items VARCHAR(500),
    preferred_delivery_time VARCHAR(20),
    
    -- Status
    first_order_date DATE,
    last_order_date DATE,
    days_since_last_order INT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Customer loyalty points transactions
CREATE OR REPLACE TABLE CUSTOMER_LOYALTY (
    transaction_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20),
    order_id VARCHAR(20),
    
    -- Points
    points_type VARCHAR(30), -- order_complete, on_time_bonus, weather_patience, referral, redemption
    points_amount INT,
    points_balance_after INT,
    
    -- Tier changes
    tier_before VARCHAR(20),
    tier_after VARCHAR(20),
    tier_changed BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    transaction_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    notes VARCHAR(255)
);

-- Route performance analytics
CREATE OR REPLACE TABLE DIM_ROUTES (
    route_id VARCHAR(30) PRIMARY KEY,
    from_zone VARCHAR(50),
    to_zone VARCHAR(50),
    
    -- Performance
    total_deliveries INT DEFAULT 0,
    on_time_deliveries INT DEFAULT 0,
    late_deliveries INT DEFAULT 0,
    on_time_rate DECIMAL(5,2),
    
    -- Timing
    avg_delivery_time_min DECIMAL(5,1),
    min_delivery_time_min INT,
    max_delivery_time_min INT,
    
    -- Issues
    traffic_delays INT DEFAULT 0,
    weather_delays INT DEFAULT 0,
    address_issues INT DEFAULT 0,
    
    -- Recommendations
    best_time_to_deliver VARCHAR(50),
    alternate_route_suggestion VARCHAR(255),
    risk_level VARCHAR(20) DEFAULT 'low', -- low, medium, high
    
    -- Metadata
    last_updated TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Weather conditions log
CREATE OR REPLACE TABLE WEATHER_LOG (
    log_id VARCHAR(30) PRIMARY KEY,
    recorded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    condition VARCHAR(30), -- Sunny, Cloudy, Rainy, Snowy, Cold, Hot
    temperature_f INT,
    wind_speed_mph INT,
    precipitation_chance INT,
    impact_level VARCHAR(20) -- none, low, moderate, severe
);

-- =============================================================================
-- STREAMS FOR REAL-TIME CDC
-- =============================================================================

USE SCHEMA OLTP;

-- Stream on ORDERS to capture changes
CREATE OR REPLACE STREAM ORDERS_STREAM ON TABLE ORDERS
    APPEND_ONLY = FALSE
    SHOW_INITIAL_ROWS = FALSE;

-- Stream on completed orders for analytics
CREATE OR REPLACE STREAM COMPLETED_ORDERS_STREAM ON TABLE ORDERS
    APPEND_ONLY = FALSE
    SHOW_INITIAL_ROWS = FALSE;

-- =============================================================================
-- SEED DATA: Menu Items
-- =============================================================================

INSERT INTO MENU_ITEMS (item_id, name, category, price, prep_time_min) VALUES
    ('PIZ001', 'Classic Pepperoni', 'pizza', 18.99, 12),
    ('PIZ002', 'Margherita', 'pizza', 16.99, 10),
    ('PIZ003', 'BBQ Chicken', 'pizza', 21.99, 14),
    ('PIZ004', 'Veggie Garden', 'pizza', 17.99, 11),
    ('PIZ005', 'Meat Lovers', 'pizza', 23.99, 15),
    ('PIZ006', 'Hawaiian Paradise', 'pizza', 18.99, 11),
    ('PIZ007', 'Supreme Deluxe', 'pizza', 22.99, 14),
    ('PIZ008', 'Truffle Mushroom', 'pizza', 24.99, 14),
    ('PIZ009', 'Buffalo Chicken', 'pizza', 21.99, 13),
    ('PIZ010', 'Four Cheese', 'pizza', 19.99, 11),
    ('SID001', 'Garlic Breadsticks', 'sides', 6.99, 5),
    ('SID002', 'Buffalo Wings (8pc)', 'sides', 11.99, 12),
    ('SID003', 'Caesar Salad', 'sides', 8.99, 3),
    ('SID004', 'Stuffed Cheesy Bread', 'sides', 7.99, 7),
    ('SID005', 'Mozzarella Sticks (6pc)', 'sides', 8.99, 6),
    ('SID006', 'Potato Wedges', 'sides', 6.49, 8),
    ('SID007', 'Chicken Tenders (5pc)', 'sides', 9.99, 10),
    ('SID008', 'Mac & Cheese Bites', 'sides', 7.49, 6),
    ('SID009', 'Onion Rings', 'sides', 6.99, 6),
    ('DRK001', 'Coca-Cola (2L)', 'drinks', 3.99, 0),
    ('DRK002', 'Sprite (2L)', 'drinks', 3.99, 0),
    ('DRK003', 'Fanta Orange (2L)', 'drinks', 3.99, 0),
    ('DRK004', 'Dr Pepper (2L)', 'drinks', 3.99, 0),
    ('DRK005', 'Lemonade', 'drinks', 4.49, 0),
    ('DRK006', 'Lemon Iced Tea', 'drinks', 3.49, 0),
    ('DRK007', 'Bottled Water', 'drinks', 1.99, 0),
    ('DRK008', 'Root Beer (2L)', 'drinks', 3.99, 0),
    ('DES001', 'Chocolate Lava Cake', 'desserts', 7.99, 8),
    ('DES002', 'Cinnamon Twists', 'desserts', 5.99, 5),
    ('DES003', 'New York Cheesecake', 'desserts', 6.99, 0),
    ('DES004', 'Brownie Bites (6pc)', 'desserts', 6.49, 0),
    ('DES005', 'Cookie Dough Bites', 'desserts', 7.49, 5),
    ('DES006', 'Churros (4pc)', 'desserts', 5.99, 5),
    ('DES007', 'Apple Pie Bites', 'desserts', 5.49, 4);

-- =============================================================================
-- SEED DATA: Drivers
-- =============================================================================

INSERT INTO DRIVERS (driver_id, name, phone, vehicle_type, status, current_lat, current_lon) VALUES
    ('DRV001', 'Carlos Martinez', '312-555-0101', 'car', 'available', 41.8819, -87.6278),
    ('DRV002', 'Mike Thompson', '312-555-0102', 'car', 'available', 41.8819, -87.6278),
    ('DRV003', 'Sarah Lee', '312-555-0103', 'car', 'available', 41.8819, -87.6278),
    ('DRV004', 'David Kim', '312-555-0104', 'bike', 'available', 41.8819, -87.6278),
    ('DRV005', 'Emma Wilson', '312-555-0105', 'scooter', 'available', 41.8819, -87.6278);

-- =============================================================================
-- SEED DATA: Sample Customers
-- =============================================================================

INSERT INTO CUSTOMERS (customer_id, name, email, phone, address, address_lat, address_lon, zone) VALUES
    ('CUS001', 'John Smith', 'john.smith@email.com', '312-555-1001', '875 N Michigan Ave', 41.8988, -87.6234, 'Gold Coast'),
    ('CUS002', 'Lisa Park', 'lisa.park@email.com', '312-555-1002', '401 N Michigan Ave', 41.8902, -87.6244, 'Magnificent Mile'),
    ('CUS003', 'Robert Kim', 'robert.kim@email.com', '312-555-1003', '233 S Wacker Dr', 41.8789, -87.6359, 'West Loop'),
    ('CUS004', 'Amy Chen', 'amy.chen@email.com', '312-555-1004', '350 N Orleans St', 41.8882, -87.6375, 'River North'),
    ('CUS005', 'David Lee', 'david.lee@email.com', '312-555-1005', '111 E Wacker Dr', 41.8870, -87.6217, 'Streeterville'),
    ('CUS006', 'Nina Patel', 'nina.patel@email.com', '312-555-1006', '200 E Randolph St', 41.8850, -87.6195, 'Lakeshore East'),
    ('CUS007', 'Tom Wilson', 'tom.wilson@email.com', '312-555-1007', '1 N State St', 41.8823, -87.6278, 'Loop Core'),
    ('CUS008', 'Grace Liu', 'grace.liu@email.com', '312-555-1008', '77 W Jackson Blvd', 41.8780, -87.6298, 'Financial District'),
    ('CUS009', 'Kevin Brown', 'kevin.brown@email.com', '312-555-1009', '500 W Madison St', 41.8818, -87.6420, 'West Loop'),
    ('CUS010', 'Maria Santos', 'maria.santos@email.com', '312-555-1010', '161 E Chicago Ave', 41.8967, -87.6225, 'Streeterville');

-- =============================================================================
-- SEED DATA: Initialize DIM_CUSTOMERS
-- =============================================================================

USE SCHEMA ANALYTICS;

INSERT INTO DIM_CUSTOMERS (customer_id, name, email, zone, total_orders, total_spent, total_points, loyalty_tier)
SELECT 
    customer_id, 
    name, 
    email, 
    zone,
    0,
    0,
    0,
    'Bronze'
FROM OLTP.CUSTOMERS;

-- =============================================================================
-- SEED DATA: Initial Weather
-- =============================================================================

INSERT INTO WEATHER_LOG (log_id, condition, temperature_f, wind_speed_mph, precipitation_chance, impact_level) VALUES
    ('WTH001', 'Cold', 28, 15, 10, 'low');

COMMIT;
