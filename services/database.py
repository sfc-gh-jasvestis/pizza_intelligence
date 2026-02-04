"""
Pizza Operations Pipeline - In-Memory Database
Simulates OLTP and OLAP tables using Python data structures
Thread-safe with event-based notifications for real-time updates
"""

import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import copy

# =============================================================================
# ENUMS
# =============================================================================

class OrderStatus(Enum):
    RECEIVED = "received"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DriverStatus(Enum):
    AVAILABLE = "available"
    ON_DELIVERY = "on_delivery"
    OFF_DUTY = "off_duty"

class KitchenStatus(Enum):
    QUEUED = "queued"
    PREP = "prep"
    OVEN = "oven"
    PACKAGING = "packaging"
    COMPLETED = "completed"

# =============================================================================
# DATA CLASSES (Table Rows)
# =============================================================================

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str = ""
    phone: str = ""
    address: str = ""
    address_lat: float = 0.0
    address_lon: float = 0.0
    zone: str = ""
    total_orders: int = 0
    total_spent: float = 0.0
    total_points: int = 0
    loyalty_tier: str = "Bronze"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Driver:
    driver_id: str
    name: str
    phone: str = ""
    vehicle_type: str = "car"
    status: DriverStatus = DriverStatus.AVAILABLE
    current_lat: float = 0.0
    current_lon: float = 0.0
    current_order_id: Optional[str] = None
    efficiency: float = 1.0
    deliveries_today: int = 0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MenuItem:
    item_id: str
    name: str
    category: str
    price: float
    prep_time_min: int
    is_available: bool = True

@dataclass
class OrderItem:
    order_item_id: str
    order_id: str
    item_id: str
    item_name: str
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    special_instructions: str = ""

@dataclass
class Order:
    order_id: str
    customer_id: str
    customer_name: str
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)
    total_amount: float = 0.0
    item_count: int = 0
    status: OrderStatus = OrderStatus.RECEIVED
    
    # Timestamps
    order_time: datetime = field(default_factory=datetime.now)
    kitchen_start_time: Optional[datetime] = None
    ready_time: Optional[datetime] = None
    dispatch_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    
    # Delivery details
    delivery_address: str = ""
    delivery_lat: float = 0.0
    delivery_lon: float = 0.0
    delivery_zone: str = ""
    estimated_delivery_min: int = 35
    actual_delivery_min: Optional[int] = None
    
    # Conditions
    weather_condition: str = "Cold"
    traffic_condition: str = "moderate"
    
    # Route
    selected_route: str = ""
    route_distance_km: float = 0.0
    route_coords: List[List[float]] = field(default_factory=list)
    
    # Delay tracking
    is_delayed: bool = False
    delay_reason: Optional[str] = None
    delay_minutes: int = 0
    
    # Kitchen progress (0-100%)
    kitchen_progress: int = 0
    kitchen_status: KitchenStatus = KitchenStatus.QUEUED
    
    # Delivery progress (0-100%)
    delivery_progress: int = 0

@dataclass
class DeliveryFact:
    """OLAP fact table record for completed deliveries"""
    delivery_id: str
    order_id: str
    customer_id: str
    driver_id: str
    
    # Time dimensions
    delivery_date: datetime
    delivery_hour: int
    day_of_week: str
    is_weekend: bool
    is_peak_hour: bool
    
    # Metrics
    order_amount: float
    item_count: int
    prep_time_min: int
    delivery_time_min: int
    total_time_min: int
    
    # Performance
    promised_time_min: int = 35
    is_on_time: bool = True
    delay_minutes: int = 0
    delay_reason: Optional[str] = None
    
    # Conditions
    weather_condition: str = ""
    traffic_condition: str = ""
    delivery_zone: str = ""
    delivery_address: str = ""  # Full street address
    route_distance_km: float = 0.0
    
    # Points
    points_earned: int = 0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class LoyaltyTransaction:
    """Customer loyalty points transaction"""
    transaction_id: str
    customer_id: str
    order_id: Optional[str]
    points_type: str  # order_complete, on_time_bonus, weather_patience, referral
    points_amount: int
    points_balance_after: int
    tier_before: str
    tier_after: str
    tier_changed: bool = False
    transaction_date: datetime = field(default_factory=datetime.now)
    notes: str = ""

