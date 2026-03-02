#!/bin/bash
# ============================================================================
# Pizza Intelligence Demo - Run All Apps
# ============================================================================
# Starts all three Streamlit apps on their designated ports.
#
# USAGE:
#   ./run_apps.sh
#
# PORTS:
#   - Ops Dashboard:  http://localhost:8510
#   - Customer App:   http://localhost:8511
#   - Driver App:     http://localhost:8512
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "Pizza Intelligence Demo"
echo "============================================"
echo ""

# Kill any existing streamlit processes
echo "Stopping any existing Streamlit apps..."
pkill -f streamlit 2>/dev/null || true
sleep 1

# Clear old state
rm -f "$SCRIPT_DIR/.pizza_demo_state.json"

echo ""
echo "Starting apps..."
echo ""

# Start all apps in background
streamlit run "$SCRIPT_DIR/pizza_ops_assistant.py" --server.port 8510 --server.headless true &
streamlit run "$SCRIPT_DIR/customer_app.py" --server.port 8511 --server.headless true &
streamlit run "$SCRIPT_DIR/driver_app.py" --server.port 8512 --server.headless true &

sleep 3

echo "============================================"
echo "Apps Running:"
echo "  Ops Dashboard:  http://localhost:8510"
echo "  Customer App:   http://localhost:8511"
echo "  Driver App:     http://localhost:8512"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all apps"
echo ""

# Wait for user interrupt
wait
