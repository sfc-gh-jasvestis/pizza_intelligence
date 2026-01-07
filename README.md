# 🍕 The Insight Kitchen

## Snowflake Intelligence Demo for QSR Partners

This repository contains everything you need to run the **Pizza Intelligence** demo showcasing Snowflake Intelligence capabilities for Quick Service Restaurant (QSR) operations.

---

## 📁 Repository Structure

```
pizza/
├── README.md                    # This file
├── DEMO_SCRIPT.md              # Step-by-step demo walkthrough
├── setup/                       # SQL setup scripts (run in order)
│   ├── 01_create_database.sql   # Create database and schemas
│   ├── 02_create_tables.sql     # Create dimension and fact tables
│   ├── 03_load_sample_data.sql  # Load dimension data
│   ├── 04_load_orders_data.sql  # Load orders and deliveries
│   ├── 05_load_inventory_staffing.sql  # Load inventory and staffing
│   ├── 06_setup_cortex_search.sql      # Create Cortex Search service
│   ├── 07_create_agent.sql      # Agent configuration reference
│   └── 08_create_views.sql      # Pre-joined views for semantic model
├── semantic_models/
│   └── pizza_intelligence.yaml  # QSR Master Semantic Model
└── documents/                   # Sample unstructured documents
    ├── invoices/               # Supplier invoices
    ├── audits/                 # Store audit reports
    └── feedback/               # Customer feedback summaries
```

---

## 🚀 Quick Start

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
```

### Step 2: Upload Semantic Model

Upload `semantic_models/pizza_intelligence.yaml` to the Snowflake stage:

```sql
PUT file:///path/to/pizza_intelligence.yaml 
    @PIZZA_INTELLIGENCE.SEMANTIC_MODELS.SEMANTIC_MODEL_STAGE;
```

Or use Snowsight's stage upload feature.

### Step 3: Create the Agent

1. Go to [ai.snowflake.com](https://ai.snowflake.com)
2. Create a new Agent named **"Pizza Ops Agent"**
3. Add two tools:
   - **Cortex Analyst** tool pointing to the semantic model
   - **Cortex Search** tool pointing to `PIZZA_DOCUMENT_SEARCH`
4. Copy orchestration instructions from `setup/07_create_agent.sql`

### Step 4: Test the Demo

Try these sample questions:
- "What were our total sales last week?"
- "Why did thin-crust sales dip in Chicago last night?"
- "What should we expect for next Friday's game day?"

---

## 📊 Data Model Overview

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
| FACT_ORDERS | Order transactions | ~50,000 |
| FACT_ORDER_ITEMS | Line items | ~100,000 |
| FACT_DELIVERIES | Delivery performance | ~17,000 |
| FACT_INVENTORY | Daily inventory snapshots | ~24,000 |
| FACT_STAFFING | Shift staffing data | ~12,000 |
| FACT_CAMPAIGN_PERFORMANCE | Campaign metrics | ~15,000 |

### Document Types
| Type | Count | Content |
|------|-------|---------|
| Invoices | 3 | Supplier delivery records |
| Audits | 2 | Q4 2024 store quality audits |
| Feedback | 2 | Customer reviews and NPS data |

---

## 🎯 Key Demo Scenarios

### 1. Root Cause Analysis
**Question:** "Why did thin-crust sales dip in Chicago last night?"

**Demonstrates:** Multi-tool orchestration combining:
- Cortex Analyst for sales metrics
- Cortex Search for customer feedback and audit context

### 2. Future Forecasting
**Question:** "What should we expect for next Friday at our stadium stores?"

**Demonstrates:** Predictive recommendations using:
- Historical pattern analysis
- Calendar events (game days)
- Actionable staffing and inventory recommendations

### 3. Document Intelligence
**Question:** "What were the main issues from our recent audits?"

**Demonstrates:** Cortex Search over unstructured documents:
- Audit reports with quality scores
- Action items and recommendations
- Competitor intelligence

---

## 🔧 Customization

### Adjusting Data Volume
Modify the `GENERATOR(ROWCOUNT => N)` values in the load scripts to increase/decrease data volume.

### Adding New Documents
Insert new documents into `PIZZA_DOCUMENTS` table:

```sql
INSERT INTO PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS 
VALUES ('DOC-ID', 'type', 'title', 'date', 'store_id', 
        'full content...', 'summary', 
        ARRAY_CONSTRUCT('tag1', 'tag2'), 
        CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
```

### Extending the Semantic Model
Edit `pizza_intelligence.yaml` to add:
- New dimensions or measures
- Additional verified queries
- More synonyms for natural language understanding

---

## 🎓 Partner Training Points

This demo illustrates four partner revenue opportunities:

1. **Kitchen Modernization** - Data ingestion and modeling
2. **QSR Master Schema** - Semantic models as reusable IP
3. **Governance & Safety** - Role design and access control
4. **Manager's Co-Pilot** - Custom apps built on SI APIs

---

## 📝 Presentation Resources

- **Slide Deck:** Pizza QBR presentation (10 slides)
- **Demo Script:** See `DEMO_SCRIPT.md` for detailed walkthrough
- **2-Week Sprint:** Week 1 (Crust & Sauce) + Week 2 (Toppings & Delivery)

---

## 🆘 Troubleshooting

### "No results found" errors
- Verify all setup scripts completed successfully
- Check that the semantic model YAML is uploaded to the stage
- Ensure the Cortex Search service is created and has processed documents

### Slow query performance
- Increase warehouse size temporarily
- Check that tables have appropriate clustering

### Agent not using both tools
- Review orchestration instructions
- Ensure both tools are properly configured in the agent
- Test each tool individually first

---

## 📞 Support

For demo issues or questions:
- Snowflake Intelligence documentation
- Partner enablement resources
- Your Snowflake account team

---

**Built for the Insight Kitchen Partner Demo**  
*Snowflake Intelligence - From Data to Competitive Advantage*

