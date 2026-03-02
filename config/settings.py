"""
Pizza Operations Pipeline - Configuration Settings
Shared configuration for all services
"""

from dataclasses import dataclass
from typing import Dict, List
import os

# =============================================================================
# STORE CONFIGURATION
# =============================================================================

STORE_CONFIG = {
    "store_id": "STR004",
    "name": "Chicago Loop",
    "address": "100 W Monroe St, Chicago, IL 60603",
    "lat": 41.8827,
    "lon": -87.6233,
    "phone": "312-555-0100",
    "timezone": "America/Chicago",
}

# =============================================================================
# DELIVERY ZONES WITH RISK PROFILES
# =============================================================================

DELIVERY_ZONES = {
    "Loop Core": {
        "risk_level": "low",
        "avg_delivery_min": 15,
        "common_issues": ["High-rise elevator wait", "Busy lobby security check"],
        "alternate_route": None,
    },
    "Financial District": {
        "risk_level": "medium",
        "avg_delivery_min": 18,
        "common_issues": ["Building security delay", "Elevator congestion", "Suite number confusion"],
        "alternate_route": None,
    },
    "West Loop": {
        "risk_level": "high",
        "avg_delivery_min": 22,
        "common_issues": ["Restaurant row traffic", "Double-parked cars", "Construction detour", "Event traffic"],
        "alternate_route": "Use Adams St → Halsted St for afternoon deliveries",
    },
    "River North": {
        "risk_level": "high",
        "avg_delivery_min": 20,
        "common_issues": ["Gallery district parking", "Bar crowd congestion", "One-way street maze", "Loading zone blocked"],
        "alternate_route": "Park on Hubbard St, walk 1 block",
    },
    "Streeterville": {
        "risk_level": "medium",
        "avg_delivery_min": 18,
        "common_issues": ["Hospital area traffic", "Tourist pedestrians", "Concierge verification delay"],
        "alternate_route": None,
    },
    "Magnificent Mile": {
        "risk_level": "high",
        "avg_delivery_min": 25,
        "common_issues": ["Shopping traffic gridlock", "Bus lane restrictions", "Wrong hotel entrance", "Valet interference"],
        "alternate_route": "Use State St → Chicago Ave → Rush St",
    },
    "Gold Coast": {
        "risk_level": "high",
        "avg_delivery_min": 28,
        "common_issues": ["Doorman verification", "No parking available", "Gate code issue", "Private road access"],
        "alternate_route": "Use Lake Shore Dr → Oak St exit",
    },
    "Lakeshore East": {
        "risk_level": "medium",
        "avg_delivery_min": 20,
        "common_issues": ["Tower identification confusion", "Park detour required", "Underground parking access"],
        "alternate_route": None,
    },
}

# =============================================================================
# MENU ITEMS
# =============================================================================

