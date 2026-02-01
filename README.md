# The Insight Kitchen

## Snowflake Intelligence Demo for QSR Partners

This repository contains everything you need to run the **Pizza Intelligence** demo showcasing Snowflake Intelligence capabilities for Quick Service Restaurant (QSR) operations.

---

## Repository Structure

```
pizza/
├── README.md                    # This file
├── DEMO_SCRIPT.md              # Step-by-step demo walkthrough
├── pizza_ops_assistant.py      # Streamlit app for Store Managers
├── setup/                       # SQL setup scripts (run in order)
│   ├── 01_create_database.sql   # Create database and schemas
│   ├── 02_create_tables.sql     # Create dimension and fact tables
│   ├── 03_load_sample_data.sql  # Load dimension data
│   ├── 04_load_orders_data.sql  # Load orders and deliveries
│   ├── 05_load_inventory_staffing.sql  # Load inventory and staffing
│   ├── 06_setup_cortex_search.sql      # Create Cortex Search service
│   ├── 07_create_agent.sql      # Agent configuration reference
│   ├── 08_create_views.sql      # Pre-joined views for semantic model
│   ├── 09_refresh_data.sql      # Data refresh and alignment script
│   └── 10_test_demo_queries.sql # Test queries to verify demo
├── semantic_models/
│   └── pizza_intelligence.yaml  # QSR Master Semantic Model
├── .streamlit/
│   └── secrets.toml.example     # Template for Streamlit credentials
└── documents/                   # Sample unstructured documents
    ├── invoices/               # Supplier invoices
    ├── audits/                 # Store audit reports
    └── feedback/               # Customer feedback summaries
```

---

## Two Demo Personas

This demo supports **two distinct user personas** with different interfaces:

| Persona | Interface | Use Case |
|---------|-----------|----------|
| **Snowflake Intelligence Users** | ai.snowflake.com | Analysts, HQ ops, partner builders doing cross-store analytics |
| **Store Managers** | Streamlit App | Front-line managers running their individual store |

---

## Quick Start

### Prerequisites
- Snowflake account with Cortex AI enabled
- Access to Snowflake Intelligence (ai.snowflake.com)
- A warehouse (COMPUTE_WH or similar)

### Step 1: Run SQL Setup Scripts

Execute the SQL scripts in order using Snowsight or your preferred SQL client:

```sql
-- Run each script in sequence
-- 01_create_database.sql
-- 02_create_tables.sql
-- 03_load_sample_data.sql
-- 04_load_orders_data.sql
-- 05_load_inventory_staffing.sql
-- 06_setup_cortex_search.sql
-- 07_create_agent.sql
-- 08_create_views.sql
-- 09_refresh_data.sql  -- Ensures data is aligned for demo
-- 10_test_demo_queries.sql  -- Verify demo works
```

### Step 2: Upload Semantic Model

Upload `semantic_models/pizza_intelligence.yaml` to the Snowflake stage:

```sql
PUT file:///path/to/pizza_intelligence.yaml 
    @PIZZA_INTELLIGENCE.SEMANTIC_MODELS.SEMANTIC_MODEL_STAGE
    AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

Or use Snowsight's stage upload feature.

### Step 3: Create the Agent

1. Go to [ai.snowflake.com](https://ai.snowflake.com)
2. Create a new Agent named **"Pizza Ops Agent"**
3. Add two tools:
   - **Cortex Analyst** tool pointing to the semantic model
   - **Cortex Search** tool pointing to `PIZZA_DOCUMENT_SEARCH`
4. Copy orchestration instructions from `setup/07_create_agent.sql`

### Step 4: Run the Streamlit App (Optional)

For the Store Manager persona:

```bash
# Copy secrets template and fill in credentials
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Snowflake credentials

