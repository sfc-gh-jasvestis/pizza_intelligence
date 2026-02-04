"""
Pizza Operations Pipeline - Order Simulator
Generates random pizza orders and inserts them into the OLTP database
"""

import random
import time
import threading
import uuid
from datetime import datetime
from typing import List, Optional, Callable

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    MENU_ITEMS, CUSTOMERS, SIMULATION_CONFIG, 
    WEATHER_CONDITIONS, TRAFFIC_BY_HOUR, DELIVERY_ZONES
)
from services.database import (
    get_database, Order, OrderItem, OrderStatus, KitchenStatus
)

# =============================================================================
# ORDER GENERATOR
# =============================================================================

# Chicago streets for random address generation
CHICAGO_STREETS = {
    "Gold Coast": ["N Michigan Ave", "E Oak St", "E Walton St", "E Delaware Pl", "N Rush St"],
    "Magnificent Mile": ["N Michigan Ave", "E Ohio St", "E Ontario St", "E Erie St", "N Wabash Ave"],
    "West Loop": ["W Madison St", "W Monroe St", "W Adams St", "S Halsted St", "W Randolph St"],
    "River North": ["N Orleans St", "N Clark St", "W Hubbard St", "W Kinzie St", "N Wells St"],
    "Streeterville": ["E Illinois St", "E Grand Ave", "N McClurg Ct", "E North Water St", "N Fairbanks Ct"],
    "Lakeshore East": ["E Randolph St", "N Harbor Dr", "E South Water St", "N Columbus Dr"],
    "Loop Core": ["N State St", "W Washington St", "N Dearborn St", "W Madison St", "N Clark St"],
    "Financial District": ["W Jackson Blvd", "S LaSalle St", "W Van Buren St", "S Clark St", "W Adams St"],
}

# Random customer names (first + last)
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kevin", "Dorothy", "Brian", "Carol", "George", "Amanda", "Timothy", "Melissa",
    "Ronald", "Deborah", "Edward", "Stephanie", "Jason", "Rebecca", "Jeffrey", "Sharon",
    "Ryan", "Laura", "Jacob", "Cynthia", "Gary", "Kathleen", "Nicholas", "Amy",
    "Eric", "Angela", "Jonathan", "Shirley", "Stephen", "Anna", "Larry", "Brenda",
    "Justin", "Pamela", "Scott", "Emma", "Brandon", "Nicole", "Benjamin", "Helen",
    "Samuel", "Samantha", "Raymond", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Patrick", "Carolyn", "Raymond", "Janet", "Jack", "Catherine",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
]

def generate_random_name() -> str:
    """Generate a random full name"""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_random_address(zone: str) -> str:
    """Generate a random Chicago street address for a zone"""
    streets = CHICAGO_STREETS.get(zone, ["W Madison St", "N State St", "S Clark St"])
    street = random.choice(streets)
    # Generate realistic Chicago address numbers (typically 1-2000 for downtown)
    number = random.randint(100, 1999)
    return f"{number} {street}"

