"""
Pizza Operations Pipeline - Kitchen Processing Service
Processes orders through the kitchen workflow: prep → oven → packaging → ready
Triggers driver dispatch when order is nearly ready
"""

import time
import threading
from datetime import datetime
from typing import Optional, Callable, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import MENU_ITEMS, SIMULATION_CONFIG
from services.database import (
    get_database, Order, OrderStatus, KitchenStatus
)

# =============================================================================
# KITCHEN PROCESSOR
# =============================================================================

class KitchenService:
    """
    Processes orders through the kitchen workflow.
    Simulates prep, oven, and packaging stages with progress updates.
    Notifies when order is ready for driver pickup.
    """
    
    def __init__(self):
        self.db = get_database()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._ready_callbacks: List[Callable] = []
        self._progress_callbacks: List[Callable] = []
        
        # Kitchen capacity
        self.max_concurrent_orders = 5
        self.processing_orders: List[str] = []
    
    def on_order_ready(self, callback: Callable):
        """Subscribe to order ready events (for driver dispatch)"""
        self._ready_callbacks.append(callback)
    
    def on_progress_update(self, callback: Callable):
        """Subscribe to kitchen progress updates"""
        self._progress_callbacks.append(callback)
    
    def _notify_ready(self, order: Order):
        """Notify that order is ready for pickup"""
        for callback in self._ready_callbacks:
            try:
                callback(order)
            except Exception as e:
                print(f"Error in ready callback: {e}")
    
    def _notify_progress(self, order: Order):
        """Notify of progress update"""
        for callback in self._progress_callbacks:
            try:
                callback(order)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def get_prep_time(self, order: Order) -> int:
        """Calculate total prep time for an order"""
        max_prep = 0
        for item in order.items:
            item_info = MENU_ITEMS.get(item.item_id, {})
            prep_time = item_info.get("prep_time_min", 10)
            max_prep = max(max_prep, prep_time * item.quantity)
        return max_prep
    
    def process_order(self, order_id: str):
        """Process a single order through the kitchen"""
        order = self.db.get_order(order_id)
        if not order:
            return
        
        speed_mult = SIMULATION_CONFIG["kitchen_speed_multiplier"]
        prep_time = self.get_prep_time(order)
        
        # Total time in seconds (accelerated for demo)
        total_time_sec = (prep_time * 60) / speed_mult
        
        # Kitchen stages with their proportions
        stages = [
            (KitchenStatus.PREP, 0.3),        # 30% - prep work
            (KitchenStatus.OVEN, 0.5),        # 50% - in oven
            (KitchenStatus.PACKAGING, 0.2),   # 20% - packaging
        ]
        
        print(f"🍕 Kitchen: Starting order {order_id} (prep time: {prep_time} min)")
        
        # Update to preparing status
        self.db.update_order(
            order_id,
            status=OrderStatus.PREPARING,
            kitchen_start_time=datetime.now(),
            kitchen_status=KitchenStatus.PREP,
            kitchen_progress=0
        )
        
        # Process through stages
        progress = 0
        for stage, proportion in stages:
            stage_time = total_time_sec * proportion
            stage_steps = int(stage_time / 0.5)  # Update every 0.5 sec
            
            # Update kitchen status
            self.db.update_order(order_id, kitchen_status=stage)
            
            stage_icon = {
                KitchenStatus.PREP: "🔪",
                KitchenStatus.OVEN: "🔥",
                KitchenStatus.PACKAGING: "📦",
            }.get(stage, "🍕")
            
            print(f"  {stage_icon} {order_id}: {stage.value}")
            
            for i in range(max(1, stage_steps)):
                if not self.running:
                    return
                
                progress = min(100, progress + (100 * proportion / max(1, stage_steps)))
                
                self.db.update_order(order_id, kitchen_progress=int(progress))
                
                # Get updated order for callback
                updated_order = self.db.get_order(order_id)
                if updated_order:
                    self._notify_progress(updated_order)
                
                # Trigger driver dispatch when ~80% done
                if progress >= 80 and stage == KitchenStatus.OVEN:
                    print(f"  📢 {order_id}: Notifying driver dispatch (80% ready)")
                    if updated_order:
                        self._notify_ready(updated_order)
                
                time.sleep(0.5)
        
        # Mark as ready
        self.db.update_order(
            order_id,
            status=OrderStatus.READY,
            kitchen_status=KitchenStatus.COMPLETED,
            kitchen_progress=100,
            ready_time=datetime.now()
        )
        
        print(f"✅ Kitchen: Order {order_id} READY for pickup")
        
        # Final notification
        final_order = self.db.get_order(order_id)
        if final_order:
            self._notify_progress(final_order)
    
    def _processing_loop(self):
        """Main processing loop - picks up new orders and processes them"""
        while self.running:
            try:
                # Get orders waiting to be processed (received or confirmed)
                waiting_orders = self.db.get_orders_by_status(OrderStatus.RECEIVED)
                waiting_orders += self.db.get_orders_by_status(OrderStatus.CONFIRMED)
                
                # Sort by order time (FIFO)
                waiting_orders.sort(key=lambda o: o.order_time)
                
                # Process orders up to capacity
                for order in waiting_orders:
                    if len(self.processing_orders) >= self.max_concurrent_orders:
                        break
                    
                    if order.order_id not in self.processing_orders:
                        self.processing_orders.append(order.order_id)
                        
                        # Process in a separate thread
                        thread = threading.Thread(
                            target=self._process_and_cleanup,
                            args=(order.order_id,),
                            daemon=True
                        )
                        thread.start()
                
                time.sleep(1)  # Check for new orders every second
                
            except Exception as e:
                print(f"Error in kitchen loop: {e}")
                time.sleep(1)
    
    def _process_and_cleanup(self, order_id: str):
        """Process order and remove from processing list when done"""
        try:
            self.process_order(order_id)
        finally:
            if order_id in self.processing_orders:
                self.processing_orders.remove(order_id)
    
    def start(self):
        """Start the kitchen service"""
        if self.running:
            print("Kitchen already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._thread.start()
        print(f"👨‍🍳 Kitchen Service started (capacity: {self.max_concurrent_orders} orders)")
    
    def stop(self):
        """Stop the kitchen service"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("🛑 Kitchen Service stopped")
    
    def is_alive(self) -> bool:
        """Check if the kitchen service thread is alive and running"""
        return self.running and self._thread is not None and self._thread.is_alive()
    
    def restart_if_dead(self) -> bool:
        """Restart the service if the thread died. Returns True if restarted."""
        if self.running and (self._thread is None or not self._thread.is_alive()):
            print("⚠️ Kitchen thread died, restarting...")
            self._thread = threading.Thread(target=self._processing_loop, daemon=True)
            self._thread.start()
            return True
        return False
    
    def get_queue_status(self) -> dict:
        """Get current kitchen queue status"""
        waiting = len(self.db.get_orders_by_status(OrderStatus.RECEIVED))
        waiting += len(self.db.get_orders_by_status(OrderStatus.CONFIRMED))
        preparing = len(self.db.get_orders_by_status(OrderStatus.PREPARING))
        ready = len(self.db.get_orders_by_status(OrderStatus.READY))
        
        return {
            "waiting": waiting,
            "preparing": preparing,
            "ready": ready,
            "processing": len(self.processing_orders),
            "capacity": self.max_concurrent_orders,
        }


# =============================================================================
# STANDALONE USAGE
# =============================================================================

def main():
    """Run the kitchen service standalone"""
    from services.order_simulator import OrderSimulator
    
    kitchen = KitchenService()
    simulator = OrderSimulator()
    
    # Connect kitchen ready notification
    def on_ready(order):
        print(f"  🔔 CALLBACK: Order {order.order_id} ready for driver!")
    
    kitchen.on_order_ready(on_ready)
    
    print("=" * 60)
    print("PIZZA KITCHEN SERVICE")
    print("=" * 60)
    print("\nCommands:")
    print("  o - Generate an order")
    print("  s - Start kitchen")
    print("  x - Stop kitchen")
    print("  q - Show queue status")
    print("  r - Quit")
    print("=" * 60)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'o':
                simulator.generate_order()
            elif cmd == 's':
                kitchen.start()
            elif cmd == 'x':
                kitchen.stop()
            elif cmd == 'q':
                status = kitchen.get_queue_status()
                print(f"Queue: {status}")
            elif cmd == 'r':
                kitchen.stop()
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        kitchen.stop()
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
