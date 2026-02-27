# Pizza Intelligence Demo

## Snowflake Cortex Demo for QSR Operations

A comprehensive demo showcasing **Snowflake Cortex** capabilities for Quick Service Restaurant (QSR) operations, featuring:
- **Ops Dashboard** — AI Co-Pilot with Cortex Analyst, demand forecasting, anomaly detection, and live order tracking
- **Customer App** — Mobile-friendly ordering with Party Bundle Assistant
- **Driver App** — Real-time delivery tracking with late-delivery cheat sheets

---

## Quick Start (5 minutes)

### Prerequisites
- Snowflake account with Cortex enabled (ACCOUNTADMIN role recommended)
- Python 3.9+ with Streamlit installed
- Snowflake CLI (`snow`) for easy deployment

### Step 1: Set Up Snowflake Database

```bash
# Connect to your Snowflake account
snow connection test -c <your_connection>

# Run the all-in-one setup script
snow sql -c <your_connection> -f setup/00_run_all_setup.sql

# Or run setup scripts individually (01-09)
snow sql -c <your_connection> -f setup/01_create_database.sql
snow sql -c <your_connection> -f setup/02_create_tables.sql
snow sql -c <your_connection> -f setup/03_load_sample_data.sql
snow sql -c <your_connection> -f setup/04_load_orders_data.sql
snow sql -c <your_connection> -f setup/05_load_inventory_staffing.sql
snow sql -c <your_connection> -f setup/06_setup_cortex_search.sql
snow sql -c <your_connection> -f setup/07_create_agent.sql
snow sql -c <your_connection> -f setup/08_create_views.sql
snow sql -c <your_connection> -f setup/09_refresh_data.sql

# Verify setup
snow sql -c <your_connection> -f setup/10_test_demo_queries.sql
```

### Step 2: Upload Semantic Model

```bash
# Upload the semantic model YAML to Snowflake stage
snow stage copy semantic_models/pizza_intelligence.yaml \
  @PIZZA_INTELLIGENCE.SEMANTIC_MODELS.SEMANTIC_MODEL_STAGE \
  -c <your_connection>
```

Or via SQL:
```sql
PUT file:///path/to/pizza_intelligence.yaml 
    @PIZZA_INTELLIGENCE.SEMANTIC_MODELS.SEMANTIC_MODEL_STAGE
    AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

### Step 3: Configure Credentials

```bash
# Copy the example secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit with your credentials
```

Example `.streamlit/secrets.toml`:
```toml
[connections.snowflake]
account = "YOUR_ACCOUNT"
user = "YOUR_USER"
password = "YOUR_PASSWORD"
warehouse = "COMPUTE_WH"
database = "PIZZA_INTELLIGENCE"
schema = "ANALYTICS"
role = "ACCOUNTADMIN"
```

### Step 4: Run the Apps

**Option A: Docker (recommended)**

```bash
# Build and run all three apps
docker build -f Dockerfile.ops -t pizza-ops .
docker build -f Dockerfile.customer -t pizza-customer .
docker build -f Dockerfile.driver -t pizza-driver .

# Run with shared state volume
mkdir -p shared_state
docker run -d -p 8510:8501 -v $(pwd)/shared_state:/shared_state \
  -e PIZZA_STATE_FILE=/shared_state/.pizza_unified_state.json pizza-ops
docker run -d -p 8511:8501 -v $(pwd)/shared_state:/shared_state \
  -e PIZZA_STATE_FILE=/shared_state/.pizza_unified_state.json pizza-customer
docker run -d -p 8512:8501 -v $(pwd)/shared_state:/shared_state \
  -e PIZZA_STATE_FILE=/shared_state/.pizza_unified_state.json pizza-driver
```

**Option B: Run locally**

```bash
# Install dependencies
pip install -r requirements.txt

