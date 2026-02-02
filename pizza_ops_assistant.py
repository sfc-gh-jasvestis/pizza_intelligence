"""
Pizza Ops Assistant - Store Manager AI Chat Interface
Powered by Snowflake Cortex Analyst + Cortex Search

This Streamlit app provides store managers with a natural language interface
to query pizza operations data including sales, deliveries, inventory, 
staffing, and campaign performance, as well as search through reviews,
feedback, and audit documents.
"""

import streamlit as st
import pandas as pd
import requests
import json
import numpy as np
from typing import Dict, List, Optional, Any

# =============================================================================
# CONFIGURATION
# =============================================================================

# Page config
st.set_page_config(
    page_title="Pizza Ops Assistant",
    page_icon=":pizza:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Snowflake account configuration (demo43)
SNOWFLAKE_ACCOUNT = "YOUR_ACCOUNT"
SNOWFLAKE_HOST = f"{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com"

# Semantic model configuration (for Cortex Analyst)
DATABASE = "PIZZA_INTELLIGENCE"
SCHEMA = "SEMANTIC_MODELS"
STAGE = "SEMANTIC_MODEL_STAGE"
SEMANTIC_MODEL_FILE = "pizza_intelligence.yaml"
SEMANTIC_MODEL_PATH = f"@{DATABASE}.{SCHEMA}.{STAGE}/{SEMANTIC_MODEL_FILE}"

# Cortex Search configuration
SEARCH_DATABASE = "PIZZA_INTELLIGENCE"
SEARCH_SCHEMA = "DOCUMENTS"
SEARCH_SERVICE = "PIZZA_DOCUMENT_SEARCH"

# API endpoints
ANALYST_API_ENDPOINT = "/api/v2/cortex/analyst/message"
API_TIMEOUT = 60000  # milliseconds

# Demo questions for store managers - aligned with repo showcase
# Mix: 3 "both" (Analyst+Search), 1 pure "analyst", 1 pure "search"
DEMO_QUESTIONS = [
    {
        "label": "Why were sales low?",
        "question": "Why were my sales lower than usual last night in this store?",
        "icon": "trending_down",
        "color": "red",
        "type": "both"  # Sales data + customer feedback from search
    },
    {
        "label": "Prep for busy weekend",
        "question": "What should I expect this Friday? How many orders do we typically get on Friday nights and what was last Friday's revenue?",
        "icon": "inventory_2",
        "color": "blue",
        "type": "both"  # Friday forecast + inventory docs + events calendar
    },
    {
        "label": "Delivery performance",
        "question": "Show me my delivery performance by week for the last month",
        "icon": "local_shipping",
        "color": "orange",
        "type": "analyst"  # Pure metrics/charts demo
    },
    {
        "label": "Top fixes this week",
        "question": "What are the top things I should fix this week to improve operations?",
        "icon": "build",
        "color": "violet",
        "type": "both"  # Performance metrics + audit documents
    },
    {
        "label": "Customer feedback",
        "question": "What are customers saying about us? Show me recent reviews - both the happy ones and complaints.",
        "icon": "sentiment_satisfied",
        "color": "green",
        "type": "search"  # Pure document search demo
    },
]


# =============================================================================
# SNOWFLAKE CONNECTION
# =============================================================================

def get_snowflake_connection():
    """Get or create Snowflake connection."""
    if "snowflake_conn" not in st.session_state:
        try:
            conn = st.connection("snowflake")
            st.session_state.snowflake_conn = conn
        except Exception as e:
            st.error(f"Failed to connect to Snowflake: {e}")
            st.info("Please configure your Snowflake connection in `.streamlit/secrets.toml`")
            st.stop()
    return st.session_state.snowflake_conn


def get_host_from_connection() -> str:
    """Get host URL for Cortex Analyst API."""
    return SNOWFLAKE_HOST


def get_auth_token() -> str:
    """Get authentication token from active connection."""
    conn = get_snowflake_connection()
    # Access the underlying snowflake-connector-python connection
    try:
        # Try different ways to access the raw connection
        if hasattr(conn, '_instance') and hasattr(conn._instance, '_raw_connection'):
            raw_conn = conn._instance._raw_connection
        elif hasattr(conn, 'raw_connection'):
            raw_conn = conn.raw_connection
        else:
            # Fallback: get session and use its connection
            session = conn.session()
            raw_conn = session._conn._conn
        return raw_conn.rest.token
    except Exception as e:
        st.error(f"Could not get auth token: {e}")
        raise


# =============================================================================
# MANAGER INSIGHTS - Generate actionable recommendations from data
# =============================================================================

def generate_manager_insights(question: str, data_summary: str, store_name: str) -> str:
    """
    Use Cortex LLM to generate actionable recommendations for store managers
    based on the data retrieved by Cortex Analyst.
    """
    if not data_summary:
        return None
        
    conn = get_snowflake_connection()
    
    prompt = f"""You are a helpful assistant for a pizza store manager at {store_name}.
Based on the following data, provide 2-3 brief, actionable recommendations.
Be concise and practical - this manager needs to know WHAT TO DO.

Question asked: {question}

Data retrieved:
{data_summary}

Provide your response in this format:
📊 **Key Insight:** [One sentence summary of what the data shows]

✅ **Recommended Actions:**
1. [First specific action]
2. [Second specific action]
3. [Third specific action if needed]

Keep it brief and actionable. No more than 100 words total."""

    # Escape single quotes for SQL
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    try:
        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                '{escaped_prompt}'
            ) as response
        """
        result = conn.session().sql(sql).collect()
        
        if result and len(result) > 0:
            response = result[0]['RESPONSE']
            # Escape $ signs to prevent LaTeX rendering in Streamlit
            response = response.replace("$", "\\$")
            return response
        return None
    except Exception as e:
        # Log error for debugging but don't break the app
        st.warning(f"Could not generate recommendations: {e}")
        return None


def generate_feedback_insights(question: str, documents: list, store_name: str) -> str:
    """
    Use Cortex LLM to generate actionable recommendations for store managers
    based on customer feedback and documents from Cortex Search.
    """
    if not documents:
        return None
        
    conn = get_snowflake_connection()
    
    # Summarize the documents for the LLM - include more content for better answers
    doc_summaries = []
    for doc in documents[:5]:  # Use up to 5 docs
        title = doc.get('DOCUMENT_TITLE', 'Untitled')
        doc_type = doc.get('DOCUMENT_TYPE', 'document')
        date = doc.get('DOCUMENT_DATE', 'Unknown')
        content = doc.get('CONTENT', '')[:2000]  # More content for context
        summary = doc.get('SUMMARY', '')
        doc_summaries.append(f"- [{doc_type.upper()}] {title} (Date: {date})\n  {summary}\n  Content: {content}")
    
    docs_text = "\n".join(doc_summaries)
    
    prompt = f"""You are a helpful assistant for a pizza store manager at {store_name}.
The manager asked: "{question}"

Based on the following documents, DIRECTLY ANSWER their question first, then provide recommendations.

Relevant documents:
{docs_text}

Provide your response in this exact format:

