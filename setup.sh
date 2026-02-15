#!/bin/bash
# ============================================================================
# Pizza Intelligence Demo - Quick Setup Script
# ============================================================================
# This script sets up the entire demo in one command.
#
# USAGE:
#   ./setup.sh <snowflake_connection_name>
#
# EXAMPLE:
#   ./setup.sh demo43
#
# PREREQUISITES:
#   - Snowflake CLI installed (snow)
#   - Valid connection in ~/.snowflake/connections.toml
#   - ACCOUNTADMIN role (or CREATE DATABASE privileges)
# ============================================================================

set -e  # Exit on error

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: ./setup.sh <snowflake_connection_name>"
    echo "Example: ./setup.sh demo43"
    exit 1
fi

CONNECTION=$1
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "Pizza Intelligence Demo Setup"
echo "Connection: $CONNECTION"
echo "============================================"

# Test connection
echo ""
echo "[1/11] Testing Snowflake connection..."
snow connection test -c "$CONNECTION"

# Run setup scripts in order
echo ""
echo "[2/11] Creating database and schemas..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/01_create_database.sql"

echo ""
echo "[3/11] Creating tables..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/02_create_tables.sql"

echo ""
echo "[4/11] Loading sample data (stores, products, customers)..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/03_load_sample_data.sql"

echo ""
echo "[5/11] Generating orders data (~50K orders)..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/04_load_orders_data.sql"

echo ""
echo "[6/11] Loading inventory and staffing data..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/05_load_inventory_staffing.sql"

echo ""
echo "[7/11] Setting up Cortex Search..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/06_setup_cortex_search.sql"

echo ""
echo "[8/11] Creating agent stage..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/07_create_agent.sql"

echo ""
echo "[9/11] Creating analytics views..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/08_create_views.sql"

echo ""
echo "[10/11] Refreshing calendar data..."
snow sql -c "$CONNECTION" -f "$SCRIPT_DIR/setup/09_refresh_data.sql"

echo ""
echo "[11/11] Uploading semantic model..."
snow stage copy "$SCRIPT_DIR/semantic_models/pizza_intelligence.yaml" \
    "@PIZZA_INTELLIGENCE.SEMANTIC_MODELS.SEMANTIC_MODEL_STAGE" \
    -c "$CONNECTION" --overwrite

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml"
echo "  2. Edit secrets.toml with your credentials"
echo "  3. Run the apps:"
echo "     streamlit run pizza_ops_assistant.py --server.port 8502"
echo "     streamlit run driver_app.py --server.port 8503"
echo "     streamlit run customer_app.py --server.port 8504"
echo ""
echo "To verify setup:"
echo "  snow sql -c $CONNECTION -f setup/10_test_demo_queries.sql"
echo ""
