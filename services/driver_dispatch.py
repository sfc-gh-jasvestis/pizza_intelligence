"""
Pizza Operations Pipeline - Driver Dispatch Service
Assigns drivers to orders based on availability, conditions, and route optimization
Handles delivery tracking and completion
"""

import time
import threading
import random
import requests
from datetime import datetime
from typing import Optional, Callable, List, Dict, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    STORE_CONFIG, DELIVERY_ZONES, WEATHER_CONDITIONS, 
    TRAFFIC_BY_HOUR, SIMULATION_CONFIG, DRIVERS
)
from services.database import (
    get_database, Order, OrderStatus, DriverStatus, Driver
)

# =============================================================================
# ROUTE OPTIMIZATION
# =============================================================================

class RouteOptimizer:
    """Handles route calculation and optimization based on conditions"""
    
    @staticmethod
    def get_route_coordinates(
        start_lon: float, start_lat: float, 
        end_lon: float, end_lat: float
    ) -> List[List[float]]:
        """
        Fetch driving route from OSRM (Open Source Routing Machine).
        Returns list of [lon, lat] coordinates for the actual road route.
        Falls back to grid-style path if API fails.
        """
        try:
            # OSRM public API - free, no key required
            url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("routes") and len(data["routes"]) > 0:
                    coords = data["routes"][0]["geometry"]["coordinates"]
                    # Sample every few points to reduce data while keeping shape
                    if len(coords) > 30:
                        step = max(1, len(coords) // 30)
                        coords = coords[::step] + [coords[-1]]  # Keep last point
                    return coords
            
            return RouteOptimizer._fallback_route(start_lon, start_lat, end_lon, end_lat)
        except Exception as e:
            return RouteOptimizer._fallback_route(start_lon, start_lat, end_lon, end_lat)
    
    @staticmethod
    def _fallback_route(
        start_lon: float, start_lat: float,
        end_lon: float, end_lat: float
    ) -> List[List[float]]:
        """
        Generate a realistic Chicago grid-style route when API is unavailable.
        Chicago has a grid street system, so routes follow streets in L-shaped
        or zigzag patterns rather than diagonal lines.
        """
        points = []
        
        # Calculate deltas
        delta_lon = end_lon - start_lon
        delta_lat = end_lat - start_lat
        
        # Start point
        points.append([start_lon, start_lat])
        
        # Chicago grid: make clear L-shaped or zigzag turns
        # This creates visible "street following" behavior
        
        # Randomly choose between 2-turn (L-shape) or 3-turn (zigzag) route
        route_style = random.choice(["L_horizontal", "L_vertical", "zigzag"])
        
        if route_style == "L_horizontal":
            # Go horizontal first, then vertical (L-shape)
            # First: move mostly horizontal (along a street)
            points.append([start_lon + delta_lon * 0.9, start_lat + delta_lat * 0.1])
            # Then: move mostly vertical (turn onto cross street)
            points.append([end_lon, end_lat])
            
        elif route_style == "L_vertical":
            # Go vertical first, then horizontal (L-shape)
            # First: move mostly vertical (along a street)
            points.append([start_lon + delta_lon * 0.1, start_lat + delta_lat * 0.9])
            # Then: move mostly horizontal (turn onto cross street)
            points.append([end_lon, end_lat])
            
        else:  # zigzag
            # Create a zigzag pattern with 2 turns
            # First leg: horizontal
            points.append([start_lon + delta_lon * 0.5, start_lat + delta_lat * 0.1])
            # Second leg: diagonal/vertical
            points.append([start_lon + delta_lon * 0.6, start_lat + delta_lat * 0.8])
            # Final leg: to destination
            points.append([end_lon, end_lat])
        
        return points
    
    @staticmethod
    def calculate_delivery_time(
        distance_km: float,
        zone: str,
        weather: str,
        traffic: str,
        driver_efficiency: float = 1.0
    ) -> Tuple[int, bool, Optional[str]]:
        """
        Calculate estimated delivery time based on conditions.
        Returns (estimated_minutes, is_delayed, delay_reason)
        """
        # Base time: 3 min/km + 5 min buffer
        base_time = distance_km * 3 + 5
        
        # Zone risk factor
        zone_info = DELIVERY_ZONES.get(zone, {"avg_delivery_min": 20})
        zone_factor = zone_info.get("avg_delivery_min", 20) / 20
        
        # Weather factor
        weather_info = WEATHER_CONDITIONS.get(weather, {})
        weather_factor = weather_info.get("delivery_multiplier", 1.0)
        
        # Traffic factor
        traffic_factors = {"light": 1.0, "moderate": 1.2, "heavy": 1.4}
        traffic_factor = traffic_factors.get(traffic, 1.2)
        
        # Driver efficiency
        efficiency_factor = 1.0 / driver_efficiency
        
        # Calculate total time
        total_time = base_time * zone_factor * weather_factor * traffic_factor * efficiency_factor
        
        # Determine if delayed and why
        is_delayed = total_time > SIMULATION_CONFIG["promised_delivery_min"]
        delay_reason = None
        
        if is_delayed:
            # Determine primary delay reason with descriptive text
            factors = {
                "traffic": (traffic_factor, f"Heavy traffic"),
                "weather": (weather_factor, f"{weather} conditions"),
                "zone_complexity": (zone_factor, None),
            }
            primary_factor = max(factors.keys(), key=lambda k: factors[k][0])
            delay_reason = factors[primary_factor][1]
            
            if primary_factor == "zone_complexity":
                # Check common issues for the zone
                common_issues = zone_info.get("common_issues", [])
                if common_issues:
                    delay_reason = random.choice(common_issues)
                else:
                    delay_reason = f"Complex route in {zone}"
        
        return int(total_time), is_delayed, delay_reason
    
    @staticmethod
    def get_alternate_route(zone: str) -> Optional[str]:
        """Get alternate route suggestion for a zone"""
        zone_info = DELIVERY_ZONES.get(zone, {})
        return zone_info.get("alternate_route")


# =============================================================================
# DRIVER DISPATCH SERVICE
# =============================================================================

class DriverDispatch:
    """
    Manages driver assignment and delivery tracking.
    Optimizes driver selection based on availability and conditions.
    """
    
    def __init__(self):
        self.db = get_database()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._delivery_threads: Dict[str, threading.Thread] = {}
        self._delivery_callbacks: List[Callable] = []
        self.route_optimizer = RouteOptimizer()
    
    def on_delivery_update(self, callback: Callable):
        """Subscribe to delivery progress updates"""
        self._delivery_callbacks.append(callback)
    
    def _notify_delivery_update(self, order: Order):
        """Notify of delivery progress"""
        for callback in self._delivery_callbacks:
            try:
                callback(order)
            except Exception as e:
                print(f"Error in delivery callback: {e}")
    
    def select_best_driver(self, order: Order) -> Optional[Driver]:
        """
        Select the best available driver for an order.
        Considers: availability, vehicle type, efficiency, current location
        """
        available_drivers = self.db.get_available_drivers()
        
        if not available_drivers:
            return None
        
        # Score each driver
        scored_drivers = []
        zone_info = DELIVERY_ZONES.get(order.delivery_zone, {})
        risk_level = zone_info.get("risk_level", "medium")
        
        for driver in available_drivers:
            score = 100
            
            # Efficiency bonus
            score += driver.efficiency * 20
            
            # Vehicle type considerations
            if risk_level == "high" and driver.vehicle_type == "car":
                score += 10  # Cars better for complex areas
            elif order.route_distance_km < 1.0 and driver.vehicle_type in ["bike", "scooter"]:
                score += 15  # Short distance = bike/scooter better
            
            # Fewer deliveries today = fresher driver
            score -= driver.deliveries_today * 2
            
            scored_drivers.append((driver, score))
        
        # Sort by score and return best
        scored_drivers.sort(key=lambda x: x[1], reverse=True)
        return scored_drivers[0][0]
    
    def assign_driver_to_order(self, order_id: str) -> bool:
        """Assign a driver to an order"""
        order = self.db.get_order(order_id)
        if not order or order.driver_id:
            return False  # Order not found or already assigned
        
        driver = self.select_best_driver(order)
        if not driver:
            print(f"⚠️ No available drivers for order {order_id}")
            return False
        
        # Get route
        route_coords = self.route_optimizer.get_route_coordinates(
            STORE_CONFIG["lon"], STORE_CONFIG["lat"],
            order.delivery_lon, order.delivery_lat
        )
        
        # Calculate delivery estimate
        conditions = self.db.get_conditions()
        est_time, is_delayed, delay_reason = self.route_optimizer.calculate_delivery_time(
            order.route_distance_km,
            order.delivery_zone,
            conditions["weather"],
            order.traffic_condition,
            driver.efficiency
        )
        
        # Update order with driver and route
        self.db.update_order(
            order_id,
            driver_id=driver.driver_id,
            driver_name=driver.name,
            route_coords=route_coords,
            estimated_delivery_min=est_time,
            is_delayed=is_delayed,
            delay_reason=delay_reason,
        )
        
        # Assign driver
        self.db.assign_driver(driver.driver_id, order_id)
        
        # Check for alternate route suggestion (silent)
        alt_route = self.route_optimizer.get_alternate_route(order.delivery_zone)
        
        return True
    
    def start_delivery(self, order_id: str):
        """Start the delivery process for an order"""
        order = self.db.get_order(order_id)
        if not order or not order.driver_id:
            return
        
        # Update status to out for delivery
        self.db.update_order(
            order_id,
            status=OrderStatus.OUT_FOR_DELIVERY,
            dispatch_time=datetime.now(),
            delivery_progress=0
        )
        
        # Get zone-specific traffic info
        zone_info = DELIVERY_ZONES.get(order.delivery_zone, {})
        risk_level = zone_info.get("risk_level", "low")
        alternate_route = zone_info.get("alternate_route")
        
        # Check time of day for traffic awareness
        current_hour = datetime.now().hour
        is_rush_hour = (7 <= current_hour <= 9) or (16 <= current_hour <= 19)
        is_lunch_rush = (11 <= current_hour <= 13)
        
        # Build dispatch message
        print(f"🚗 {order_id} → {order.delivery_zone} ({order.driver_name})")
        
        # Add traffic alert for high-risk zones during busy times
        if risk_level == "high" and (is_rush_hour or is_lunch_rush):
            if alternate_route:
                print(f"   🛣️ Traffic tip: {alternate_route}")
        
        # Start delivery simulation in separate thread
        thread = threading.Thread(
            target=self._simulate_delivery,
            args=(order_id,),
            daemon=True
        )
        self._delivery_threads[order_id] = thread
        thread.start()
    
    def _simulate_delivery(self, order_id: str):
        """Simulate the delivery process with progress updates"""
        order = self.db.get_order(order_id)
        if not order:
            return
        
        speed_mult = SIMULATION_CONFIG["delivery_speed_multiplier"]
        
        # Calculate delivery time in seconds (accelerated)
        delivery_time_sec = (order.estimated_delivery_min * 60) / speed_mult
        
        # Add random variation (±15%)
        delivery_time_sec *= random.uniform(0.85, 1.15)
        
        # Simulate delivery with progress updates
        start_time = time.time()
        
        while True:
            if not self.running:
                break
            
            elapsed = time.time() - start_time
            progress = min(100, int((elapsed / delivery_time_sec) * 100))
            
            # Update progress
            self.db.update_order(order_id, delivery_progress=progress)
            
            # Update driver position along route
            if order.route_coords and len(order.route_coords) > 1:
                route_index = int((progress / 100) * (len(order.route_coords) - 1))
                route_index = min(route_index, len(order.route_coords) - 1)
                pos = order.route_coords[route_index]
                self.db.update_driver_position(order.driver_id, pos[1], pos[0])
            
            # Notify listeners
            updated_order = self.db.get_order(order_id)
            if updated_order:
                self._notify_delivery_update(updated_order)
            
            if progress >= 100:
                break
            
            time.sleep(0.5)
        
        # Complete delivery
        self._complete_delivery(order_id)
    
    def _complete_delivery(self, order_id: str):
        """Mark delivery as complete"""
        order = self.db.get_order(order_id)
        if not order:
            return
        
        # Calculate actual delivery time
        if order.order_time:
            total_time = (datetime.now() - order.order_time).total_seconds() / 60
            # Scale back up from accelerated time
            actual_time = int(total_time * SIMULATION_CONFIG["delivery_speed_multiplier"])
        else:
            actual_time = order.estimated_delivery_min
        
        # Add dramatic variation for demo purposes
        # Mix of outcomes: some early, some just on time, some late
        import random
        
        scenario = random.choices(
            ["early", "on_time", "close_call", "late", "very_late"],
            weights=[20, 25, 20, 25, 10],  # Weighted distribution
            k=1
        )[0]
        
        promised_time = SIMULATION_CONFIG["promised_delivery_min"]
        delay_reason = order.delay_reason
        
        if scenario == "early":
            # Fast delivery - 5-10 min under promised
            actual_time = promised_time - random.randint(5, 12)
            delay_reason = None
        elif scenario == "on_time":
            # Comfortable on-time - 2-5 min under
            actual_time = promised_time - random.randint(2, 5)
            delay_reason = None
        elif scenario == "close_call":
            # Just barely on time - 0-2 min under
            actual_time = promised_time - random.randint(0, 2)
            delay_reason = None
        elif scenario == "late":
            # Late by 3-10 min
            actual_time = promised_time + random.randint(3, 10)
            if not delay_reason:
                # Zone-specific delay reasons
                zone = order.delivery_zone or "Downtown"
                zone_delays = {
                    "West Loop": [
                        "Restaurant row double-parked vehicles",
                        "Randolph St construction detour",
                        "Event traffic near United Center",
                        "Adams St congestion during rush",
                    ],
                    "Gold Coast": [
                        "Doorman verification took extra time",
                        "No street parking - had to circle block",
                        "Private gate code issue",
                        "Lake Shore Dr traffic backup",
                    ],
                    "Magnificent Mile": [
                        "Michigan Ave shopping traffic gridlock",
                        "Wrong hotel entrance - redirected",
                        "Bus lane restrictions slowed route",
                        "Tourist pedestrian congestion",
                    ],
                    "River North": [
                        "Gallery district parking unavailable",
                        "One-way street maze caused delay",
                        "Bar crowd blocking Hubbard St",
                        "Loading zone occupied",
                    ],
                    "Streeterville": [
                        "Hospital area traffic congestion",
                        "Concierge verification delay",
                        "Northwestern campus pedestrians",
                        "Navy Pier tourist traffic",
                    ],
                    "Financial District": [
                        "LaSalle St lunch rush traffic",
                        "Building security checkpoint delay",
                        "Elevator wait in high-rise",
                        "Suite number confusion",
                    ],
                    "Loop Core": [
                        "State St pedestrian congestion",
                        "CTA bus blocking lane",
                        "High-rise elevator queue",
                        "Lobby security verification",
                    ],
                    "Lakeshore East": [
                        "Tower identification confusion",
                        "Park detour required",
                        "Underground parking access delay",
                        "Harbor Dr construction",
                    ],
                }
                delay_reason = random.choice(zone_delays.get(zone, [
                    "Traffic congestion on route",
                    "Building access delay",
                    "Parking difficulty",
                ]))
        else:  # very_late
            # Very late - 12-20 min over
            actual_time = promised_time + random.randint(12, 20)
            if not delay_reason:
                # Zone-specific severe delays
                zone = order.delivery_zone or "Downtown"
                severe_delays = {
                    "West Loop": [
                        "Major backup on I-290 exit ramp",
                        "Halsted St water main break",
                        "Bulls/Blackhawks game traffic",
                    ],
                    "Gold Coast": [
                        "Oak St completely blocked for event",
                        "Multiple building access issues",
                        "Rush St road closure",
                    ],
                    "Magnificent Mile": [
                        "Michigan Ave parade/protest closure",
                        "Severe shopping traffic - took 20 min",
                        "Multiple wrong turns in traffic",
                    ],
                    "River North": [
                        "Art gallery opening blocked streets",
                        "Friday night bar crowd gridlock",
                        "Kinzie St flooding from rain",
                    ],
                    "Streeterville": [
                        "Northwestern Medical emergency traffic",
                        "Navy Pier fireworks crowd",
                        "Illinois St completely blocked",
                    ],
                    "Financial District": [
                        "Board of Trade area gridlocked",
                        "Multiple elevator breakdowns",
                        "Jackson Blvd accident backup",
                    ],
                    "Loop Core": [
                        "CTA service disruption traffic surge",
                        "Multiple street closures downtown",
                        "Washington St water main break",
                    ],
                    "Lakeshore East": [
                        "Columbus Dr completely closed",
                        "Massive park event overflow",
                        "All towers had access issues",
                    ],
                }
                delay_reason = random.choice(severe_delays.get(zone, [
                    "Major traffic incident on route",
                    "Severe weather causing delays",
                    "Multiple delivery complications",
                ]))
        
        # Ensure minimum sensible time
        actual_time = max(15, actual_time)
        
        # Determine if on-time
        is_on_time = actual_time <= promised_time
        
        # Update order with delay reason if late
        self.db.update_order(
            order_id,
            status=OrderStatus.DELIVERED,
            delivery_time=datetime.now(),
            actual_delivery_min=actual_time,
            delivery_progress=100,
            is_delayed=not is_on_time,
            delay_reason=delay_reason if not is_on_time else None,
        )
        
        # Release driver
        if order.driver_id:
            self.db.release_driver(order.driver_id)
        
        # Compact delivery completion message
        status_emoji = "✅" if is_on_time else "⚠️"
        time_info = f"{actual_time} min"
        if not is_on_time and delay_reason:
            print(f"{status_emoji} {order_id} delivered in {time_info} — {delay_reason}")
        else:
            print(f"{status_emoji} {order_id} delivered in {time_info}")
        
        # Clean up thread reference
        if order_id in self._delivery_threads:
            del self._delivery_threads[order_id]
        
        # Final notification
        final_order = self.db.get_order(order_id)
        if final_order:
            self._notify_delivery_update(final_order)
    
    def handle_ready_order(self, order: Order):
        """
        Called when kitchen signals order is nearly ready (80%).
        Pre-assigns driver so they can be ready for pickup.
        Actual delivery start happens when dispatch loop sees READY status.
        """
        order_id = order.order_id
        
        # Pre-assign driver if not already assigned (this is called at 80% done)
        current_order = self.db.get_order(order_id)
        if current_order and not current_order.driver_id:
            self.assign_driver_to_order(order_id)
    
    def _dispatch_loop(self):
        """Main loop - monitors for ready orders without drivers"""
        while self.running:
            try:
                # Get ready orders
                ready_orders = self.db.get_orders_by_status(OrderStatus.READY)
                
                for order in ready_orders:
                    # Assign driver if needed
                    if not order.driver_id:
                        self.assign_driver_to_order(order.order_id)
                    
                    # Start delivery if driver assigned
                    current = self.db.get_order(order.order_id)
                    if current and current.driver_id and current.status == OrderStatus.READY:
                        self.start_delivery(order.order_id)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in dispatch loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the dispatch service"""
        if self.running:
            print("Dispatch already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._thread.start()
        print("🚗 Driver Dispatch Service started")
    
    def stop(self):
        """Stop the dispatch service"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("🛑 Driver Dispatch Service stopped")
    
    def is_alive(self) -> bool:
        """Check if the dispatch service thread is alive and running"""
        return self.running and self._thread is not None and self._thread.is_alive()
    
    def restart_if_dead(self) -> bool:
        """Restart the service if the thread died. Returns True if restarted."""
        if self.running and (self._thread is None or not self._thread.is_alive()):
            print("⚠️ Dispatch thread died, restarting...")
            self._thread = threading.Thread(target=self._dispatch_loop, daemon=True)
            self._thread.start()
            return True
        return False
    
    def get_driver_status(self) -> Dict:
        """Get status of all drivers"""
        drivers = list(self.db.drivers.values())
        available = sum(1 for d in drivers if d.status == DriverStatus.AVAILABLE)
        on_delivery = sum(1 for d in drivers if d.status == DriverStatus.ON_DELIVERY)
        
        return {
            "total": len(drivers),
            "available": available,
            "on_delivery": on_delivery,
            "active_deliveries": len(self._delivery_threads),
        }


# =============================================================================
# STANDALONE USAGE
# =============================================================================

def main():
    """Run the dispatch service standalone"""
    from services.order_simulator import OrderSimulator
    from services.kitchen_service import KitchenService
    
    dispatch = DriverDispatch()
    kitchen = KitchenService()
    simulator = OrderSimulator()
    
    # Connect kitchen to dispatch
    kitchen.on_order_ready(dispatch.handle_ready_order)
    
    print("=" * 60)
    print("PIZZA DRIVER DISPATCH SERVICE")
    print("=" * 60)
    print("\nCommands:")
    print("  o - Generate an order")
    print("  s - Start all services")
    print("  x - Stop all services")
    print("  d - Show driver status")
    print("  r - Quit")
    print("=" * 60)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'o':
                simulator.generate_order()
            elif cmd == 's':
                kitchen.start()
                dispatch.start()
            elif cmd == 'x':
                dispatch.stop()
                kitchen.stop()
            elif cmd == 'd':
                status = dispatch.get_driver_status()
                print(f"Drivers: {status}")
            elif cmd == 'r':
                dispatch.stop()
                kitchen.stop()
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        dispatch.stop()
        kitchen.stop()
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