📋 **Direct Answer:**
[Answer the manager's specific question(s) directly using information from the documents. If they asked multiple things, answer each one clearly.]

📊 **Key Insight:** [One sentence summary of the main finding]

✅ **Recommended Actions:**
1. [First specific action]
2. [Second specific action]
3. [Third specific action if needed]

IMPORTANT: 
- Answer their EXACT questions first (e.g., if they asked about last audit date, tell them the date)
- If they asked for a list (like items to order), provide that list
- If they asked about events/games, check the calendar documents and tell them
- Be specific with dates, numbers, and items from the documents
- Keep total response under 200 words."""

    # Escape single quotes for SQL
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    try:
        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                '{escaped_prompt}'
            ) as response
        """
        result = conn.session().sql(sql).collect()
        
        if result and len(result) > 0:
            response = result[0]['RESPONSE']
            # Escape $ signs to prevent LaTeX rendering in Streamlit
            response = response.replace("$", "\\$")
            return response
        return None
    except Exception as e:
        st.warning(f"Could not generate recommendations: {e}")
        return None


def generate_combined_insights(question: str, sql_results: str, documents: list, store_name: str) -> str:
    """
    Generate unified insights combining structured data and document findings.
    Used for "both" type queries that leverage Cortex Analyst AND Cortex Search.
    """
    conn = get_snowflake_connection()
    
    # Prepare data summary
    data_summary = sql_results if sql_results else "No structured data available."
    
    # Prepare document summaries
    doc_summaries = []
    for doc in documents[:5]:
        title = doc.get('DOCUMENT_TITLE', 'Untitled')
        doc_type = doc.get('DOCUMENT_TYPE', 'document')
        content = doc.get('CONTENT', '')[:1500]
        summary = doc.get('SUMMARY', '')
        doc_summaries.append(f"- [{doc_type.upper()}] {title}\n  {summary}\n  Key content: {content}")
    
    docs_text = "\n".join(doc_summaries) if doc_summaries else "No relevant documents found."
    
    prompt = f"""You are an AI assistant for a pizza store manager at {store_name}.
The manager asked: "{question}"

You have TWO sources of information:

**1. STRUCTURED DATA (from database):**
{data_summary}

**2. DOCUMENTS (from search):**
{docs_text}

Provide a UNIFIED answer that combines insights from both sources in this format:

📊 **Data Summary:**
[Summarize what the numbers/data show - be specific with metrics]

📋 **Document Insights:**
[Key findings from relevant documents - inventory needs, calendar events, audit findings, etc.]

🎯 **Recommended Actions:**
1. [Action based on data]
2. [Action based on documents]
3. [Additional action if needed]

IMPORTANT:
- Combine insights from BOTH data and documents
- Be specific with numbers, dates, and item names
- If the question has multiple parts, answer ALL of them
- Keep total response under 250 words"""

    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    try:
        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                '{escaped_prompt}'
            ) as response
        """
        result = conn.session().sql(sql).collect()
        
        if result and len(result) > 0:
            response = result[0]['RESPONSE']
            response = response.replace("$", "\\$")
            return response
        return None
    except Exception as e:
        st.warning(f"Could not generate combined insights: {e}")
        return None


# =============================================================================
# QUERY TYPE DETECTION
# =============================================================================

def detect_query_type(question: str) -> str:
    """
    Detect whether a question should use Cortex Analyst (structured data)
    or Cortex Search (documents/reviews).
    
    Returns: 'analyst', 'search', or 'both'
    """
    question_lower = question.lower()
    
    # Keywords that suggest document/review search
    search_keywords = [
        'review', 'reviews', 'feedback', 'complaint', 'complaints',
        'audit', 'audits', 'customer said', 'customers saying',
        'mention', 'mentions', 'mentioned', 'comment', 'comments',
        'sentiment', 'opinion', 'quote', 'invoice', 'invoices',
        'supplier', 'quality issue', 'quality issues', 'document',
        'report', 'crispy crust', 'competitor', 'competitors',
        # New keywords for inventory/calendar queries
        'order from supplier', 'need to order', 'reorder', 'restock',
        'ingredient', 'ingredients', 'kitchen', 'par level', 'par levels',
        'calendar', 'game', 'games', 'event', 'events', 'bulls', 'super bowl',
        'weekend', 'upcoming', 'maintenance', 'equipment'
    ]
    
    # Keywords that suggest structured data analysis
    analyst_keywords = [
        'total', 'sum', 'average', 'count', 'how many', 'how much',
        'sales', 'revenue', 'orders', 'delivery rate', 'late delivery',
        'inventory', 'stock', 'staffing', 'staff', 'roster', 'schedule',
        'campaign', 'roi', 'performance', 'trend', 'compare', 'comparison',
        'by store', 'by city', 'by region', 'this week', 'last week',
        'this month', 'last month', 'today', 'yesterday', 'last night',
        'friday', 'saturday', 'sunday', 'game day', 'thin-crust', 'thin crust',
        'pan pizza', 'pan-pizza', 'crust type', 'product'
    ]
    
    # Keywords that suggest needing BOTH data and documents
    combined_keywords = [
        'why did', 'why are', 'why is', 'what caused', 'root cause',
        'reason for', 'dip', 'decline', 'drop', 'decrease', 'getting worse',
        'what\'s causing', 'whats causing'
    ]
    
    search_score = sum(1 for kw in search_keywords if kw in question_lower)
    analyst_score = sum(1 for kw in analyst_keywords if kw in question_lower)
    combined_score = sum(1 for kw in combined_keywords if kw in question_lower)
    
    # If question asks "why" about data trends, use both
    if combined_score > 0 and analyst_score > 0:
        return 'both'
    
    # If question asks "why" in general, might need both
    if 'why' in question_lower and analyst_score > 0:
        return 'both'
    
    if search_score > analyst_score:
        return 'search'
    elif analyst_score > 0:
        return 'analyst'
    else:
        # Default to analyst for data questions
        return 'analyst'


# =============================================================================
# CORTEX ANALYST API
# =============================================================================

def send_analyst_message(messages: List[Dict]) -> Dict[str, Any]:
    """
    Send a message to Cortex Analyst API and return the response.
    
    Args:
        messages: Conversation history in Cortex Analyst format
        
    Returns:
        API response with analyst message and metadata
    """
    host = get_host_from_connection()
    token = get_auth_token()
    
    request_body = {
        "messages": messages,
        "semantic_model_file": SEMANTIC_MODEL_PATH,
    }
    
    headers = {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    url = f"https://{host}{ANALYST_API_ENDPOINT}"
    
    try:
        response = requests.post(
            url=url,
            json=request_body,
            headers=headers,
            timeout=API_TIMEOUT / 1000,
        )
        
        request_id = response.headers.get("X-Snowflake-Request-Id", "unknown")
        
        if response.status_code < 400:
            result = response.json()
            result["request_id"] = request_id
            return result
        else:
            error_data = response.json() if response.text else {}
            raise Exception(
                f"API Error (request_id: {request_id})\n"
                f"Status: {response.status_code}\n"
                f"Message: {error_data.get('message', response.text)}"
            )
            
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. Please try a simpler question.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")


# =============================================================================
# CORTEX SEARCH
# =============================================================================

def search_documents(query: str, limit: int = 5) -> List[Dict]:
    """
    Search documents using keyword matching with relevance ranking.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of matching documents with metadata
    """
    conn = get_snowflake_connection()
    
    # Extract key terms for matching (filter out common/generic words)
    stop_words = {'what', 'are', 'the', 'about', 'this', 'that', 'with', 'from', 
                  'they', 'have', 'been', 'were', 'saying', 'customers', 'does',
                  'said', 'tell', 'show', 'find', 'search', 'look', 'give', 'any',
                  'pizza', 'store', 'stores', 'our', 'their', 'customer', 'last',
                  'days', 'week', 'month', 'mentioned', 'for', 'chicago', 'loop',
                  'when', 'was', 'time', 'ran', 'all', 'provide', 'list', 'need',
                  'check', 'see', 'can', 'you', 'please', 'also', 'and', 'do', 'me'}
    
    # Priority terms that should always be included in search if found in query
    priority_terms = {'audit', 'inventory', 'ingredient', 'ingredients', 'supplier', 
                      'suppliers', 'order', 'reorder', 'game', 'games', 'weekend',
                      'calendar', 'event', 'events', 'kitchen', 'stock', 'bulls',
                      'review', 'feedback', 'invoice'}
    
    # First, check for priority terms in the query
    query_lower = query.lower()
    key_terms = []
    
    # Add priority terms first
    for pt in priority_terms:
        if pt in query_lower:
            key_terms.append(pt)
    
    # Then add other significant terms from the query
    for term in query.split():
        clean_term = term.lower().strip('?.,!')
        if len(clean_term) > 2 and clean_term not in stop_words and clean_term not in key_terms:
            key_terms.append(clean_term)
    
    if not key_terms:
        # Return all documents if no good search terms
        search_sql = f"""
        SELECT 
            DOCUMENT_ID,
            DOCUMENT_TYPE,
            DOCUMENT_TITLE,
            DOCUMENT_DATE,
            STORE_ID,
            SUMMARY,
            CONTENT
        FROM {SEARCH_DATABASE}.{SEARCH_SCHEMA}.PIZZA_DOCUMENTS
        LIMIT {limit}
        """
    else:
        # Build relevance score - boost for hyphenated compound terms (e.g., "thin-crust")
        score_parts = []
        conditions = []
        
        # Use up to 10 key terms for better matching
        for i, term in enumerate(key_terms[:10]):
            safe_term = term.replace("'", "''")
            # Score for exact term match - boost content matches
            score_parts.append(f"CASE WHEN LOWER(content) LIKE '%{safe_term}%' THEN 3 ELSE 0 END")
            score_parts.append(f"CASE WHEN LOWER(summary) LIKE '%{safe_term}%' THEN 1 ELSE 0 END")
            score_parts.append(f"CASE WHEN LOWER(document_title) LIKE '%{safe_term}%' THEN 2 ELSE 0 END")
            conditions.append(f"LOWER(content) LIKE '%{safe_term}%'")
            conditions.append(f"LOWER(summary) LIKE '%{safe_term}%'")
            conditions.append(f"LOWER(document_title) LIKE '%{safe_term}%'")
            
            # Also check for hyphenated version with next term (e.g., thin-crust)
            if i < len(key_terms) - 1:
                compound = f"{safe_term}-{key_terms[i+1].replace(chr(39), chr(39)+chr(39))}"
                score_parts.append(f"CASE WHEN LOWER(CONTENT) LIKE '%{compound}%' THEN 5 ELSE 0 END")
        
        score_calc = " + ".join(score_parts)
        where_clause = " OR ".join(conditions)
        
        search_sql = f"""
        WITH scored_docs AS (
            SELECT 
                DOCUMENT_ID,
                DOCUMENT_TYPE,
                DOCUMENT_TITLE,
                DOCUMENT_DATE,
                STORE_ID,
                SUMMARY,
                CONTENT,
                ({score_calc}) AS RELEVANCE_SCORE
            FROM {SEARCH_DATABASE}.{SEARCH_SCHEMA}.PIZZA_DOCUMENTS
            WHERE {where_clause}
        )
        SELECT * FROM scored_docs
        WHERE RELEVANCE_SCORE >= 1
        ORDER BY RELEVANCE_SCORE DESC, DOCUMENT_DATE DESC
        LIMIT {limit}
        """
    
    try:
        df = conn.query(search_sql)
        results = df.to_dict('records')
        return results
    except Exception as e:
        # Try reconnecting
        try:
            if "snowflake_conn" in st.session_state:
                del st.session_state.snowflake_conn
            conn = get_snowflake_connection()
            df = conn.query(search_sql)
            return df.to_dict('records')
        except Exception as retry_error:
            st.error(f"Document search failed: {retry_error}")
            return []


def format_search_results(results: List[Dict], query: str, show_documents: bool = False) -> str:
    """Format search results into a readable response.
    
    Args:
        results: List of document results from Cortex Search
        query: The user's query
        show_documents: If True, show document details. If False, just acknowledge what was found.
    """
    if not results:
        return f"I couldn't find any documents matching '{query}'. Try rephrasing your question or ask about specific topics like reviews, audits, or invoices."
    
    # Check if this is a happy/unhappy customers query
    is_customer_query = any(word in query.lower() for word in ['happy', 'unhappy', 'customer', 'review', 'feedback'])
    
    if is_customer_query:
        return format_customer_reviews(results, query)
    
    # For non-customer queries, just provide a brief acknowledgment
    # The recommendations will provide the actual insights
    doc_types = set()
    for doc in results:
        doc_type = doc.get('DOCUMENT_TYPE', 'document')
        if doc_type:
            doc_types.add(doc_type.lower())
    
    type_str = ", ".join(sorted(doc_types)) if doc_types else "documents"
    response = f"I found **{len(results)} relevant document(s)** ({type_str}) to help answer your question."
    
    # Optionally show document details
    if show_documents:
        response_parts = [response, "\n"]
        for i, doc in enumerate(results, 1):
            doc_type = doc.get('DOCUMENT_TYPE', 'document').title()
            title = doc.get('DOCUMENT_TITLE', 'Untitled')
            date = doc.get('DOCUMENT_DATE', 'Unknown date')
            store = doc.get('STORE_ID', 'All stores')
            summary = doc.get('SUMMARY', '')
            
            response_parts.append(f"### {i}. {title}")
            response_parts.append(f"**Type:** {doc_type} | **Date:** {date} | **Store:** {store}")
            if summary:
                response_parts.append(f"\n> {summary}\n")
            response_parts.append("---")
        return "\n".join(response_parts)
    
    return response


def format_customer_reviews(results: List[Dict], query: str) -> str:
    """Format customer reviews with clear happy/unhappy sections."""
    import re
    
    response_parts = ["## 📋 Customer Feedback Summary\n"]
    response_parts.append(f"Found **{len(results)} review(s)** from recent customer feedback:\n")
    
    happy_reviews = []
    unhappy_reviews = []
    
    for doc in results:
        title = doc.get('DOCUMENT_TITLE', 'Untitled')
        content = doc.get('CONTENT', '')
        summary = doc.get('SUMMARY', '')
        doc_date = doc.get('DOCUMENT_DATE', 'Unknown')
        
        # Use content if available, otherwise summary
        text_to_parse = content if content else summary
        
        if not text_to_parse:
            continue
        
        # Split into sections based on headers
        # Look for HAPPIEST/POSITIVE and UNHAPPIEST/NEGATIVE sections
        happy_section = ""
        unhappy_section = ""
        
        # Find happy section
        happy_patterns = [
            r'HAPPIEST CUSTOMERS.*?(?=UNHAPPIEST|NEGATIVE|WEEKLY|$)',
            r'POSITIVE REVIEWS.*?(?=NEGATIVE|UNHAPPIEST|Daily|$)',
            r'HAPPY:.*?(?=UNHAPPY|$)',
        ]
        for pattern in happy_patterns:
            match = re.search(pattern, text_to_parse, re.DOTALL | re.IGNORECASE)
            if match:
                happy_section = match.group(0)
                break
        
        # Find unhappy section
        unhappy_patterns = [
            r'UNHAPPIEST CUSTOMERS.*?(?=WEEKLY|TOP ISSUES|$)',
            r'NEGATIVE REVIEWS.*?(?=Daily|WEEKLY|$)',
            r'UNHAPPY:.*?$',
        ]
        for pattern in unhappy_patterns:
            match = re.search(pattern, text_to_parse, re.DOTALL | re.IGNORECASE)
            if match:
                unhappy_section = match.group(0)
                break
        
        # Parse individual reviews from happy section
        if happy_section:
            reviews = parse_review_section(happy_section, 'happy', doc_date)
            happy_reviews.extend(reviews)
        
        # Parse individual reviews from unhappy section
        if unhappy_section:
            reviews = parse_review_section(unhappy_section, 'unhappy', doc_date)
            unhappy_reviews.extend(reviews)
    
    # Display Happy Customers
    response_parts.append("### 😊 Happy Customers\n")
    if happy_reviews:
        for i, review in enumerate(happy_reviews[:5], 1):
            name = review.get('name', 'Anonymous')
            rating = review.get('rating', '5')
            comment = review.get('comment', '')
            date = review.get('date', '')
            
            stars = int(rating) if rating.isdigit() else 5
            rating_stars = '⭐' * stars
            date_str = f" ({date})" if date else ""
            response_parts.append(f"**{i}. {name}**{date_str} {rating_stars}")
            response_parts.append(f"> _{comment}_\n")
    else:
        response_parts.append("_No specific happy customer reviews found in recent feedback._\n")
    
    # Display Unhappy Customers
    response_parts.append("### 😞 Unhappy Customers\n")
    if unhappy_reviews:
        for i, review in enumerate(unhappy_reviews[:5], 1):
            name = review.get('name', 'Anonymous')
            rating = review.get('rating', '1')
            comment = review.get('comment', '')
            date = review.get('date', '')
            
            stars = int(rating) if rating.isdigit() else 1
            rating_stars = '⭐' * stars
            date_str = f" ({date})" if date else ""
            response_parts.append(f"**{i}. {name}**{date_str} {rating_stars}")
            response_parts.append(f"> ⚠️ _{comment}_\n")
    else:
        response_parts.append("_No specific unhappy customer reviews found in recent feedback._\n")
    
    return "\n".join(response_parts)


def parse_review_section(section: str, sentiment: str, doc_date: str) -> List[Dict]:
    """Parse individual reviews from a section of text."""
    import re
    reviews = []
    
    # Pattern: "Name X. (Date, N stars):" or "Name X. (Date):" followed by quoted text
    # Examples: 
    #   Sarah M. (Jan 30): "Best deep dish..."
    #   Robert H. (Jan 30, 2 stars): "Waited 55 minutes..."
    #   Tom B. (5 stars): "Perfect late-night..."
    
    # Main pattern - capture name, metadata, and quoted comment
    pattern = r'([A-Z][a-z]+\s+[A-Z]\.?)\s*\(([^)]+)\):\s*"([^"]+)"'
    
    matches = re.findall(pattern, section)
    
    for match in matches:
        name = match[0].strip()
        meta = match[1].strip()  # Could be "Jan 30" or "Jan 30, 2 stars" or "5 stars"
        comment = match[2].strip()
        
        # Extract rating from meta if present
        rating_match = re.search(r'(\d)\s*star', meta, re.IGNORECASE)
        if rating_match:
            rating = rating_match.group(1)
        else:
            rating = '5' if sentiment == 'happy' else '2'
        
        # Extract date from meta if present
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d+', meta, re.IGNORECASE)
        if date_match:
            review_date = date_match.group(0)
        else:
            review_date = doc_date
        
        reviews.append({
            'name': name,
            'rating': rating,
            'comment': comment,
            'date': review_date
        })
    
    return reviews


def extract_individual_reviews(text: str, sentiment: str) -> List[Dict]:
    """Extract individual customer reviews from text - legacy function."""
    return parse_review_section(text, sentiment, '')


# =============================================================================
# SQL EXECUTION
# =============================================================================

def execute_sql(sql: str) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame."""
    conn = get_snowflake_connection()
    return conn.query(sql)