@dataclass
class WeatherLog:
    """Weather conditions log"""
    log_id: str
    recorded_at: datetime
    condition: str
    temperature_f: int
    wind_speed_mph: int
    precipitation_chance: int
    impact_level: str  # none, low, moderate, severe

# =============================================================================
# IN-MEMORY DATABASE
# =============================================================================

class PizzaDatabase:
    """
    Thread-safe in-memory database simulating OLTP and OLAP tables.
    Supports event callbacks for real-time UI updates.
    Now includes persistence to SQLite for data survival across restarts.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for shared database access"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._data_lock = threading.RLock()
        
        # OLTP Tables
        self.customers: Dict[str, Customer] = {}
        self.drivers: Dict[str, Driver] = {}
        self.menu_items: Dict[str, MenuItem] = {}
        self.orders: Dict[str, Order] = {}
        
        # OLAP Tables
        self.delivery_facts: Dict[str, DeliveryFact] = {}
        self.loyalty_transactions: List[LoyaltyTransaction] = []
        self.weather_logs: List[WeatherLog] = []
        
        # Current conditions - randomize for demo variety
        import random
        weather_options = ["Sunny", "Cloudy", "Rainy", "Snowy", "Clear", "Cold"]
        self.current_weather: str = random.choice(weather_options)
        self.current_traffic: str = random.choice(["light", "moderate", "heavy"])
        
        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Persistence manager (lazy loaded)
        self._persistence = None
        
        # Order counter for generating IDs
        self._order_counter = 0
        
        # Initialize with seed data
        self._seed_data()
        
        # Load persisted data
        self._load_persisted_data()
    
    def _get_persistence(self):
        """Get the persistence manager (lazy load to avoid circular imports)"""
        if self._persistence is None:
            try:
                from services.persistence import get_persistence_manager
                self._persistence = get_persistence_manager()
            except Exception as e:
                print(f"Warning: Persistence not available: {e}")
        return self._persistence
    
    def _load_persisted_data(self):
        """Load data from SQLite on startup"""
        pm = self._get_persistence()
        if not pm:
            return
        
        try:
            # Load orders
            order_rows = pm.load_orders()
            for row in order_rows:
                order = self._row_to_order(row)
                if order:
                    self.orders[order.order_id] = order
                    # Track highest order number
                    try:
                        num = int(order.order_id.split("-")[1])
                        self._order_counter = max(self._order_counter, num)
                    except:
                        pass
            
            # Load delivery facts
            fact_rows = pm.load_delivery_facts()
            for row in fact_rows:
                fact = self._row_to_delivery_fact(row)
                if fact:
                    self.delivery_facts[fact.delivery_id] = fact
            
            # Load loyalty transactions
            tx_rows = pm.load_loyalty_transactions()
            for row in tx_rows:
                tx = self._row_to_loyalty_transaction(row)
                if tx:
                    self.loyalty_transactions.append(tx)
            
            # Load customer states (update loyalty info)
            customer_states = pm.load_customer_states()
            for customer_id, state in customer_states.items():
                if customer_id in self.customers:
                    self.customers[customer_id].total_orders = state.get("total_orders", 0)
                    self.customers[customer_id].total_spent = state.get("total_spent", 0.0)
                    self.customers[customer_id].total_points = state.get("total_points", 0)
                    self.customers[customer_id].loyalty_tier = state.get("loyalty_tier", "Bronze")
            
            stats = pm.get_stats()
            if stats.get("total_orders", 0) > 0:
                print(f"📂 Loaded {stats['total_orders']} orders, {stats['delivery_facts']} deliveries from history")
                
        except Exception as e:
            print(f"Warning: Error loading persisted data: {e}")
    
    def _row_to_order(self, row: Dict) -> Optional[Order]:
        """Convert a database row to an Order object"""
        try:
            import json
            from services.persistence import str_to_datetime
            
            # Parse items JSON
            items_json = row.get("items_json", "[]")
            items_data = json.loads(items_json) if items_json else []
            items = [
                OrderItem(
                    order_item_id=item["order_item_id"],
                    order_id=item["order_id"],
                    item_id=item["item_id"],
                    item_name=item["item_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["total_price"],
                    special_instructions=item.get("special_instructions", ""),
                )
                for item in items_data
            ]
            
            # Parse route coords
            route_coords_json = row.get("route_coords_json", "[]")
            route_coords = json.loads(route_coords_json) if route_coords_json else []
            
            return Order(
                order_id=row["order_id"],
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                driver_id=row.get("driver_id"),
                driver_name=row.get("driver_name"),
                items=items,
                total_amount=row["total_amount"],
                item_count=row["item_count"],
                status=OrderStatus(row["status"]),
                order_time=str_to_datetime(row.get("order_time")) or datetime.now(),
                kitchen_start_time=str_to_datetime(row.get("kitchen_start_time")),
                ready_time=str_to_datetime(row.get("ready_time")),
                dispatch_time=str_to_datetime(row.get("dispatch_time")),
                delivery_time=str_to_datetime(row.get("delivery_time")),
                delivery_address=row.get("delivery_address", ""),
                delivery_lat=row.get("delivery_lat", 0.0),
                delivery_lon=row.get("delivery_lon", 0.0),
                delivery_zone=row.get("delivery_zone", ""),
                estimated_delivery_min=row.get("estimated_delivery_min", 35),
                actual_delivery_min=row.get("actual_delivery_min"),
                weather_condition=row.get("weather_condition", "Cold"),
                traffic_condition=row.get("traffic_condition", "moderate"),
                selected_route=row.get("selected_route", ""),
                route_distance_km=row.get("route_distance_km", 0.0),
                route_coords=route_coords,
                is_delayed=bool(row.get("is_delayed", 0)),
                delay_reason=row.get("delay_reason"),
                delay_minutes=row.get("delay_minutes", 0),
                kitchen_progress=row.get("kitchen_progress", 0),
                kitchen_status=KitchenStatus(row.get("kitchen_status", "queued")),
                delivery_progress=row.get("delivery_progress", 0),
            )
        except Exception as e:
            print(f"Error converting row to order: {e}")
            return None
    
    def _row_to_delivery_fact(self, row: Dict) -> Optional[DeliveryFact]:
        """Convert a database row to a DeliveryFact object"""
        try:
            from services.persistence import str_to_datetime
            
            return DeliveryFact(
                delivery_id=row["delivery_id"],
                order_id=row["order_id"],
                customer_id=row["customer_id"],
                driver_id=row["driver_id"],
                delivery_date=str_to_datetime(row.get("delivery_date")) or datetime.now(),
                delivery_hour=row.get("delivery_hour", 0),
                day_of_week=row.get("day_of_week", ""),
                is_weekend=bool(row.get("is_weekend", 0)),
                is_peak_hour=bool(row.get("is_peak_hour", 0)),
                order_amount=row.get("order_amount", 0.0),
                item_count=row.get("item_count", 0),
                prep_time_min=row.get("prep_time_min", 0),
                delivery_time_min=row.get("delivery_time_min", 0),
                total_time_min=row.get("total_time_min", 0),
                promised_time_min=row.get("promised_time_min", 35),
                is_on_time=bool(row.get("is_on_time", 1)),
                delay_minutes=row.get("delay_minutes", 0),
                delay_reason=row.get("delay_reason"),
                weather_condition=row.get("weather_condition", ""),
                traffic_condition=row.get("traffic_condition", ""),
                delivery_zone=row.get("delivery_zone", ""),
                delivery_address=row.get("delivery_address", ""),
                route_distance_km=row.get("route_distance_km", 0.0),
                points_earned=row.get("points_earned", 0),
            )
        except Exception as e:
            print(f"Error converting row to delivery fact: {e}")
            return None
    
    def _row_to_loyalty_transaction(self, row: Dict) -> Optional[LoyaltyTransaction]:
        """Convert a database row to a LoyaltyTransaction object"""
        try:
            from services.persistence import str_to_datetime
            
            return LoyaltyTransaction(
                transaction_id=row["transaction_id"],
                customer_id=row["customer_id"],
                order_id=row.get("order_id"),
                points_type=row.get("points_type", ""),
                points_amount=row.get("points_amount", 0),
                points_balance_after=row.get("points_balance_after", 0),
                tier_before=row.get("tier_before", "Bronze"),
                tier_after=row.get("tier_after", "Bronze"),
                tier_changed=bool(row.get("tier_changed", 0)),
                transaction_date=str_to_datetime(row.get("transaction_date")) or datetime.now(),
                notes=row.get("notes", ""),
            )
        except Exception as e:
            print(f"Error converting row to loyalty transaction: {e}")
            return None
    
    def get_next_order_number(self) -> int:
        """Get the next order number"""
        with self._data_lock:
            self._order_counter += 1
            return self._order_counter
    
    def _seed_data(self):
        """Initialize database with seed data from settings"""
        from config.settings import MENU_ITEMS, DRIVERS, CUSTOMERS, STORE_CONFIG
        
        # Seed menu items
        for item_id, item_data in MENU_ITEMS.items():
            self.menu_items[item_id] = MenuItem(
                item_id=item_id,
                name=item_data["name"],
                category=item_data["category"],
                price=item_data["price"],
                prep_time_min=item_data["prep_time_min"],
            )
        
        # Seed drivers
        for d in DRIVERS:
            self.drivers[d["driver_id"]] = Driver(
                driver_id=d["driver_id"],
                name=d["name"],
                vehicle_type=d["vehicle"],
                efficiency=d["efficiency"],
                current_lat=STORE_CONFIG["lat"],
                current_lon=STORE_CONFIG["lon"],
            )
        
        # Seed customers
        for c in CUSTOMERS:
            self.customers[c["customer_id"]] = Customer(
                customer_id=c["customer_id"],
                name=c["name"],
                address=c["address"],
                address_lat=c["lat"],
                address_lon=c["lon"],
                zone=c["zone"],
            )
    
    # =========================================================================
    # EVENT SYSTEM
    # =========================================================================
    
    def subscribe(self, event: str, callback: Callable):
        """Subscribe to database events"""
        self._callbacks[event].append(callback)
    
    def unsubscribe(self, event: str, callback: Callable):
        """Unsubscribe from database events"""
        if callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def _emit(self, event: str, data: Any = None):
        """Emit an event to all subscribers"""
        for callback in self._callbacks[event]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in callback for {event}: {e}")
    
    # =========================================================================
    # ORDER OPERATIONS
    # =========================================================================
    
    def create_order(self, order: Order) -> Order:
        """Insert a new order into the database"""
        with self._data_lock:
            self.orders[order.order_id] = order
            self._emit("order_created", order)
            # Persist to SQLite
            pm = self._get_persistence()
            if pm:
                pm.save_order(order)
        return order
    
    def update_order(self, order_id: str, **updates) -> Optional[Order]:
        """Update an existing order"""
        with self._data_lock:
            if order_id not in self.orders:
                return None
            order = self.orders[order_id]
            for key, value in updates.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            self._emit("order_updated", order)
            # Persist to SQLite (only on significant status changes to avoid too many writes)
            if "status" in updates or "delivery_progress" in updates and updates.get("delivery_progress", 0) >= 100:
                pm = self._get_persistence()
                if pm:
                    pm.save_order(order)
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        with self._data_lock:
            return copy.deepcopy(self.orders.get(order_id))
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get all orders with a specific status"""
        with self._data_lock:
            return [copy.deepcopy(o) for o in self.orders.values() if o.status == status]
    
    def get_active_orders(self) -> List[Order]:
        """Get all non-completed orders"""
        with self._data_lock:
            active_statuses = [
                OrderStatus.RECEIVED, OrderStatus.CONFIRMED, 
                OrderStatus.PREPARING, OrderStatus.READY,
                OrderStatus.OUT_FOR_DELIVERY
            ]
            return [copy.deepcopy(o) for o in self.orders.values() if o.status in active_statuses]
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        with self._data_lock:
            return [copy.deepcopy(o) for o in self.orders.values()]
    
    # =========================================================================
    # DRIVER OPERATIONS
    # =========================================================================
    
    def get_available_drivers(self) -> List[Driver]:
        """Get all available drivers"""
        with self._data_lock:
            return [copy.deepcopy(d) for d in self.drivers.values() 
                    if d.status == DriverStatus.AVAILABLE]
    
    def assign_driver(self, driver_id: str, order_id: str) -> bool:
        """Assign a driver to an order"""
        with self._data_lock:
            if driver_id not in self.drivers:
                return False
            driver = self.drivers[driver_id]
            driver.status = DriverStatus.ON_DELIVERY
            driver.current_order_id = order_id
            self._emit("driver_assigned", {"driver": driver, "order_id": order_id})
        return True
    
    def release_driver(self, driver_id: str) -> bool:
        """Release a driver after delivery"""
        with self._data_lock:
            if driver_id not in self.drivers:
                return False
            driver = self.drivers[driver_id]
            driver.status = DriverStatus.AVAILABLE
            driver.current_order_id = None
            driver.deliveries_today += 1
            self._emit("driver_released", driver)
        return True
    
    def update_driver_position(self, driver_id: str, lat: float, lon: float):
        """Update driver's current position"""
        with self._data_lock:
            if driver_id in self.drivers:
                self.drivers[driver_id].current_lat = lat
                self.drivers[driver_id].current_lon = lon
    
    # =========================================================================
    # CUSTOMER OPERATIONS
    # =========================================================================
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID"""
        with self._data_lock:
            return copy.deepcopy(self.customers.get(customer_id))
    
    def get_driver(self, driver_id: str) -> Optional[Driver]:
        """Get a driver by ID"""
        with self._data_lock:
            return copy.deepcopy(self.drivers.get(driver_id))
    
    def update_customer_loyalty(self, customer_id: str, points: int, tier: str):
        """Update customer loyalty points and tier"""
        with self._data_lock:
            if customer_id in self.customers:
                customer = self.customers[customer_id]
                customer.total_points += points
                customer.total_orders += 1  # Increment order count
                customer.loyalty_tier = tier
                self._emit("customer_updated", customer)
                # Persist customer state
                pm = self._get_persistence()
                if pm:
                    pm.save_customer_state(customer)
    
    # =========================================================================
    # ANALYTICS OPERATIONS (OLAP)
    # =========================================================================
    
    def record_delivery(self, fact: DeliveryFact):
        """Record a completed delivery to OLAP"""
        with self._data_lock:
            self.delivery_facts[fact.delivery_id] = fact
            self._emit("delivery_recorded", fact)
            # Persist to SQLite
            pm = self._get_persistence()
            if pm:
                pm.save_delivery_fact(fact)
    
    def record_loyalty_transaction(self, transaction: LoyaltyTransaction):
        """Record a loyalty points transaction"""
        with self._data_lock:
            self.loyalty_transactions.append(transaction)
            self._emit("loyalty_updated", transaction)
            # Persist to SQLite
            pm = self._get_persistence()
            if pm:
                pm.save_loyalty_transaction(transaction)
    
    def get_delivery_stats(self) -> Dict:
        """Get delivery statistics"""
        with self._data_lock:
            facts = list(self.delivery_facts.values())
            if not facts:
                return {"total": 0, "on_time": 0, "late": 0, "avg_time": 0}
            
            total = len(facts)
            on_time = sum(1 for f in facts if f.is_on_time)
            late = total - on_time
            avg_time = sum(f.total_time_min for f in facts) / total if total > 0 else 0
            
            return {
                "total": total,
                "on_time": on_time,
                "late": late,
                "on_time_rate": round(on_time / total * 100, 1) if total > 0 else 0,
                "avg_time": round(avg_time, 1),
            }
    
    def get_zone_stats(self) -> Dict[str, Dict]:
        """Get delivery statistics by zone"""
        with self._data_lock:
            zone_stats = defaultdict(lambda: {"total": 0, "late": 0, "total_time": 0})
            for fact in self.delivery_facts.values():
                zone = fact.delivery_zone
                zone_stats[zone]["total"] += 1
                zone_stats[zone]["total_time"] += fact.total_time_min
                if not fact.is_on_time:
                    zone_stats[zone]["late"] += 1
            
            result = {}
            for zone, stats in zone_stats.items():
                result[zone] = {
                    "total": stats["total"],
                    "late": stats["late"],
                    "late_rate": round(stats["late"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
                    "avg_time": round(stats["total_time"] / stats["total"], 1) if stats["total"] > 0 else 0,
                }
            return result
    
    # =========================================================================
    # WEATHER & TRAFFIC
    # =========================================================================
    
    def set_weather(self, condition: str):
        """Set current weather condition"""
        with self._data_lock:
            self.current_weather = condition
            self._emit("weather_changed", condition)
    
    def set_traffic(self, condition: str):
        """Set current traffic condition"""
        with self._data_lock:
            self.current_traffic = condition
            self._emit("traffic_changed", condition)
    
    def get_conditions(self) -> Dict[str, str]:
        """Get current weather and traffic conditions"""
        with self._data_lock:
            return {
                "weather": self.current_weather,
                "traffic": self.current_traffic,
            }
    
    # =========================================================================
    # RESET
    # =========================================================================
    
    def reset(self, clear_persistence: bool = True):
        """Reset the database to initial state"""
        import random
        with self._data_lock:
            self.orders.clear()
            self.delivery_facts.clear()
            self.loyalty_transactions.clear()
            self._order_counter = 0
            
            # Reset drivers
            for driver in self.drivers.values():
                driver.status = DriverStatus.AVAILABLE
                driver.current_order_id = None
                driver.deliveries_today = 0
            
            # Reset customers
            for customer in self.customers.values():
                customer.total_orders = 0
                customer.total_spent = 0.0
                customer.total_points = 0
                customer.loyalty_tier = "Bronze"
            
            # Randomize weather for variety in demos
            weather_options = ["Sunny", "Cloudy", "Rainy", "Snowy", "Clear", "Cold"]
            weather_weights = [25, 20, 20, 10, 15, 10]
            self.current_weather = random.choices(weather_options, weights=weather_weights)[0]
            
            # Clear persistence if requested
            if clear_persistence:
                pm = self._get_persistence()
                if pm:
                    pm.clear_all()
            
            self._emit("database_reset", None)


# Global database singleton instance
_db_instance: Optional[PizzaDatabase] = None

def get_database() -> PizzaDatabase:
    """Get the singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PizzaDatabase()
    return _db_instance

def reset_database_singleton():
    """Force reset the database singleton (creates fresh instance)"""
    global _db_instance
    if _db_instance is not None:
        _db_instance.reset(clear_persistence=True)
    _db_instance = None
