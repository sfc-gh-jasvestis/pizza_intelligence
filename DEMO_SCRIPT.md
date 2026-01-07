# 🍕 Pizza Time Machine Kitchen - Demo Script

## Snowflake Intelligence Demo for QSR Partners

This demo script is designed to accompany your partner presentation. It showcases how Snowflake Intelligence transforms scattered pizza data into actionable intelligence.

---

## Pre-Demo Setup Checklist

- [ ] Run all SQL scripts in order (01 through 07)
- [ ] Upload `semantic_models/pizza_intelligence.yaml` to the stage
- [ ] Create the Pizza Ops Agent in Snowflake Intelligence UI
- [ ] Test 2-3 queries to ensure everything is working
- [ ] Have the partner presentation open alongside the demo

---

## Demo Flow (Aligned with Slides)

### 🎬 Opening Hook (Slide 1)
**Set the scene** while showing the Snowflake Intelligence UI:

> "Let me show you what the Pizza Time Machine Kitchen looks like in action..."

---

### 📊 Demo Section 1: Past Pizza (Structured Data)
**Slide Reference:** Act 1 - Stuck in Pizza Past

Start with basic analytics to show what's in the data:

#### Question 1: Basic Sales Overview
```
What were our total sales last week by store?
```
**Expected:** Table of stores with store names, revenue, and order counts. Shows regional performance.

#### Question 2: Delivery Performance
```
What's our late delivery rate this month by city?
```
**Expected:** Shows late delivery rates broken down by city, with insights on which regions need attention.

#### Question 2b: Delivery Root Causes
```
What are the main reasons for late deliveries?
```
**Expected:** Breakdown of late_reason (traffic, kitchen_delay, rider_shortage, weather).

**Talking Point:** 
> "This is the kind of question that used to require a BI analyst and 2 days. Now any operator can ask in natural language."

---

### 🔧 Demo Section 2: The Engine (Multi-Tool Power)
**Slide Reference:** Slide 3 - Snowflake Intelligence Engine

Show how the agent combines structured and unstructured data:

#### Question 3: Root Cause Analysis (THE KEY DEMO MOMENT)
```
Why did thin-crust sales dip in Chicago last night?
```

**What happens:**
1. Agent queries `pizza_analytics` → analyzes order patterns, finds anomalies
2. Agent searches `pizza_documents` → finds relevant context:
   - Customer reviews mentioning "Crispy Crust Co." competitor
   - Audit reports noting equipment issues and quality concerns
   - Feedback about delivery challenges

**What makes this powerful:**
The agent doesn't just answer your question - it **discovers unexpected patterns** in the data. It might find:
- Operational anomalies (early closures, staffing gaps)
- Time-based patterns (peak hour issues)
- Store-specific problems

Then it enriches this with **document context** about competitors, quality issues, and customer sentiment.

**Talking Point:**
> "Notice how the agent found something we didn't explicitly ask about - that's the power of AI-driven analysis. It doesn't just answer what you ask, it finds what actually matters. AND it pulled in context from our unstructured documents about competitor threats and equipment issues."

**Partner Value:**
> "This is the multi-tool orchestration the partner configures. The semantic model defines WHAT data means, the agent decides HOW to analyze it. The partner owns that intelligence layer."

---

### 🏈 Demo Section 3: Future Pizza Prophecy
**Slide Reference:** Slide 7 - Future Pizza Prophecy

This is the "wow" moment - predictive recommendations:

#### Question 4: Next Friday Forecast
```
What should we expect for next Friday night at our stores near stadiums?
```

**Expected Response:**
> "Next Friday is an NFL game day at [Stadium]. Based on historical patterns:
> - Expect 22% spike in pepperoni and family combo orders
> - Peak hours: 5-9 PM
> 
> **Recommendations:**
> - Increase pepperoni inventory by 20% at stores within 5km of stadium
> - Schedule 2 additional riders per store from 5-9 PM
> - Pre-stage dough prep 2 hours before game time
> - Consider activating 'Game Day Feast' promotion"

#### Question 5: Weather-Based Promo Recommendation
```
What's the best promo to run if Phoenix has a heatwave next week?
```