# =============================================================================
# CHAT UI COMPONENTS
# =============================================================================

def display_message_content(content: List[Dict], message_index: int) -> Optional[str]:
    """
    Display message content blocks (text, sql, suggestions).
    
    Returns the SQL statement if present, for data display.
    """
    sql_statement = None
    
    # Handle case where content is a string instead of list
    if isinstance(content, str):
        st.markdown(content)
        return None
    
    # Handle empty or None content
    if not content:
        return None
    
    for item in content:
        # Skip if item is not a dict (defensive)
        if not isinstance(item, dict):
            st.markdown(str(item))
            continue
            
        content_type = item.get("type")
        
        if content_type == "text":
            st.markdown(item.get("text", ""))
            
        elif content_type == "sql":
            sql_statement = item.get("statement", "")
            with st.expander("View SQL Query", expanded=False):
                st.code(sql_statement, language="sql")
                
        elif content_type == "suggestions":
            suggestions = item.get("suggestions", [])
            if suggestions:
                st.markdown("**Suggested follow-up questions:**")
                for idx, suggestion in enumerate(suggestions):
                    if st.button(
                        suggestion,
                        key=f"suggestion_{message_index}_{idx}",
                        use_container_width=True,
                    ):
                        st.session_state.pending_question = suggestion
                        st.rerun()
    
    return sql_statement


