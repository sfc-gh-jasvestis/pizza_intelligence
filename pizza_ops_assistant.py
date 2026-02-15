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
import time
import random
import pydeck as pdk
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from streamlit_autorefresh import st_autorefresh

# Import pizza pipeline services
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.database import get_database, OrderStatus, KitchenStatus, reset_database_singleton
    from services.order_simulator import OrderSimulator
    from services.kitchen_service import KitchenService
    from services.driver_dispatch import DriverDispatch
    from services.analytics_pipeline import AnalyticsPipeline
    from services.weather_service import get_weather_service, WeatherData
    from config.settings import LOYALTY_TIERS, SIMULATION_CONFIG, MAP_CONFIG, STORE_CONFIG, TRAFFIC_BY_HOUR, DELIVERY_ZONES
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    print(f"Pipeline services not available: {e}")

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

# Snowflake account configuration - reads from secrets.toml, env var, or uses placeholder
def get_snowflake_account():
    """Get Snowflake account from secrets or environment."""
    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets'):
            if 'snowflake' in st.secrets and 'account' in st.secrets['snowflake']:
                return st.secrets['snowflake']['account']
            if 'connections' in st.secrets and 'snowflake' in st.secrets['connections']:
                return st.secrets['connections']['snowflake'].get('account', 'YOUR_ACCOUNT')
    except:
        pass
    # Fall back to environment variable
    return os.environ.get("SNOWFLAKE_ACCOUNT", "YOUR_ACCOUNT")

