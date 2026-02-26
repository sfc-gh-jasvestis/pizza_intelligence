"""
Shared state management for Pizza Demo Apps.
Enables communication between Ops, Driver, and Customer apps.
"""

import json
import os
import time
from datetime import datetime
from typing import Optional

try:
    from menu_data import MENU_ITEMS, DELIVERY_ZONES, DRIVERS
except ImportError:
    MENU_ITEMS = None
    DELIVERY_ZONES = None
    DRIVERS = None

# Shared state file path
STATE_FILE = os.environ.get(
    "PIZZA_STATE_FILE",
    os.path.join(os.path.dirname(__file__), ".pizza_demo_state.json"),
)

def get_default_state():
    """Return default state structure."""
    default_drivers = {
        "DRV001": {"name": "Mike Rodriguez", "phone": "555-0101", "rating": 4.8, "vehicle": "Honda Civic", "color": "Silver", "deliveries_today": 0, "tips_today": 0},
        "DRV002": {"name": "Sarah Chen", "phone": "555-0102", "rating": 4.9, "vehicle": "Toyota Prius", "color": "Blue", "deliveries_today": 0, "tips_today": 0},
        "DRV003": {"name": "James Wilson", "phone": "555-0103", "rating": 4.7, "vehicle": "Ford Focus", "color": "Red", "deliveries_today": 0, "tips_today": 0},
        "DRV004": {"name": "Emma Thompson", "phone": "555-0104", "rating": 4.9, "vehicle": "Hyundai Elantra", "color": "White", "deliveries_today": 0, "tips_today": 0},
    }
    
    if DRIVERS:
        default_drivers = {
            k: {**v, "deliveries_today": 0, "tips_today": 0} 
            for k, v in DRIVERS.items()
        }
    
    return {
        "orders": {},
        "drivers": default_drivers,
        "last_updated": datetime.now().isoformat()
    }