def display_search_content(content: str, documents: List[Dict], message_index: int):
    """Display Cortex Search results with document details."""
    st.markdown(content)
    
    # Show expandable document details
    if documents:
        with st.expander("View Full Document Content", expanded=False):
            for doc in documents:
                title = doc.get('DOCUMENT_TITLE', 'Untitled')
                full_content = doc.get('CONTENT', '')
                st.markdown(f"**{title}**")
                st.text(full_content[:2000] + "..." if len(full_content) > 2000 else full_content)
                st.divider()


def display_sql_results(sql: str) -> str:
    """Execute SQL and display results with visualization options. Returns data as string for LLM."""
    try:
        with st.spinner("Running query..."):
            df = execute_sql(sql)
        
        if df is None or df.empty:
            st.info("Query returned no results.")
            return None
        
        st.success(f"Found {len(df)} row(s)")
        
        # Create tabs for different views - only show chart tab if enough data points
        if len(df) >= 3 and len(df.columns) >= 2:
            tab_data, tab_chart = st.tabs(["📊 Data", "📈 Chart"])
            
            with tab_data:
                st.dataframe(df, use_container_width=True, hide_index=True)
                
            with tab_chart:
                # Auto-select chart type based on data
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                
                # Filter out non-meaningful columns for charting
                skip_columns = ['priority', 'rank', 'id', 'index', 'row', 'num', 'number']
                chartable_cols = [c for c in numeric_cols if not any(skip in c.lower() for skip in skip_columns)]
                
                if chartable_cols and len(chartable_cols) >= 1:
                    x_col = df.columns[0]  # First column is usually the category/date
                    
                    # Smart column selection based on column names
                    # Priority: Revenue > Orders > Late% > other metrics
                    priority_keywords = [
                        ('revenue', '#2ECC71'),   # Green for money
                        ('order', '#3498DB'),     # Blue for orders  
                        ('%', '#E74C3C'),         # Red for percentages (usually problems)
                        ('rate', '#E74C3C'),      # Red for rates
                        ('late', '#E74C3C'),      # Red for late
                        ('time', '#9B59B6'),      # Purple for time
                        ('deliver', '#3498DB'),   # Blue for deliveries
                    ]
                    
                    y_col = None
                    chart_color = '#3498DB'  # Default blue
                    
                    for keyword, color in priority_keywords:
                        matching = [c for c in chartable_cols if keyword in c.lower()]
                        if matching:
                            y_col = matching[0]
                            chart_color = color
                            break
                    
                    # Fallback to first chartable column
                    if not y_col:
                        y_col = chartable_cols[0]
                    
                    st.bar_chart(df, x=x_col, y=y_col, color=chart_color)
                    st.caption(f"📊 {y_col} by {x_col}")
                else:
                    st.info("This data is best viewed as a table.")
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Return data as string for LLM processing (limit to first 10 rows)
        return df.head(10).to_string(index=False)
            
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None