SNOWFLAKE_ACCOUNT = get_snowflake_account()
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
        "question": "Why were my sales lower than usual last week? What's causing the drop and what promo would help?",
        "icon": "trending_down",
        "color": "red",
        "type": "both"  # Sales data + customer feedback + promo suggestion
    },
    {
        "label": "Friday night forecast",
        "question": "What should we expect next Friday night? There's a football game nearby. Give me demand forecast and staffing recommendations.",
        "icon": "sports_football",
        "color": "blue",
        "type": "both"  # Football game + weather + history → staffing & demand forecast
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
# LIVE ORDER SIMULATION DATA
# =============================================================================

# Chicago Loop store location
STORE_LOCATION = {"lat": 41.8827, "lon": -87.6233, "name": "Chicago Loop Pizza"}

# Sample customer names
CUSTOMER_NAMES = [
    "Mike Johnson", "Sarah Williams", "David Chen", "Emily Rodriguez",
    "James Wilson", "Maria Garcia", "Robert Taylor", "Jennifer Lee",
    "William Brown", "Amanda Martinez", "Christopher Davis", "Jessica Moore"
]

# Sample pizza items - aligned with PIZZA_INTELLIGENCE.ANALYTICS.DIM_PRODUCTS
PIZZA_ITEMS = [
    {"name": "Classic Pepperoni", "prep_time": 12, "price": 18.99},
    {"name": "Margherita", "prep_time": 10, "price": 16.99},
    {"name": "BBQ Chicken", "prep_time": 14, "price": 21.99},
    {"name": "Veggie Garden", "prep_time": 11, "price": 17.99},
    {"name": "Meat Lovers", "prep_time": 15, "price": 23.99},
    {"name": "Hawaiian Paradise", "prep_time": 11, "price": 18.99},
    {"name": "Supreme Deluxe", "prep_time": 14, "price": 22.99},
]

# Sample delivery addresses near Chicago Loop with risk indicators
DELIVERY_ADDRESSES = [
    {"address": "233 S Wacker Dr", "lat": 41.8789, "lon": -87.6359, "distance_km": 1.2, "zone": "West Loop", "risk_level": "high", "common_issues": ["traffic", "parking"]},
    {"address": "111 E Wacker Dr", "lat": 41.8870, "lon": -87.6217, "distance_km": 0.8, "zone": "Streeterville", "risk_level": "medium", "common_issues": ["building_access"]},
    {"address": "401 N Michigan Ave", "lat": 41.8902, "lon": -87.6244, "distance_km": 1.5, "zone": "Magnificent Mile", "risk_level": "high", "common_issues": ["traffic", "wrong_address"]},
    {"address": "875 N Michigan Ave", "lat": 41.8988, "lon": -87.6234, "distance_km": 2.1, "zone": "Gold Coast", "risk_level": "high", "common_issues": ["traffic", "parking", "building_access"]},
    {"address": "1 N State St", "lat": 41.8823, "lon": -87.6278, "distance_km": 0.3, "zone": "Loop Core", "risk_level": "low", "common_issues": []},
    {"address": "77 W Jackson Blvd", "lat": 41.8780, "lon": -87.6298, "distance_km": 0.5, "zone": "Financial District", "risk_level": "medium", "common_issues": ["building_access"]},
    {"address": "200 E Randolph St", "lat": 41.8850, "lon": -87.6195, "distance_km": 1.0, "zone": "Lakeshore East", "risk_level": "medium", "common_issues": ["wrong_address", "building_access"]},
    {"address": "350 N Orleans St", "lat": 41.8882, "lon": -87.6375, "distance_km": 1.3, "zone": "River North", "risk_level": "high", "common_issues": ["traffic", "parking"]},
]

# Delay reasons with icons and descriptions
DELAY_REASONS = {
    "traffic": {"icon": "🚗", "label": "Heavy Traffic", "color": "orange", "avg_delay_min": 12},
    "weather": {"icon": "🌧️", "label": "Bad Weather", "color": "blue", "avg_delay_min": 15},
    "wrong_address": {"icon": "📍", "label": "Wrong Address", "color": "red", "avg_delay_min": 18},
    "building_access": {"icon": "🏢", "label": "Building Access Issue", "color": "purple", "avg_delay_min": 8},
    "parking": {"icon": "🅿️", "label": "No Parking Available", "color": "gray", "avg_delay_min": 10},
    "kitchen_delay": {"icon": "🍕", "label": "Kitchen Backup", "color": "yellow", "avg_delay_min": 7},
}

# Historical delivery data for analysis (simulated past 7 days)
DELIVERY_HISTORY = [
    # Late deliveries with issues
    {"order_id": "ORD-78234", "customer": "John Smith", "address": "875 N Michigan Ave", "zone": "Gold Coast", 
     "promised_min": 35, "actual_min": 52, "status": "late", "delay_reason": "traffic", 
     "date": "2026-02-01", "time": "18:45", "driver": "Carlos M.", "weather": "Cold"},
    {"order_id": "ORD-78190", "customer": "Lisa Park", "address": "401 N Michigan Ave", "zone": "Magnificent Mile",
     "promised_min": 35, "actual_min": 58, "status": "late", "delay_reason": "wrong_address",
     "date": "2026-02-01", "time": "19:30", "driver": "Mike T.", "weather": "Cold"},
    {"order_id": "ORD-78156", "customer": "Robert Kim", "address": "233 S Wacker Dr", "zone": "West Loop",
     "promised_min": 35, "actual_min": 48, "status": "late", "delay_reason": "traffic",
     "date": "2026-02-01", "time": "12:15", "driver": "Sarah L.", "weather": "Cold"},
    {"order_id": "ORD-78089", "customer": "Amy Chen", "address": "350 N Orleans St", "zone": "River North",
     "promised_min": 35, "actual_min": 51, "status": "late", "delay_reason": "parking",
     "date": "2026-01-31", "time": "19:00", "driver": "Carlos M.", "weather": "Cold"},
    {"order_id": "ORD-78045", "customer": "David Lee", "address": "875 N Michigan Ave", "zone": "Gold Coast",
     "promised_min": 35, "actual_min": 55, "status": "late", "delay_reason": "building_access",
     "date": "2026-01-31", "time": "20:15", "driver": "Mike T.", "weather": "Rainy"},
    {"order_id": "ORD-77998", "customer": "Nina Patel", "address": "200 E Randolph St", "zone": "Lakeshore East",
     "promised_min": 35, "actual_min": 62, "status": "late", "delay_reason": "wrong_address",
     "date": "2026-01-31", "time": "18:00", "driver": "Sarah L.", "weather": "Cold"},
    {"order_id": "ORD-77945", "customer": "Tom Wilson", "address": "401 N Michigan Ave", "zone": "Magnificent Mile",
     "promised_min": 35, "actual_min": 47, "status": "late", "delay_reason": "traffic",
     "date": "2026-01-30", "time": "12:30", "driver": "Carlos M.", "weather": "Sunny"},
    {"order_id": "ORD-77890", "customer": "Grace Liu", "address": "233 S Wacker Dr", "zone": "West Loop",
     "promised_min": 35, "actual_min": 50, "status": "late", "delay_reason": "traffic",
     "date": "2026-01-30", "time": "18:45", "driver": "Mike T.", "weather": "Cold"},
    {"order_id": "ORD-77834", "customer": "Kevin Brown", "address": "350 N Orleans St", "zone": "River North",
     "promised_min": 35, "actual_min": 44, "status": "late", "delay_reason": "parking",
     "date": "2026-01-30", "time": "19:30", "driver": "Sarah L.", "weather": "Cold"},
    {"order_id": "ORD-77789", "customer": "Maria Santos", "address": "875 N Michigan Ave", "zone": "Gold Coast",
     "promised_min": 35, "actual_min": 53, "status": "late", "delay_reason": "weather",
     "date": "2026-01-29", "time": "17:00", "driver": "Carlos M.", "weather": "Rainy"},
    {"order_id": "ORD-77745", "customer": "James Taylor", "address": "111 E Wacker Dr", "zone": "Streeterville",
     "promised_min": 35, "actual_min": 42, "status": "late", "delay_reason": "building_access",
     "date": "2026-01-29", "time": "20:00", "driver": "Mike T.", "weather": "Cold"},
    {"order_id": "ORD-77698", "customer": "Sophie Chang", "address": "200 E Randolph St", "zone": "Lakeshore East",
     "promised_min": 35, "actual_min": 56, "status": "late", "delay_reason": "wrong_address",
     "date": "2026-01-29", "time": "12:45", "driver": "Sarah L.", "weather": "Sunny"},
    # On-time deliveries
    {"order_id": "ORD-78210", "customer": "Alex Rivera", "address": "1 N State St", "zone": "Loop Core",
     "promised_min": 35, "actual_min": 22, "status": "on_time", "delay_reason": None,
     "date": "2026-02-01", "time": "17:30", "driver": "Carlos M.", "weather": "Cold"},
    {"order_id": "ORD-78178", "customer": "Emily White", "address": "77 W Jackson Blvd", "zone": "Financial District",
     "promised_min": 35, "actual_min": 28, "status": "on_time", "delay_reason": None,
     "date": "2026-02-01", "time": "13:00", "driver": "Mike T.", "weather": "Cold"},
    {"order_id": "ORD-78134", "customer": "Chris Park", "address": "1 N State St", "zone": "Loop Core",
     "promised_min": 35, "actual_min": 19, "status": "on_time", "delay_reason": None,
     "date": "2026-02-01", "time": "11:30", "driver": "Sarah L.", "weather": "Cold"},
    {"order_id": "ORD-78067", "customer": "Diana Ross", "address": "77 W Jackson Blvd", "zone": "Financial District",
     "promised_min": 35, "actual_min": 31, "status": "on_time", "delay_reason": None,
     "date": "2026-01-31", "time": "18:15", "driver": "Carlos M.", "weather": "Cold"},
    {"order_id": "ORD-78023", "customer": "Mark Johnson", "address": "1 N State St", "zone": "Loop Core",
     "promised_min": 35, "actual_min": 18, "status": "on_time", "delay_reason": None,
     "date": "2026-01-31", "time": "12:00", "driver": "Mike T.", "weather": "Cold"},
]

# Alternate routes for problem areas
ALTERNATE_ROUTES = {
    "Gold Coast": {
        "problem": "Michigan Ave traffic during rush hour",
        "suggestion": "Use Lake Shore Dr → Oak St exit",
        "time_saved_min": 8,
    },
    "Magnificent Mile": {
        "problem": "Construction on Michigan Ave between Wacker and Ohio",
        "suggestion": "Use State St → Chicago Ave → Rush St",
        "time_saved_min": 6,
    },
    "West Loop": {
        "problem": "Heavy lunch traffic on Wacker Dr",
        "suggestion": "Use Adams St → Halsted St for afternoon deliveries",
        "time_saved_min": 5,
    },
    "River North": {
        "problem": "Limited parking on Orleans St",
        "suggestion": "Park on Hubbard St, walk 1 block - faster than circling",
        "time_saved_min": 7,
    },
}

# Weather-based route recommendations
WEATHER_ROUTE_ADJUSTMENTS = {
    "Cold": {
        "general_advice": "Cold weather slows traffic. Allow extra time.",
        "route_tips": [
            {"zone": "Lake Shore", "tip": "Avoid Lake Shore Dr - icy conditions near lake", "alt_route": "Use inner streets: Clark St or State St"},
            {"zone": "Gold Coast", "tip": "Side streets may have black ice", "alt_route": "Stick to salted main roads: Michigan Ave → Oak St"},
            {"zone": "River North", "tip": "Bridge decks freeze first", "alt_route": "Use Chicago Ave bridge (more traffic but safer)"},
        ],
        "delivery_tips": "Keep food in insulated bags. Customers may take longer to answer doors.",
        "time_adjustment": 1.2,  # 20% longer deliveries
    },
    "Rainy": {
        "general_advice": "Wet roads increase stopping distance. Drive cautiously.",
        "route_tips": [
            {"zone": "West Loop", "tip": "Flooding common on lower Wacker Dr", "alt_route": "Use upper Wacker or Adams St"},
            {"zone": "Streeterville", "tip": "Poor visibility near lake", "alt_route": "Use Illinois St instead of Grand Ave"},
            {"zone": "Loop Core", "tip": "Pedestrians jaywalking to avoid rain", "alt_route": "Use side streets, watch for umbrellas blocking view"},
        ],
        "delivery_tips": "Use rain covers for pizza bags. Watch for slippery building entrances.",
        "time_adjustment": 1.25,  # 25% longer deliveries
    },
    "Snowy": {
        "general_advice": "Snow significantly impacts all routes. Consider delaying non-urgent deliveries.",
        "route_tips": [
            {"zone": "ALL", "tip": "Avoid Lake Shore Dr completely", "alt_route": "Use Clark St or State St north-south"},
            {"zone": "Gold Coast", "tip": "Steep grades on side streets", "alt_route": "Approach from Division St, not North Ave"},
            {"zone": "West Loop", "tip": "Unplowed side streets", "alt_route": "Stick to Randolph St and Madison St"},
        ],
        "delivery_tips": "Allow 50% extra time. Confirm customer is home before leaving store.",
        "time_adjustment": 1.5,  # 50% longer deliveries
    },
    "Sunny": {
        "general_advice": "Good conditions. Watch for sun glare during golden hour.",
        "route_tips": [
            {"zone": "Lake Shore", "tip": "Sun glare eastbound in morning, westbound in evening", "alt_route": "Wear sunglasses, use visor"},
        ],
        "delivery_tips": "Great day for deliveries! Keep pizzas shaded in car.",
        "time_adjustment": 1.0,  # No adjustment
    },
}

# Chicago Loop Traffic Hotspots - areas drivers should avoid
# These are real Chicago intersections/areas known for congestion
TRAFFIC_HOTSPOTS = {
    "always": [  # Always congested
        {"name": "I-90/94 Junction", "lat": 41.8756, "lon": -87.6244, "radius": 350, "reason": "Highway interchange"},
        {"name": "Michigan & Wacker", "lat": 41.8870, "lon": -87.6245, "radius": 250, "reason": "Tourist congestion"},
    ],
    "rush_hour": [  # Rush hour (7-9 AM, 4-7 PM)
        {"name": "Lake Shore Dr & Ohio", "lat": 41.8920, "lon": -87.6130, "radius": 300, "reason": "Commuter backup"},
        {"name": "Congress Pkwy", "lat": 41.8754, "lon": -87.6290, "radius": 280, "reason": "Highway merge"},
        {"name": "Chicago & State", "lat": 41.8967, "lon": -87.6280, "radius": 200, "reason": "Transit hub"},
        {"name": "Clark & Division", "lat": 41.9040, "lon": -87.6315, "radius": 220, "reason": "Nightlife district"},
    ],
    "lunch": [  # Lunch hour (11 AM - 2 PM)
        {"name": "Randolph & Michigan", "lat": 41.8846, "lon": -87.6246, "radius": 200, "reason": "Millennium Park lunch rush"},
        {"name": "Adams & Wacker", "lat": 41.8792, "lon": -87.6370, "radius": 180, "reason": "Willis Tower lunch crowd"},
        {"name": "Hubbard & Clark", "lat": 41.8898, "lon": -87.6310, "radius": 180, "reason": "River North restaurants"},
    ],
    "weekend": [  # Weekend specific
        {"name": "Navy Pier area", "lat": 41.8917, "lon": -87.6059, "radius": 400, "reason": "Tourist attraction"},
        {"name": "Magnificent Mile", "lat": 41.8950, "lon": -87.6245, "radius": 300, "reason": "Shopping traffic"},
    ],
}

# Alternative routes to avoid hotspots
AVOIDANCE_ROUTES = {
    "I-90/94 Junction": {"avoid_via": "Halsted St", "detour_coords": [[-87.6465, 41.8756], [-87.6465, 41.8820]]},
    "Michigan & Wacker": {"avoid_via": "State St", "detour_coords": [[-87.6280, 41.8850], [-87.6280, 41.8900]]},
    "Lake Shore Dr & Ohio": {"avoid_via": "Clark St", "detour_coords": [[-87.6310, 41.8920], [-87.6310, 41.8980]]},
    "Congress Pkwy": {"avoid_via": "Harrison St", "detour_coords": [[-87.6290, 41.8740], [-87.6350, 41.8740]]},
    "Navy Pier area": {"avoid_via": "Illinois St", "detour_coords": [[-87.6150, 41.8907], [-87.6200, 41.8907]]},
}

# Order stages with expected durations (in seconds for demo speed)
ORDER_STAGES = [
    {"id": "received", "label": "Order Received", "icon": "📥", "duration": 3},
    {"id": "kitchen", "label": "In Kitchen", "icon": "🍕", "duration": 8},
    {"id": "ready", "label": "Ready for Pickup", "icon": "✅", "duration": 2},
    {"id": "delivery", "label": "Out for Delivery", "icon": "🚗", "duration": 10},
    {"id": "delivered", "label": "Delivered", "icon": "📍", "duration": 0},
]


def generate_random_order():
    """Generate a random order for simulation."""
    customer = random.choice(CUSTOMER_NAMES)
    items = random.sample(PIZZA_ITEMS, k=random.randint(1, 3))
    destination = random.choice(DELIVERY_ADDRESSES)
    
    total_prep_time = sum(item["prep_time"] for item in items)
    total_price = sum(item["price"] for item in items)
    
    # Estimate delivery time based on distance (roughly 3 min per km + 5 min buffer)
    delivery_time_min = int(destination["distance_km"] * 3 + 5)
    
    return {
        "order_id": f"ORD-{random.randint(10000, 99999)}",
        "customer": customer,
        "items": items,
        "destination": destination,
        "total_price": round(total_price, 2),
        "prep_time_min": total_prep_time,
        "delivery_time_min": delivery_time_min,
        "total_time_min": total_prep_time + delivery_time_min,
        "created_at": datetime.now(),
        "current_stage": 0,
        "stage_start_time": time.time(),
        "is_delayed": False,
        "delay_reason": None,
        "route_coords": None,  # Will be populated with route coordinates
    }


def get_active_traffic_hotspots() -> List[dict]:
    """Get currently active traffic hotspots based on time of day and day of week."""
    now = datetime.now()
    hour = now.hour
    is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
    
    active = list(TRAFFIC_HOTSPOTS["always"])  # Always include these
    
    # Add time-based hotspots
    if 7 <= hour <= 9 or 16 <= hour <= 19:  # Rush hour
        active.extend(TRAFFIC_HOTSPOTS["rush_hour"])
    
    if 11 <= hour <= 14:  # Lunch hour
        active.extend(TRAFFIC_HOTSPOTS["lunch"])
    
    if is_weekend:  # Weekend
        active.extend(TRAFFIC_HOTSPOTS["weekend"])
    
    return active


def point_near_hotspot(lon: float, lat: float, hotspots: List[dict], threshold_km: float = 0.3) -> Optional[dict]:
    """Check if a point is near any hotspot. Returns the hotspot if found, None otherwise."""
    for hotspot in hotspots:
        # Simple distance calculation (approx km at Chicago latitude)
        dlat = (lat - hotspot["lat"]) * 111  # ~111 km per degree latitude
        dlon = (lon - hotspot["lon"]) * 85   # ~85 km per degree longitude at 41.8°N
        dist_km = (dlat**2 + dlon**2) ** 0.5
        
        if dist_km < threshold_km:
            return hotspot
    return None


def get_route_coordinates(start_lon: float, start_lat: float, end_lon: float, end_lat: float) -> tuple:
    """
    Generate a driving route that avoids traffic hotspots.
    Returns tuple of (route_coords, avoided_hotspots, alternative_route_name).
    """
    active_hotspots = get_active_traffic_hotspots()
    avoided = []
    alt_route_name = None
    
    # Check if direct path passes through any hotspots
    # Sample points along the direct path
    num_samples = 5
    for i in range(num_samples + 1):
        t = i / num_samples
        sample_lon = start_lon + t * (end_lon - start_lon)
        sample_lat = start_lat + t * (end_lat - start_lat)
        
        hotspot = point_near_hotspot(sample_lon, sample_lat, active_hotspots)
        if hotspot and hotspot not in avoided:
            avoided.append(hotspot)
    
    # Generate route - either avoiding hotspots or direct
    if avoided:
        # Get avoidance route info
        for hotspot in avoided:
            if hotspot["name"] in AVOIDANCE_ROUTES:
                alt_route_name = AVOIDANCE_ROUTES[hotspot["name"]]["avoid_via"]
                break
        
        # Generate a curved route that goes around hotspots
        route = generate_avoidance_route(start_lon, start_lat, end_lon, end_lat, avoided)
    else:
        # No hotspots to avoid - generate normal curved route
        route = generate_simple_route(start_lon, start_lat, end_lon, end_lat)
    
    return route, avoided, alt_route_name


def generate_avoidance_route(start_lon: float, start_lat: float, end_lon: float, end_lat: float, 
                             hotspots_to_avoid: List[dict]) -> List[List[float]]:
    """Generate a route that curves away from hotspots."""
    # Calculate the centroid of hotspots to avoid
    if not hotspots_to_avoid:
        return generate_simple_route(start_lon, start_lat, end_lon, end_lat)
    
    hotspot_lon = sum(h["lon"] for h in hotspots_to_avoid) / len(hotspots_to_avoid)
    hotspot_lat = sum(h["lat"] for h in hotspots_to_avoid) / len(hotspots_to_avoid)
    
    # Calculate midpoint of direct route
    mid_lon = (start_lon + end_lon) / 2
    mid_lat = (start_lat + end_lat) / 2
    
    # Push the midpoint away from the hotspot centroid
    push_lon = mid_lon - hotspot_lon
    push_lat = mid_lat - hotspot_lat
    push_dist = (push_lon**2 + push_lat**2) ** 0.5
    
    if push_dist > 0.001:  # Avoid division by zero
        # Normalize and scale the push
        push_scale = 0.008  # How far to deviate (in degrees, ~0.8km)
        adjusted_mid_lon = mid_lon + (push_lon / push_dist) * push_scale
        adjusted_mid_lat = mid_lat + (push_lat / push_dist) * push_scale
    else:
        # Hotspot is at midpoint, push perpendicular to route
        route_dx = end_lon - start_lon
        route_dy = end_lat - start_lat
        # Perpendicular vector
        adjusted_mid_lon = mid_lon - route_dy * 0.15
        adjusted_mid_lat = mid_lat + route_dx * 0.15
    
    # Generate multi-point route for smoother curve
    return [
        [start_lon, start_lat],
        [start_lon + (adjusted_mid_lon - start_lon) * 0.4, start_lat + (adjusted_mid_lat - start_lat) * 0.4],
        [adjusted_mid_lon, adjusted_mid_lat],
        [adjusted_mid_lon + (end_lon - adjusted_mid_lon) * 0.6, adjusted_mid_lat + (end_lat - adjusted_mid_lat) * 0.6],
        [end_lon, end_lat]
    ]


def generate_simple_route(start_lon: float, start_lat: float, end_lon: float, end_lat: float) -> List[List[float]]:
    """Generate a simple curved route (no hotspots to avoid)."""
    # Create a slight curve to make it look more like a real route
    mid_lon = (start_lon + end_lon) / 2 + 0.002
    mid_lat = (start_lat + end_lat) / 2 + 0.001
    return [
        [start_lon, start_lat],
        [mid_lon, mid_lat],
        [end_lon, end_lat]
    ]


def get_driver_position(route_coords: List[List[float]], progress: float) -> dict:
    """
    Calculate driver position along route based on progress (0.0 to 1.0).
    Returns {"lon": float, "lat": float}
    """
    if not route_coords or len(route_coords) < 2:
        return None
    
    # Calculate total route length
    total_distance = 0
    segments = []
    for i in range(len(route_coords) - 1):
        dx = route_coords[i+1][0] - route_coords[i][0]
        dy = route_coords[i+1][1] - route_coords[i][1]
        dist = (dx**2 + dy**2) ** 0.5
        segments.append({"start": route_coords[i], "end": route_coords[i+1], "dist": dist})
        total_distance += dist
    
    # Find position at given progress
    target_distance = progress * total_distance
    traveled = 0
    
    for seg in segments:
        if traveled + seg["dist"] >= target_distance:
            # Position is within this segment
            seg_progress = (target_distance - traveled) / seg["dist"] if seg["dist"] > 0 else 0
            lon = seg["start"][0] + seg_progress * (seg["end"][0] - seg["start"][0])
            lat = seg["start"][1] + seg_progress * (seg["end"][1] - seg["start"][1])
            return {"lon": lon, "lat": lat}
        traveled += seg["dist"]
    
    # At end of route
    return {"lon": route_coords[-1][0], "lat": route_coords[-1][1]}


# =============================================================================
# SNOWFLAKE CONNECTION
# =============================================================================

def get_snowflake_connection(force_refresh: bool = False):
    """Get or create Snowflake connection. Handles session expiration."""
    if force_refresh and "snowflake_conn" in st.session_state:
        del st.session_state.snowflake_conn
    
    if "snowflake_conn" not in st.session_state:
        try:
            conn = st.connection("snowflake")
            st.session_state.snowflake_conn = conn
            st.session_state.snowflake_conn_time = time.time()
        except Exception as e:
            st.error(f"Failed to connect to Snowflake: {e}")
            st.info("Please configure your Snowflake connection in `.streamlit/secrets.toml`")
            st.stop()
    
    # Check if connection might be stale (older than 50 minutes)
    conn_time = st.session_state.get("snowflake_conn_time", 0)
    if time.time() - conn_time > 3000:  # 50 minutes
        try:
            # Test the connection with a simple query
            conn = st.session_state.snowflake_conn
            conn.session().sql("SELECT 1").collect()
        except Exception:
            # Connection is stale, refresh it
            del st.session_state.snowflake_conn
            return get_snowflake_connection(force_refresh=True)
    
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
Based on the data below, provide actionable recommendations in table format.

Question asked: {question}

Data retrieved:
{data_summary}

Provide your response using markdown tables:

### 📊 Key Insight
[One sentence summary of what the data shows]

### ✅ Recommended Actions
| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| 1 | [specific action] | [benefit] |
| 2 | [specific action] | [benefit] |
| 3 | [specific action] | [benefit] |

Keep it brief and actionable. Use REAL numbers from the data."""

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

Provide a UNIFIED answer using markdown tables for readability:

### 📊 Key Metrics
| Metric | Value | Note |
|--------|-------|------|
| Expected Orders | [number] | [comparison to normal] |
| Revenue Forecast | [amount] | [trend] |
| Avg Order Size | [amount] | [vs normal] |
| Peak Hours | [times] | [staffing impact] |

### 📋 Intelligence from Documents
| Source | Key Finding |
|--------|-------------|
| [doc type] | [finding 1] |
| [doc type] | [finding 2] |
| [doc type] | [finding 3] |

### 🎯 Action Plan
| Priority | Category | Action | Why |
|----------|----------|--------|-----|
| 1 | Staffing | [action] | [reason] |
| 2 | Inventory | [action] | [reason] |
| 3 | Operations | [action] | [reason] |

IMPORTANT:
- Use REAL numbers from the data - no placeholders
- Include 3-5 rows per table based on available data
- Be specific with item names, quantities, and times
- Keep it concise and actionable"""

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


def generate_delivery_message(order_id: str, customer_name: str, driver_name: str, 
                               eta_minutes: int, items: list, weather_condition: str = None,
                               use_cortex: bool = True) -> str:
    """
    Generate a personalized delivery status message using Snowflake Cortex AI.
    Falls back to template if Cortex is unavailable.
    
    Args:
        order_id: Order ID for reference
        customer_name: Customer's name
        driver_name: Driver's name
        eta_minutes: Estimated minutes until delivery
        items: List of item names being delivered
        weather_condition: Current weather (e.g., "Rainy", "Sunny")
        use_cortex: Whether to use Cortex AI (True) or template (False)
    
    Returns:
        Personalized delivery message string
    """
    items_str = ", ".join(items[:3]) if items else "your order"
    if len(items) > 3:
        items_str += f" and {len(items) - 3} more items"
    
    # Template fallback
    template_message = f"Hi {customer_name}! Your {items_str} is on the way with {driver_name}. ETA: ~{eta_minutes} minutes."
    
    if not use_cortex:
        return template_message
    
    try:
        conn = get_snowflake_connection()
        
        weather_note = ""
        if weather_condition and weather_condition.lower() in ["rainy", "snowy", "stormy"]:
            weather_note = f"Note: It's {weather_condition.lower()} outside, so delivery may take a bit longer."
        
        prompt = f"""Generate a brief, friendly delivery notification message (max 50 words) for a pizza customer.

Details:
- Customer: {customer_name}
- Driver: {driver_name}
- Items: {items_str}
- ETA: {eta_minutes} minutes
- Weather: {weather_condition or 'Clear'}

Requirements:
- Be warm and conversational
- Include a pizza emoji 🍕
- Mention the driver by first name only
- Keep it under 50 words
- If weather is bad, acknowledge potential slight delay
- Don't include the order ID

Just return the message text, nothing else."""
        
        escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
        
        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'llama3.1-8b',
                '{escaped_prompt}'
            ) as response
        """
        result = conn.session().sql(sql).collect()
        
        if result and len(result) > 0:
            response = result[0]['RESPONSE'].strip()
            # Clean up any extra quotes or formatting
            response = response.strip('"').strip("'")
            if len(response) > 10:  # Sanity check
                return response
        
        return template_message
        
    except Exception as e:
        # Silently fall back to template
        return template_message


def generate_delivery_summary(deliveries_data: list, weather_condition: str = None) -> str:
    """
    Generate an AI summary of current delivery operations.
    
    Args:
        deliveries_data: List of dicts with delivery info
        weather_condition: Current weather
    
    Returns:
        Summary string for display
    """
    if not deliveries_data:
        return "No active deliveries at the moment."
    
    try:
        conn = get_snowflake_connection()
        
        # Build delivery summary
        delivery_info = []
        for d in deliveries_data[:5]:
            delivery_info.append(f"- {d.get('order_id', 'N/A')}: {d.get('zone', 'Unknown')} zone, ETA {d.get('eta', 'N/A')} min")
        
        deliveries_text = "\n".join(delivery_info)
        
        prompt = f"""As a pizza delivery operations AI, provide a 2-sentence summary of current operations.

