-- ============================================================================
-- PIZZA TIME MACHINE KITCHEN - Snowflake Intelligence Demo Setup
-- Step 6: Configure Cortex Search for Unstructured Documents
-- ============================================================================

USE DATABASE PIZZA_INTELLIGENCE;
USE SCHEMA DOCUMENTS;

-- ============================================================================
-- Create table to store document content
-- ============================================================================
CREATE OR REPLACE TABLE PIZZA_DOCUMENTS (
    document_id         VARCHAR(50) PRIMARY KEY,
    document_type       VARCHAR(30),      -- 'invoice', 'audit', 'feedback', 'review'
    document_title      VARCHAR(200),
    document_date       DATE,
    store_id            VARCHAR(10),
    content             VARCHAR(16777216), -- Full document text
    summary             VARCHAR(2000),
    tags                ARRAY,
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- Load sample documents (using SELECT to allow ARRAY_CONSTRUCT)
-- ============================================================================

-- Invoice documents
INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'INV-2025-001',
    'invoice',
    'Midwest Cheese Co. Invoice - Chicago Loop',
    '2025-01-03'::DATE,
    'STR004',
    'SUPPLIER INVOICE - Invoice Number: INV-2025-001, Date: January 3, 2025, Supplier: Midwest Cheese Co., Bill To: Pizza Time Machine - Chicago Loop (STR004). Line Items: Premium Mozzarella 200 kg at $8.50 = $1,700.00, Parmesan Aged 12mo 50 kg at $15.00 = $750.00, Provolone Blend 75 kg at $9.25 = $693.75. Subtotal: $3,143.75, Tax (8%): $251.50, Shipping: $125.00, Total Due: $3,520.25. Payment Terms: Net 30, Due Date: February 2, 2025. Notes: Delivery confirmed by store manager Michael Brown on Jan 3, 2025 at 6:45 AM. All items passed quality inspection. Temperature at delivery: 38°F (within acceptable range). Next scheduled delivery: January 10, 2025. Quality Certificate: QC-2025-0103-CHI.',
    'Cheese delivery invoice for Chicago Loop store totaling $3,520.25. All items passed quality inspection.',
    ARRAY_CONSTRUCT('invoice', 'cheese', 'chicago', 'quality-passed'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'INV-2025-002',
    'invoice',
    'Arizona Produce Direct Invoice - Phoenix',
    '2025-01-04'::DATE,
    'STR001',
    'SUPPLIER INVOICE - Invoice Number: INV-2025-002, Date: January 4, 2025, Supplier: Arizona Produce Direct, Bill To: Pizza Time Machine - Downtown Phoenix (STR001). Line Items: Roma Tomatoes 150 kg at $3.25 = $487.50, Bell Peppers (Mixed) 80 kg at $4.50 = $360.00, Yellow Onions 100 kg at $1.75 = $175.00, Fresh Mushrooms 60 kg at $6.00 = $360.00, Fresh Basil 10 kg at $12.00 = $120.00. Subtotal: $1,502.50, Tax (5.6%): $84.14, Total Due: $1,586.64. QUALITY ISSUES: Bell peppers showed early signs of spoilage in 2 of 8 crates. 10 kg rejected. Credit memo to be issued for $45.00. Supplier notified; replacement shipment scheduled for Jan 6.',
    'Produce delivery for Phoenix store. Quality issue: Bell peppers rejected due to spoilage (10 kg). Credit memo pending.',
    ARRAY_CONSTRUCT('invoice', 'produce', 'phoenix', 'quality-issue', 'credit-pending'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'INV-2025-003',
    'invoice',
    'Premium Meats Inc. Invoice - Distribution',
    '2025-01-05'::DATE,
    NULL,
    'SUPPLIER INVOICE - Invoice Number: INV-2025-003, Date: January 5, 2025, Supplier: Premium Meats Inc., Bill To: Pizza Time Machine - Regional Distribution Center. Line Items: Pepperoni (Sliced) 500 kg at $12.00 = $6,000.00, Italian Sausage 300 kg at $10.50 = $3,150.00, Bacon Bits 150 kg at $14.00 = $2,100.00, Grilled Chicken 200 kg at $11.00 = $2,200.00, Ham (Diced) 100 kg at $9.00 = $900.00. Total Due: $15,876.25. Distribution: STR001 Phoenix 35 kg pepperoni, STR004 Chicago Loop 45 kg pepperoni, STR005 Wrigleyville 40 kg pepperoni. Cold Chain Verification: Truck temperature maintained 34-36°F throughout transport. USDA Inspection: Passed - Certificate #USDA-2025-0105-PM.',
    'Large meat order for regional distribution totaling $15,876.25. Pepperoni largest item at 500 kg. All USDA inspections passed.',
    ARRAY_CONSTRUCT('invoice', 'meat', 'pepperoni', 'distribution', 'usda-passed'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

-- Audit documents
INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'AUDIT-2025-Q4-STR004',
    'audit',
    'Q4 2024 Store Audit - Chicago Loop',
    '2024-12-15'::DATE,
    'STR004',
    'STORE QUALITY AUDIT REPORT - Store: Chicago Loop (STR004), Audit Date: December 15, 2024, Auditor: Jennifer Walsh. OVERALL SCORE: 87/100 (Good). Category Scores: Food Safety 28/30 (minor temp log gaps), Cleanliness 24/25 (excellent), Customer Service 18/20 (training needed), Inventory Management 10/15 (HIGH WASTAGE NOTED), Equipment Condition 7/10 (Oven 2 needs service). KEY ISSUES: Pepperoni wastage 15% above target due to expired product. Dough overproduction on slow days. Oven 2 temperature inconsistent (+/- 25°F variance). Two customer complaints about delivery driver attitude. ACTION ITEMS: HIGH PRIORITY - Schedule Oven 2 repair by Dec 22, Reduce pepperoni wastage by Jan 15. MEDIUM - Customer service training by Jan 30.',
    'Chicago Loop audit score 87/100. Issues: High pepperoni wastage (15% above target), Oven 2 needs repair, customer service training needed.',
    ARRAY_CONSTRUCT('audit', 'chicago', 'wastage', 'equipment-issue', 'training-needed'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'AUDIT-2025-Q4-STR005',
    'audit',
    'Q4 2024 Store Audit - Wrigleyville',
    '2024-12-18'::DATE,
    'STR005',
    'STORE QUALITY AUDIT REPORT - Store: Chicago Wrigleyville (STR005), Audit Date: December 18, 2024, Auditor: Jennifer Walsh. OVERALL SCORE: 94/100 (Excellent). Category Scores: Food Safety 30/30 (Perfect), Cleanliness 25/25 (Perfect), Customer Service 19/20 (Outstanding), Inventory Management 13/15 (Good), Equipment Condition 7/10 (Aging equipment). COMMENDATIONS: Best Practice - Game Day Prep Protocol implemented with great success. 15% faster order fulfillment on game days. Staff Recognition: Maria Gonzalez received 12 positive customer mentions. THIN-CRUST SALES DECLINE NOTED: Regional data shows thin-crust pizza sales in Chicago declining 11% quarter-over-quarter. Contributing factors: Competitor Crispy Crust Co. opened 2 locations within 3 miles, Customer preference for pan-style during cold weather. Recommend seasonal menu adjustment. ACTION ITEMS: Replace freezer door seal, prep table compressor service needed.',
    'Wrigleyville audit score 94/100 (Excellent). Best practice: Game Day Prep Protocol. Alert: Thin-crust sales declining 11% due to competitor Crispy Crust Co.',
    ARRAY_CONSTRUCT('audit', 'chicago', 'wrigleyville', 'excellent', 'thin-crust-decline', 'competitor'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

-- Feedback documents
INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'FEEDBACK-2025-01',
    'feedback',
    'Customer Feedback Summary - January 2025',
    '2025-01-06'::DATE,
    NULL,
    'CUSTOMER FEEDBACK SUMMARY - Period: January 1-6, 2025, Total Reviews: 847. Overall NPS: 64 (+3 vs Dec). Scores: Food Quality 4.3/5, Delivery Speed 3.9/5 (DOWN 0.2), App Experience 4.5/5, Value 4.0/5. TOP POSITIVE: Pizza quality (312 mentions), App convenience (198 mentions), Friendly staff (156 mentions). TOP NEGATIVE: DELIVERY DELAYS (178 mentions) - 45% from Chicago stores, traffic congestion around I-90 construction, game day staffing issues. Order accuracy (89 mentions) - highest error rates at STR007 Manhattan, STR003 Tempe, STR004 Chicago Loop. Price concerns (67 mentions). COMPETITOR MENTIONS: Crispy Crust Co. (34 mentions in Chicago), FastSlice (28 mentions on delivery speed). Notable quote: "Crispy Crust Co. opened near my office. Their thin crust is crispier and $3 cheaper."',
    'January feedback: NPS 64. Main issues: Delivery delays (especially Chicago/I-90), order accuracy. Competitor Crispy Crust Co. mentioned 34 times.',
    ARRAY_CONSTRUCT('feedback', 'nps', 'delivery-delays', 'chicago', 'competitor', 'crispy-crust'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

INSERT INTO PIZZA_DOCUMENTS (document_id, document_type, document_title, document_date, store_id, content, summary, tags, created_at, updated_at)
SELECT 
    'REVIEW-CHI-20250106',
    'review',
    'Chicago Customer Reviews - January 6, 2025',
    '2025-01-06'::DATE,
    'STR004',
    'CUSTOMER REVIEWS - CHICAGO STORES - January 6, 2025. STR004 Chicago Loop: Rating 3.2/5 (Below Average), 23 reviews. Issues: Thin crust soggy and cold, delivery delays 20-45 minutes, I-90 construction affecting times, multiple customers mentioning switching to Crispy Crust. Quote: "Pizza arrived an hour late, completely cold. WORST experience ever." Quote: "Third late delivery this month. Switching to Crispy Crust." STR005 Wrigleyville: Rating 4.1/5 (Good), 31 reviews. Positive game day experience, Maria praised for service. Some thin-crust quality complaints. STR006 Naperville: Rating 3.8/5, 18 reviews. Thin-crust decline mentioned. KEY INSIGHTS: 11 mentions of thin-crust quality issues, 4 explicit Crispy Crust Co. mentions, 3 customers explicitly switching. I-90 construction in 8 reviews. Evening deliveries most affected (5-8pm).',
    'Chicago reviews Jan 6: Loop rated 3.2/5 (delivery issues, I-90 traffic), Wrigleyville 4.1/5 (good). Thin-crust quality declining, Crispy Crust competitor threat.',
    ARRAY_CONSTRUCT('review', 'chicago', 'thin-crust', 'delivery-delay', 'i90-traffic', 'crispy-crust', 'competitor'),
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP();

-- Verify documents loaded
SELECT document_id, document_type, document_title, store_id FROM PIZZA_DOCUMENTS;

-- ============================================================================
-- Create Cortex Search Service
-- ============================================================================

-- Create the search service on the documents table
-- NOTE: Update WAREHOUSE name to match your environment
CREATE OR REPLACE CORTEX SEARCH SERVICE PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENT_SEARCH
  ON content
  ATTRIBUTES document_type, document_title, store_id, document_date, summary
  WAREHOUSE = CORTEX  -- Replace with your warehouse name
  TARGET_LAG = '1 hour'
  AS (
    SELECT 
      document_id,
      document_type,
      document_title,
      document_date,
      store_id,
      content,
      summary
    FROM PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS
  );

-- ============================================================================
-- Verify the search service was created
-- ============================================================================
SHOW CORTEX SEARCH SERVICES IN SCHEMA PIZZA_INTELLIGENCE.DOCUMENTS;

-- ============================================================================
-- Verify documents are loaded and searchable
-- ============================================================================
-- Test query: Find documents about delivery delays in Chicago
SELECT 
    document_id,
    document_type,
    document_title,
    summary
FROM PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS
WHERE CONTAINS(LOWER(content), 'delivery') 
   AND CONTAINS(LOWER(content), 'chicago');

-- Test query: Find documents about thin crust and competitors
SELECT 
    document_id,
    document_type,
    document_title,
    summary
FROM PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENTS
WHERE CONTAINS(LOWER(content), 'thin') 
   AND CONTAINS(LOWER(content), 'crispy crust');

-- ============================================================================
-- SUCCESS! 
-- ============================================================================
-- The Cortex Search service is now ready for Snowflake Intelligence.
-- 
-- NEXT STEP: Create the Pizza Ops Agent in Snowflake Intelligence UI
-- 1. Go to ai.snowflake.com
-- 2. Create a new Agent
-- 3. Add Cortex Search tool pointing to: PIZZA_INTELLIGENCE.DOCUMENTS.PIZZA_DOCUMENT_SEARCH
-- 4. The agent will automatically use this service when answering questions
--    like "Why did thin-crust sales dip in Chicago?"
-- ============================================================================

SELECT 'Cortex Search setup complete! Ready for Snowflake Intelligence.' AS status;
