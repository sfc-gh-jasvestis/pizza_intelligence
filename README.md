# Pizza Intelligence Demo

## Snowflake Cortex Demo for QSR Operations

A comprehensive demo showcasing **Snowflake Cortex** capabilities for Quick Service Restaurant (QSR) operations, featuring:
- **Ops Dashboard** - AI-powered operations assistant with Cortex Analyst
- **Customer App** - Mobile-friendly ordering interface
- **Driver App** - Real-time delivery tracking with traffic visualization

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

# Run setup scripts in order (01-09)
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

```bash
# Install dependencies
pip install streamlit pydeck requests

# Run all three apps
streamlit run pizza_ops_assistant.py --server.port 8502  # Ops Dashboard
streamlit run driver_app.py --server.port 8503           # Driver App
streamlit run customer_app.py --server.port 8504         # Customer App
```

---

## Repository Structure

```
pizza/
├── README.md                    # This file
├── DEMO_SCRIPT.md              # Step-by-step demo walkthrough
│
├── # STREAMLIT APPS
├── pizza_ops_assistant.py      # Ops Dashboard (port 8502)
├── driver_app.py               # Driver delivery app (port 8503)
├── customer_app.py             # Customer ordering app (port 8504)
├── menu_data.py                # Shared menu data (synced with Snowflake)
├── shared_state.py             # Cross-app state management
│
├── # SNOWFLAKE SETUP
├── setup/
│   ├── 01_create_database.sql  # Create PIZZA_INTELLIGENCE database
│   ├── 02_create_tables.sql    # Create dimension and fact tables
│   ├── 03_load_sample_data.sql # Load stores, products, customers
│   ├── 04_load_orders_data.sql # Generate 50K+ orders
│   ├── 05_load_inventory_staffing.sql # Inventory and staffing data
│   ├── 06_setup_cortex_search.sql # Configure Cortex Search service
│   ├── 07_create_agent.sql     # Create semantic model stage
│   ├── 08_create_views.sql     # Create pre-joined views
│   ├── 09_refresh_data.sql     # Refresh calendar data
│   ├── 10_test_demo_queries.sql # Verify setup
│   └── 11_add_game_day_data.sql # Optional: Add game day variations
│
├── semantic_models/
│   └── pizza_intelligence.yaml # Cortex Analyst semantic model
│
├── services/                   # Backend services for ops app
│   ├── weather_service.py
│   ├── kitchen_service.py
│   ├── driver_dispatch.py
│   └── database.py
│
├── config/
│   └── settings.py
│
└── .streamlit/
    └── secrets.toml.example    # Template for credentials
```

---

## The Three Apps

### 1. Ops Dashboard (port 8502)
**URL:** http://localhost:8502

The main operations interface for store managers:
- **Live Orders** - Real-time order tracking through kitchen → dispatch → delivery
- **Chat Assistant** - Natural language queries via Cortex Analyst
- **Dashboard** - Historical analytics and delivery performance

### 2. Driver App (port 8503)
**URL:** http://localhost:8503

Mobile-friendly delivery driver interface:
- Real-time route visualization with OSRM routing
- Traffic hotspot awareness
- Order pickup and delivery workflow
- ETA tracking

### 3. Customer App (port 8504)
**URL:** http://localhost:8504

Customer ordering interface:
- Menu with real food images
- Shopping cart
- Order tracking with live driver location
- Rating and tipping

---

## Data Consistency

All apps share consistent data aligned with Snowflake:

| Data | Source | Snowflake Table |
|------|--------|-----------------|
| Menu Items | `menu_data.py` | `DIM_PRODUCTS` |
| Store Location | `menu_data.py` | `DIM_STORES` (Chicago Loop) |
| Order IDs | `ORD-{5-digit}` | `FACT_ORDERS` |
| Drivers | `menu_data.py` | (simulated) |

### Menu Items (from DIM_PRODUCTS)
| Item | Price | Prep Time |
|------|-------|-----------|
| Classic Pepperoni | $18.99 | 12 min |
| Margherita | $16.99 | 10 min |
| BBQ Chicken | $21.99 | 14 min |
| Veggie Garden | $17.99 | 11 min |
| Meat Lovers | $23.99 | 15 min |
| Hawaiian Paradise | $18.99 | 11 min |
| Supreme Deluxe | $22.99 | 14 min |

---

## Demo Script Highlights

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the full walkthrough.

### Key Demo Questions (Cortex Analyst)

1. **Capacity Analysis**
   > "Show me the capacity gap by city for last Friday"

2. **Delivery Performance**
   > "Which stores had the highest late delivery rates last Friday?"

3. **Revenue Impact**
   > "How much revenue are we losing with kitchen capacity issues?"

4. **Crisis Dashboard**
   > "Which stores are in crisis mode right now?"

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

### Apps Not Syncing
1. Delete the state file: `rm .pizza_demo_state.json`
2. Restart all three apps
3. Create a test order in the customer app

---

## Configuration

### Environment Variables (Optional)
| Variable | Description |
|----------|-------------|
| `SNOWFLAKE_CONNECTION_NAME` | Connection name from `~/.snowflake/connections.toml` |
| `ORS_API_KEY` | OpenRouteService API key for routing (optional) |

### Store Location
All apps use Chicago Loop as the default store:
- **Latitude:** 41.8827
- **Longitude:** -87.6233
- **Name:** Chicago Loop Pizza

---

**Built for Snowflake Cortex Demo**  
*Chicago Loop Pizza Operations*