Active Deliveries ({len(deliveries_data)} total):
{deliveries_text}

Weather: {weather_condition or 'Clear'}

Focus on: delivery volume, any concerning patterns, and weather impact.
Keep it under 40 words. Be helpful and actionable."""

        escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
        
        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'llama3.1-8b',
                '{escaped_prompt}'
            ) as response
        """
        result = conn.session().sql(sql).collect()
        
        if result and len(result) > 0:
            return result[0]['RESPONSE'].strip().strip('"').strip("'")
        
        return f"{len(deliveries_data)} active deliveries. Operations running normally."
        
    except Exception:
        return f"{len(deliveries_data)} active deliveries. Operations running normally."


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

def send_analyst_message(messages: List[Dict], retry_on_auth_error: bool = True) -> Dict[str, Any]:
    """
    Send a message to Cortex Analyst API and return the response.
    
    Args:
        messages: Conversation history in Cortex Analyst format
        retry_on_auth_error: Whether to retry with fresh connection on auth error
        
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
        elif response.status_code in (401, 403) and retry_on_auth_error:
            # Session expired - try to refresh connection and retry once
            get_snowflake_connection(force_refresh=True)
            return send_analyst_message(messages, retry_on_auth_error=False)
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', response.text)
            
            # Check for session expiration in error message
            if retry_on_auth_error and ('session' in error_msg.lower() or 'expired' in error_msg.lower() or 'token' in error_msg.lower()):
                get_snowflake_connection(force_refresh=True)
                return send_analyst_message(messages, retry_on_auth_error=False)
            
            raise Exception(
                f"API Error (request_id: {request_id})\n"
                f"Status: {response.status_code}\n"
                f"Message: {error_msg}"
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
    
    # Sort reviews by date (most recent first) and deduplicate by name
    def get_sort_date(review):
        """Convert date to string for sorting."""
        date_val = review.get('date', '')
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        return str(date_val) if date_val else ''
    
    seen_happy = set()
    unique_happy = []
    for review in sorted(happy_reviews, key=get_sort_date, reverse=True):
        if review.get('name') not in seen_happy:
            seen_happy.add(review.get('name'))
            unique_happy.append(review)
    
    seen_unhappy = set()
    unique_unhappy = []
    for review in sorted(unhappy_reviews, key=get_sort_date, reverse=True):
        if review.get('name') not in seen_unhappy:
            seen_unhappy.add(review.get('name'))
            unique_unhappy.append(review)
    
    # Display Happy Customers - top 5
    response_parts.append("### 😊 Happy Customers (Top 5)\n")
    if unique_happy:
        for i, review in enumerate(unique_happy[:5], 1):
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
    
    # Display Unhappy Customers - top 5
    response_parts.append("### 😞 Unhappy Customers (Top 5)\n")
    if unique_unhappy:
        for i, review in enumerate(unique_unhappy[:5], 1):
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


def display_grouped_dataframe(df):
    """Display dataframe with section grouping if first column appears to be a category."""
    if df is None or df.empty:
        return
    
    first_col = df.columns[0]
    unique_values = df[first_col].unique()
    
    # Check if first column looks like a category/section header
    # (uppercase text, repeated values, or contains keywords like RECOMMENDATIONS, PERFORMANCE, etc.)
    section_keywords = ['RECOMMENDATION', 'PERFORMANCE', 'IMPACT', 'ANALYSIS', 'SUMMARY', 
                        'FORECAST', 'WEATHER', 'PROMO', 'METRICS', 'ISSUES', 'TRENDS',
                        'DEMAND', 'STAFFING']
    
    is_section_column = (
        len(unique_values) >= 2 and 
        len(unique_values) <= 6 and
        len(df) > len(unique_values) and
        (any(keyword in str(v).upper() for v in unique_values for keyword in section_keywords) or
         all(str(v).isupper() for v in unique_values if isinstance(v, str)))
    )
    
    if is_section_column:
        # Display with section headers
        other_cols = [c for c in df.columns if c != first_col]
        
        # Section emoji mapping
        section_emojis = {
            'RECOMMENDATION': '💡',
            'PROMO': '🏷️',
            'PERFORMANCE': '📈',
            'WEATHER': '🌤️',
            'IMPACT': '📊',
            'FORECAST': '🔮',
            'DEMAND': '📊',
            'STAFFING': '👥',
            'ANALYSIS': '🔍',
            'ISSUES': '⚠️',
            'TRENDS': '📉',
        }
        
        # Smart column renaming based on section type
        section_column_names = {
            'RECOMMENDATION': ['Promo Name', 'Description', 'Why It Works'],
            'PROMO': ['Promo Name', 'Description', 'Why It Works'],
            'WEATHER': ['Weather', 'Avg Revenue', 'Recommendation'],
            'IMPACT': ['Factor', 'Value', 'Recommendation'],
            'PERFORMANCE': ['Date', 'Metrics', 'Status'],
            'FORECAST': ['Metric', 'Value', 'Insight'],
            'DEMAND': ['Metric', 'Value', 'Insight'],
            'STAFFING': ['Role', 'Requirement', 'Action'],
        }
        
        for section in unique_values:
            # Get emoji for section
            emoji = '📋'
            matched_section = None
            for keyword, em in section_emojis.items():
                if keyword in str(section).upper():
                    emoji = em
                    matched_section = keyword
                    break
            
            # Section header
            st.markdown(f"### {emoji} {section}")
            
            # Filter data for this section
            section_df = df[df[first_col] == section][other_cols].reset_index(drop=True)
            
            # Rename columns if we have a mapping for this section type
            if matched_section and matched_section in section_column_names:
                new_names = section_column_names[matched_section]
                # Only rename if we have enough column names
                if len(new_names) >= len(section_df.columns):
                    section_df.columns = new_names[:len(section_df.columns)]
            
            # Display as clean table
            st.dataframe(section_df, use_container_width=True, hide_index=True)
            st.markdown("")  # Add spacing
    else:
        # Regular display
        st.dataframe(df, use_container_width=True, hide_index=True)


def display_sql_results(sql: str) -> str:
    """Execute SQL and display results with visualization options. Returns data as string for LLM."""
    try:
        with st.spinner("Running query..."):
            df = execute_sql(sql)
        
        if df is None or df.empty:
            st.info("Query returned no results.")
            return None
        
        st.success(f"Found {len(df)} row(s)")
        
        # Check if data has section grouping (category column)
        first_col = df.columns[0]
        unique_values = df[first_col].unique()
        section_keywords = ['RECOMMENDATION', 'PERFORMANCE', 'IMPACT', 'ANALYSIS', 'SUMMARY', 
                            'FORECAST', 'WEATHER', 'PROMO', 'METRICS', 'ISSUES', 'TRENDS']
        
        is_section_data = (
            len(unique_values) >= 2 and 
            len(unique_values) <= 6 and
            len(df) > len(unique_values) and
            (any(keyword in str(v).upper() for v in unique_values for keyword in section_keywords) or
             all(str(v).isupper() for v in unique_values if isinstance(v, str)))
        )
        
        if is_section_data:
            # Use grouped display for sectioned data
            display_grouped_dataframe(df)
        elif len(df) >= 3 and len(df.columns) >= 2:
            # Create tabs for different views - only show chart tab if enough data points
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
            # Show Cortex badges
            # Cortex badges removed for cleaner UI
            
            # Use Cortex Search for document queries
            with st.spinner("Searching documents..."):
                try:
                    # Use higher limit for review/feedback queries to get more reviews
                    is_review_query = any(word in question.lower() for word in ['review', 'feedback', 'happy', 'unhappy', 'customer', 'saying'])
                    search_limit = 15 if is_review_query else 5
                    results = search_documents(question, limit=search_limit)
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
            # Show Cortex badges for analyst + LLM
            # Badges removed for cleaner UI
            
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


def get_performance_factors(store_name: str) -> dict:
    """Get factors that contribute to on-time vs late deliveries."""
    conn = get_snowflake_connection()
    
    # Get late reasons breakdown
    late_sql = f"""
    SELECT 
        late_reason,
        COUNT(*) as count
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date >= CURRENT_DATE() - 7
      AND is_late = TRUE
    GROUP BY late_reason
    ORDER BY count DESC
    """
    late_df = conn.query(late_sql)
    
    # Get on-time factors (weather, day of week, distance)
    ontime_sql = f"""
    SELECT 
        weather_condition,
        day_of_week,
        ROUND(AVG(delivery_distance_km), 1) as avg_distance,
        COUNT(*) as count
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date >= CURRENT_DATE() - 7
      AND is_late = FALSE
    GROUP BY weather_condition, day_of_week
    ORDER BY count DESC
    LIMIT 5
    """
    ontime_df = conn.query(ontime_sql)
    
    # Get comparison stats
    compare_sql = f"""
    SELECT 
        is_late,
        ROUND(AVG(delivery_distance_km), 2) as avg_distance,
        ROUND(AVG(delivery_duration_min), 1) as avg_duration,
        COUNT(*) as count
    FROM PIZZA_INTELLIGENCE.ANALYTICS.V_DELIVERIES
    WHERE store_name = '{store_name}'
      AND delivery_date >= CURRENT_DATE() - 7
    GROUP BY is_late
    """
    compare_df = conn.query(compare_sql)
    
    return {
        "late_reasons": late_df,
        "ontime_factors": ontime_df,
        "comparison": compare_df
    }


def get_delivery_stats(store_name: str) -> dict:
    """Get quick delivery stats for dashboard - combines Snowflake historical + live pipeline data."""
    conn = get_snowflake_connection()
    
    # Get historical data from Snowflake (last 7 days)
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
        sf_total, sf_late, sf_duration, sf_rating = 0, 0, 0, 0
    else:
        row = df.iloc[0]
        sf_total = int(row['TOTAL_DELIVERIES']) if row['TOTAL_DELIVERIES'] else 0
        sf_late = int(row['LATE_DELIVERIES']) if row['LATE_DELIVERIES'] else 0
        sf_duration = float(row['AVG_DURATION']) if row['AVG_DURATION'] else 0
        sf_rating = float(row['AVG_RATING']) if row['AVG_RATING'] else 0
    
    # Add live pipeline data if available
    pipeline_total, pipeline_late, pipeline_duration = 0, 0, 0
    if PIPELINE_AVAILABLE and "pipeline_db" in st.session_state:
        db = st.session_state.pipeline_db
        all_orders = list(db.orders.values())
        
        # Helper to handle string/enum comparison
        def is_delivered(order):
            s = order.status
            if isinstance(s, str):
                return s == "delivered"
            return s == OrderStatus.DELIVERED
        
        delivered = [o for o in all_orders if is_delivered(o)]
        pipeline_total = len(delivered)
        
        # Calculate late deliveries from pipeline (> 35 min)
        for order in delivered:
            # Use actual_delivery_min if available, otherwise calculate from timestamps
            if order.actual_delivery_min:
                duration = order.actual_delivery_min
            elif order.delivery_time and order.order_time:
                duration = (order.delivery_time - order.order_time).total_seconds() / 60
            else:
                duration = 0
            
            if duration > 35:
                pipeline_late += 1
            pipeline_duration += duration
        
        if pipeline_total > 0:
            pipeline_duration = pipeline_duration / pipeline_total
    
    # Combine totals
    total = sf_total + pipeline_total
    late = sf_late + pipeline_late
    
    # Weighted average for duration and rating
    if sf_total + pipeline_total > 0:
        avg_duration = (sf_duration * sf_total + pipeline_duration * pipeline_total) / (sf_total + pipeline_total) if (sf_total + pipeline_total) > 0 else 0
    else:
        avg_duration = 0
    
    return {
        "total": total,
        "late": late,
        "late_pct": round(late / total * 100, 1) if total > 0 else 0,
        "avg_duration": round(avg_duration, 1),
        "avg_rating": sf_rating,  # Pipeline doesn't have ratings yet
        "sf_total": sf_total,
        "pipeline_total": pipeline_total,
    }


# =============================================================================
# LIVE ORDER TRACKING - INTEGRATED PIPELINE
# =============================================================================

def init_pipeline_services():
    """Initialize pipeline services in session state."""
    if not PIPELINE_AVAILABLE:
        return False
    
    if "pipeline_db" not in st.session_state:
        st.session_state.pipeline_db = get_database()
    if "pipeline_simulator" not in st.session_state:
        st.session_state.pipeline_simulator = OrderSimulator()
    if "pipeline_kitchen" not in st.session_state:
        st.session_state.pipeline_kitchen = KitchenService()
    if "pipeline_dispatch" not in st.session_state:
        st.session_state.pipeline_dispatch = DriverDispatch()
    if "pipeline_analytics" not in st.session_state:
        st.session_state.pipeline_analytics = AnalyticsPipeline()
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "pipeline_wired" not in st.session_state:
        # Wire up the pipeline callbacks
        st.session_state.pipeline_kitchen.on_order_ready(
            st.session_state.pipeline_dispatch.handle_ready_order
        )
        st.session_state.pipeline_wired = True
    
    return True


def check_and_recover_pipelines():
    """Check if pipeline threads are alive and restart them if needed.
    Call this on every page refresh to auto-recover from idle state.
    """
    if not st.session_state.get("pipeline_running", False):
        return  # Pipeline not supposed to be running
    
    kitchen = st.session_state.get("pipeline_kitchen")
    dispatch = st.session_state.get("pipeline_dispatch")
    analytics = st.session_state.get("pipeline_analytics")
    
    recovered = False
    
    # Check and restart each service if its thread died
    if kitchen and hasattr(kitchen, 'restart_if_dead'):
        if kitchen.restart_if_dead():
            recovered = True
    
    if dispatch and hasattr(dispatch, 'restart_if_dead'):
        if dispatch.restart_if_dead():
            recovered = True
    
    if analytics and hasattr(analytics, 'restart_if_dead'):
        if analytics.restart_if_dead():
            recovered = True
    
    if recovered:
        print("🔄 Auto-recovered dead pipeline threads")


def render_live_orders():
    """Render clean single-page operations dashboard."""
    
    # Check if pipeline is available
    if not PIPELINE_AVAILABLE:
        st.error("Pipeline services not available.")
        return
    
    # Initialize services
    if not init_pipeline_services():
        st.error("Failed to initialize pipeline services")
        return
    
    # Auto-recover dead pipeline threads (handles idle timeout issues)
    check_and_recover_pipelines()
    
    # Get fresh database reference (not from session state cache)
    db = get_database()
    
    simulator = st.session_state.pipeline_simulator
    kitchen = st.session_state.pipeline_kitchen
    dispatch = st.session_state.pipeline_dispatch
    analytics = st.session_state.pipeline_analytics
    
    # Get weather (check for demo override first)
    try:
        if st.session_state.get("demo_weather"):
            # Use demo weather override
            weather_condition = st.session_state.demo_weather
            weather = None  # Will use condition-based logic
        else:
            weather_service = get_weather_service()
            weather = weather_service.get_current_weather()
            weather_condition = weather.condition if weather else "Clear"
    except:
        weather = None
        weather_condition = st.session_state.get("demo_weather", "Clear")
    
    # =========================================================================
    # HEADER & CONTROLS
    # =========================================================================
    
    # Control buttons - simple row
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn1:
        if st.button("🍕 New Order", use_container_width=True):
            # Auto-start pipeline if not running
            if not st.session_state.pipeline_running:
                kitchen.start()
                dispatch.start()
                analytics.start()
                st.session_state.pipeline_running = True
            simulator.generate_order()
            st.rerun()
    
    with col_btn2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col_btn3:
        if st.button("🗑️ Reset", use_container_width=True):
            # Stop all pipelines
            if st.session_state.pipeline_running:
                analytics.stop()
                dispatch.stop()
                kitchen.stop()
                st.session_state.pipeline_running = False
            
            # Force reset the database singleton (clears everything)
            reset_database_singleton()
            
            # Clear session state pipeline references to force re-init
            for key in list(st.session_state.keys()):
                if key.startswith("pipeline_"):
                    del st.session_state[key]
            
            st.rerun()
    
    # Auto-refresh every 3 seconds (always on for live demo)
    st_autorefresh(interval=3000, limit=None, key="live_orders_refresh")
    
    # =========================================================================
    # HERO METRICS
    # =========================================================================
    
    # Get fresh copies of orders to avoid stale cached data
    # Use db.get_all_orders() for a clean snapshot
    all_orders = db.get_all_orders()
    delivery_facts = list(db.delivery_facts.values())
    
    # Helper to normalize status for comparison
    def get_status(order):
        s = order.status
        if isinstance(s, str):
            try:
                return OrderStatus(s)
            except:
                return s
        return s
    
    # Filter out delivered orders from all_orders for active display
    # Check both status AND progress to catch orders that haven't been marked DELIVERED yet
    def is_truly_active(order):
        status = get_status(order)
        if status == OrderStatus.DELIVERED:
            return False
        # Consider delivery complete if progress >= 95% (accounts for timing lag)
        if status == OrderStatus.OUT_FOR_DELIVERY and (order.delivery_progress or 0) >= 95:
            return False
        return True
    
    # Deduplicate active orders by order_id (keep most recent version)
    active_dict = {}
    for o in all_orders:
        if is_truly_active(o):
            # If we've seen this order, keep the one with higher progress
            if o.order_id in active_dict:
                existing = active_dict[o.order_id]
                if (o.delivery_progress or 0) > (existing.delivery_progress or 0):
                    active_dict[o.order_id] = o
            else:
                active_dict[o.order_id] = o
    active_order_list = list(active_dict.values())
    
    # Calculate metrics
    total_orders = len(all_orders)
    delivered = [o for o in all_orders if get_status(o) == OrderStatus.DELIVERED]
    # Filter out completed deliveries (status DELIVERED or progress >= 95%)
    active_deliveries = [o for o in all_orders 
                         if get_status(o) == OrderStatus.OUT_FOR_DELIVERY 
                         and (o.delivery_progress or 0) < 95]
    
    # On-time calculation from delivery facts (processed deliveries)
    if delivery_facts:
        on_time_count = len([f for f in delivery_facts if f.is_on_time])
        on_time_pct = (on_time_count / len(delivery_facts)) * 100
        avg_time = sum(f.total_time_min for f in delivery_facts) / len(delivery_facts)
        late_count = len(delivery_facts) - on_time_count
    elif delivered:
        # Fall back to delivered orders if facts haven't been processed yet
        on_time_count = len([o for o in delivered if not o.is_delayed])
        on_time_pct = (on_time_count / len(delivered)) * 100 if delivered else 100
        avg_time = sum(o.actual_delivery_min or 0 for o in delivered) / len(delivered) if delivered else 0
        late_count = len(delivered) - on_time_count
    else:
        on_time_pct = 100
        avg_time = 0
        late_count = 0
    
    # Use the larger count between delivery_facts and delivered orders
    completed_count = max(len(delivery_facts), len(delivered))
    
    # Big metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Orders", total_orders)
    col2.metric("✅ On-Time Rate", f"{on_time_pct:.0f}%", f"{late_count} late" if late_count > 0 else None, delta_color="inverse")
    col3.metric("🚗 Active Deliveries", len(active_deliveries))
    col4.metric("⏱️ Avg Delivery", f"{avg_time:.0f} min" if avg_time > 0 else "—")
    
    # AI Saved Counter - calculate savings from on-time deliveries and routing
    if completed_count > 0:
        # Calculate AI value metrics
        # Assume: each late delivery costs $15 (refund/compensation), AI routing saves 3 min per delivery
        baseline_late_rate = 0.25  # Industry average 25% late without AI
        expected_late = int(completed_count * baseline_late_rate)
        actual_late = late_count
        prevented_late = max(0, expected_late - actual_late)
        money_saved = prevented_late * 15  # $15 per prevented late delivery
        time_saved = completed_count * 3  # 3 min saved per delivery via smart routing
        
        # Track cumulative savings in session state
        if "ai_money_saved" not in st.session_state:
            st.session_state.ai_money_saved = 0
            st.session_state.ai_time_saved = 0
        st.session_state.ai_money_saved = money_saved
        st.session_state.ai_time_saved = time_saved
        
        # Display AI Impact banner
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #29B5E8 0%, #0068C9 100%); padding: 12px 20px; border-radius: 8px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; color: white;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">🤖</span>
                    <span style="font-weight: 600;">AI Impact Today</span>
                </div>
                <div style="display: flex; gap: 30px;">
                    <div style="text-align: center;">
                        <div style="font-size: 20px; font-weight: 700;">${money_saved}</div>
                        <div style="font-size: 11px; opacity: 0.9;">Saved in Refunds</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 20px; font-weight: 700;">{time_saved} min</div>
                        <div style="font-size: 11px; opacity: 0.9;">Routing Efficiency</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 20px; font-weight: 700;">{prevented_late}</div>
                        <div style="font-size: 11px; opacity: 0.9;">Late Orders Prevented</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Weather & Status bar - check actual thread health
    # Use consistent icons with global WEATHER_ICONS (lowercase key lookup)
    w_icon = WEATHER_ICONS.get(weather_condition.lower() if weather_condition else "clear", "🌤️")
    
    if st.session_state.pipeline_running:
        # Check actual thread health
        all_alive = (
            kitchen.is_alive() if hasattr(kitchen, 'is_alive') else kitchen.running
        ) and (
            dispatch.is_alive() if hasattr(dispatch, 'is_alive') else dispatch.running
        ) and (
            analytics.is_alive() if hasattr(analytics, 'is_alive') else analytics.running
        )
    
    # Show active demo scenario indicator
    demo_weather = st.session_state.get("demo_weather")
    demo_rush = st.session_state.get("demo_rush_hour")
    if demo_weather or demo_rush:
        scenario_parts = []
        if demo_weather:
            weather_icons = {"Rainy": "🌧️", "Snowy": "❄️"}
            scenario_parts.append(f"{weather_icons.get(demo_weather, '🌤️')} {demo_weather} Weather")
        if demo_rush:
            scenario_parts.append("🚗 Rush Hour Traffic")
        
        st.markdown(f"""
        <div style="background: #FF6B35; padding: 8px 16px; border-radius: 6px; margin: 5px 0;">
            <span style="color: white; font-weight: 500;">🎬 Demo Scenario Active: {" • ".join(scenario_parts)}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Weather-based route advisory (always visible, compact)
    weather_adjustments = WEATHER_ROUTE_ADJUSTMENTS.get(weather_condition, {})
    if weather_adjustments:
        st.markdown(f"**🚗 Weather Route Advisory: {weather_condition}**")
        advice_text = weather_adjustments.get('general_advice', '')
        route_tips = weather_adjustments.get('route_tips', [])
        time_adj = weather_adjustments.get('time_adjustment', 1.0)
        
        # Compact display
        advice_parts = [advice_text] if advice_text else []
        if route_tips:
            tip_text = " | ".join([f"**{tip['zone']}**: {tip['tip']}" for tip in route_tips[:2]])
            advice_parts.append(tip_text)
        if time_adj > 1.0:
            advice_parts.append(f"⏱️ +{int((time_adj - 1) * 100)}% delivery times")
        
        st.caption(" • ".join(advice_parts) if advice_parts else "Normal conditions")
    
    # Traffic Hotspots for Drivers (based on time of day)
    current_hour = datetime.now().hour
    is_rush_hour = (7 <= current_hour <= 9) or (16 <= current_hour <= 19)
    is_lunch_rush = (11 <= current_hour <= 13)
    
    if is_rush_hour or is_lunch_rush:
        # Show traffic alerts for high-risk zones
        rush_type = "Rush Hour" if is_rush_hour else "Lunch Rush"
        hotspot_zones = [zone for zone, info in DELIVERY_ZONES.items() if info.get("risk_level") == "high"]
        
        if hotspot_zones:
            hotspot_tips = []
            for zone in hotspot_zones[:3]:  # Show top 3
                zone_info = DELIVERY_ZONES[zone]
                alt = zone_info.get("alternate_route")
                if alt:
                    hotspot_tips.append(f"**{zone}**: {alt}")
            
            if hotspot_tips:
                st.markdown(f"**🚦 {rush_type} Traffic Tips**")
                st.caption(" | ".join(hotspot_tips))
    
    st.divider()
    
    # =========================================================================
    # TWO-COLUMN LAYOUT: MAP + ORDERS
    # =========================================================================
    
    col_map, col_orders = st.columns([3, 2])
    
    # LEFT: LIVE MAP
    with col_map:
        st.markdown("#### 🗺️ Live Deliveries")
        
        if active_deliveries:
            map_data = build_delivery_map_data(db, active_deliveries, weather)
            if map_data["has_data"]:
                render_pydeck_map(map_data)
        else:
            render_empty_map()
            if not all_orders:
                st.info("👆 Click **New Order** to start")
    
    # RIGHT: ORDER PIPELINE
    with col_orders:
        st.markdown("#### 📋 Order Pipeline")
        
        # Count by status (using helper for consistent comparison)
        # Use active_order_list which excludes delivered orders
        received = [o for o in active_order_list if get_status(o) == OrderStatus.RECEIVED]
        preparing = [o for o in active_order_list if get_status(o) in [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]]
        delivering = active_deliveries  # Already filtered to exclude delivered
        
        # Pipeline summary - compact metrics (3 columns now)
        pipeline_cols = st.columns(3)
        pipeline_cols[0].metric("📥", len(received), "Order In")
        pipeline_cols[1].metric("🍕", len(preparing), "Kitchen")
        pipeline_cols[2].metric("🚗", len(delivering), "Out")
        
        # Scrollable container for orders grouped by status
        # Order In section (Received orders)
        if received:
            st.markdown("**📥 Order In**")
            queue_text = " → ".join([f"`{o.order_id[-3:]}`" for o in sorted(received, key=lambda x: x.order_time)[:10]])
            if len(received) > 10:
                queue_text += f" +{len(received)-10} more"
            st.caption(queue_text)
        
        # Kitchen section (Preparing orders) - compact single line
        if preparing:
            st.markdown("**🍕 Kitchen**")
            kitchen_lines = []
            for order in sorted(preparing, key=lambda o: o.kitchen_progress or 0, reverse=True)[:8]:
                progress = order.kitchen_progress or 0
                remaining_min = max(1, int((100 - progress) / 100 * 10))
                order_short = order.order_id[-3:]
                zone = order.delivery_zone or "Downtown"
                # Modern progress indicator
                filled = int(progress / 10)
                bar = "●" * filled + "○" * (10 - filled)
                kitchen_lines.append(f"`{order_short}` {zone} {bar} {remaining_min}m")
            st.caption("  \n".join(kitchen_lines))
            if len(preparing) > 8:
                st.caption(f"_+{len(preparing)-8} more_")
        
        # Out for Delivery section - with driver colors and traffic tips
        if delivering:
            st.markdown("**🚗 Out for Delivery**")
            # Driver color palette (matches map markers)
            driver_color_emojis = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚪"]
            
            # Get persistent driver color mapping from session state
            if "driver_color_mapping" not in st.session_state:
                st.session_state.driver_color_mapping = {}
            if "next_driver_color_idx" not in st.session_state:
                st.session_state.next_driver_color_idx = 0
            
            # Assign colors to any new drivers
            for order in delivering:
                if order.driver_id and order.driver_id not in st.session_state.driver_color_mapping:
                    st.session_state.driver_color_mapping[order.driver_id] = st.session_state.next_driver_color_idx % len(driver_color_emojis)
                    st.session_state.next_driver_color_idx += 1
            
            delivery_lines = []
            for order in sorted(delivering, key=lambda o: o.dispatch_time or datetime.now())[:8]:
                driver = db.get_driver(order.driver_id) if order.driver_id else None
                driver_name = driver.name.split()[0] if driver else "—"
                order_short = order.order_id[-3:]
                zone = order.delivery_zone or "Downtown"
                
                # Get persistent color for this driver
                idx = st.session_state.driver_color_mapping.get(order.driver_id, 0)
                driver_color = driver_color_emojis[idx]
                
                # Calculate ETA and progress
                if order.dispatch_time:
                    elapsed = (datetime.now() - order.dispatch_time).total_seconds() / 60
                    eta = max(1, int((order.estimated_delivery_min or 15) - elapsed))
                    total_est = order.estimated_delivery_min or 15
                    progress = min(100, int((elapsed / total_est) * 100))
                else:
                    eta = order.estimated_delivery_min or 15
                    progress = 5
                
                # Modern progress indicator
                filled = int(progress / 10)
                bar = "●" * filled + "○" * (10 - filled)
                
                # Get traffic tip for zone
                zone_info = DELIVERY_ZONES.get(zone, {})
                alt_route = zone_info.get("alternate_route", "")
                risk = zone_info.get("risk_level", "low")
                
                line = f"{driver_color} `{order_short}` {driver_name} → {zone} {bar} {eta}m"
                if risk == "high" and alt_route:
                    line += f"  \n   _💡 {alt_route}_"
                delivery_lines.append(line)
            
            st.caption("  \n".join(delivery_lines))
            if len(delivering) > 8:
                st.caption(f"_+{len(delivering)-8} more_")
        
        # Show total if nothing active
        if not (received or preparing or delivering):
            st.caption("No active orders")
    
    # =========================================================================
    # ORDER HISTORY (with late delivery info)
    # =========================================================================
    
    # Show history from delivery_facts OR delivered orders (whichever has more)
    show_history = delivery_facts or delivered
    
    if show_history:
        st.divider()
        
        # Build order data for table
        order_table_data = []
        
        if delivery_facts:
            # Deduplicate by order_id
            seen_orders = set()
            unique_facts = []
            for f in delivery_facts:
                if f.order_id not in seen_orders:
                    seen_orders.add(f.order_id)
                    unique_facts.append(f)
            delivery_facts = unique_facts
            
            history_count = len(delivery_facts)
            late_count = len([f for f in delivery_facts if not f.is_on_time])
            late_label = f" · {late_count} late" if late_count > 0 else ""
            
            st.markdown(f"#### 📜 Order History ({history_count} completed{late_label})")
            
            on_time_orders = [f for f in delivery_facts if f.is_on_time]
            total_revenue = sum(f.order_amount for f in delivery_facts)
            avg_delivery = sum(f.total_time_min for f in delivery_facts) / len(delivery_facts)
            on_time_pct = (len(on_time_orders) / len(delivery_facts)) * 100
            
            hist_cols = st.columns(4)
            hist_cols[0].metric("Completed", len(delivery_facts))
            hist_cols[1].metric("On-Time", f"{on_time_pct:.0f}%")
            hist_cols[2].metric("Revenue", f"${total_revenue:.0f}")
            hist_cols[3].metric("Avg Time", f"{avg_delivery:.0f} min")
            
            # AI Insight for late deliveries
            late_facts = [f for f in delivery_facts if not f.is_on_time]
            if late_facts and len(late_facts) >= 2:
                # Analyze delay patterns
                delay_reasons = {}
                zones_affected = set()
                for f in late_facts:
                    reason = f.delay_reason or "Unknown"
                    delay_reasons[reason] = delay_reasons.get(reason, 0) + 1
                    if f.delivery_zone:
                        zones_affected.add(f.delivery_zone)
                top_reason = max(delay_reasons.items(), key=lambda x: x[1])
                top_reason_text = top_reason[0].lower()
                
                # Smart recommendation based on cause category
                if any(word in top_reason_text for word in ['traffic', 'gridlock', 'accident', 'rush', 'congestion']):
                    quick_tip = "Consider alternate routes or adjusting dispatch timing."
                elif any(word in top_reason_text for word in ['kitchen', 'oven', 'prep', 'queue', 'backed up']):
                    quick_tip = "Review kitchen workflow and consider adding prep staff."
                elif any(word in top_reason_text for word in ['weather', 'rain', 'snow', 'storm']):
                    quick_tip = "Extend delivery time estimates during bad weather."
                elif any(word in top_reason_text for word in ['building', 'elevator', 'security', 'access', 'doorman']):
                    quick_tip = "Add building access notes to customer profiles."
                elif any(word in top_reason_text for word in ['driver', 'vehicle', 'breakdown']):
                    quick_tip = "Check driver availability and vehicle maintenance."
                else:
                    quick_tip = "Review delivery routes and kitchen timing."
                
                # Check if we need to generate a fresh Cortex insight
                insight_key = f"{len(late_facts)}_{top_reason[0]}"
                if "last_insight_key" not in st.session_state or st.session_state.last_insight_key != insight_key:
                    # Generate fresh insight with Cortex
                    try:
                        zones_str = ", ".join(list(zones_affected)[:3]) if zones_affected else "various zones"
                        prompt = f"""You are analyzing pizza delivery operations. In one sentence, give a specific actionable insight for this situation:
- {len(late_facts)} late deliveries today
- Top cause: {top_reason[0]} ({top_reason[1]} times)
- Zones affected: {zones_str}
- Current on-time rate: {on_time_pct:.0f}%

Be specific and actionable. Start with a verb."""
                        
                        conn = get_snowflake_connection()
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', '{prompt.replace(chr(39), chr(39)+chr(39))}')")
                        result = cursor.fetchone()
                        cortex_insight = result[0].strip() if result else quick_tip
                        cursor.close()
                        
                        st.session_state.last_insight_key = insight_key
                        st.session_state.cached_cortex_insight = cortex_insight
                    except Exception as e:
                        st.session_state.cached_cortex_insight = quick_tip
                
                # Display the insight
                cortex_insight = st.session_state.get("cached_cortex_insight", quick_tip)
                st.info(f"🤖 **AI Insight:** {len(late_facts)} late deliveries — top cause: **{top_reason[0]}**. {cortex_insight}")
            
            st.divider()
            
            # Build table data from facts
            for fact in sorted(delivery_facts, key=lambda f: f.delivery_date, reverse=True)[:15]:
                order = db.get_order(fact.order_id)
                customer_name = order.customer_name if order else "Unknown"
                
                items_str = ""
                if order and order.items:
                    item_names = [item.item_name for item in order.items[:2]]
                    items_str = ", ".join(item_names)
                    if len(order.items) > 2:
                        items_str += f" +{len(order.items) - 2}"
                
                address = fact.delivery_address or (order.delivery_address if order else "") or "—"
                status = "✅ On-Time" if fact.is_on_time else f"🔴 Late (+{fact.delay_minutes}m)"
                delay_reason = "" if fact.is_on_time else (fact.delay_reason or "Traffic")
                
                # Format date
                delivery_date_str = fact.delivery_date.strftime("%b %d %H:%M") if fact.delivery_date else "—"
                
                order_table_data.append({
                    "status": status,
                    "order_id": fact.order_id,
                    "customer": customer_name,
                    "items": items_str,
                    "address": address,
                    "amount": f"${fact.order_amount:.0f}",
                    "time": f"{fact.total_time_min} min",
                    "date": delivery_date_str,
                    "zone": fact.delivery_zone or "—",
                    "delay_reason": delay_reason,
                })
        else:
            # Use delivered orders directly
            history_count = len(delivered)
            late_count = len([o for o in delivered if o.is_delayed])
            late_label = f" · {late_count} late" if late_count > 0 else ""
            
            st.markdown(f"#### 📜 Order History ({history_count} completed{late_label})")
            
            on_time_orders = [o for o in delivered if not o.is_delayed]
            total_revenue = sum(o.total_amount for o in delivered)
            avg_delivery = sum(o.actual_delivery_min or 0 for o in delivered) / len(delivered) if delivered else 0
            on_time_pct = (len(on_time_orders) / len(delivered)) * 100 if delivered else 100
            
            hist_cols = st.columns(4)
            hist_cols[0].metric("Completed", len(delivered))
            hist_cols[1].metric("On-Time", f"{on_time_pct:.0f}%")
            hist_cols[2].metric("Revenue", f"${total_revenue:.0f}")
            hist_cols[3].metric("Avg Time", f"{avg_delivery:.0f} min")
            
            st.divider()
            
            # Build table data from orders
            for order in sorted(delivered, key=lambda o: o.delivery_time or o.order_time, reverse=True)[:15]:
                items_str = ""
                if order.items:
                    item_names = [item.item_name for item in order.items[:2]]
                    items_str = ", ".join(item_names)
                    if len(order.items) > 2:
                        items_str += f" +{len(order.items) - 2}"
                
                delivery_min = order.actual_delivery_min or 0
                address = order.delivery_address or "—"
                status = "✅ On-Time" if not order.is_delayed else "🔴 Late"
                delay_reason = "" if not order.is_delayed else (order.delay_reason or "Traffic")
                
                # Format date
                delivery_date_str = order.delivery_time.strftime("%b %d %H:%M") if order.delivery_time else (
                    order.order_time.strftime("%b %d %H:%M") if order.order_time else "—"
                )
                
                order_table_data.append({
                    "status": status,
                    "order_id": order.order_id,
                    "customer": order.customer_name or "Unknown",
                    "items": items_str,
                    "address": address,
                    "amount": f"${order.total_amount:.0f}",
                    "time": f"{delivery_min} min",
                    "date": delivery_date_str,
                    "zone": order.delivery_zone or "—",
                    "delay_reason": delay_reason,
                })
        
        # Display as table
        if order_table_data:
            import pandas as pd
            
            # Check if there are any late orders
            has_late_orders = any(row["delay_reason"] for row in order_table_data)
            
            # Check if date field exists
            has_date = any(row.get("date") for row in order_table_data)
            
            if has_late_orders:
                df_display = pd.DataFrame([
                    {
                        "Status": row["status"],
                        "Order": row["order_id"],
                        "Customer": row["customer"],
                        "Address": row["address"],
                        "Items": row["items"],
                        "Amount": row["amount"],
                        "Delivered": row.get("date", "—"),
                        "Duration": row["time"],
                        "Zone": row["zone"],
                        "Delay Reason": row["delay_reason"],
                    }
                    for row in order_table_data
                ])
            else:
                df_display = pd.DataFrame([
                    {
                        "Status": row["status"],
                        "Order": row["order_id"],
                        "Customer": row["customer"],
                        "Address": row["address"],
                        "Items": row["items"],
                        "Amount": row["amount"],
                        "Delivered": row.get("date", "—"),
                        "Duration": row["time"],
                        "Zone": row["zone"],
                    }
                    for row in order_table_data
                ])
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)