MENU_ITEMS = {
    "PIZ001": {"name": "Classic Pepperoni", "category": "pizza", "price": 18.99, "prep_time_min": 12},
    "PIZ002": {"name": "Margherita", "category": "pizza", "price": 16.99, "prep_time_min": 10},
    "PIZ003": {"name": "BBQ Chicken", "category": "pizza", "price": 21.99, "prep_time_min": 14},
    "PIZ004": {"name": "Veggie Garden", "category": "pizza", "price": 17.99, "prep_time_min": 11},
    "PIZ005": {"name": "Meat Lovers", "category": "pizza", "price": 23.99, "prep_time_min": 15},
    "PIZ006": {"name": "Hawaiian Paradise", "category": "pizza", "price": 18.99, "prep_time_min": 11},
    "PIZ007": {"name": "Buffalo Chicken", "category": "pizza", "price": 21.99, "prep_time_min": 13},
    "PIZ008": {"name": "Four Cheese", "category": "pizza", "price": 19.99, "prep_time_min": 11},
    "PIZ009": {"name": "Supreme Deluxe", "category": "pizza", "price": 22.99, "prep_time_min": 14},
    "PIZ010": {"name": "Truffle Mushroom", "category": "pizza", "price": 24.99, "prep_time_min": 14},
    "SID001": {"name": "Garlic Breadsticks", "category": "sides", "price": 6.99, "prep_time_min": 5},
    "SID002": {"name": "Buffalo Wings (8pc)", "category": "sides", "price": 11.99, "prep_time_min": 12},
    "SID003": {"name": "Caesar Salad", "category": "sides", "price": 8.99, "prep_time_min": 3},
    "SID004": {"name": "Stuffed Cheesy Bread", "category": "sides", "price": 7.99, "prep_time_min": 7},
    "SID005": {"name": "Mozzarella Sticks (6pc)", "category": "sides", "price": 8.99, "prep_time_min": 6},
    "SID006": {"name": "Potato Wedges", "category": "sides", "price": 6.49, "prep_time_min": 8},
    "SID007": {"name": "Chicken Tenders (5pc)", "category": "sides", "price": 9.99, "prep_time_min": 10},
    "SID008": {"name": "Mac & Cheese Bites", "category": "sides", "price": 7.49, "prep_time_min": 6},
    "SID009": {"name": "Onion Rings", "category": "sides", "price": 6.99, "prep_time_min": 6},
    "DRK001": {"name": "Coca-Cola (2L)", "category": "drinks", "price": 3.99, "prep_time_min": 0},
    "DRK002": {"name": "Sprite (2L)", "category": "drinks", "price": 3.99, "prep_time_min": 0},
    "DRK003": {"name": "Fanta Orange (2L)", "category": "drinks", "price": 3.99, "prep_time_min": 0},
    "DRK004": {"name": "Dr Pepper (2L)", "category": "drinks", "price": 3.99, "prep_time_min": 0},
    "DRK005": {"name": "Lemonade", "category": "drinks", "price": 4.49, "prep_time_min": 0},
    "DRK006": {"name": "Lemon Iced Tea", "category": "drinks", "price": 3.49, "prep_time_min": 0},
    "DRK007": {"name": "Bottled Water", "category": "drinks", "price": 1.99, "prep_time_min": 0},
    "DRK008": {"name": "Root Beer (2L)", "category": "drinks", "price": 3.99, "prep_time_min": 0},
    "DES001": {"name": "Chocolate Lava Cake", "category": "dessert", "price": 7.99, "prep_time_min": 8},
    "DES002": {"name": "Cinnamon Twists", "category": "dessert", "price": 5.99, "prep_time_min": 5},
    "DES003": {"name": "New York Cheesecake", "category": "dessert", "price": 6.99, "prep_time_min": 0},
    "DES004": {"name": "Brownie Bites (6pc)", "category": "dessert", "price": 6.49, "prep_time_min": 0},
    "DES005": {"name": "Cookie Dough Bites", "category": "dessert", "price": 7.49, "prep_time_min": 5},
    "DES006": {"name": "Churros (4pc)", "category": "dessert", "price": 5.99, "prep_time_min": 5},
    "DES007": {"name": "Apple Pie Bites", "category": "dessert", "price": 5.49, "prep_time_min": 4},
}

# =============================================================================
# DRIVERS
# =============================================================================

DRIVERS = [
    {"driver_id": "DRV001", "name": "Carlos Martinez", "vehicle": "car", "efficiency": 0.95},
    {"driver_id": "DRV002", "name": "Mike Thompson", "vehicle": "car", "efficiency": 0.88},
    {"driver_id": "DRV003", "name": "Sarah Lee", "vehicle": "car", "efficiency": 0.92},
    {"driver_id": "DRV004", "name": "David Kim", "vehicle": "bike", "efficiency": 0.85},
    {"driver_id": "DRV005", "name": "Emma Wilson", "vehicle": "scooter", "efficiency": 0.90},
]

# =============================================================================
# SAMPLE CUSTOMERS
# =============================================================================

