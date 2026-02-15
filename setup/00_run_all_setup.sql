-- ============================================================================
-- PIZZA INTELLIGENCE DEMO - COMPLETE SETUP SCRIPT
-- ============================================================================
-- This single script runs all setup steps in order.
-- 
-- PREREQUISITES:
--   1. ACCOUNTADMIN role (or role with CREATE DATABASE privileges)
--   2. A warehouse to run the scripts (e.g., COMPUTE_WH)
--
-- USAGE:
--   1. Open this file in Snowsight or your SQL client
--   2. Execute the entire script
--   3. After completion, upload the semantic model YAML (see Step 7)
--
-- ESTIMATED TIME: ~5 minutes
-- ============================================================================

-- Set your warehouse
USE WAREHOUSE COMPUTE_WH;  -- Change this to your warehouse name

-- ============================================================================
-- STEP 1: Create Database and Schemas (from 01_create_database.sql)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS PIZZA_INTELLIGENCE;
USE DATABASE PIZZA_INTELLIGENCE;

CREATE SCHEMA IF NOT EXISTS RAW_DATA;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
CREATE SCHEMA IF NOT EXISTS DOCUMENTS;
CREATE SCHEMA IF NOT EXISTS SEMANTIC_MODELS;
CREATE SCHEMA IF NOT EXISTS AGENTS;

-- ============================================================================
-- STEP 2: Run individual setup scripts in order
-- ============================================================================
-- Execute each script in sequence. In Snowsight, you can run each file:
--   setup/02_create_tables.sql
--   setup/03_load_sample_data.sql
--   setup/04_load_orders_data.sql
--   setup/05_load_inventory_staffing.sql
--   setup/06_setup_cortex_search.sql
--   setup/07_create_agent.sql
--   setup/08_create_views.sql
--   setup/09_refresh_data.sql
--   setup/11_add_game_day_data.sql

-- ============================================================================
-- VERIFICATION: Run after all scripts complete
-- ============================================================================
-- Execute setup/10_test_demo_queries.sql to verify everything is working

SELECT 'Setup script executed. Run individual SQL files 02-09 in order.' AS status;