def load_state() -> dict:
    """Load shared state from file."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return get_default_state()


def save_state(state: dict):
    """Save shared state to file."""
    state["last_updated"] = datetime.now().isoformat()
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except IOError as e:
        print(f"Error saving state: {e}")


def create_order(order_id: str, customer_name: str, customer_phone: str, 
                 items: list, address: str, zone: str, 
                 lat: float, lon: float, total: float,
                 special_instructions: str = "") -> dict:
    """Create a new order and add to shared state."""
    state = load_state()
    
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
        "status": "pending",  # pending, preparing, ready, picked_up, on_the_way, delivered
        "driver_id": None,
        "driver_lat": None,
        "driver_lon": None,
        "created_at": datetime.now().isoformat(),
        "picked_up_at": None,
        "delivered_at": None,
        "eta_minutes": None,
        "rating": None,
        "tip": None
    }
    
    state["orders"][order_id] = order
    save_state(state)
    return order


def assign_driver(order_id: str, driver_id: str):
    """Assign a driver to an order."""
    state = load_state()
    if order_id in state["orders"]:
        state["orders"][order_id]["driver_id"] = driver_id
        state["orders"][order_id]["status"] = "preparing"
        # Set initial driver position (store location)
        state["orders"][order_id]["driver_lat"] = 41.8827
        state["orders"][order_id]["driver_lon"] = -87.6233
        state["orders"][order_id]["eta_minutes"] = 25
        save_state(state)


def update_order_status(order_id: str, status: str):
    """Update order status."""
    state = load_state()
    if order_id in state["orders"]:
        state["orders"][order_id]["status"] = status
        if status == "picked_up":
            state["orders"][order_id]["picked_up_at"] = datetime.now().isoformat()
        elif status == "delivered":
            state["orders"][order_id]["delivered_at"] = datetime.now().isoformat()
            # Update driver stats
            driver_id = state["orders"][order_id]["driver_id"]
            if driver_id and driver_id in state["drivers"]:
                state["drivers"][driver_id]["deliveries_today"] += 1
        save_state(state)


def update_driver_location(order_id: str, lat: float, lon: float, eta_minutes: int = None):
    """Update driver location for an order."""
    state = load_state()
    if order_id in state["orders"]:
        state["orders"][order_id]["driver_lat"] = lat
        state["orders"][order_id]["driver_lon"] = lon
        if eta_minutes is not None:
            state["orders"][order_id]["eta_minutes"] = eta_minutes
        save_state(state)


def rate_order(order_id: str, rating: int, tip: float = 0):
    """Customer rates and tips the order."""
    state = load_state()
    if order_id in state["orders"]:
        state["orders"][order_id]["rating"] = rating
        state["orders"][order_id]["tip"] = tip
        # Update driver tips
        driver_id = state["orders"][order_id]["driver_id"]
        if driver_id and driver_id in state["drivers"]:
            state["drivers"][driver_id]["tips_today"] += tip
        save_state(state)


def get_order(order_id: str) -> Optional[dict]:
    """Get a specific order."""
    state = load_state()
    return state["orders"].get(order_id)


def get_driver_orders(driver_id: str) -> list:
    """Get all orders assigned to a driver."""
    state = load_state()
    orders = []
    for order_id, order in state["orders"].items():
        if order["driver_id"] == driver_id and order["status"] not in ["delivered", "cancelled"]:
            orders.append(order)
    return sorted(orders, key=lambda x: x["created_at"])


def get_driver_info(driver_id: str) -> Optional[dict]:
    """Get driver information."""
    state = load_state()
    return state["drivers"].get(driver_id)


def get_all_active_orders() -> list:
    """Get all active (non-delivered) orders."""
    state = load_state()
    return [o for o in state["orders"].values() if o["status"] not in ["delivered", "cancelled"]]


def clear_old_orders(hours: int = 24):
    """Clear orders older than specified hours."""
    state = load_state()
    cutoff = datetime.now().timestamp() - (hours * 3600)
    
    orders_to_remove = []
    for order_id, order in state["orders"].items():
        try:
            created = datetime.fromisoformat(order["created_at"]).timestamp()
            if created < cutoff:
                orders_to_remove.append(order_id)
        except:
            pass
    
    for order_id in orders_to_remove:
        del state["orders"][order_id]
    
    if orders_to_remove:
        save_state(state)


# Demo helper functions
def create_demo_order():
    """Create a demo order for testing."""
    import random
    
    if DELIVERY_ZONES:
        customers = [
            ("John Smith", "555-1234", dz["address"], dz["zone"], dz["lat"], dz["lon"])
            for dz in DELIVERY_ZONES
        ]
    else:
        customers = [
            ("John Smith", "555-1234", "456 Oak Ave, River North", "River North", 41.8925, -87.6340),
            ("Emily Davis", "555-2345", "789 State St, West Loop", "West Loop", 41.8827, -87.6474),
            ("Michael Brown", "555-3456", "321 Wacker Dr, Loop", "Loop", 41.8869, -87.6368),
            ("Sarah Johnson", "555-4567", "654 Michigan Ave, Streeterville", "Streeterville", 41.8951, -87.6244),
        ]
    
    if MENU_ITEMS:
        pizzas = MENU_ITEMS.get("Pizzas", [])
        sides = MENU_ITEMS.get("Sides", [])
        drinks = MENU_ITEMS.get("Drinks", [])
        desserts = MENU_ITEMS.get("Desserts", [])
        
        items_options = []
        for _ in range(4):
            combo = []
            if pizzas:
                combo.append(random.choice(pizzas)["name"])
            if sides:
                combo.append(random.choice(sides)["name"])
            if drinks:
                combo.append(random.choice(drinks)["name"])
            items_options.append(combo)
    else:
        items_options = [
            ["Pepperoni Classic", "Garlic Bread", "2L Coca-Cola"],
            ["Margherita", "Caesar Salad", "Tiramisu"],
            ["Meat Lovers", "Buffalo Wings (8pc)", "Cheesy Bread"],
            ["BBQ Chicken", "Mozzarella Sticks", "Chocolate Brownie"],
        ]
    
    customer = random.choice(customers)
    items = random.choice(items_options)
    total = random.uniform(28, 65)
    
    state = load_state()
    counter = state.get("order_counter", 0) + 1
    state["order_counter"] = counter
    save_state(state)
    order_id = f"ORD-{counter:05d}"
    
    order = create_order(
        order_id=order_id,
        customer_name=customer[0],
        customer_phone=customer[1],
        items=items,
        address=customer[2],
        zone=customer[3],
        lat=customer[4],
        lon=customer[5],
        total=round(total, 2),
        special_instructions=random.choice(["", "Ring doorbell twice", "Leave at door", "Extra napkins please"])
    )
    
    driver_ids = list(DRIVERS.keys()) if DRIVERS else ["DRV001", "DRV002", "DRV003", "DRV004"]
    driver_id = random.choice(driver_ids)
    assign_driver(order_id, driver_id)
    
    return order_id, driver_id


if __name__ == "__main__":
    # Test the shared state
    print("Creating demo order...")
    order_id, driver_id = create_demo_order()
    print(f"Created order {order_id} assigned to {driver_id}")
    
    order = get_order(order_id)
    print(f"Order details: {json.dumps(order, indent=2)}")
