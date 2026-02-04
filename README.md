# Pizza Intelligence Demo

## Snowflake Cortex Demo for QSR Operations

A demo showcasing **Snowflake Cortex** capabilities for Quick Service Restaurant (QSR) operations, featuring a single-store Pizza Operations Assistant for the **Chicago Loop** location.

---

## What This Demo Shows

| Feature | Description |
|---------|-------------|
| **Cortex Analyst** | Natural language queries against structured sales, delivery, and operations data |
| **Cortex Search** | Semantic search across customer reviews, audits, and feedback documents |
| **Live Orders Pipeline** | Real-time order simulation with kitchen, dispatch, and delivery tracking |
| **Weather-Based Routing** | Dynamic route recommendations based on weather conditions |

---

## Repository Structure

```
pizza/
├── README.md                    # This file
├── DEMO_SCRIPT.md              # Step-by-step demo walkthrough
├── pizza_ops_assistant.py      # Main Streamlit app
├── services/                    # Pipeline services
│   ├── weather_service.py      # Weather simulation
│   ├── kitchen_service.py      # Kitchen order processing
│   ├── driver_dispatch.py      # Delivery dispatch
│   ├── order_simulator.py      # Order generation
│   └── database.py             # In-memory order database
├── config/
│   └── settings.py             # Configuration settings
├── setup/                       # SQL setup scripts (run in order)
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_load_sample_data.sql
│   ├── 04_load_orders_data.sql
│   ├── 05_load_inventory_staffing.sql
│   ├── 06_setup_cortex_search.sql
│   ├── 07_create_agent.sql
│   ├── 08_create_views.sql
│   ├── 09_refresh_data.sql
│   └── 10_test_demo_queries.sql
├── semantic_models/
│   └── pizza_intelligence.yaml  # Semantic model with verified queries
├── .streamlit/
│   └── secrets.toml.example     # Template for credentials
└── documents/                   # Sample unstructured documents
    ├── invoices/
    ├── audits/
    └── feedback/
```

---

## Quick Start

### Prerequisites
- Snowflake account with Cortex enabled
- Python 3.9+
- Streamlit

### Step 1: Run SQL Setup Scripts

Execute the SQL scripts in order in Snowsight:

```sql
-- Run each script in sequence (01 through 10)
```

### Step 2: Upload Semantic Model

```sql
PUT file:///path/to/pizza_intelligence.yaml 
    @PIZZA_INTELLIGENCE.SEMANTIC_MODELS.SEMANTIC_MODEL_STAGE
    AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

### Step 3: Configure and Run the App

```bash
# Copy secrets template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit secrets.toml with your Snowflake credentials
# Then run:
streamlit run pizza_ops_assistant.py
```

---

## Demo Flow

### 1. Live Orders View
Start here to show the real-time operations dashboard:
- Click **New Order** to generate orders
- Watch orders flow through: Received → Kitchen → Ready → Delivery
- See weather-based route advisories
- Toggle **Auto-refresh** to see live updates

### 2. Chat Assistant
Switch to Chat to demonstrate Cortex capabilities:

| Sample Question | What It Shows |
|-----------------|---------------|
| "How does weather impact sales? What promos work best?" | Cortex Analyst - weather analysis with promo recommendations |
| "What should we expect next Friday night? There's a football game nearby." | Demand forecasting with staffing recommendations |
| "Why were sales lower than usual? What promo would help?" | Root cause analysis with actionable recommendations |
| "What are customers saying? Show me happy and unhappy reviews." | Cortex Search - customer sentiment analysis |

### 3. Dashboard View
Historical analytics from Snowflake data:
- Delivery performance metrics
- Traffic patterns and hotspots
- Late delivery analysis

---

## Key Features

### Weather Route Advisory
The app shows weather-based routing recommendations:

| Weather | Impact | Route Tips |
|---------|--------|------------|
| Cold | +20% delivery time | Avoid icy Lake Shore Dr, use salted main roads |
| Rainy | +25% delivery time | Avoid lower Wacker Dr flooding |
| Snowy | +50% delivery time | Stick to main streets only |

### Verified Queries
The semantic model includes verified queries for consistent demo results:
- Weather impact analysis
- Friday game night forecasting  
- Sales analysis with promo recommendations

---

## Configuration

### Environment Variables (Optional)

| Variable | Description |
|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier |
| `ORS_API_KEY` | OpenRouteService API key for real routing (optional) |

### Streamlit Secrets

Configure in `.streamlit/secrets.toml`:

```toml
[connections.snowflake]
account = "YOUR_ACCOUNT"
user = "YOUR_USER"
password = "YOUR_PASSWORD"
warehouse = "COMPUTE_WH"
database = "PIZZA_INTELLIGENCE"
schema = "ANALYTICS"
```

---

## Troubleshooting

### "No results found" errors
- Run `10_test_demo_queries.sql` to verify data exists
- Check semantic model is uploaded to stage

### Live Orders not updating
- Check **Auto-refresh** checkbox is enabled
- Click **Refresh** button manually
- Click **Reset** to clear and restart

### Weather showing inconsistent values
- The app uses simulated "Cold" weather to match historical data
- Both Dashboard and Live Orders should show consistent weather

---

## Data Model

### Key Tables
| Table | Description |
|-------|-------------|
| V_ORDERS | Orders with store and calendar info |
| V_DELIVERIES | Delivery performance metrics |
| PIZZA_DOCUMENTS | Customer reviews and feedback |

### Document Types
| Type | Content |
|------|---------|
| Reviews | Customer feedback with ratings |
| Audits | Store quality assessments |
| Invoices | Supplier records |

---

**Built for Snowflake Cortex Demo**  
*Chicago Loop Pizza Operations*
