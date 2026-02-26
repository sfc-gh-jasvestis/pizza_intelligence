"""
Unified State Management for Pizza Demo
Single source of truth for all three apps: Customer, Ops, Driver
"""

import json
import os
import time
import threading
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import random

try:
    from shared_routes import get_route_from_osrm, get_driver_position_on_route
    ROUTES_AVAILABLE = True
except ImportError:
    ROUTES_AVAILABLE = False

STATE_FILE = os.environ.get(
    "PIZZA_STATE_FILE",
    os.path.join(os.path.dirname(__file__), ".pizza_unified_state.json"),
)
_lock = threading.Lock()

# Store location
STORE_LAT = 41.8827
STORE_LON = -87.6233

# Default drivers - synced with config/settings.py
DEFAULT_DRIVERS = {
    "DRV001": {"name": "Carlos Martinez", "phone": "555-0101", "rating": 4.8, "vehicle": "Honda Civic", "color": "Silver"},
    "DRV002": {"name": "Mike Thompson", "phone": "555-0102", "rating": 4.9, "vehicle": "Toyota Prius", "color": "Blue"},
    "DRV003": {"name": "Sarah Lee", "phone": "555-0103", "rating": 4.7, "vehicle": "Ford Focus", "color": "Red"},
    "DRV004": {"name": "David Kim", "phone": "555-0104", "rating": 4.9, "vehicle": "Bike", "color": "Black"},
    "DRV005": {"name": "Emma Wilson", "phone": "555-0105", "rating": 4.8, "vehicle": "Scooter", "color": "White"},
}

def get_default_state():
    return {
        "orders": {},
        "drivers": {k: {**v, "deliveries_today": 0, "tips_today": 0, "current_order": None} for k, v in DEFAULT_DRIVERS.items()},
        "last_assigned_driver_idx": -1,
        "order_counter": 0,
        "last_updated": datetime.now().isoformat()
    }