CUSTOMERS = [
    {"customer_id": "CUS001", "name": "John Smith", "address": "875 N Michigan Ave", "lat": 41.8988, "lon": -87.6234, "zone": "Gold Coast"},
    {"customer_id": "CUS002", "name": "Lisa Park", "address": "401 N Michigan Ave", "lat": 41.8902, "lon": -87.6244, "zone": "Magnificent Mile"},
    {"customer_id": "CUS003", "name": "Robert Kim", "address": "233 S Wacker Dr", "lat": 41.8789, "lon": -87.6359, "zone": "West Loop"},
    {"customer_id": "CUS004", "name": "Amy Chen", "address": "350 N Orleans St", "lat": 41.8882, "lon": -87.6375, "zone": "River North"},
    {"customer_id": "CUS005", "name": "David Lee", "address": "111 E Wacker Dr", "lat": 41.8870, "lon": -87.6217, "zone": "Streeterville"},
    {"customer_id": "CUS006", "name": "Nina Patel", "address": "200 E Randolph St", "lat": 41.8850, "lon": -87.6195, "zone": "Lakeshore East"},
    {"customer_id": "CUS007", "name": "Tom Wilson", "address": "1 N State St", "lat": 41.8823, "lon": -87.6278, "zone": "Loop Core"},
    {"customer_id": "CUS008", "name": "Grace Liu", "address": "77 W Jackson Blvd", "lat": 41.8780, "lon": -87.6298, "zone": "Financial District"},
    {"customer_id": "CUS009", "name": "Kevin Brown", "address": "500 W Madison St", "lat": 41.8818, "lon": -87.6420, "zone": "West Loop"},
    {"customer_id": "CUS010", "name": "Maria Santos", "address": "161 E Chicago Ave", "lat": 41.8967, "lon": -87.6225, "zone": "Streeterville"},
]

# =============================================================================
# WEATHER CONDITIONS
# =============================================================================

WEATHER_CONDITIONS = {
    "Sunny": {"impact": "none", "delivery_multiplier": 1.0, "description": "Clear skies"},
    "Cloudy": {"impact": "low", "delivery_multiplier": 1.0, "description": "Overcast"},
    "Cold": {"impact": "low", "delivery_multiplier": 1.1, "description": "Below freezing"},
    "Hot": {"impact": "low", "delivery_multiplier": 1.05, "description": "High temperature"},
    "Rainy": {"impact": "moderate", "delivery_multiplier": 1.25, "description": "Rain affecting visibility"},
    "Snowy": {"impact": "severe", "delivery_multiplier": 1.5, "description": "Snow on roads"},
    "Stormy": {"impact": "severe", "delivery_multiplier": 1.75, "description": "Severe weather alert"},
}

# =============================================================================
# TRAFFIC CONDITIONS BY TIME OF DAY
# =============================================================================

TRAFFIC_BY_HOUR = {
    # Hour: (condition, multiplier)
    0: ("light", 1.0), 1: ("light", 1.0), 2: ("light", 1.0), 3: ("light", 1.0),
    4: ("light", 1.0), 5: ("light", 1.0), 6: ("moderate", 1.15), 7: ("heavy", 1.35),
    8: ("heavy", 1.4), 9: ("moderate", 1.2), 10: ("moderate", 1.15), 11: ("moderate", 1.2),
    12: ("heavy", 1.3), 13: ("moderate", 1.2), 14: ("moderate", 1.15), 15: ("moderate", 1.2),
    16: ("heavy", 1.35), 17: ("heavy", 1.45), 18: ("heavy", 1.4), 19: ("moderate", 1.25),
    20: ("moderate", 1.15), 21: ("light", 1.05), 22: ("light", 1.0), 23: ("light", 1.0),
}

# =============================================================================
# DELAY REASONS
# =============================================================================

DELAY_REASONS = {
    "traffic": {"label": "Heavy Traffic", "icon": "🚗", "avg_delay_min": 12},
    "weather": {"label": "Bad Weather", "icon": "🌧️", "avg_delay_min": 15},
    "wrong_address": {"label": "Wrong Address", "icon": "📍", "avg_delay_min": 18},
    "building_access": {"label": "Building Access Issue", "icon": "🏢", "avg_delay_min": 8},
    "parking": {"label": "No Parking Available", "icon": "🅿️", "avg_delay_min": 10},
    "kitchen_delay": {"label": "Kitchen Backup", "icon": "🍕", "avg_delay_min": 7},
}

