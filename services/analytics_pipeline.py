"""
Pizza Operations Pipeline - Analytics Pipeline
Processes completed deliveries into OLAP facts and calculates loyalty points
Simulates the OLTP → OLAP data flow
"""

import time
import threading
import uuid
from datetime import datetime
from typing import Optional, Callable, List, Dict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    LOYALTY_POINTS, LOYALTY_TIERS, SIMULATION_CONFIG
)
from services.database import (
    get_database, Order, OrderStatus, DeliveryFact, LoyaltyTransaction
)

# =============================================================================
# LOYALTY CALCULATOR
# =============================================================================

class LoyaltyCalculator:
    """Calculates loyalty points and tier updates for customers"""
    
    @staticmethod
    def calculate_points(order: Order, delivery_fact: DeliveryFact) -> Dict:
        """
        Calculate loyalty points earned for a delivery.
        Returns dict with points breakdown and new tier.
        """
        points_earned = {}
        total_points = 0
        
        # Base points for completing order
        base_points = LOYALTY_POINTS["order_complete"]
        points_earned["order_complete"] = base_points
        total_points += base_points
        
        # Bonus for on-time delivery
        if delivery_fact.is_on_time:
            on_time_bonus = LOYALTY_POINTS["on_time_bonus"]
            points_earned["on_time_bonus"] = on_time_bonus
            total_points += on_time_bonus
        
        # Patience bonus for weather delays
        if delivery_fact.weather_condition in ["Rainy", "Snowy", "Stormy"]:
            weather_bonus = LOYALTY_POINTS["weather_patience"]
            points_earned["weather_patience"] = weather_bonus
            total_points += weather_bonus
        
        # Review bonus (random chance for demo)
        import random
        if random.random() < 0.3:  # 30% chance of review
            review_bonus = LOYALTY_POINTS["review_bonus"]
            points_earned["review_bonus"] = review_bonus
            total_points += review_bonus
        
        return {
            "breakdown": points_earned,
            "total": total_points
        }
    
    @staticmethod
    def determine_tier(total_points: int) -> str:
        """Determine loyalty tier based on total points"""
        current_tier = "Bronze"
        
        for tier, info in LOYALTY_TIERS.items():
            if total_points >= info["min_points"]:
                current_tier = tier
        
        return current_tier
    
    @staticmethod
    def get_tier_benefits(tier: str) -> Dict:
        """Get benefits for a loyalty tier"""
        return LOYALTY_TIERS.get(tier, LOYALTY_TIERS["Bronze"])


# =============================================================================
# ANALYTICS PIPELINE
# =============================================================================