# Run the app
streamlit run pizza_ops_assistant.py
```

---

## Demo Questions by Persona

### For Snowflake Intelligence Users
*(Analysts, HQ ops, partner builders working in the SI UI)*

| # | Question | What It Demonstrates |
|---|----------|---------------------|
| 1 | **"Show me the capacity gap by city for last Friday"** | Multi-table joins (orders + kitchen capacity + stores), cross-city comparison |
| 2 | **"Which stores had the highest late delivery rates last Friday and what were the main causes?"** | Delivery performance metrics, root cause analysis, store-level comparison |
| 3 | **"Compare thin-crust vs pan-pizza performance across channels over the last 8 weeks"** | Product mix analysis by channel with trend explanation |
| 4 | **"How much revenue are we losing across all stores with kitchen capacity issues?"** | Financial impact quantification, capacity-to-revenue correlation |
| 5 | **"Which stores are in crisis mode right now and what's causing it?"** | Combined crisis analysis (capacity + delivery), multi-tool orchestration |

### For Store Managers using the Streamlit App
*(Front-line users of your "Manager's Co-Pilot")*

| # | Question | What It Demonstrates |
|---|----------|---------------------|
| 1 | **"Why were my sales lower than usual last night in this store?"** | Single-store root cause analysis |
| 2 | **"What should I get ready for this Friday night shift?"** | Shift planning with weather, events, and historical patterns |
| 3 | **"Are my delivery times getting worse, and what's causing it?"** | Week-over-week performance comparison with drivers |
| 4 | **"What are the top 3 things I should fix this week to improve my store score?"** | Prioritized action items from KPIs + customer complaints |
| 5 | **"Show me my happiest and unhappiest customers from the last 7 days and what they mentioned."** | Customer sentiment from feedback for a single store |

---

## Data Model Overview

### Dimension Tables
| Table | Description |
|-------|-------------|
| DIM_STORES | 15 pizza stores across 5 regions |
| DIM_PRODUCTS | 20 menu items (pizzas, sides, drinks) |
| DIM_CAMPAIGNS | 10 marketing campaigns |
| DIM_CUSTOMERS | 500 sample customers |
| DIM_CALENDAR | 2025-2026 with events and weather |

### Fact Tables
| Table | Description | Records |
|-------|-------------|---------|
| FACT_ORDERS | Order transactions | ~60,000 |
| FACT_ORDER_ITEMS | Line items with crust type | ~144,000 |
| FACT_DELIVERIES | Delivery performance | ~20,000 |
| FACT_INVENTORY | Daily inventory snapshots | ~24,000 |
| FACT_STAFFING | Shift staffing data | ~20,000 |
| FACT_KITCHEN_CAPACITY | Oven/production tracking | ~1,350 |
| FACT_CAMPAIGN_PERFORMANCE | Campaign metrics | ~15,000 |

### Pre-Joined Views (for Semantic Model)
| View | Description |
|------|-------------|
| V_ORDERS | Orders + Store + Calendar |
| V_DELIVERIES | Deliveries + Store + Calendar |
| V_ORDER_ITEMS | Order Items + Product + Store + Calendar |
| V_KITCHEN_CAPACITY | Kitchen Capacity + Store + Calendar |
| V_STAFFING | Staffing + Store + Calendar |
| V_INVENTORY | Inventory + Store + Product |
| V_CAMPAIGN_PERFORMANCE | Campaigns + Performance metrics |

### Document Types
| Type | Count | Content |
|------|-------|---------|
| Invoices | 3 | Supplier delivery records |
| Audits | 2 | Q4 2024 store quality audits |
| Reviews | 1 | Customer reviews with ratings |
| Feedback | 1 | Customer feedback summaries |
| Maintenance | 1 | Kitchen equipment status reports |

---

## Key Demo Story: Multi-City Capacity Crisis

The demo is built around a compelling multi-city operations crisis:

**The Question:** "Which stores are in crisis mode and what's causing it?"

**The Answer (discovered through AI):**

| City | Store | Kitchen Capacity | Late Delivery % | Crisis Level | Root Cause |
|------|-------|------------------|-----------------|--------------|------------|
| Chicago | Chicago Loop | 45% | 44.0% | CRITICAL | Oven repair pending, temperature calibration |
| Los Angeles | LA Downtown | 55% | 66.7% | CRITICAL | Exhaust fan failure - ovens offline |
| New York | Manhattan Midtown | 62% | 48.0% | CRITICAL | Gas line issue - awaiting repair |
| Miami | Miami Beach | 70% | 52.0% | CRITICAL | Electrical panel upgrade in progress |

**Revenue Impact:** Over $15,000/month in lost revenue across 4 cities

**Supporting Evidence:**
- Cortex Analyst shows capacity constraints and delivery delays in structured data
- Cortex Search finds maintenance reports detailing equipment failures
- Customer reviews mention delivery delays and quality issues

---

## Customization

### Adjusting Data Volume
Modify the `GENERATOR(ROWCOUNT => N)` values in the load scripts to increase/decrease data volume.

### Adding New Documents
Insert new documents into `PIZZA_DOCUMENTS` table:

```sql
INSERT INTO PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS 
VALUES ('DOC-ID', 'type', 'title', 'date', 'store_id', 
        'full content...', 'summary');
```

### Extending the Semantic Model
Edit `pizza_intelligence.yaml` to add:
- New dimensions or measures
- Additional verified queries
- More synonyms for natural language understanding

---

## Partner Training Points

This demo illustrates four partner revenue opportunities:

1. **Kitchen Modernization** - Data ingestion and modeling
2. **QSR Master Schema** - Semantic models as reusable IP
3. **Governance & Safety** - Role design and access control
4. **Manager's Co-Pilot** - Custom apps built on SI APIs

---

## Troubleshooting

### "No results found" errors
- Run `10_test_demo_queries.sql` to verify data exists
- Check that the semantic model YAML is uploaded to the stage
- Ensure the Cortex Search service is created and has processed documents

### Date-related issues
- Run `09_refresh_data.sql` to realign all date ranges
- "Last Friday" queries require data for that specific date

### Slow query performance
- Increase warehouse size temporarily
- Check that tables have appropriate clustering

### Agent not using both tools
- Review orchestration instructions
- Ensure both tools are properly configured in the agent
- Test each tool individually first

---

## Support

For demo issues or questions:
- Snowflake Intelligence documentation
- Partner enablement resources
- Your Snowflake account team

---

**Built for the Insight Kitchen Partner Demo**  
*Snowflake Intelligence - From Data to Competitive Advantage*