def process_user_question(question: str, force_type: Optional[str] = None):
    """Process a user question through Cortex Analyst or Cortex Search."""
    # Detect query type
    query_type = force_type or detect_query_type(question)
    
    # Add user message to history
    user_message = {
        "role": "user",
        "content": [{"type": "text", "text": question}],
        "query_type": query_type
    }
    st.session_state.messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(question)
    
    # Process based on query type
    with st.chat_message("assistant", avatar=":material/robot:"):
        if query_type == "search":
            # Use Cortex Search for document queries
            with st.spinner("Searching documents..."):
                try:
                    results = search_documents(question, limit=5)
                    response_text = format_search_results(results, question)
                    
                    # Display results
                    display_search_content(response_text, results, len(st.session_state.messages))
                    
                    # Generate recommendations from feedback
                    store_name = st.session_state.get("selected_store", "your store")
                    insights = None
                    if results:
                        with st.spinner("Generating recommendations..."):
                            insights = generate_feedback_insights(question, results, store_name)
                            if insights:
                                st.divider()
                                st.markdown("### 💡 Answer & Recommendations")
                                st.markdown(insights)
                    
                    # Store assistant response WITH recommendations
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": response_text}],
                        "query_type": "search",
                        "documents": results,
                        "recommendations": insights,
                    })
                    
                except Exception as e:
                    st.error(f"Search error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": f"Sorry, I encountered a search error: {e}"}],
                        "query_type": "search",
                    })
        
        elif query_type == "both":
            # Answer with both data and documents - the power combo!
            st.info("🔍 Combining data analysis with document search...")
            
            sql_results_text = ""
            sql_statement = None
            analyst_content = []
            results = []
            
            # First, get structured data from Cortex Analyst
            with st.spinner("📊 Analyzing structured data..."):
                try:
                    api_messages = [{
                        "role": "user",
                        "content": [{"type": "text", "text": question}]
                    }]
                    response = send_analyst_message(api_messages)
                    
                    # Extract response content with safety checks
                    message_obj = response.get("message", {})
                    if isinstance(message_obj, str):
                        analyst_content = [{"type": "text", "text": message_obj}]
                    else:
                        analyst_content = message_obj.get("content", [])
                    
                    # Extract SQL and execute to get results for LLM context
                    for item in analyst_content:
                        if isinstance(item, dict) and item.get("type") == "sql":
                            sql_statement = item.get("statement", "")
                            if sql_statement:
                                try:
                                    df = execute_sql(sql_statement)
                                    if not df.empty:
                                        sql_results_text = df.to_string(index=False)
                                except Exception:
                                    pass
                            break
                        elif isinstance(item, dict) and item.get("type") == "text":
                            sql_results_text += item.get("text", "") + "\n"
                    
                    # Display data section
                    st.markdown("### 📊 Data Analysis")
                    display_message_content(analyst_content, len(st.session_state.messages))
                    if sql_statement:
                        display_sql_results(sql_statement)
                        
                except Exception as e:
                    st.warning(f"Could not get data analysis: {e}")
            
            # Then, search documents for context
            with st.spinner("📋 Searching related documents..."):
                try:
                    # Expand search query with topic-relevant keywords for better doc matching
                    search_query = question
                    question_lower = question.lower()
                    
                    # For weekend/Friday prep questions, add inventory and events keywords
                    if any(word in question_lower for word in ['friday', 'weekend', 'prep', 'prepare', 'busy']):
                        search_query = question + " inventory order restock events games calendar weekend prep"
                    # For operations/fixes questions, add audit keywords
                    elif any(word in question_lower for word in ['fix', 'improve', 'operations', 'issues']):
                        search_query = question + " audit findings issues maintenance equipment"
                    # For sales questions, add customer feedback
                    elif any(word in question_lower for word in ['sales', 'revenue', 'lower', 'down']):
                        search_query = question + " customer review feedback complaints"
                    
                    results = search_documents(search_query, limit=5)
                    if results:
                        st.markdown("### 📋 Related Documents Found")
                        doc_types = set(doc.get('DOCUMENT_TYPE', '') for doc in results)
                        st.caption(f"Found {len(results)} relevant documents: {', '.join(filter(None, doc_types))}")
                except Exception as e:
                    st.warning(f"Could not search documents: {e}")
                    results = []
            
            # Generate unified insights combining both sources
            combined_insights = None
            if sql_results_text or results:
                with st.spinner("🎯 Generating unified recommendations..."):
                    store_name = st.session_state.get("selected_store", "your store")
                    combined_insights = generate_combined_insights(
                        question, 
                        sql_results_text, 
                        results, 
                        store_name
                    )
                    if combined_insights:
                        st.divider()
                        st.markdown("### 🎯 Combined Analysis & Recommendations")
                        st.markdown(combined_insights)
            
            # Store combined response
            st.session_state.messages.append({
                "role": "assistant",
                "content": analyst_content,
                "query_type": "both",
                "sql": sql_statement,
                "documents": results,
                "recommendations": combined_insights,
            })
        
        else:
            # Default: Use Cortex Analyst for structured data
            with st.spinner("Analyzing your question..."):
                try:
                    # Build message history for multi-turn conversation
                    api_messages = []
                    for msg in st.session_state.messages:
                        if msg.get("query_type") != "search":  # Only include analyst messages
                            # Ensure content is in proper format for API
                            msg_content = msg["content"]
                            if isinstance(msg_content, str):
                                msg_content = [{"type": "text", "text": msg_content}]
                            elif not isinstance(msg_content, list):
                                msg_content = [{"type": "text", "text": str(msg_content)}]
                            
                            api_messages.append({
                                "role": msg["role"] if msg["role"] != "assistant" else "analyst",
                                "content": msg_content
                            })
                    
                    response = send_analyst_message(api_messages)
                    
                    # Extract response content with safety checks
                    message_obj = response.get("message", {})
                    if isinstance(message_obj, str):
                        analyst_content = [{"type": "text", "text": message_obj}]
                    else:
                        analyst_content = message_obj.get("content", [])
                    request_id = response.get("request_id")
                    
                    # Display the response
                    message_idx = len(st.session_state.messages)
                    sql_statement = display_message_content(analyst_content, message_idx)
                    
                    # Execute and display SQL results if present
                    data_summary = None
                    if sql_statement:
                        st.divider()
                        data_summary = display_sql_results(sql_statement)
                    
                    # Generate manager insights/recommendations
                    store_name = st.session_state.get("selected_store", "your store")
                    insights = None
                    if data_summary:
                        with st.spinner("Generating recommendations..."):
                            insights = generate_manager_insights(question, data_summary, store_name)
                            if insights:
                                st.divider()
                                st.markdown("### 💡 Manager Recommendations")
                                st.markdown(insights)
                            else:
                                st.info("Could not generate recommendations for this query.")
                    elif sql_statement:
                        # SQL exists but no data returned
                        st.warning("⚠️ Query returned no data. Try adjusting your question or date range.")
                    
                    # Store assistant response WITH recommendations
                    st.session_state.messages.append({
                        "role": "analyst",
                        "content": analyst_content,
                        "request_id": request_id,
                        "sql": sql_statement,
                        "query_type": "analyst",
                        "recommendations": insights,  # Store recommendations!
                    })
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.messages.append({
                        "role": "analyst",
                        "content": [{"type": "text", "text": f"Sorry, I encountered an error: {e}"}],
                        "query_type": "analyst",
                    })