def build_delivery_map_data(db, active_deliveries, weather=None):
    """Build data structures for the pydeck map."""
    
    # Store location
    store_lat = STORE_CONFIG.get("lat", 41.8819)
    store_lon = STORE_CONFIG.get("lon", -87.6278)
    
    # Store marker
    store_data = [{
        "name": "Chicago Loop Pizza",
        "reason": "Store Location",
        "lat": store_lat,
        "lon": store_lon,
        "color": MAP_CONFIG.get("colors", {}).get("store", [255, 87, 51, 255]),
        "size": 100,
    }]
    
    # Driver/delivery markers
    driver_data = []
    customer_data = []
    route_data = []
    
    # Get active traffic hotspots based on time of day
    current_hour = datetime.now().hour
    traffic_condition, traffic_mult = TRAFFIC_BY_HOUR.get(current_hour, ("moderate", 1.2))
    
    # Use the centralized traffic hotspot system
    active_hotspots = get_active_traffic_hotspots()
    
    # Convert hotspots to traffic_zones format for map display
    traffic_zones = []
    for hotspot in active_hotspots:
        # Determine severity based on hotspot type
        if hotspot in TRAFFIC_HOTSPOTS["always"]:
            level = "heavy" if traffic_condition == "heavy" else "moderate"
        elif hotspot in TRAFFIC_HOTSPOTS.get("rush_hour", []):
            level = "heavy"
        elif hotspot in TRAFFIC_HOTSPOTS.get("lunch", []):
            level = "moderate"
        else:
            level = "moderate"
        
        traffic_zones.append({
            "name": hotspot["name"],
            "lat": hotspot["lat"],
            "lon": hotspot["lon"],
            "radius": hotspot["radius"],
            "level": level,
            "reason": hotspot.get("reason", "Congestion area"),
        })
    
    # Add colors to traffic zones
    for zone in traffic_zones:
        if zone["level"] == "heavy":
            zone["color"] = [244, 67, 54, 100]  # Red with transparency
        elif zone["level"] == "moderate":
            zone["color"] = [255, 193, 7, 80]  # Yellow with transparency
        else:
            zone["color"] = [76, 175, 80, 50]  # Green with transparency
    
    for order in active_deliveries:
        customer = db.get_customer(order.customer_id)
        driver = db.get_driver(order.driver_id) if order.driver_id else None
        
        # Get delivery coordinates - prefer order's delivery coords, fallback to customer address
        if order.delivery_lat and order.delivery_lon:
            dest_lat = order.delivery_lat
            dest_lon = order.delivery_lon
        elif customer and customer.address_lat and customer.address_lon:
            dest_lat = customer.address_lat
            dest_lon = customer.address_lon
        else:
            # Fallback to store area with small offset
            dest_lat = store_lat + random.uniform(-0.01, 0.01)
            dest_lon = store_lon + random.uniform(-0.01, 0.01)
        
        if customer or (order.delivery_lat and order.delivery_lon):
            # Customer destination
            customer_data.append({
                "name": customer.name if customer else "Customer",
                "reason": order.delivery_address or "Delivery destination",
                "lat": dest_lat,
                "lon": dest_lon,
                "color": MAP_CONFIG.get("colors", {}).get("customer", [33, 150, 243, 255]),
                "size": 60,
            })
            
            # Get actual delivery progress from order
            progress = (order.delivery_progress or 0) / 100.0
            
            # Use actual route coordinates if available
            if order.route_coords and len(order.route_coords) > 1:
                # Calculate driver position along the actual route
                route_index = int(progress * (len(order.route_coords) - 1))
                route_index = min(route_index, len(order.route_coords) - 1)
                pos = order.route_coords[route_index]
                driver_lon = pos[0]
                driver_lat = pos[1]
            else:
                # Fallback: interpolate position between store and customer
                driver_lat = store_lat + progress * (dest_lat - store_lat)
                driver_lon = store_lon + progress * (dest_lon - store_lon)
            
            if driver:
                order_short = order.order_id[-3:]
                # Color palette for drivers (RGB values matching emoji colors)
                driver_color_palette = [
                    [255, 59, 48, 255],    # Red 🔴
                    [255, 149, 0, 255],    # Orange 🟠
                    [255, 204, 0, 255],    # Yellow 🟡
                    [52, 199, 89, 255],    # Green 🟢
                    [0, 122, 255, 255],    # Blue 🔵
                    [175, 82, 222, 255],   # Purple 🟣
                    [162, 132, 94, 255],   # Brown 🟤
                    [255, 255, 255, 255],  # White ⚪
                ]
                # Get persistent color from session state mapping
                driver_color_mapping = st.session_state.get("driver_color_mapping", {})
                color_idx = driver_color_mapping.get(order.driver_id, 0) % len(driver_color_palette)
                driver_color = driver_color_palette[color_idx]
                
                driver_data.append({
                    "name": f"#{order_short} - {driver.name}",
                    "reason": f"Order #{order_short}",
                    "lat": driver_lat,
                    "lon": driver_lon,
                    "color": driver_color,
                    "size": 90,
                    "angle": 0,
                    "order_label": order_short,
                    "driver_id": order.driver_id,
                })
            
            # Route color based on conditions - default to green (normal)
            route_color = [76, 175, 80, 180]  # Green for normal routes
            
            if weather and weather.delivery_multiplier >= 1.5:
                route_color = [244, 67, 54, 180]  # Red for severe weather
            elif weather and weather.delivery_multiplier >= 1.2:
                route_color = [255, 152, 0, 180]  # Orange for weather delay
            
            # Build route path using actual road coordinates
            if order.route_coords and len(order.route_coords) > 1:
                # Use OSRM route coordinates - format for PathLayer
                route_path = [[coord[0], coord[1]] for coord in order.route_coords]
            else:
                # Generate route
                route_result = get_route_coordinates(store_lon, store_lat, dest_lon, dest_lat)
                if isinstance(route_result, tuple):
                    route_path = route_result[0]
                else:
                    route_path = route_result
            
            # Build route name for tooltip
            customer_name = customer.name if customer else "Customer"
            order_short = order.order_id[-3:]
            route_reason = f"Order #{order_short}"
            
            route_data.append({
                "path": route_path,
                "color": route_color,
                "name": f"#{order_short} → {customer_name}",
                "reason": route_reason,
                "order_id": order_short,
                "avoided_zones": [],
                "alt_route_via": None,
            })
    
    return {
        "has_data": len(active_deliveries) > 0,
        "store": store_data,
        "drivers": driver_data,
        "customers": customer_data,
        "routes": route_data,
        "traffic_zones": traffic_zones,
        "traffic_condition": traffic_condition,
        "traffic_multiplier": traffic_mult,
        "center_lat": store_lat,
        "center_lon": store_lon,
    }