class AnalyticsPipeline:
    """
    Processes completed deliveries into OLAP facts.
    Calculates loyalty points and updates customer tiers.
    Simulates CDC (Change Data Capture) from OLTP to OLAP.
    """
    
    def __init__(self):
        self.db = get_database()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._processed_orders: set = set()
        self._analytics_callbacks: List[Callable] = []
        self.loyalty_calc = LoyaltyCalculator()
        
        # Subscribe to database reset events
        self.db.subscribe("database_reset", self._on_database_reset)
    
    def _on_database_reset(self, data):
        """Clear processed orders when database is reset"""
        self._processed_orders.clear()
    
    def on_analytics_update(self, callback: Callable):
        """Subscribe to analytics updates"""
        self._analytics_callbacks.append(callback)
    
    def _notify_analytics(self, data: Dict):
        """Notify listeners of analytics update"""
        for callback in self._analytics_callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in analytics callback: {e}")
    
    def process_delivery(self, order: Order) -> Optional[DeliveryFact]:
        """
        Process a completed delivery into OLAP fact table.
        Creates delivery fact record and updates customer loyalty.
        """
        if order.order_id in self._processed_orders:
            return None
        
        if order.status != OrderStatus.DELIVERED:
            return None
        
        # Create delivery fact
        delivery_date = order.delivery_time or datetime.now()
        day_of_week = delivery_date.strftime("%A")
        hour = delivery_date.hour
        
        # Calculate times (scale back from accelerated simulation)
        speed_mult = SIMULATION_CONFIG["delivery_speed_multiplier"]
        
        prep_time = 0
        if order.kitchen_start_time and order.ready_time:
            prep_time_raw = (order.ready_time - order.kitchen_start_time).total_seconds() / 60
            prep_time = int(prep_time_raw * speed_mult)  # Scale back to real time
        
        delivery_time = 0
        if order.dispatch_time and order.delivery_time:
            delivery_time_raw = (order.delivery_time - order.dispatch_time).total_seconds() / 60
            delivery_time = int(delivery_time_raw * speed_mult)  # Scale back to real time
        
        # Use actual_delivery_min if set, otherwise calculate
        if order.actual_delivery_min and order.actual_delivery_min < 120:  # Sanity check
            total_time = order.actual_delivery_min
        else:
            total_time = prep_time + delivery_time
            # Ensure reasonable bounds (10-60 min typical)
            total_time = max(15, min(60, total_time))
        
        is_on_time = total_time <= SIMULATION_CONFIG["promised_delivery_min"]
        
        # Determine delay reason if late
        delay_reason = order.delay_reason
        if not is_on_time and not delay_reason:
            # Infer delay reason from conditions
            weather = order.weather_condition or "Clear"
            traffic = order.traffic_condition or "moderate"
            
            # Check weather impact
            weather_delays = {
                "Rainy": "Rain slowed delivery",
                "Snowy": "Snow conditions",
                "Heavy Rain": "Heavy rain delay",
            }
            traffic_delays = {
                "heavy": "Heavy traffic",
                "congested": "Traffic congestion",
            }
            
            if weather in weather_delays:
                delay_reason = weather_delays[weather]
            elif traffic in traffic_delays:
                delay_reason = traffic_delays[traffic]
            elif order.route_distance_km > 2.0:
                delay_reason = "Long distance"
            elif delivery_time > prep_time:
                delay_reason = f"{traffic.title()} traffic"
            else:
                delay_reason = "Kitchen backup"
        
        # Create fact record
        fact = DeliveryFact(
            delivery_id=f"DEL-{uuid.uuid4().hex[:8].upper()}",
            order_id=order.order_id,
            customer_id=order.customer_id,
            driver_id=order.driver_id or "",
            delivery_date=delivery_date,
            delivery_hour=hour,
            day_of_week=day_of_week,
            is_weekend=day_of_week in ["Saturday", "Sunday"],
            is_peak_hour=hour in [12, 13, 17, 18, 19, 20],
            order_amount=order.total_amount,
            item_count=order.item_count,
            prep_time_min=prep_time,
            delivery_time_min=delivery_time,
            total_time_min=total_time,
            promised_time_min=SIMULATION_CONFIG["promised_delivery_min"],
            is_on_time=is_on_time,
            delay_minutes=max(0, total_time - SIMULATION_CONFIG["promised_delivery_min"]),
            delay_reason=delay_reason,  # Use the inferred delay reason
            weather_condition=order.weather_condition,
            traffic_condition=order.traffic_condition,
            delivery_zone=order.delivery_zone,
            delivery_address=order.delivery_address or "",  # Include street address
            route_distance_km=order.route_distance_km,
        )
        
        # Calculate loyalty points
        points_result = self.loyalty_calc.calculate_points(order, fact)
        fact.points_earned = points_result["total"]
        
        # Record fact
        self.db.record_delivery(fact)
        
        # Update customer loyalty
        self._update_customer_loyalty(order, fact, points_result)
        
        # Mark as processed
        self._processed_orders.add(order.order_id)
        
        on_time_emoji = "✅" if is_on_time else "⚠️"
        print(f"📊 Analytics: {order.order_id} | {on_time_emoji} | Points: +{fact.points_earned}")
        
        # Notify listeners
        self._notify_analytics({
            "type": "delivery_processed",
            "fact": fact,
            "points": points_result,
        })
        
        return fact
    
    def _update_customer_loyalty(self, order: Order, fact: DeliveryFact, points_result: Dict):
        """Update customer loyalty points and tier"""
        customer = self.db.get_customer(order.customer_id)
        if not customer:
            return
        
        # Get current state
        old_points = customer.total_points
        old_tier = customer.loyalty_tier
        
        # Calculate new state
        new_points = old_points + points_result["total"]
        new_tier = self.loyalty_calc.determine_tier(new_points)
        tier_changed = new_tier != old_tier
        
        # Update customer
        self.db.update_customer_loyalty(order.customer_id, points_result["total"], new_tier)
        
        # Record loyalty transaction
        for points_type, amount in points_result["breakdown"].items():
            transaction = LoyaltyTransaction(
                transaction_id=f"LYL-{uuid.uuid4().hex[:8].upper()}",
                customer_id=order.customer_id,
                order_id=order.order_id,
                points_type=points_type,
                points_amount=amount,
                points_balance_after=new_points,
                tier_before=old_tier,
                tier_after=new_tier,
                tier_changed=tier_changed and points_type == list(points_result["breakdown"].keys())[-1],
            )
            self.db.record_loyalty_transaction(transaction)
        
        # Log tier change
        if tier_changed:
            print(f"  🎉 {customer.name} upgraded: {old_tier} → {new_tier}!")
            self._notify_analytics({
                "type": "tier_change",
                "customer_id": order.customer_id,
                "customer_name": customer.name,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "total_points": new_points,
            })
    
    def _processing_loop(self):
        """Main loop - processes completed deliveries"""
        while self.running:
            try:
                # Get delivered orders
                delivered_orders = self.db.get_orders_by_status(OrderStatus.DELIVERED)
                
                for order in delivered_orders:
                    if order.order_id not in self._processed_orders:
                        self.process_delivery(order)
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Error in analytics loop: {e}")
                time.sleep(2)
    
    def start(self):
        """Start the analytics pipeline"""
        if self.running:
            print("Analytics already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._thread.start()
        print("📊 Analytics Pipeline started")
    
    def stop(self):
        """Stop the analytics pipeline"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("🛑 Analytics Pipeline stopped")
    
    def is_alive(self) -> bool:
        """Check if the analytics pipeline thread is alive and running"""
        return self.running and self._thread is not None and self._thread.is_alive()
    
    def restart_if_dead(self) -> bool:
        """Restart the pipeline if the thread died. Returns True if restarted."""
        if self.running and (self._thread is None or not self._thread.is_alive()):
            print("⚠️ Analytics thread died, restarting...")
            self._thread = threading.Thread(target=self._processing_loop, daemon=True)
            self._thread.start()
            return True
        return False
    
    def get_summary(self) -> Dict:
        """Get analytics summary"""
        stats = self.db.get_delivery_stats()
        zone_stats = self.db.get_zone_stats()
        
        # Get customer tier distribution
        tier_counts = {"Bronze": 0, "Silver": 0, "Gold": 0, "Platinum": 0}
        for customer in self.db.customers.values():
            tier = customer.loyalty_tier
            if tier in tier_counts:
                tier_counts[tier] += 1
        
        return {
            "delivery_stats": stats,
            "zone_stats": zone_stats,
            "tier_distribution": tier_counts,
            "processed_orders": len(self._processed_orders),
        }
    
    def get_loyalty_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top customers by loyalty points"""
        customers = list(self.db.customers.values())
        customers.sort(key=lambda c: c.total_points, reverse=True)
        
        leaderboard = []
        for i, customer in enumerate(customers[:limit]):
            if customer.total_points > 0:
                leaderboard.append({
                    "rank": i + 1,
                    "name": customer.name,
                    "points": customer.total_points,
                    "tier": customer.loyalty_tier,
                    "orders": customer.total_orders,
                })
        
        return leaderboard


# =============================================================================
# STANDALONE USAGE
# =============================================================================

def main():
    """Run the full pipeline standalone"""
    from services.order_simulator import OrderSimulator
    from services.kitchen_service import KitchenService
    from services.driver_dispatch import DriverDispatch
    
    # Initialize all services
    db = get_database()
    simulator = OrderSimulator()
    kitchen = KitchenService()
    dispatch = DriverDispatch()
    analytics = AnalyticsPipeline()
    
    # Wire up the pipeline
    kitchen.on_order_ready(dispatch.handle_ready_order)
    
    print("=" * 60)
    print("PIZZA OPERATIONS - FULL PIPELINE")
    print("=" * 60)
    print("\nCommands:")
    print("  o - Generate single order")
    print("  b - Generate burst (5 orders)")
    print("  s - Start all services")
    print("  x - Stop all services")
    print("  a - Show analytics summary")
    print("  l - Show loyalty leaderboard")
    print("  r - Reset database")
    print("  q - Quit")
    print("=" * 60)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'o':
                simulator.generate_order()
            elif cmd == 'b':
                simulator.generate_burst()
            elif cmd == 's':
                kitchen.start()
                dispatch.start()
                analytics.start()
                print("\n✅ All services started!")
            elif cmd == 'x':
                analytics.stop()
                dispatch.stop()
                kitchen.stop()
                print("\n🛑 All services stopped!")
            elif cmd == 'a':
                summary = analytics.get_summary()
                print(f"\n📊 Analytics Summary:")
                print(f"   Deliveries: {summary['delivery_stats']}")
                print(f"   Processed: {summary['processed_orders']}")
                print(f"   Tiers: {summary['tier_distribution']}")
            elif cmd == 'l':
                leaderboard = analytics.get_loyalty_leaderboard()
                print(f"\n🏆 Loyalty Leaderboard:")
                for entry in leaderboard:
                    print(f"   #{entry['rank']} {entry['name']} - {entry['points']} pts ({entry['tier']})")
            elif cmd == 'r':
                db.reset()
                analytics._processed_orders.clear()
                print("🔄 Database reset!")
            elif cmd == 'q':
                analytics.stop()
                dispatch.stop()
                kitchen.stop()
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        analytics.stop()
        dispatch.stop()
        kitchen.stop()
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
