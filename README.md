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
| 1 | **"Across all stores last Friday, which cities saw the biggest gap between order demand and kitchen capacity, and why?"** | Multi-table joins across orders, capacity, delays, and events |
| 2 | **"Show me stores where delivery time has been worsening over the last 4 Fridays but revenue hasn't dropped yet. What's driving the delay risk?"** | Leading indicator analysis, trend detection across time |
| 3 | **"Compare thin-crust vs pan-pizza performance across channels (app vs in-store vs aggregators) over the last 8 weeks and explain the main trends."** | Product mix analysis by channel with trend explanation |
| 4 | **"Using order history, weather, and local events, which 10 stores are most at risk of stock-outs this coming Friday, and what should their target dough prep be?"** | Predictive analytics combining multiple data sources |
| 5 | **"For our top 50 stores by revenue, summarize the most common complaint themes in reviews from the past month and map them to operational issues (delivery, quality, pricing)."** | Cortex Search + Analyst combining structured and unstructured data |

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

## Key Demo Story: Chicago Thin-Crust Decline

The demo is built around a compelling root cause analysis scenario:

**The Question:** "Why did thin-crust sales dip in Chicago?"

**The Answer (discovered through AI):**

| Store | Thin-Crust Share | Kitchen Capacity | Ovens Working | Root Cause |
|-------|------------------|------------------|---------------|------------|
| Chicago Loop | 22.8% | 45% | 2 of 4 | Oven 2 repair pending, Oven 3 temperature calibration |
| Chicago Wrigleyville | 42.9% | 93% | 4 of 4 | No issues |

**Supporting Evidence:**
- Cortex Analyst shows capacity constraints in structured data
- Cortex Search finds audit reports mentioning "Oven 2 temperature inconsistent"
- Customer reviews mention "thin crust soggy" and "switching to Crispy Crust Co."

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
