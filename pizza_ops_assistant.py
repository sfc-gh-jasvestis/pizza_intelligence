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

# Demo questions for store managers - focused on day-to-day operations
DEMO_QUESTIONS = [
    {
        "label": "Why is delivery so bad?",
        "question": "Are my delivery times getting worse, and what's causing it? Compare this week vs last week.",
        "icon": "local_shipping",
        "color": "red",
        "type": "analyst"
    },
    {
        "label": "What's wrong with my kitchen?",
        "question": "What is my kitchen capacity right now and are there any equipment issues affecting my store?",
        "icon": "kitchen",
        "color": "orange",
        "type": "analyst"
    },
    {
        "label": "Get ready for Friday",
        "question": "What should I get ready for this Friday night shift? What were sales like last Friday and what's the weather forecast?",
        "icon": "calendar_today",
        "color": "blue",
        "type": "analyst"
    },
    {
        "label": "Unhappy customers?",
        "question": "Show me customer complaints and negative feedback for my store. What are people unhappy about?",
        "icon": "sentiment_dissatisfied",
        "color": "violet",
        "type": "search"
    },
    {
        "label": "How do I compare?",
        "question": "How does my store compare to other stores in terms of delivery performance and late delivery rates?",
        "icon": "compare",
        "color": "green",
        "type": "analyst"
    },
]

# Crisis stores for demo (to show dramatic data)
CRISIS_STORES = ["Chicago Loop", "LA Downtown", "Manhattan Midtown", "Miami Beach"]


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
        'report', 'crispy crust', 'competitor', 'competitors'
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
                  'pizza', 'store', 'stores', 'our', 'their', 'customer'}
    
    key_terms = [term.lower().strip('?.,!') for term in query.split() 
                 if len(term) > 2 and term.lower() not in stop_words]
    
    if not key_terms:
        # Return all documents if no good search terms
        search_sql = f"""
        SELECT 
            document_id,
            document_type,
            document_title,
            document_date,
            store_id,
            summary,
            content
        FROM {SEARCH_DATABASE}.{SEARCH_SCHEMA}.PIZZA_DOCUMENTS
        LIMIT {limit}
        """
    else:
        # Build relevance score - boost for hyphenated compound terms (e.g., "thin-crust")
        score_parts = []
        conditions = []
        
        # Check for compound terms like "thin crust" -> also search "thin-crust"
        for i, term in enumerate(key_terms[:5]):
            safe_term = term.replace("'", "''")
            # Score for exact term match
            score_parts.append(f"CASE WHEN LOWER(content) LIKE '%{safe_term}%' THEN 2 ELSE 0 END")
            score_parts.append(f"CASE WHEN LOWER(summary) LIKE '%{safe_term}%' THEN 1 ELSE 0 END")
            conditions.append(f"LOWER(content) LIKE '%{safe_term}%'")
            conditions.append(f"LOWER(summary) LIKE '%{safe_term}%'")
            
            # Also check for hyphenated version with next term (e.g., thin-crust)
            if i < len(key_terms) - 1:
                compound = f"{safe_term}-{key_terms[i+1].replace(chr(39), chr(39)+chr(39))}"
                score_parts.append(f"CASE WHEN LOWER(content) LIKE '%{compound}%' THEN 5 ELSE 0 END")
        
        score_calc = " + ".join(score_parts)
        where_clause = " OR ".join(conditions)
        
        search_sql = f"""
        WITH scored_docs AS (
            SELECT 
                document_id,
                document_type,
                document_title,
                document_date,
                store_id,
                summary,
                content,
                ({score_calc}) AS relevance_score
            FROM {SEARCH_DATABASE}.{SEARCH_SCHEMA}.PIZZA_DOCUMENTS
            WHERE {where_clause}
        )
        SELECT * FROM scored_docs
        WHERE relevance_score >= 4
        ORDER BY relevance_score DESC
        LIMIT {limit}
        """
    
    try:
        df = conn.query(search_sql)
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Document search failed: {e}")
        return []


def format_search_results(results: List[Dict], query: str) -> str:
    """Format search results into a readable response."""
    if not results:
        return f"I couldn't find any documents matching '{query}'. Try rephrasing your question or ask about specific topics like reviews, audits, or invoices."
    
    response_parts = [f"I found **{len(results)} relevant document(s)** related to your question:\n"]
    
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
    
    for item in content:
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