def render_pydeck_map(map_data):
    """Render the pydeck map with delivery data."""
    
    # Create layers
    layers = []
    
    # Traffic zones layer (render first, so it's behind other elements)
    if map_data.get("traffic_zones"):
        traffic_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data["traffic_zones"],
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            pickable=True,
            opacity=0.3,
        )
        layers.append(traffic_layer)
    
    # Route paths layer - shows actual road routes
    if map_data.get("routes"):
        path_layer = pdk.Layer(
            "PathLayer",
            data=map_data["routes"],
            get_path="path",
            get_color="color",
            get_width=5,
            width_min_pixels=3,
            pickable=True,
        )
        layers.append(path_layer)
    
    # Store marker layer (large red dot)
    if map_data.get("store"):
        store_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data["store"],
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="size",
            pickable=True,
        )
        layers.append(store_layer)
    
    # Customer markers layer (blue dots)
    if map_data.get("customers"):
        customer_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data["customers"],
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="size",
            pickable=True,
        )
        layers.append(customer_layer)
    
    # Driver markers layer (colored dots - moving)
    if map_data.get("drivers"):
        driver_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data["drivers"],
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="size",
            pickable=True,
        )
        layers.append(driver_layer)
    
    # Create the deck
    view_state = pdk.ViewState(
        latitude=map_data["center_lat"],
        longitude=map_data["center_lon"],
        zoom=13,
        pitch=45,
        bearing=0,
    )
    
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={
            "html": "<b>{name}</b><br/>{reason}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        },
        height=450,
    )
    
    st.pydeck_chart(deck, use_container_width=True, height=450)
    
    # Compact legend
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 12px; margin-top: 10px;">
        <span>🔴 Store</span>
        <span>🔵 Customer</span>
        <span>🔴🟠🟡🟢🔵🟣 Drivers (hover for order #)</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Show alternate route suggestions if there are routes with heavy traffic
    routes_with_traffic = [r for r in map_data.get("routes", []) if r.get("has_traffic")]
    if routes_with_traffic:
        st.warning(f"⚠️ **Traffic Alert:** {len(routes_with_traffic)} route(s) affected by congestion. AI suggests alternate routing via side streets.")


def render_empty_map():
    """Render an empty map centered on the store."""
    
    store_lat = STORE_CONFIG.get("lat", 41.8819)
    store_lon = STORE_CONFIG.get("lon", -87.6278)
    
    store_data = [{
        "name": "Chicago Loop Pizza",
        "reason": "Store Location",
        "lat": store_lat,
        "lon": store_lon,
        "color": [255, 87, 51, 255],
        "size": 100,
    }]
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=store_data,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="size",
        pickable=True,
    )
    
    view_state = pdk.ViewState(
        latitude=store_lat,
        longitude=store_lon,
        zoom=13,
        pitch=45,
        bearing=0,
    )
    
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={
            "html": "<b>{name}</b><br/>{reason}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        },
        height=450,
    )
    
    st.pydeck_chart(deck, use_container_width=True, height=450)


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Header with live status indicator
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title(":pizza: Pizza Ops Assistant")
        st.caption("Store Manager's AI Co-Pilot — Powered by **Snowflake Cortex**")
    with header_col2:
        # Live indicator
        if "pipeline_running" in st.session_state and st.session_state.pipeline_running:
            st.markdown("""
            <div style="text-align: right; padding-top: 20px;">
                <span style="background: #00D26A; color: white; padding: 4px 12px; border-radius: 12px; font-size: 14px;">
                    🔴 LIVE
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    # Show active demo scenario indicator
    demo_weather = st.session_state.get("demo_weather")
    demo_rush = st.session_state.get("demo_rush_hour")
    if demo_weather or demo_rush:
        scenario_parts = []
        if demo_weather:
            weather_icons = {"Rainy": "🌧️", "Snowy": "❄️"}
            scenario_parts.append(f"{weather_icons.get(demo_weather, '🌤️')} {demo_weather} Weather")
        if demo_rush:
            scenario_parts.append("🚗 Rush Hour Traffic")
        
        st.markdown(f"""
        <div style="background: #FF6B35; padding: 8px 16px; border-radius: 6px; margin: 5px 0;">
            <span style="color: white; font-weight: 500;">🎬 Demo Scenario Active: {" • ".join(scenario_parts)}</span>
        </div>
        """, unsafe_allow_html=True)
    
    
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
        st.session_state.active_view = "LiveOrders"  # Default to Live Orders for demo
    
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
        
        # Powered by Snowflake section
        st.markdown("""
        <div style="text-align: center; padding: 10px; opacity: 0.8;">
            <small>Powered by</small><br/>
            <b>❄️ Snowflake Cortex</b><br/>
            <small style="opacity: 0.6;">Analyst • Search • LLM</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area - view selector that syncs with session state
    view_options = ["🚀 Live Orders", "💬 Chat Assistant"]
    
    # Determine current index based on active view
    if st.session_state.active_view == "Chat":
        current_index = 1
    else:
        current_index = 0
    
    selected_view = st.radio(
        "View",
        view_options,
        index=current_index,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Update session state based on selection
    if selected_view == "💬 Chat Assistant":
        st.session_state.active_view = "Chat"
    else:
        st.session_state.active_view = "LiveOrders"
    
    st.divider()
    
    # Render the selected view
    if st.session_state.active_view == "LiveOrders":
        render_live_orders()
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
