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

## Question 1: Capacity Gap Analysis (THE KEY DEMO MOMENT)

```
Across all stores last Friday, which cities saw the biggest gap between order demand and kitchen capacity, and why?
```

**What It Demonstrates:**
- Multi-table joins (orders + kitchen capacity + deliveries + events)
- Cross-city comparison
- Root cause identification

**Expected Response:**
Agent should identify Chicago Loop with:
- 45% thin-crust capacity (vs 90%+ elsewhere)
- Only 2 of 4 ovens operational
- Main issue: "Oven 2 repair pending, Oven 3 temperature calibration issues"

**Talking Point:**
> "Notice how the agent combined order data, kitchen capacity, and operational context to find not just WHAT happened but WHY. This query would have taken a BI analyst hours to build manually."

---

## Question 2: Leading Indicator Analysis

```
Show me stores where delivery time has been worsening over the last 4 Fridays but revenue hasn't dropped yet. What's driving the delay risk?
```

**What It Demonstrates:**
- Trend analysis over time
- Leading vs lagging indicator detection
- Proactive risk identification

**Expected Response:**
Agent should analyze:
- Week-over-week delivery time trends
- Revenue stability despite service degradation
- Root causes (rider shortage, traffic, kitchen delays)

**Talking Point:**
> "This is proactive intelligence - finding problems BEFORE they hit the bottom line. Traditional BI shows you the fire after the house burns down. This shows you the smoke."

---

## Question 3: Product Channel Analysis

```
Compare thin-crust vs pan-pizza performance across channels (app vs in-store vs aggregators) over the last 8 weeks and explain the main trends.
```

**What It Demonstrates:**
- Product mix analysis
- Channel performance comparison
- Trend explanation with context

**Expected Response:**
Agent should show:
- Thin-crust vs pan performance by channel
- Aggregator channel trends (third-party apps)
- Possible explanations (competitor activity, weather, promotions)

**Talking Point:**
> "Partners building QSR intelligence need to understand not just what's selling, but WHERE and WHY. This is the kind of analysis that informs menu strategy and channel investments."

---

## Question 4: Predictive Recommendations

```
Using order history, weather, and local events, which 10 stores are most at risk of stock-outs this coming Friday, and what should their target dough prep be?
```

**What It Demonstrates:**
- Multi-source predictive analytics
- Actionable recommendations
- Operational prescriptions

**Expected Response:**
Agent should:
- Rank stores by stock-out risk
- Factor in weather forecast and events
- Provide specific dough prep targets

**Talking Point:**
> "This is the Future Pizza Prophecy - the agent doesn't just describe the past, it prescribes action for the future. This is where partner IP becomes incredibly valuable."

---

## Question 5: Unstructured + Structured Fusion

```
For our top 50 stores by revenue, summarize the most common complaint themes in reviews from the past month and map them to operational issues (delivery, quality, pricing).
```

**What It Demonstrates:**
- Cortex Search for unstructured documents
- Cortex Analyst for structured rankings
- Theme extraction and categorization

**Expected Response:**
Agent should:
- Identify top stores by revenue
- Search customer reviews and feedback
- Categorize complaints into operational buckets
- Highlight Chicago Loop quality issues and competitor mentions

**Talking Point:**
> "This is the magic of multi-tool orchestration. The agent queried structured sales data AND searched through unstructured customer reviews to connect financial performance with customer sentiment. No manual report could do this in real-time."

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