def display_sql_results(sql: str):
    """Execute SQL and display results with visualization options."""
    try:
        with st.spinner("Running query..."):
            df = execute_sql(sql)
        
        if df.empty:
            st.info("Query returned no results.")
            return
            
        # Create tabs for different views
        if len(df) > 1 and len(df.columns) >= 2:
            tab_data, tab_chart = st.tabs(["Data", "Chart"])
            
            with tab_data:
                st.dataframe(df, use_container_width=True, hide_index=True)
                
            with tab_chart:
                # Auto-select chart type based on data
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                if numeric_cols:
                    # Use first column as x-axis, first numeric as y
                    x_col = df.columns[0]
                    y_col = numeric_cols[0] if df.columns[0] not in numeric_cols else numeric_cols[-1]
                    st.bar_chart(df, x=x_col, y=y_col)
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Error executing query: {e}")


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
                    results = search_documents(question, limit=3)
                    response_text = format_search_results(results, question)
                    
                    # Display results
                    display_search_content(response_text, results, len(st.session_state.messages))
                    
                    # Store assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": response_text}],
                        "query_type": "search",
                        "documents": results,
                    })
                    
                except Exception as e:
                    st.error(f"Search error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": f"Sorry, I encountered a search error: {e}"}],
                        "query_type": "search",
                    })
        
        elif query_type == "both":
            # Answer with both data and documents
            st.info("Looking at both data and documents for a complete answer...")
            
            # First, get structured data
            with st.spinner("Analyzing data..."):
                try:
                    api_messages = [{
                        "role": "user",
                        "content": [{"type": "text", "text": question}]
                    }]
                    response = send_analyst_message(api_messages)
                    analyst_content = response.get("message", {}).get("content", [])
                    
                    st.markdown("### Data Analysis")
                    sql_statement = display_message_content(analyst_content, len(st.session_state.messages))
                    if sql_statement:
                        display_sql_results(sql_statement)
                        
                except Exception as e:
                    st.warning(f"Could not get data analysis: {e}")
                    analyst_content = []
                    sql_statement = None
            
            # Then, search documents for context
            with st.spinner("Searching related documents..."):
                try:
                    results = search_documents(question, limit=3)
                    if results:
                        st.markdown("### Related Documents")
                        response_text = format_search_results(results, question)
                        st.markdown(response_text)
                except Exception as e:
                    st.warning(f"Could not search documents: {e}")
                    results = []
            
            # Store combined response
            st.session_state.messages.append({
                "role": "assistant",
                "content": analyst_content,
                "query_type": "both",
                "sql": sql_statement,
                "documents": results if 'results' in dir() else [],
            })
        
        else:
            # Default: Use Cortex Analyst for structured data
            with st.spinner("Analyzing your question..."):
                try:
                    # Build message history for multi-turn conversation
                    api_messages = []
                    for msg in st.session_state.messages:
                        if msg.get("query_type") != "search":  # Only include analyst messages
                            api_messages.append({
                                "role": msg["role"] if msg["role"] != "assistant" else "analyst",
                                "content": msg["content"]
                            })
                    
                    response = send_analyst_message(api_messages)
                    
                    # Extract response content
                    analyst_content = response.get("message", {}).get("content", [])
                    request_id = response.get("request_id")
                    
                    # Display the response
                    message_idx = len(st.session_state.messages)
                    sql_statement = display_message_content(analyst_content, message_idx)
                    
                    # Execute and display SQL results if present
                    if sql_statement:
                        st.divider()
                        display_sql_results(sql_statement)
                    
                    # Store assistant response
                    st.session_state.messages.append({
                        "role": "analyst",
                        "content": analyst_content,
                        "request_id": request_id,
                        "sql": sql_statement,
                        "query_type": "analyst",
                    })
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.messages.append({
                        "role": "analyst",
                        "content": [{"type": "text", "text": f"Sorry, I encountered an error: {e}"}],
                        "query_type": "analyst",
                    })


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
    
    # Ensure connection is established
    get_snowflake_connection()
    
    # Sidebar with store selector and demo questions
    with st.sidebar:
        st.header(":pizza: Store Manager View")
        
        # Store selector
        st.session_state.selected_store = st.selectbox(
            "Select Your Store",
            options=CRISIS_STORES + ["Chicago Wrigleyville", "Downtown Phoenix", "Naperville"],
            index=0,
            help="Demo tip: Select a crisis store (Chicago Loop, LA Downtown, Manhattan Midtown, Miami Beach) for dramatic results!"
        )
        
        # Show crisis indicator
        if st.session_state.selected_store in CRISIS_STORES:
            st.error(f"⚠️ **{st.session_state.selected_store}** is in CRISIS mode!")
        else:
            st.success(f"✅ **{st.session_state.selected_store}** is operating normally")
        
        st.divider()
        
        # Demo Questions section
        st.subheader("🎯 Demo Questions")
        st.caption("Click any question to ask the AI assistant")
        
        for i, q in enumerate(DEMO_QUESTIONS):
            # Create colored button label
            btn_label = f":{q['color']}[:material/{q['icon']}:] {q['label']}"
            if st.button(btn_label, key=f"demo_q_{i}", use_container_width=True):
                # Prepend store context to question
                store_question = f"For {st.session_state.selected_store}: {q['question']}"
                st.session_state.pending_question = store_question
                st.session_state.pending_type = q.get("type")
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
        
        # Show quick stats for selected store
        if st.session_state.selected_store in CRISIS_STORES:
            st.warning(f"""
            ⚠️ **Alert for {st.session_state.selected_store}:**
            Your store is currently experiencing operational challenges. 
            Use the demo questions to investigate!
            """)
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        query_type = message.get("query_type", "analyst")
        
        if role == "user":
            with st.chat_message("user"):
                # User content is simple text
                text = content[0].get("text", "") if content else ""
                st.markdown(text)
        else:
            with st.chat_message("assistant", avatar=":material/robot:"):
                if query_type == "search":
                    # Display search results
                    text = content[0].get("text", "") if content else ""
                    documents = message.get("documents", [])
                    display_search_content(text, documents, idx)
                elif query_type == "both":
                    # Display combined results
                    sql = message.get("sql")
                    documents = message.get("documents", [])
                    st.markdown("### Data Analysis")
                    display_message_content(content, idx)
                    if sql:
                        display_sql_results(sql)
                    if documents:
                        st.markdown("### Related Documents")
                        st.markdown(format_search_results(documents, ""))
                else:
                    # Display analyst results
                    sql = display_message_content(content, idx)
                    if sql:
                        st.divider()
                        display_sql_results(sql)
    
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