# Run all three apps (each in a separate terminal)
streamlit run pizza_ops_assistant.py --server.port 8510
streamlit run customer_app.py --server.port 8511
streamlit run driver_app.py --server.port 8512
```

| App | URL |
|-----|-----|
| Ops Dashboard | http://localhost:8510 |
| Customer App | http://localhost:8511 |
| Driver App | http://localhost:8512 |

---

## Repository Structure

```
pizza/
├── README.md                    # This file
├── DEMO_SCRIPT.md              # Step-by-step demo walkthrough
├── requirements.txt            # Python dependencies
│
├── # DOCKERFILES
├── Dockerfile.ops              # Ops Dashboard container
├── Dockerfile.customer         # Customer App container
├── Dockerfile.driver           # Driver App container
│
├── # STREAMLIT APPS
├── pizza_ops_assistant.py      # Ops Dashboard + AI Co-Pilot
├── customer_app.py             # Customer ordering app
├── driver_app.py               # Driver delivery app
├── menu_data.py                # Shared menu data (synced with Snowflake DIM_PRODUCTS)
├── unified_state.py            # Cross-app state management (shared JSON file)
├── shared_state.py             # Legacy state helpers
├── shared_routes.py            # OSRM route fetching and caching
│
├── # BACKEND SERVICES (used by Ops app)
├── services/
│   ├── database.py             # In-memory order database
│   ├── analytics_pipeline.py   # Delivery analytics pipeline
│   ├── kitchen_service.py      # Kitchen simulation
│   ├── driver_dispatch.py      # Driver assignment logic
│   ├── order_simulator.py      # Auto-generate demo orders
│   ├── weather_service.py      # Weather simulation
│   └── persistence.py          # State persistence
│
├── config/
│   └── settings.py             # App configuration (map colors, store config)
│
├── # SNOWFLAKE SETUP
├── setup/
│   ├── 00_run_all_setup.sql    # All-in-one setup runner
│   ├── 01_create_database.sql  # Create PIZZA_INTELLIGENCE database
│   ├── 02_create_tables.sql    # Create dimension and fact tables
│   ├── 03_load_sample_data.sql # Load stores, products, customers, campaigns
│   ├── 04_load_orders_data.sql # Generate 50K+ orders with realistic patterns
│   ├── 05_load_inventory_staffing.sql # Inventory and staffing data
│   ├── 06_setup_cortex_search.sql     # Configure Cortex Search service
│   ├── 07_create_agent.sql     # Create semantic model stage
│   ├── 08_create_views.sql     # Create pre-joined analytics views
│   ├── 09_refresh_data.sql     # Refresh calendar and recent data
│   ├── 10_test_demo_queries.sql # Verify setup with test queries
│   └── 11_add_game_day_data.sql # Optional: Add game day variations
│
├── semantic_models/
│   └── pizza_intelligence.yaml # Cortex Analyst semantic model
│
└── .streamlit/
    ├── secrets.toml.example    # Template for credentials
    └── secrets.toml            # Your credentials (git-ignored)
