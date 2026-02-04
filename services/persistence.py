"""
Pizza Operations Pipeline - Data Persistence Layer
Saves and loads database state to/from SQLite for persistence across restarts
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

# Get the data directory path
DATA_DIR = Path(__file__).parent.parent / "data"
DB_FILE = DATA_DIR / "pizza_store.db"


def ensure_data_dir():
    """Ensure the data directory exists"""
    DATA_DIR.mkdir(exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database"""
    ensure_data_dir()
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection):
    """Initialize the database schema"""
    cursor = conn.cursor()
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            customer_name TEXT,
            driver_id TEXT,
            driver_name TEXT,
            items_json TEXT,
            total_amount REAL,
            item_count INTEGER,
            status TEXT,
            order_time TEXT,
            kitchen_start_time TEXT,
            ready_time TEXT,
            dispatch_time TEXT,
            delivery_time TEXT,
            delivery_address TEXT,
            delivery_lat REAL,
            delivery_lon REAL,
            delivery_zone TEXT,
            estimated_delivery_min INTEGER,
            actual_delivery_min INTEGER,
            weather_condition TEXT,
            traffic_condition TEXT,
            selected_route TEXT,
            route_distance_km REAL,
            route_coords_json TEXT,
            is_delayed INTEGER,
            delay_reason TEXT,
            delay_minutes INTEGER,
            kitchen_progress INTEGER,
            kitchen_status TEXT,
            delivery_progress INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Delivery facts (OLAP)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_facts (
            delivery_id TEXT PRIMARY KEY,
            order_id TEXT,
            customer_id TEXT,
            driver_id TEXT,
            delivery_date TEXT,
            delivery_hour INTEGER,
            day_of_week TEXT,
            is_weekend INTEGER,
            is_peak_hour INTEGER,
            order_amount REAL,
            item_count INTEGER,
            prep_time_min INTEGER,
            delivery_time_min INTEGER,
            total_time_min INTEGER,
            promised_time_min INTEGER,
            is_on_time INTEGER,
            delay_minutes INTEGER,
            delay_reason TEXT,
            weather_condition TEXT,
            traffic_condition TEXT,
            delivery_zone TEXT,
            delivery_address TEXT,
            route_distance_km REAL,
            points_earned INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Loyalty transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loyalty_transactions (
            transaction_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_id TEXT,
            points_type TEXT,
            points_amount INTEGER,
            points_balance_after INTEGER,
            tier_before TEXT,
            tier_after TEXT,
            tier_changed INTEGER,
            transaction_date TEXT,
            notes TEXT
        )
    """)
    
    # Customer state (for persisting loyalty points)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_state (
            customer_id TEXT PRIMARY KEY,
            total_orders INTEGER,
            total_spent REAL,
            total_points INTEGER,
            loyalty_tier TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Driver state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS driver_state (
            driver_id TEXT PRIMARY KEY,
            deliveries_total INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Metadata table for tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migration: Add delivery_address column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE delivery_facts ADD COLUMN delivery_address TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()


def datetime_to_str(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string"""
    if dt is None:
        return None
    return dt.isoformat()


def str_to_datetime(s: Optional[str]) -> Optional[datetime]:
    """Convert ISO string to datetime"""
    if s is None or s == "":
        return None
    try:
        return datetime.fromisoformat(s)
    except:
        return None


class PersistenceManager:
    """Manages saving and loading database state"""
    
    def __init__(self):
        self.conn = get_connection()
        init_schema(self.conn)
    
    def save_order(self, order) -> bool:
        """Save or update an order"""
        try:
            cursor = self.conn.cursor()
            
            # Serialize items to JSON
            items_json = json.dumps([{
                "order_item_id": item.order_item_id,
                "order_id": item.order_id,
                "item_id": item.item_id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "special_instructions": item.special_instructions,
            } for item in order.items])
            
            # Serialize route coords
            route_coords_json = json.dumps(order.route_coords) if order.route_coords else "[]"
            
            cursor.execute("""
                INSERT OR REPLACE INTO orders (
                    order_id, customer_id, customer_name, driver_id, driver_name,
                    items_json, total_amount, item_count, status, order_time,
                    kitchen_start_time, ready_time, dispatch_time, delivery_time,
                    delivery_address, delivery_lat, delivery_lon, delivery_zone,
                    estimated_delivery_min, actual_delivery_min, weather_condition,
                    traffic_condition, selected_route, route_distance_km, route_coords_json,
                    is_delayed, delay_reason, delay_minutes, kitchen_progress,
                    kitchen_status, delivery_progress
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.order_id, order.customer_id, order.customer_name,
                order.driver_id, order.driver_name, items_json,
                order.total_amount, order.item_count, order.status.value,
                datetime_to_str(order.order_time),
                datetime_to_str(order.kitchen_start_time),
                datetime_to_str(order.ready_time),
                datetime_to_str(order.dispatch_time),
                datetime_to_str(order.delivery_time),
                order.delivery_address, order.delivery_lat, order.delivery_lon,
                order.delivery_zone, order.estimated_delivery_min,
                order.actual_delivery_min, order.weather_condition,
                order.traffic_condition, order.selected_route,
                order.route_distance_km, route_coords_json,
                1 if order.is_delayed else 0, order.delay_reason,
                order.delay_minutes, order.kitchen_progress,
                order.kitchen_status.value, order.delivery_progress
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving order: {e}")
            return False
    
    def save_delivery_fact(self, fact) -> bool:
        """Save a delivery fact"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO delivery_facts (
                    delivery_id, order_id, customer_id, driver_id, delivery_date,
                    delivery_hour, day_of_week, is_weekend, is_peak_hour,
                    order_amount, item_count, prep_time_min, delivery_time_min,
                    total_time_min, promised_time_min, is_on_time, delay_minutes,
                    delay_reason, weather_condition, traffic_condition,
                    delivery_zone, delivery_address, route_distance_km, points_earned
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fact.delivery_id, fact.order_id, fact.customer_id, fact.driver_id,
                datetime_to_str(fact.delivery_date), fact.delivery_hour,
                fact.day_of_week, 1 if fact.is_weekend else 0,
                1 if fact.is_peak_hour else 0, fact.order_amount,
                fact.item_count, fact.prep_time_min, fact.delivery_time_min,
                fact.total_time_min, fact.promised_time_min,
                1 if fact.is_on_time else 0, fact.delay_minutes,
                fact.delay_reason, fact.weather_condition, fact.traffic_condition,
                fact.delivery_zone, fact.delivery_address, fact.route_distance_km, fact.points_earned
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving delivery fact: {e}")
            return False
    
    def save_loyalty_transaction(self, tx) -> bool:
        """Save a loyalty transaction"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO loyalty_transactions (
                    transaction_id, customer_id, order_id, points_type,
                    points_amount, points_balance_after, tier_before,
                    tier_after, tier_changed, transaction_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx.transaction_id, tx.customer_id, tx.order_id,
                tx.points_type, tx.points_amount, tx.points_balance_after,
                tx.tier_before, tx.tier_after, 1 if tx.tier_changed else 0,
                datetime_to_str(tx.transaction_date), tx.notes
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving loyalty transaction: {e}")
            return False
    
    def save_customer_state(self, customer) -> bool:
        """Save customer loyalty state"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO customer_state (
                    customer_id, total_orders, total_spent, total_points,
                    loyalty_tier, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer.customer_id, customer.total_orders,
                customer.total_spent, customer.total_points,
                customer.loyalty_tier, datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving customer state: {e}")
            return False
    
    def load_orders(self) -> List[Dict]:
        """Load all orders from the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM orders ORDER BY order_time DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error loading orders: {e}")
            return []
    
    def load_delivery_facts(self) -> List[Dict]:
        """Load all delivery facts"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM delivery_facts ORDER BY delivery_date DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error loading delivery facts: {e}")
            return []
    
    def load_loyalty_transactions(self) -> List[Dict]:
        """Load all loyalty transactions"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM loyalty_transactions ORDER BY transaction_date DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error loading loyalty transactions: {e}")
            return []
    
    def load_customer_states(self) -> Dict[str, Dict]:
        """Load customer states"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM customer_state")
            rows = cursor.fetchall()
            return {row["customer_id"]: dict(row) for row in rows}
        except Exception as e:
            print(f"Error loading customer states: {e}")
            return {}
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            order_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM delivery_facts")
            fact_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM loyalty_transactions")
            tx_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT MIN(order_time) as first, MAX(order_time) as last FROM orders")
            row = cursor.fetchone()
            first_order = row["first"]
            last_order = row["last"]
            
            return {
                "total_orders": order_count,
                "delivery_facts": fact_count,
                "loyalty_transactions": tx_count,
                "first_order": first_order,
                "last_order": last_order,
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def clear_all(self):
        """Clear all data (reset database)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM delivery_facts")
            cursor.execute("DELETE FROM loyalty_transactions")
            cursor.execute("DELETE FROM customer_state")
            cursor.execute("DELETE FROM driver_state")
            self.conn.commit()
            print("🗑️ All persistence data cleared")
            return True
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()


# Singleton instance
_persistence_manager: Optional[PersistenceManager] = None


def get_persistence_manager() -> PersistenceManager:
    """Get the singleton persistence manager"""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = PersistenceManager()
    return _persistence_manager