# =============================================================================
# LOYALTY POINTS CONFIGURATION
# =============================================================================

LOYALTY_POINTS = {
    "order_complete": 10,       # Points per completed order
    "on_time_bonus": 5,         # Bonus for on-time delivery
    "weather_patience": 3,      # Customer waited in bad weather
    "referral": 50,             # Referred a new customer
    "review_bonus": 5,          # Left a review
}

LOYALTY_TIERS = {
    "Bronze": {"min_points": 0, "discount_pct": 0, "benefits": ["Standard service"]},
    "Silver": {"min_points": 100, "discount_pct": 5, "benefits": ["5% discount", "Priority support"]},
    "Gold": {"min_points": 300, "discount_pct": 10, "benefits": ["10% discount", "Priority delivery", "Free sides"]},
    "Platinum": {"min_points": 500, "discount_pct": 15, "benefits": ["15% discount", "Free delivery", "Exclusive items"]},
}

# =============================================================================
# SIMULATION SETTINGS
# =============================================================================

SIMULATION_CONFIG = {
    "order_interval_sec": 5,        # New order every N seconds (demo speed)
    "kitchen_speed_multiplier": 30,  # 30x faster than real time for demo
    "delivery_speed_multiplier": 30, # 30x faster than real time for demo
    "promised_delivery_min": 35,     # Our delivery promise
}

# =============================================================================
# WEATHER API CONFIGURATION
# =============================================================================

# OpenWeatherMap API (free tier: 1000 calls/day)
# Get your free API key at: https://openweathermap.org/api
# Set via environment variable or leave None for simulated weather
WEATHER_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", None)

WEATHER_CONFIG = {
    "api_key": WEATHER_API_KEY,
    "cache_duration_sec": 600,      # Cache weather for 10 minutes
    "chicago_lat": 41.8781,
    "chicago_lon": -87.6298,
}

# =============================================================================
# MAP DISPLAY CONFIGURATION
# =============================================================================

MAP_CONFIG = {
    # Chicago downtown center
    "center_lat": 41.8819,
    "center_lon": -87.6278,
    "default_zoom": 13,
    "pitch": 45,                     # 3D tilt angle
    "bearing": 0,                    # Map rotation
    
    # Refresh rate for live tracking
    "refresh_interval_sec": 3,
    
    # Map style (pydeck/mapbox)
    "style": "dark",
    
    # Marker colors (RGBA)
    "colors": {
        "store": [255, 87, 51, 255],      # Pizza red-orange
        "driver_active": [76, 175, 80, 255],   # Green
        "driver_idle": [158, 158, 158, 255],   # Gray
        "customer": [187, 134, 252, 255],      # Purple
        "route_normal": [76, 175, 80, 180],    # Green transparent
        "route_delayed": [255, 152, 0, 180],   # Orange transparent
        "route_severe": [244, 67, 54, 180],    # Red transparent
    },
    
    # Icon sizes
    "store_icon_size": 80,
    "driver_icon_size": 50,
    "customer_icon_size": 40,
}

# =============================================================================
# TRAFFIC ZONE COLORS (for map overlay)
# =============================================================================

TRAFFIC_COLORS = {
    "light": [76, 175, 80, 100],      # Green
    "moderate": [255, 193, 7, 100],   # Yellow/Amber
    "heavy": [244, 67, 54, 100],      # Red
}

# =============================================================================
# ORDER STATUS FLOW
# =============================================================================

ORDER_STATUSES = [
    "received",        # Order just placed
    "confirmed",       # Order confirmed, payment processed
    "preparing",       # In kitchen
    "ready",           # Ready for pickup
    "out_for_delivery", # Driver picked up
    "delivered",       # Successfully delivered
    "cancelled",       # Order cancelled
]

KITCHEN_STATUSES = [
    "queued",          # Waiting in queue
    "prep",            # Prep station (cutting, topping)
    "oven",            # In the oven
    "packaging",       # Boxing and finishing
    "completed",       # Ready for driver
]