# =============================================================================
# DASHBOARD FUNCTIONS - Traffic Map & Weather
# =============================================================================

# Store coordinates for map centering (Chicago Loop only)
STORE_COORDINATES = {
    "Chicago Loop": {"lat": 41.8819, "lon": -87.6278},
}

WEATHER_ICONS = {
    "sunny": "☀️",
    "clear": "☀️",
    "cold": "❄️",
    "snowy": "🌨️",
    "rainy": "🌧️",
    "hot": "🌡️",
    "mild": "🌤️",
    "cloudy": "☁️",
}

def get_delivery_map_data(store_name: str) -> pd.DataFrame:
    """Get delivery data with generated coordinates for mapping."""
    conn = get_snowflake_connection()
    
    # Get store center coordinates
    store_coords = STORE_COORDINATES.get(store_name, {"lat": 41.8819, "lon": -87.6278})
    
    sql = f"""
    SELECT 
        delivery_id,
        delivery_date,
        delivery_duration_min,
        is_late,
        late_minutes,
        late_reason,
        weather_condition,
        delivery_distance_km,
        customer_rating
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date >= CURRENT_DATE() - 7
    ORDER BY delivery_date DESC
    LIMIT 100
    """
    
    df = conn.query(sql)
    
    if df.empty:
        return pd.DataFrame()
    
    # Generate coordinates around store center based on delivery distance
    np.random.seed(42)  # For consistent demo results
    n = len(df)
    
    # Spread deliveries based on distance (further = more spread)
    distance_factor = df['DELIVERY_DISTANCE_KM'].fillna(3) / 10
    
    # Random angle for each delivery
    angles = np.random.uniform(0, 2 * np.pi, n)
    
    # Calculate lat/lon offsets (roughly 0.01 degree = 1km)
    lat_offsets = distance_factor * np.sin(angles) * 0.01
    lon_offsets = distance_factor * np.cos(angles) * 0.01
    
    df['lat'] = store_coords['lat'] + lat_offsets
    df['lon'] = store_coords['lon'] + lon_offsets
    
    return df


def get_weather_stats(store_name: str) -> dict:
    """Get current weather and its impact on deliveries."""
    conn = get_snowflake_connection()
    
    sql = f"""
    SELECT 
        weather_condition,
        COUNT(*) as total_deliveries,
        SUM(CASE WHEN is_late THEN 1 ELSE 0 END) as late_deliveries,
        ROUND(AVG(delivery_duration_min), 1) as avg_duration,
        ROUND(AVG(CASE WHEN is_late THEN late_minutes ELSE 0 END), 1) as avg_delay
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date = CURRENT_DATE() - 1
    GROUP BY weather_condition
    ORDER BY total_deliveries DESC
    LIMIT 1
    """
    
    df = conn.query(sql)
    
    if df.empty:
        # Get most recent weather if no data for yesterday
        sql2 = f"""
        SELECT 
            weather_condition,
            COUNT(*) as total_deliveries,
            SUM(CASE WHEN is_late THEN 1 ELSE 0 END) as late_deliveries,
            ROUND(AVG(delivery_duration_min), 1) as avg_duration
        FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
        WHERE store_name = '{store_name}'
          AND delivery_date >= CURRENT_DATE() - 7
        GROUP BY weather_condition
        ORDER BY total_deliveries DESC
        LIMIT 1
        """
        df = conn.query(sql2)
    
    if df.empty:
        return {
            "condition": "unknown",
            "icon": "❓",
            "total": 0,
            "late": 0,
            "late_pct": 0,
            "avg_duration": 0
        }
    
    row = df.iloc[0]
    condition = str(row['WEATHER_CONDITION']).lower()
    
    return {
        "condition": condition.title(),
        "icon": WEATHER_ICONS.get(condition, "🌡️"),
        "total": int(row['TOTAL_DELIVERIES']),
        "late": int(row['LATE_DELIVERIES']),
        "late_pct": round(row['LATE_DELIVERIES'] / row['TOTAL_DELIVERIES'] * 100, 1) if row['TOTAL_DELIVERIES'] > 0 else 0,
        "avg_duration": float(row['AVG_DURATION'])
    }


def get_traffic_hotspots(store_name: str) -> pd.DataFrame:
    """Get aggregated traffic delay hotspots."""
    conn = get_snowflake_connection()
    
    sql = f"""
    SELECT 
        late_reason,
        COUNT(*) as count,
        ROUND(AVG(late_minutes), 1) as avg_delay,
        ROUND(AVG(delivery_duration_min), 1) as avg_duration
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date >= CURRENT_DATE() - 7
      AND is_late = TRUE
    GROUP BY late_reason
    ORDER BY count DESC
    """
    
    return conn.query(sql)


