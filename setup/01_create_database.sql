-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 1: Create Database and Schemas
-- ============================================================================

-- Create the Pizza Intelligence database
CREATE DATABASE IF NOT EXISTS PIZZA_INTELLIGENCE;

USE DATABASE PIZZA_INTELLIGENCE;

-- Create schemas for organized data management
CREATE SCHEMA IF NOT EXISTS RAW_DATA;           -- Raw ingested data
CREATE SCHEMA IF NOT EXISTS ANALYTICS;          -- Transformed analytics tables
CREATE SCHEMA IF NOT EXISTS DOCUMENTS;          -- Unstructured document storage
CREATE SCHEMA IF NOT EXISTS SEMANTIC_MODELS;    -- Cortex Analyst semantic models
CREATE SCHEMA IF NOT EXISTS AGENTS;             -- Agent configurations

-- Grant usage (adjust roles as needed for your environment)
-- GRANT USAGE ON DATABASE PIZZA_INTELLIGENCE TO ROLE <your_role>;
-- GRANT USAGE ON ALL SCHEMAS IN DATABASE PIZZA_INTELLIGENCE TO ROLE <your_role>;

SELECT 'Pizza Intelligence database created successfully!' AS status;