def next_order_id() -> str:
    """Generate the next sequential order ID (ORD-00001, ORD-00002, ...)."""
    with _lock:
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
            else:
                state = get_default_state()
        except Exception:
            state = get_default_state()
        counter = state.get("order_counter", 0) + 1
        state["order_counter"] = counter
        state["last_updated"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving state: {e}")
        return f"ORD-{counter:05d}"

def _pick_next_driver(state):
    driver_ids = sorted(state["drivers"].keys())
    available = [d for d in driver_ids if not state["drivers"][d].get("current_order")]
    if not available:
        return None
    last_idx = state.get("last_assigned_driver_idx", -1)
    for i in range(1, len(driver_ids) + 1):
        candidate_idx = (last_idx + i) % len(driver_ids)
        candidate = driver_ids[candidate_idx]
        if candidate in available:
            state["last_assigned_driver_idx"] = candidate_idx
            return candidate
    return available[0]

def load_state() -> dict:
    with _lock:
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return get_default_state()

def save_state(state: dict):
    with _lock:
        state["last_updated"] = datetime.now().isoformat()
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving state: {e}")

def create_order(order_id: str, customer_name: str, customer_phone: str,
                 items: list, address: str, zone: str, lat: float, lon: float,
                 total: float, special_instructions: str = "") -> dict:
    """Create new order - called from Customer App"""
    state = load_state()
    
    route_coords = None
    try:
        route_coords, _, _ = get_route_from_osrm(STORE_LON, STORE_LAT, lon, lat)
    except:
        route_coords = [[STORE_LON, STORE_LAT], [lon, lat]]
    
    order = {
        "order_id": order_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items,
        "address": address,
        "zone": zone,
        "lat": lat,
        "lon": lon,
        "total": total,
        "special_instructions": special_instructions,
        # Status flow: pending -> preparing -> ready -> picked_up -> on_the_way -> delivered
        "status": "pending",
        "kitchen_progress": 0,  # 0-100%
        "driver_id": None,
        "driver_lat": STORE_LAT,
        "driver_lon": STORE_LON,
        "delivery_progress": 0,  # 0-100%
        "route_coords": route_coords,  # OSRM route coordinates [lon, lat] pairs
        "created_at": datetime.now().isoformat(),
        "ready_at": None,
        "picked_up_at": None,
        "delivered_at": None,
        "eta_minutes": 25,
        "rating": None,
        "tip": None
    }
    
    state["orders"][order_id] = order
    save_state(state)
    return order

def get_order(order_id: str) -> Optional[dict]:
    state = load_state()
    return state["orders"].get(order_id)

def get_all_orders() -> List[dict]:
    state = load_state()
    return list(state["orders"].values())

def get_active_orders() -> List[dict]:
    state = load_state()
    return [o for o in state["orders"].values() if o["status"] not in ["delivered", "cancelled"]]

def get_driver_orders(driver_id: str) -> List[dict]:
    state = load_state()
    return [o for o in state["orders"].values() 
            if o["driver_id"] == driver_id and o["status"] not in ["delivered", "cancelled"]]

def get_driver_info(driver_id: str) -> Optional[dict]:
    state = load_state()
    return state["drivers"].get(driver_id)

def get_all_drivers() -> dict:
    state = load_state()
    return state["drivers"]

def update_order(order_id: str, **updates):
    """Update any order field"""
    state = load_state()
    if order_id in state["orders"]:
        for key, value in updates.items():
            state["orders"][order_id][key] = value
        save_state(state)
        return state["orders"][order_id]
    return None

def advance_kitchen(order_id: str, increment: int = 10):
    """Advance kitchen progress - called from Ops App simulation"""
    state = load_state()
    if order_id not in state["orders"]:
        return None
    
    order = state["orders"][order_id]
    
    if order["status"] == "pending":
        order["status"] = "preparing"
    
    if order["status"] == "preparing":
        order["kitchen_progress"] = min(100, order["kitchen_progress"] + increment)
        
        # At 80%, auto-assign driver if not assigned
        if order["kitchen_progress"] >= 80 and not order["driver_id"]:
            driver_id = _pick_next_driver(state)
            if driver_id:
                order["driver_id"] = driver_id
                state["drivers"][driver_id]["current_order"] = order_id
        
        # At 100%, mark ready
        if order["kitchen_progress"] >= 100:
            order["status"] = "ready"
            order["ready_at"] = datetime.now().isoformat()
    
    save_state(state)
    return order

def driver_pickup(order_id: str):
    """Driver picks up order"""
    state = load_state()
    if order_id not in state["orders"]:
        return None
    
    order = state["orders"][order_id]
    order["status"] = "picked_up"
    order["picked_up_at"] = datetime.now().isoformat()
    order["driver_lat"] = STORE_LAT
    order["driver_lon"] = STORE_LON
    
    save_state(state)
    return order

def start_delivery(order_id: str):
    """Driver starts delivery"""
    state = load_state()
    if order_id not in state["orders"]:
        return None
    
    order = state["orders"][order_id]
    order["status"] = "on_the_way"
    order["delivery_progress"] = 0
    order["eta_minutes"] = 15
    
    save_state(state)
    return order

def advance_delivery(order_id: str, increment: int = 10):
    """Advance delivery progress and update driver position"""
    state = load_state()
    if order_id not in state["orders"]:
        return None
    
    order = state["orders"][order_id]
    
    if order["status"] == "on_the_way":
        order["delivery_progress"] = min(100, order["delivery_progress"] + increment)
        
        # Interpolate driver position
        progress = order["delivery_progress"] / 100.0
        order["driver_lat"] = STORE_LAT + (order["lat"] - STORE_LAT) * progress
        order["driver_lon"] = STORE_LON + (order["lon"] - STORE_LON) * progress
        order["eta_minutes"] = max(1, int(15 * (1 - progress)))
        
        # Complete delivery at 100%
        if order["delivery_progress"] >= 100:
            order["status"] = "delivered"
            order["delivered_at"] = datetime.now().isoformat()
            order["driver_lat"] = order["lat"]
            order["driver_lon"] = order["lon"]
            
            # Free up driver and record delivery in history
            if order["driver_id"] and order["driver_id"] in state["drivers"]:
                driver = state["drivers"][order["driver_id"]]
                driver["current_order"] = None
                driver["deliveries_today"] += 1
                
                # Add to driver's delivery history
                if "delivery_history" not in driver:
                    driver["delivery_history"] = []
                driver["delivery_history"].append({
                    "order_id": order["order_id"],
                    "customer_name": order["customer_name"],
                    "zone": order["zone"],
                    "total": order["total"],
                    "tip": order.get("tip", round(order["total"] * 0.18, 2)),  # Default 18% tip
                    "completed_at": order["delivered_at"],
                })
    
    save_state(state)
    return order

def rate_order(order_id: str, rating: int, tip: float = 0):
    state = load_state()
    if order_id not in state["orders"]:
        return None
    
    order = state["orders"][order_id]
    order["rating"] = rating
    order["tip"] = tip
    
    if order["driver_id"] and order["driver_id"] in state["drivers"]:
        state["drivers"][order["driver_id"]]["tips_today"] += tip
    
    save_state(state)
    return order

def reset_state():
    """Reset to clean state"""
    state = get_default_state()
    save_state(state)
    return state

def run_simulation_step():
    """Run one step of simulation - advance all orders automatically.
    
    Designed for ~3 second intervals across multiple apps:
    - Kitchen: +3% per step = ~34 steps to complete = ~100 seconds
    - Delivery: +4% per step = ~25 steps to complete = ~75 seconds
    """
    state = load_state()
    changed = False
    
    for order_id, order in state["orders"].items():
        if order["status"] == "pending":
            order["status"] = "preparing"
            order["kitchen_progress"] = 3
            changed = True
        
        elif order["status"] == "preparing" and order["kitchen_progress"] < 100:
            order["kitchen_progress"] = min(100, order["kitchen_progress"] + 3)
            
            # Auto-assign driver at 80%
            if order["kitchen_progress"] >= 80 and not order["driver_id"]:
                driver_id = _pick_next_driver(state)
                if driver_id:
                    order["driver_id"] = driver_id
                    state["drivers"][driver_id]["current_order"] = order_id
            
            if order["kitchen_progress"] >= 100:
                order["status"] = "ready"
                order["ready_at"] = datetime.now().isoformat()
            changed = True
        
        elif order["status"] == "ready":
            order["status"] = "picked_up"
            order["picked_up_at"] = datetime.now().isoformat()
            changed = True
        
        elif order["status"] == "picked_up":
            order["status"] = "on_the_way"
            order["delivery_progress"] = 4
            changed = True
        
        elif order["status"] == "on_the_way" and order["delivery_progress"] < 100:
            order["delivery_progress"] = min(100, order["delivery_progress"] + 4)
            progress = order["delivery_progress"] / 100.0
            
            # Fetch or use cached route, then interpolate driver position
            if ROUTES_AVAILABLE:
                if not order.get("route_coords"):
                    route_coords, _, _ = get_route_from_osrm(
                        STORE_LON, STORE_LAT, order["lon"], order["lat"]
                    )
                    order["route_coords"] = route_coords
                
                if order.get("route_coords"):
                    lat, lon = get_driver_position_on_route(order["route_coords"], progress)
                    if lat and lon:
                        order["driver_lat"] = lat
                        order["driver_lon"] = lon
                    else:
                        order["driver_lat"] = STORE_LAT + (order["lat"] - STORE_LAT) * progress
                        order["driver_lon"] = STORE_LON + (order["lon"] - STORE_LON) * progress
                else:
                    order["driver_lat"] = STORE_LAT + (order["lat"] - STORE_LAT) * progress
                    order["driver_lon"] = STORE_LON + (order["lon"] - STORE_LON) * progress
            else:
                order["driver_lat"] = STORE_LAT + (order["lat"] - STORE_LAT) * progress
                order["driver_lon"] = STORE_LON + (order["lon"] - STORE_LON) * progress
            
            order["eta_minutes"] = max(1, int(12 * (1 - progress)))
            
            if order["delivery_progress"] >= 100:
                order["status"] = "delivered"
                order["delivered_at"] = datetime.now().isoformat()
                if order["driver_id"] and order["driver_id"] in state["drivers"]:
                    driver = state["drivers"][order["driver_id"]]
                    driver["current_order"] = None
                    driver["deliveries_today"] += 1
                    
                    # Add to driver's delivery history
                    if "delivery_history" not in driver:
                        driver["delivery_history"] = []
                    driver["delivery_history"].append({
                        "order_id": order["order_id"],
                        "customer_name": order["customer_name"],
                        "zone": order["zone"],
                        "total": order["total"],
                        "tip": order.get("tip", round(order["total"] * 0.18, 2)),
                        "completed_at": order["delivered_at"],
                    })
            changed = True
    
    if changed:
        save_state(state)
    
    return state
