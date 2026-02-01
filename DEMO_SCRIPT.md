# Pizza Time Machine Kitchen - Demo Script

## Snowflake Intelligence Demo for QSR Partners

This demo script walks through both personas: **Snowflake Intelligence users** (HQ analysts) and **Store Managers** (Streamlit app). Use this guide to deliver a compelling demo of AI-powered pizza operations.

---

## Pre-Demo Setup Checklist

- [ ] Run all SQL scripts in order (01 through 10)
- [ ] Upload `semantic_models/pizza_intelligence.yaml` to the stage
- [ ] Create the Pizza Ops Agent in Snowflake Intelligence UI
- [ ] (Optional) Start the Streamlit app for Store Manager demo
- [ ] Test 2-3 queries from each persona to ensure everything works
- [ ] Have the partner presentation open alongside the demo

---

## Demo Overview

| Section | Persona | Interface | Duration |
|---------|---------|-----------|----------|
| Part 1 | Snowflake Intelligence Users | ai.snowflake.com | 15 min |
| Part 2 | Store Managers | Streamlit App | 10 min |
| Wrap-up | Both | Side-by-side | 5 min |

---

# PART 1: Snowflake Intelligence Users

*For Analysts, HQ ops, and partner builders working in the SI UI*

## Opening Hook

> "Let me show you what happens when we turn 12 months of pizza data into an intelligent assistant that HQ analysts can query in natural language..."