class OrderSimulator:
    """
    Simulates incoming pizza orders at configurable intervals.
    Generates realistic order patterns based on time of day and conditions.
    """
    
    def __init__(self):
        self.db = get_database()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._order_count = 0
        self._callbacks: List[Callable] = []
    
    def subscribe(self, callback: Callable):
        """Subscribe to new order events"""
        self._callbacks.append(callback)
    
    def _notify(self, order: Order):
        """Notify subscribers of new order"""
        for callback in self._callbacks:
            try:
                callback(order)
            except Exception as e:
                print(f"Error in order callback: {e}")
    
    def generate_order(self) -> Order:
        """Generate a single random order"""
        # Pick a random customer
        customer_id = random.choice(list(self.db.customers.keys()))
        customer = self.db.customers[customer_id]
        
        # Generate order ID using database counter (ensures unique IDs across restarts)
        order_num = self.db.get_next_order_number()
        order_id = f"ORD-{order_num:05d}"
        
        # Pick random menu items (1-4 items)
        num_items = random.choices([1, 2, 3, 4], weights=[30, 40, 20, 10])[0]
        
        # Favor pizzas but include other items
        pizza_items = [k for k, v in MENU_ITEMS.items() if v["category"] == "pizza"]
        other_items = [k for k, v in MENU_ITEMS.items() if v["category"] != "pizza"]
        
        selected_items = []
        # Always at least one pizza
        selected_items.append(random.choice(pizza_items))
        
        # Add more items
        for _ in range(num_items - 1):
            if random.random() < 0.6:
                selected_items.append(random.choice(pizza_items))
            else:
                selected_items.append(random.choice(other_items))
        
        # Create order items
        order_items = []
        total_amount = 0.0
        total_prep_time = 0
        
        for i, item_id in enumerate(selected_items):
            item_data = MENU_ITEMS[item_id]
            quantity = random.choices([1, 2], weights=[85, 15])[0]
            unit_price = item_data["price"]
            item_total = unit_price * quantity
            
            order_item = OrderItem(
                order_item_id=f"{order_id}-{i+1:02d}",
                order_id=order_id,
                item_id=item_id,
                item_name=item_data["name"],
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total,
            )
            order_items.append(order_item)
            total_amount += item_total
            total_prep_time = max(total_prep_time, item_data["prep_time_min"])
        
        # Get current weather - consistent for all orders at this moment
        # Weather changes slowly (cached in database), not per-order
        conditions = self.db.get_conditions()
        weather = conditions["weather"]
        
        # Get traffic based on hour AND zone (different zones can have different traffic)
        current_hour = datetime.now().hour
        base_traffic, base_mult = TRAFFIC_BY_HOUR.get(current_hour, ("moderate", 1.2))
        
        # Zone-based traffic variation - some zones are busier than others
        zone = customer.zone
        zone_traffic_bias = {
            "Loop Core": 0.3,           # Often heavier traffic
            "Magnificent Mile": 0.2,    # Tourist area, moderate bias
            "River North": 0.1,         # Slight bias
            "West Loop": 0.0,           # Use base traffic
            "Streeterville": -0.1,      # Slightly lighter
            "Financial District": 0.2,  # Business area
            "Lakeshore East": -0.2,     # Residential, lighter
        }
        
        # Adjust traffic based on zone
        bias = zone_traffic_bias.get(zone, 0.0)
        traffic_options = ["light", "moderate", "heavy"]
        traffic_mults = {"light": 1.0, "moderate": 1.2, "heavy": 1.5}
        
        # Find current traffic index and potentially shift based on zone
        current_idx = traffic_options.index(base_traffic)
        
        # Random chance to shift traffic level based on zone bias
        if random.random() < abs(bias):
            if bias > 0 and current_idx < 2:  # Zone tends heavier
                current_idx += 1
            elif bias < 0 and current_idx > 0:  # Zone tends lighter
                current_idx -= 1
        
        traffic_condition = traffic_options[current_idx]
        traffic_mult = traffic_mults[traffic_condition]
        
        # Get zone info
        zone = customer.zone
        zone_info = DELIVERY_ZONES.get(zone, {"avg_delivery_min": 20, "risk_level": "medium"})
        
        # Calculate estimated delivery time
        weather_mult = WEATHER_CONDITIONS.get(weather, {}).get("delivery_multiplier", 1.0)
        base_delivery = zone_info["avg_delivery_min"]
        estimated_delivery = int(total_prep_time + (base_delivery * weather_mult * traffic_mult))
        
        # Calculate distance (simplified - based on lat/lon difference)
        from config.settings import STORE_CONFIG
        lat_diff = abs(customer.address_lat - STORE_CONFIG["lat"])
        lon_diff = abs(customer.address_lon - STORE_CONFIG["lon"])
        distance_km = round((lat_diff + lon_diff) * 111 * 0.7, 2)  # Rough conversion
        
        # Generate random customer name and address for this order
        random_name = generate_random_name()
        random_address = generate_random_address(zone)
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=customer_id,
            customer_name=random_name,  # Use randomized name
            items=order_items,
            total_amount=round(total_amount, 2),
            item_count=len(order_items),
            status=OrderStatus.RECEIVED,
            order_time=datetime.now(),
            delivery_address=random_address,  # Use randomized address
            delivery_lat=customer.address_lat,
            delivery_lon=customer.address_lon,
            delivery_zone=zone,
            estimated_delivery_min=min(estimated_delivery, 45),  # Cap at 45 min
            weather_condition=weather,
            traffic_condition=traffic_condition,
            route_distance_km=distance_km,
            kitchen_status=KitchenStatus.QUEUED,
        )
        
        # Insert into database
        self.db.create_order(order)
        
        # Notify subscribers
        self._notify(order)
        
        print(f"📥 New Order: {order_id} | {random_name} | {zone} | ${total_amount:.2f} | ETA: {estimated_delivery} min")
        
        return order
    
    def _simulation_loop(self):
        """Main simulation loop"""
        interval = SIMULATION_CONFIG["order_interval_sec"]
        
        while self.running:
            try:
                self.generate_order()
            except Exception as e:
                print(f"Error generating order: {e}")
            
            # Variable interval for realism (±30%)
            actual_interval = interval * random.uniform(0.7, 1.3)
            time.sleep(actual_interval)
    
    def start(self, interval_override: Optional[float] = None):
        """Start the order simulation"""
        if self.running:
            print("Simulator already running")
            return
        
        if interval_override:
            SIMULATION_CONFIG["order_interval_sec"] = interval_override
        
        self.running = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()
        print(f"🚀 Order Simulator started (interval: {SIMULATION_CONFIG['order_interval_sec']}s)")
    
    def stop(self):
        """Stop the order simulation"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("🛑 Order Simulator stopped")
    
    def generate_burst(self, count: int = 5, delay: float = 0.5):
        """Generate a burst of orders (for demo)"""
        print(f"⚡ Generating burst of {count} orders...")
        for i in range(count):
            self.generate_order()
            if i < count - 1:
                time.sleep(delay)
        print(f"✅ Burst complete: {count} orders generated")


# =============================================================================
# STANDALONE USAGE
# =============================================================================

def main():
    """Run the order simulator standalone"""
    simulator = OrderSimulator()
    
    print("=" * 60)
    print("PIZZA ORDER SIMULATOR")
    print("=" * 60)
    print("\nCommands:")
    print("  g - Generate single order")
    print("  b - Generate burst (5 orders)")
    print("  s - Start continuous simulation")
    print("  x - Stop simulation")
    print("  q - Quit")
    print("=" * 60)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'g':
                simulator.generate_order()
            elif cmd == 'b':
                simulator.generate_burst()
            elif cmd == 's':
                simulator.start()
            elif cmd == 'x':
                simulator.stop()
            elif cmd == 'q':
                simulator.stop()
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        simulator.stop()
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