**Expected Response:**
> "Based on historical performance during hot weather periods:
> - Cold drinks and light options see 15% increase
> - Delivery orders increase (people don't want to go out)
> 
> **Recommended:** 'Sun & Slice' summer bundle with 20% discount
> - Historical ROI: 180% on similar campaigns
> - Projected uplift: $45K in Phoenix region"

**Talking Point:**
> "This is the Future Pizza Prophecy - not just showing what happened, but recommending what to do next. The partner builds this intelligence layer, we provide the engine."

---

### 📄 Demo Section 4: Document Intelligence
**Slide Reference:** Slide 4 - Kitchen Modernization

Show the power of unstructured data:

#### Question 6: Customer Sentiment (GREAT FOR SHOWING SEARCH)
```
What are customers saying about our Chicago stores?
```

**Expected:** Agent searches feedback documents and finds:
- Delivery delay complaints (I-90 construction)
- Thin-crust quality concerns
- Competitor mentions (Crispy Crust Co.)
- Positive feedback about Wrigleyville staff

**Talking Point:**
> "This question goes directly to our unstructured customer feedback - reviews, NPS comments, social mentions. Data that used to sit in PDFs and never get analyzed."

#### Question 7: Audit Findings
```
What were the key findings from our recent store audits?
```

**Expected:** Agent searches audit documents and finds:
- Chicago Loop: 87/100 score, pepperoni wastage issue, Oven 2 needs repair
- Wrigleyville: 94/100 score, Game Day Prep Protocol best practice
- Equipment issues and action items

#### Question 8: Supplier Quality
```
Have there been any supplier quality issues recently?
```

**Expected:** Agent finds invoice documents mentioning:
- Bell pepper spoilage from Arizona Produce (credit memo pending)
- All cheese and meat deliveries passed inspection

---

### 🎯 Demo Section 5: Campaign ROI
**Slide Reference:** Slide 5 - QSR Master Schema (Your IP)

Show the value of semantic models:

#### Question 8: Campaign Performance
```
Which of our current campaigns has the best ROI?
```

**Expected Response:**
Table showing campaigns ranked by ROI with revenue, cost, and recommendations.

#### Question 9: Promotional Optimization
```
How is the Tuesday 2-for-1 promotion performing compared to Game Day Feast?
```

**Expected:** Comparative analysis with actionable insights.

---

## 💡 Improvised Questions to Try

Based on partner interest, try these follow-up questions:

### For Operations-Focused Partners:
```
Which stores are understaffed during evening shifts?
```
```
What's our current pepperoni inventory across Chicago stores?
```
```
Show me labor costs vs revenue by store this week.
```

### For Marketing-Focused Partners:
```
What customer segments have the highest lifetime value?
```
```
How do app orders compare to phone orders in average ticket size?
```
```
What are customers saying about our loyalty program?
```

### For Executive Audiences:
```
Give me a summary of this week's key operational issues.
```
```
What are our top 3 opportunities to improve profitability?
```
```
Compare our Chicago region performance to Miami.
```

---

## 🚫 Questions to Avoid (Known Limitations)

- Real-time inventory updates (data is daily snapshots)
- Individual customer PII queries
- Future dates beyond calendar data (through 2026)
- Questions about competitors' internal data

---

## Partner Value Callouts

Throughout the demo, reinforce these partner opportunities:

| After This Demo Section | Say This |
|------------------------|----------|
| Root cause analysis | "This multi-tool intelligence is what partners configure - the semantic models and agent orchestration" |
| Forecast recommendations | "Partners own this IP - the QSR-specific logic that turns generic AI into Pizza Intelligence" |
| Document search | "Kitchen Modernization brings these dark data sources into Snowflake where SI can use them" |
| Campaign ROI | "These metrics and verified queries are the partner's reusable schema" |

---

## Closing Demo Summary

End the demo with a side-by-side:

**Before (Legacy Pantry):**
- "What were thin-crust sales?" → 2-day BI request
- "Why did sales drop?" → Manual investigation, maybe never answered
- "What should we do Friday?" → Gut feel and experience

**After (Pizza Time Machine):**
- "What were thin-crust sales?" → Instant answer with context
- "Why did sales drop?" → Multi-source analysis in seconds
- "What should we do Friday?" → Data-driven recommendations

> "This is what the partner builds on Snowflake Intelligence - Pizza Intelligence as a Service. Reusable across every QSR client."

---

## Troubleshooting

### If queries return unexpected results:
1. Check that all SQL scripts ran successfully
2. Verify semantic model is uploaded to stage
3. Ensure agent has both tools configured
4. Check warehouse is running

### If documents aren't being searched:
1. Verify Cortex Search service is created and running
2. Check that documents are in PIZZA_DOCUMENTS table
3. Test search service directly with SEARCH_PREVIEW function

---

## Next Steps After Demo

1. Identify target pizza/QSR client for pilot
2. Schedule 2-week sprint kickoff
3. Define initial semantic model scope
4. Plan document ingestion pipeline

**Remember:** We're not selling a tool, we're selling a partnership to build Pizza Intelligence as a Service!