```

---

## The Three Apps

### 1. Ops Dashboard (port 8510)
**URL:** http://localhost:8510

The main operations interface for store managers, with two views:

**Live Orders** — Real-time order pipeline from kitchen to delivery, interactive map with driver routes, and a Capacity vs Demand chart (Altair) showing kitchen utilization over the last 7 days.

**AI Co-Pilot** — Unified conversational interface combining:
- **Quick Actions** — Shift Brief (with Kitchen Prep Checklist), Demand Forecast, Anomaly Scan
- **Chat** — Natural language queries via Cortex Analyst + Cortex Search
- **Suggested Questions** — Delivery performance, promo recommendations, customer feedback

**Sidebar** — Live Intelligence Ticker showing thin crust capacity, kitchen utilization, and worst-store late delivery % from Snowflake.

### 2. Customer App (port 8511)
**URL:** http://localhost:8511

Customer ordering interface:
- Full menu with real food images and shopping cart
- **Party Bundle Assistant** — Describe your event (e.g., "Game day with 8 friends") and get themed bundle suggestions with pricing
- Order tracking with live driver location on map
- Rating and tipping after delivery

### 3. Driver App (port 8512)
**URL:** http://localhost:8512

Mobile-friendly delivery driver interface:
- Real-time route visualization with OSRM routing
- Order pickup and delivery workflow with ETA tracking
- **Late-Delivery Cheat Sheet** — Zone-specific routing tips shown as high-contrast notification when delivery is running late
- Delivery celebration screen on completion

---

## Cross-App Communication

All three apps share state through a common JSON file (`.pizza_unified_state.json`). When running in Docker, this is mounted as a shared volume so orders placed in the Customer App appear in the Ops Dashboard and are assigned to drivers in the Driver App.

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `PIZZA_STATE_FILE` | Path to shared state JSON file | `.pizza_unified_state.json` (local) |

---

## Semantic Model

The `pizza_intelligence.yaml` semantic model includes:
- **10 tables** — orders, deliveries, stores, products, campaigns, campaign_performance, inventory, staffing, calendar, customers, kitchen_capacity, order_items
- **Custom Instructions** — AI speaks as "Pizza Intelligence Director" with strategic tone; flags capacity < 80% as critical; applies lost-revenue formula
- **Synonym Saturation** — Natural queries like "what dough type sells best?" or "show me recent orders" work out of the box
- **30+ Verified Queries** — Pre-validated SQL for common questions (sales analysis, delivery performance, capacity gaps, promo recommendations)
- **Capacity Utilization** measure — `(actual_pizzas_made / max_pizzas_per_hour) * 100`

---

## Data Consistency

All apps share consistent data aligned with Snowflake:

| Data | Source | Snowflake Table |
|------|--------|-----------------|
| Menu Items | `menu_data.py` | `DIM_PRODUCTS` |
| Store Location | `menu_data.py` | `DIM_STORES` (Chicago Loop) |
| Order IDs | `ORD-{5-digit}` sequential | `FACT_ORDERS` |
| Drivers | `menu_data.py` | (simulated) |

---

## Demo Script Highlights

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the full walkthrough.

### Key Demo Questions (Snowflake Intelligence)

1. **Capacity Analysis** — "Show me the capacity gap by city for last Friday"
2. **Delivery Performance** — "Which stores had the highest late delivery rates last Friday?"
3. **Revenue Impact** — "How much revenue are we losing with kitchen capacity issues?"
4. **Crisis Dashboard** — "Which stores are in crisis mode right now?"
5. **Promo Recommendations** — "How does weather impact sales at Chicago Loop? What promos work for each weather type?"

---

## Troubleshooting

### Database Setup Issues
```bash
# Verify database exists
snow sql -c <connection> -q "SHOW DATABASES LIKE 'PIZZA%'"

# Check tables have data
snow sql -c <connection> -f setup/10_test_demo_queries.sql
```

### App Connection Issues
1. Verify `.streamlit/secrets.toml` has correct credentials
2. Check warehouse is running: `snow sql -q "SELECT CURRENT_WAREHOUSE()"`
3. Ensure user has access to PIZZA_INTELLIGENCE database

### Apps Not Syncing (orders not appearing across apps)
1. Ensure all apps point to the same state file via `PIZZA_STATE_FILE`
2. For Docker: verify the shared volume is mounted to all three containers
3. For local: all apps should run from the same directory
4. Delete state and restart: `rm .pizza_unified_state.json` then restart all apps

---

## Configuration

### Environment Variables
| Variable | Description |
|----------|-------------|
| `PIZZA_STATE_FILE` | Path to shared state JSON file |
| `ORS_API_KEY` | OpenRouteService API key for routing (optional) |

### Store Location
All apps use Chicago Loop as the default store:
- **Latitude:** 41.8827
- **Longitude:** -87.6233
- **Name:** Chicago Loop Pizza

---

**Built for Snowflake Cortex Demo**  
*Chicago Loop Pizza Operations*