Open [ai.snowflake.com](https://ai.snowflake.com) and select the **Pizza Ops Agent**.

---

## Question 1: Capacity Gap Analysis (THE KEY DEMO MOMENT) 🔥🔥🔥

```
Show me the capacity gap by city for last Friday
```

**What It Demonstrates:**
- Multi-table joins (orders + kitchen capacity + stores)
- Cross-city comparison with dramatic contrast
- Equipment issue identification

**Expected Response:**
Agent should show **FOUR cities in crisis** with varying severity:
- **Chicago: 45% capacity** - Oven 2 repair pending, temperature calibration issues
- **Los Angeles: 55% capacity** - CRITICAL exhaust fan failure
- **New York: 62% capacity** - Gas line maintenance 
- **Miami: 70% capacity** - Electrical upgrade in progress
- All other cities: 85-98% capacity, fully operational

**Talking Point:**
> "Notice the multi-city crisis - this isn't just one store, it's a SYSTEMIC equipment problem across our biggest markets. Chicago at 45%, LA at 55% - that's nearly half our production capacity in our top revenue cities."

---

## Question 2: Late Delivery Analysis 🔥🔥

```
Which stores had the highest late delivery rates last Friday and what were the main causes?
```

**What It Demonstrates:**
- Delivery performance metrics
- Root cause analysis
- Store-level comparison with dramatic variance

**Expected Response:**
Agent should identify stores with WILDLY varying late rates:
- **LA Downtown: 42.7% late rate** (Driver shortage + kitchen overflow)
- **Miami Beach: 33.6% late rate** (Traffic + weather)
- **Chicago Loop: 30.5% late rate** (Kitchen delays from equipment issues)
- **Manhattan Midtown: 28.2% late rate** (Peak hour congestion)

**Talking Point:**
> "Look at that spread - LA is losing nearly HALF their deliveries to late arrivals while other stores run at 15-20%. This is a crisis that's costing us customer loyalty."

---

## Question 3: Product Channel Analysis 🔥🔥

```
Compare thin-crust vs pan-pizza performance across channels over the last 8 weeks
```

**What It Demonstrates:**
- Product mix analysis by channel
- Revenue comparison
- Channel strategy insights

**Expected Response:**
Agent should show:
- Thin-crust dominates **in-store** ($93K revenue)
- Pan pizza dominates **web** ($59K) and **phone** ($38K)
- App channel underperforming for both

**Talking Point:**
> "This reveals a strategic insight - thin-crust customers prefer dining in, while pan-pizza customers order remotely. This affects how you design menus and promotions by channel."

---

## Question 4: Revenue at Risk Analysis 🔥🔥🔥

```
How much revenue are we losing across all stores with kitchen capacity issues?
```

**What It Demonstrates:**
- Financial impact across ALL problem cities
- Capacity-to-revenue correlation
- Urgency for equipment investment

**Expected Response:**
Agent should calculate revenue at risk for EACH city:
- **Chicago Loop: ~$11,000 estimated lost revenue** (45% capacity)
- **LA Downtown: ~$8,500 estimated lost revenue** (55% capacity)  
- **Manhattan: ~$6,200 estimated lost revenue** (62% capacity)
- **Miami Beach: ~$4,800 estimated lost revenue** (70% capacity)
- **Total at risk: $30,000+ monthly**

**Talking Point:**
> "This is the CFO question - 'What's it costing us?' Now we have a number: Over $30K per month in lost revenue across four cities. That's the business case for emergency equipment investment."

---

## Question 5: Crisis Mode Dashboard 🔥🔥🔥

```
Which stores are in crisis mode right now and what's causing it?
```

**What It Demonstrates:**
- **Combined crisis analysis** - both capacity AND delivery problems
- Multi-tool orchestration  
- Severity ranking for prioritization

**Expected Response:**
Agent should show stores ranked by crisis severity:
- **CRITICAL**: Chicago Loop (45% capacity + 30.5% late delivery)
- **CRITICAL**: LA Downtown (55% capacity + 42.7% late delivery)
- **HIGH**: Miami Beach (70% capacity + 33.6% late delivery)
- **HIGH**: Manhattan Midtown (62% capacity + 28.2% late delivery)

**Talking Point:**
> "This is the ops command center view - stores with BOTH capacity AND delivery problems get flagged CRITICAL. Chicago and LA need immediate attention because they're failing on both fronts."

---

## Suggested Questions for SI UI

Add these 5 questions as "Suggested Questions" in the Pizza Ops Agent settings:

1. Show me the capacity gap by city for last Friday
2. Which stores had the highest late delivery rates last Friday and what were the main causes?
3. Compare thin-crust vs pan-pizza performance across channels over the last 8 weeks
4. How much revenue are we losing across all stores with kitchen capacity issues?
5. Which stores are in crisis mode right now and what's causing it?

---

# PART 2: Store Managers (Streamlit App)

*For front-line users of your "Manager's Co-Pilot"*

## Setting the Scene

> "Now let's see what this looks like for a store manager - someone who doesn't know SQL and just wants to run their store better."

Open the Streamlit app (`pizza_ops_assistant.py`) or show the Manager's Co-Pilot UI.

---

## Question 1: Last Night Analysis

```
Why were my sales lower than usual last night in this store?
```

**Alternative (pre-canned button):**
> "Explain last night's dip for Store 42"

**What It Demonstrates:**
- Single-store focus
- Historical comparison
- Root cause for a specific shift

**Expected Response:**
Agent should analyze:
- Comparison to same day last week
- Any capacity or staffing issues
- Weather or event factors

**Talking Point:**
> "Store managers don't want to query across 50 stores - they want to understand THEIR store. The app automatically filters to their location."

---

## Question 2: Friday Night Prep

```
What should I get ready for this Friday night shift?
```

**Alternative:**
> "Given past Fridays, weather, and events, what do I need more of (staff, dough, riders) from 5-9pm?"

**What It Demonstrates:**
- Shift-level planning
- Multi-factor forecasting
- Actionable prep list

**Expected Response:**
Agent should provide:
- Expected order volume (vs typical Friday)
- Staffing recommendations
- Dough prep targets
- Any special events to prepare for

**Talking Point:**
> "This is the 'what do I do' question every manager asks. Instead of gut feel, they get data-driven prep guidance."

---

## Question 3: Delivery Performance

```
Are my delivery times getting worse, and what's causing it?
```

**Alternative:**
> "Compare my delivery performance this week vs last week and tell me why it changed."

**What It Demonstrates:**
- Trend comparison
- Root cause by factor
- Actionable insights

**Expected Response:**
Agent should show:
- Week-over-week delivery time comparison
- Breakdown by reason (traffic, kitchen, riders)
- Specific recommendations

---

## Question 4: Store Improvement Priorities

```
What are the top 3 things I should fix this week to improve my store score?
```

**What It Demonstrates:**
- KPI + complaint fusion
- Prioritized recommendations
- Actionable to-do list

**Expected Response:**
Agent should blend:
- Operational KPIs (delivery time, order accuracy)
- Customer complaints from reviews
- Prioritized action items

**Talking Point:**
> "This is the Manager's Co-Pilot generating a personalized action plan. It's not just dashboards - it's a to-do list powered by AI."

---

## Question 5: Customer Sentiment

```
Show me my happiest and unhappiest customers from the last 7 days and what they mentioned.
```

**What It Demonstrates:**
- Customer-level sentiment
- Review summarization
- Feedback categorization

**Expected Response:**
Agent should:
- Identify 5-star vs 1-2 star reviews
- Summarize what made customers happy/unhappy
- Highlight specific issues mentioned

---

# Wrap-Up: Side-by-Side Comparison

## Before vs After

| Before (Legacy Pantry) | After (Pizza Time Machine) |
|------------------------|---------------------------|
| "What were thin-crust sales?" → 2-day BI request | Instant answer with context |
| "Why did sales drop?" → Manual investigation | Multi-source analysis in seconds |
| "What should we do Friday?" → Gut feel | Data-driven recommendations |
| "What are customers saying?" → Unread PDF reports | Real-time sentiment fusion |

## Partner Value Callouts

| Demo Section | Partner Opportunity |
|--------------|---------------------|
| Multi-tool orchestration | Partners configure the semantic model + agent logic |
| Predictive recommendations | QSR-specific IP that turns generic AI into Pizza Intelligence |
| Document search | Kitchen Modernization brings dark data into SI |
| Store Manager app | Manager's Co-Pilot as custom app on SI APIs |

---

# Questions to Avoid

These may not work well with current data:

- Real-time inventory updates (data is daily snapshots)
- Individual customer PII queries
- Future dates beyond calendar data (through 2026)
- Questions about competitors' internal data

---

# Troubleshooting

### If queries return no results:
1. Run `setup/10_test_demo_queries.sql` to verify data
2. Check "last Friday" is within the data range
3. Verify semantic model is uploaded to stage

### If documents aren't being searched:
1. Check Cortex Search service status: `DESCRIBE CORTEX SEARCH SERVICE PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENT_SEARCH;`
2. Verify documents exist in `PIZZA_DOCUMENTS` table
3. Wait for index refresh if documents were recently added

### If Streamlit app doesn't connect:
1. Verify `.streamlit/secrets.toml` has correct credentials
2. Check warehouse is running
3. Confirm user has access to PIZZA_INTELLIGENCE database

---

# After the Demo

1. Identify target pizza/QSR client for pilot
2. Schedule 2-week sprint kickoff
3. Define initial semantic model scope
4. Plan document ingestion pipeline

**Remember:** We're not selling a tool, we're selling a partnership to build Pizza Intelligence as a Service!

---

*For detailed setup instructions, see README.md*