def get_delivery_stats(store_name: str) -> dict:
    """Get quick delivery stats for dashboard."""
    conn = get_snowflake_connection()
    
    sql = f"""
    SELECT 
        COUNT(*) as total_deliveries,
        SUM(CASE WHEN is_late THEN 1 ELSE 0 END) as late_deliveries,
        ROUND(AVG(delivery_duration_min), 1) as avg_duration,
        ROUND(AVG(customer_rating), 1) as avg_rating
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date >= CURRENT_DATE() - 7
    """
    
    df = conn.query(sql)
    
    if df.empty:
        return {"total": 0, "late": 0, "late_pct": 0, "avg_duration": 0, "avg_rating": 0}
    
    row = df.iloc[0]
    total = int(row['TOTAL_DELIVERIES']) if row['TOTAL_DELIVERIES'] else 0
    late = int(row['LATE_DELIVERIES']) if row['LATE_DELIVERIES'] else 0
    
    return {
        "total": total,
        "late": late,
        "late_pct": round(late / total * 100, 1) if total > 0 else 0,
        "avg_duration": float(row['AVG_DURATION']) if row['AVG_DURATION'] else 0,
        "avg_rating": float(row['AVG_RATING']) if row['AVG_RATING'] else 0
    }


def render_dashboard(store_name: str):
    """Render the traffic map and weather dashboard."""
    
    # Quick Stats Row
    st.subheader("📊 Last 7 Days Overview")
    stats = get_delivery_stats(store_name)
    weather = get_weather_stats(store_name)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Deliveries", stats['total'])
    with col2:
        st.metric("Late Deliveries", stats['late'], f"{stats['late_pct']}%")
    with col3:
        st.metric("Avg Delivery Time", f"{stats['avg_duration']} min")
    with col4:
        st.metric("Avg Rating", f"⭐ {stats['avg_rating']}")
    with col5:
        st.metric("Weather", f"{weather['icon']} {weather['condition']}")
    
    st.divider()
    
    # Map and Details in two columns
    map_col, details_col = st.columns([2, 1])
    
    with map_col:
        st.subheader("🗺️ Delivery Traffic Map")
        
        # Get delivery data with coordinates
        map_data = get_delivery_map_data(store_name)
        
        if not map_data.empty:
            # Separate on-time and late deliveries for display
            late_deliveries = map_data[map_data['IS_LATE'] == True]
            ontime_deliveries = map_data[map_data['IS_LATE'] == False]
            
            # View selector
            view_option = st.radio(
                "Filter deliveries:",
                ["All Deliveries", "Late Only", "On-Time Only"],
                horizontal=True,
                key="map_view_selector"
            )
            
            # Filter data based on selection
            if view_option == "Late Only":
                display_data = late_deliveries
                map_color = '#ff4444'
            elif view_option == "On-Time Only":
                display_data = ontime_deliveries
                map_color = '#44ff44'
            else:
                display_data = map_data
                map_color = '#4444ff'
            
            # Store the filtered data in session state for the breakdown
            st.session_state.filtered_deliveries = display_data
            
            if not display_data.empty:
                st.map(display_data[['lat', 'lon']], zoom=12, color=map_color)
                st.caption(f"Showing {len(display_data)} deliveries")
            else:
                st.info(f"No {view_option.lower().replace(' only', '')} deliveries to show.")
            
            # Summary stats below map
            st.markdown("---")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("📍 Total Shown", len(display_data))
            with col_b:
                traffic_delays = len(display_data[display_data['LATE_REASON'] == 'traffic']) if not display_data.empty else 0
                st.metric("🚗 Traffic", traffic_delays)
            with col_c:
                weather_delays = len(display_data[display_data['LATE_REASON'] == 'weather']) if not display_data.empty else 0
                st.metric("🌧️ Weather", weather_delays)
        else:
            st.info("No delivery data available for mapping.")
            st.session_state.filtered_deliveries = pd.DataFrame()
    
    with details_col:
        # Use filtered data if available
        filtered_data = st.session_state.get('filtered_deliveries', pd.DataFrame())
        view_option = st.session_state.get('map_view_selector', 'All Deliveries')
        
        if view_option == "Late Only":
            # LATE ONLY VIEW: Show delay breakdown by reason
            st.subheader("⚠️ Delay Breakdown")
            
            if not filtered_data.empty and 'LATE_REASON' in filtered_data.columns:
                breakdown = filtered_data.groupby('LATE_REASON').agg({
                    'DELIVERY_ID': 'count',
                    'LATE_MINUTES': 'mean'
                }).reset_index()
                breakdown.columns = ['LATE_REASON', 'COUNT', 'AVG_DELAY']
                breakdown = breakdown.sort_values('COUNT', ascending=False)
                
                for _, row in breakdown.iterrows():
                    reason = str(row['LATE_REASON']).replace('_', ' ').title()
                    count = int(row['COUNT'])
                    avg_delay = round(row['AVG_DELAY'], 1) if row['AVG_DELAY'] else 0
                    
                    icons = {
                        'Traffic': '🚗',
                        'Weather': '🌧️',
                        'Driver Shortage': '👤',
                        'Kitchen Delay': '🍕',
                        'High Demand': '📈',
                        'Address Issue': '📍'
                    }
                    icon = icons.get(reason, '⚠️')
                    
                    st.markdown(f"**{icon} {reason}**")
                    st.caption(f"{count} delays | Avg: +{avg_delay} min")
                    st.progress(min(count / 20, 1.0))
            else:
                st.info("No late deliveries to analyze")
                
        elif view_option == "On-Time Only":
            # ON-TIME VIEW: Show success metrics
            st.subheader("✅ On-Time Performance")
            
            if not filtered_data.empty:
                avg_time = filtered_data['DELIVERY_DURATION_MIN'].mean()
                fastest = filtered_data['DELIVERY_DURATION_MIN'].min()
                
                st.metric("⏱️ Avg Delivery Time", f"{avg_time:.0f} min")
                st.metric("🚀 Fastest Delivery", f"{fastest:.0f} min")
                st.metric("📦 On-Time Count", len(filtered_data))
                
                # Show delivery time distribution
                st.markdown("**Delivery Times**")
                if 'DELIVERY_DURATION_MIN' in filtered_data.columns:
                    bins = [0, 25, 30, 35, 100]
                    labels = ['< 25 min', '25-30 min', '30-35 min', '> 35 min']
                    filtered_data['time_bucket'] = pd.cut(filtered_data['DELIVERY_DURATION_MIN'], bins=bins, labels=labels)
                    time_dist = filtered_data['time_bucket'].value_counts().sort_index()
                    for bucket, count in time_dist.items():
                        st.caption(f"{bucket}: {count} deliveries")
            else:
                st.info("No on-time deliveries to show")
                
        else:
            # ALL DELIVERIES VIEW: Show overview stats
            st.subheader("📊 Delivery Overview")
            
            if not filtered_data.empty:
                total = len(filtered_data)
                late_count = len(filtered_data[filtered_data['IS_LATE'] == True])
                ontime_count = total - late_count
                ontime_pct = (ontime_count / total * 100) if total > 0 else 0
                late_pct = (late_count / total * 100) if total > 0 else 0
                
                st.metric("📦 Total Deliveries", total)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("✅ On-Time", ontime_count)
                    st.caption(f"{ontime_pct:.0f}% of deliveries")
                with col2:
                    st.metric("⚠️ Late", late_count)
                    st.caption(f"{late_pct:.0f}% of deliveries")
                
                # Avg delivery time
                avg_time = filtered_data['DELIVERY_DURATION_MIN'].mean()
                st.metric("⏱️ Avg Time", f"{avg_time:.0f} min")
                st.caption("Average delivery duration")
                
                # Top delay reason if any late
                if late_count > 0:
                    late_data = filtered_data[filtered_data['IS_LATE'] == True]
                    top_reason = late_data['LATE_REASON'].mode().iloc[0] if not late_data['LATE_REASON'].mode().empty else 'Unknown'
                    st.markdown(f"**🔍 Top Issue:** {top_reason}")
                    st.caption("Most common delay reason")
            else:
                st.info("No delivery data available")
        
        st.divider()
        
        # Weather Impact
        st.subheader("🌤️ Weather Impact")
        st.markdown(f"### {weather['icon']} {weather['condition']}")
        st.caption(f"Late rate: **{weather['late_pct']}%** | Avg time: **{weather['avg_duration']} min**")


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Header
    st.title(":pizza: Pizza Ops Assistant")
    st.caption("Store Manager's AI Co-Pilot - Powered by Snowflake Cortex")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "selected_store" not in st.session_state:
        st.session_state.selected_store = "Chicago Loop"
    if "active_view" not in st.session_state:
        st.session_state.active_view = "Dashboard"
    
    # Ensure connection is established
    get_snowflake_connection()
    
    # Sidebar with store info and demo questions
    with st.sidebar:
        st.header(":pizza: Chicago Loop")
        
        # Hardcode Chicago Loop as the store
        st.session_state.selected_store = "Chicago Loop"
        
        st.divider()
        
        # Demo Questions section
        st.subheader("🎯 Sample Questions")
        st.caption("Click any question to ask the AI assistant")
        
        for i, q in enumerate(DEMO_QUESTIONS):
            # Create colored button label
            btn_label = f":{q['color']}[:material/{q['icon']}:] {q['label']}"
            if st.button(btn_label, key=f"demo_q_{i}", use_container_width=True):
                # Prepend store context to question
                store_question = f"For {st.session_state.selected_store}: {q['question']}"
                st.session_state.pending_question = store_question
                st.session_state.pending_type = q.get("type")
                st.session_state.active_view = "Chat"  # Switch to chat view
                st.rerun()
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.processing = False
            st.rerun()
        
        st.divider()
        
        # Info section
        with st.expander("ℹ️ About this app"):
            st.markdown("""
            **Cortex Analyst** analyzes:
            - Sales & Orders
            - Delivery Performance
            - Kitchen Capacity
            - Staffing Data
            
            **Cortex Search** finds:
            - Customer Reviews
            - Equipment Reports
            - Store Audits
            """)
            st.caption(f"Model: `{SEMANTIC_MODEL_FILE}`")
    
    # Main content area - view selector that syncs with session state
    view_options = ["📊 Dashboard", "💬 Chat Assistant"]
    current_index = 1 if st.session_state.active_view == "Chat" else 0
    
    selected_view = st.radio(
        "View",
        view_options,
        index=current_index,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Update session state based on selection
    st.session_state.active_view = "Chat" if selected_view == "💬 Chat Assistant" else "Dashboard"
    
    st.divider()
    
    # Render the selected view
    if st.session_state.active_view == "Dashboard":
        render_dashboard(st.session_state.selected_store)
    else:
        # Chat view
        # Process pending question from sidebar
        if st.session_state.pending_question:
            question = st.session_state.pending_question
            q_type = st.session_state.get("pending_type")
            st.session_state.pending_question = None
            st.session_state.pending_type = None
            st.session_state.processing = True
            process_user_question(question, q_type)
            st.session_state.processing = False
            st.rerun()
        
        # Main content area - show welcome message if no chat history
        if not st.session_state.messages and not st.session_state.processing:
            st.markdown(f"""
            ### Welcome, {st.session_state.selected_store} Manager! 👋
            
            I'm your AI assistant powered by **Snowflake Cortex**. I can help you understand:
            
            - 📦 **Delivery Performance** - Are deliveries on time? What's causing delays?
            - 🍕 **Kitchen Capacity** - Equipment status, production capacity
            - 💰 **Revenue Impact** - How issues are affecting your bottom line
            - 💬 **Customer Feedback** - What are customers saying about your store?
            
            **👈 Click a demo question in the sidebar** or type your own question below!
            """)
        
        # Display chat history
        for idx, message in enumerate(st.session_state.messages):
            role = message["role"]
            content = message["content"]
            query_type = message.get("query_type", "analyst")
            
            if role == "user":
                with st.chat_message("user"):
                    # User content is simple text - handle both list and string formats
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list) and content:
                        text = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
                    else:
                        text = ""
                    st.markdown(text)
            else:
                with st.chat_message("assistant", avatar=":material/robot:"):
                    if query_type == "search":
                        # Display search results - handle both list and string formats
                        if isinstance(content, str):
                            text = content
                        elif isinstance(content, list) and content:
                            text = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
                        else:
                            text = ""
                        documents = message.get("documents", [])
                        display_search_content(text, documents, idx)
                        # Display stored recommendations for search
                        recommendations = message.get("recommendations")
                        if recommendations:
                            st.divider()
                            st.markdown("### 💡 Answer & Recommendations")
                            st.markdown(recommendations)
                    elif query_type == "both":
                        # Display combined results
                        sql = message.get("sql")
                        documents = message.get("documents", [])
                        recommendations = message.get("recommendations")
                        
                        st.markdown("### 📊 Data Analysis")
                        display_message_content(content, idx)
                        if sql:
                            display_sql_results(sql)
                        if documents:
                            st.markdown("### 📋 Related Documents Found")
                            doc_types = set(doc.get('DOCUMENT_TYPE', '') for doc in documents)
                            st.caption(f"Found {len(documents)} relevant documents: {', '.join(filter(None, doc_types))}")
                        if recommendations:
                            st.divider()
                            st.markdown("### 🎯 Combined Analysis & Recommendations")
                            st.markdown(recommendations)
                    else:
                        # Display analyst results
                        sql = display_message_content(content, idx)
                        if sql:
                            st.divider()
                            display_sql_results(sql)
                        # Display stored recommendations
                        recommendations = message.get("recommendations")
                        if recommendations:
                            st.divider()
                            st.markdown("### 💡 Manager Recommendations")
                            st.markdown(recommendations)
        
        # Handle pending question from suggestion buttons
        if st.session_state.pending_question and not st.session_state.processing:
            question = st.session_state.pending_question
            st.session_state.pending_question = None
            st.session_state.processing = True
            process_user_question(question)
            st.session_state.processing = False
            st.rerun()
        
        # Chat input
        if prompt := st.chat_input("Ask about sales, deliveries, inventory, or customer reviews..."):
            st.session_state.processing = True
            process_user_question(prompt)
            st.session_state.processing = False
            st.rerun()


if __name__ == "__main__":
    main()
