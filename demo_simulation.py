#!/usr/bin/env python3
"""
Pizza Demo Simulation - Realistic timing for live demos

Simulates a realistic pizza ordering workflow:
- Kitchen preparation: ~2-3 minutes (10-15 steps)
- Driver assignment: At 80% kitchen progress
- Pickup & departure: ~30 seconds
- Delivery drive: ~2 minutes (8-10 steps)

Total demo time: ~5 minutes for full order lifecycle

Usage:
  python demo_simulation.py              # Run with defaults (5 second intervals)
  python demo_simulation.py --fast       # Fast mode (3 second intervals)
  python demo_simulation.py --reset      # Reset state before starting
"""

import time
import argparse
import sys
from datetime import datetime
from unified_state import run_simulation_step, load_state, reset_state

def clear_line():
    """Clear current line for progress updates."""
    sys.stdout.write('\r' + ' ' * 80 + '\r')
    sys.stdout.flush()

def print_header():
    """Print demo header."""
    print("\n" + "="*65)
    print("   🍕 PIZZA DEMO - Live Order Simulation")
    print("="*65)
    print("\n📱 Open these apps side-by-side to watch the demo:\n")
    print("   Customer App:   http://localhost:8506")
    print("   Ops Dashboard:  http://localhost:8504")
    print("   Driver App:     http://localhost:8505")
    print("\n" + "-"*65)

def get_status_emoji(status):
    """Get emoji for order status."""
    return {
        "pending": "📋",
        "preparing": "👨‍🍳",
        "ready": "✅",
        "picked_up": "📦",
        "on_the_way": "🚗",
        "delivered": "🎉"
    }.get(status, "❓")

def format_progress_bar(progress, width=20):
    """Create a visual progress bar."""
    filled = int(width * progress / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {progress:3d}%"

def print_order_status(state, show_header=True):
    """Print current status of all orders in a nice format."""
    orders = state.get("orders", {})
    drivers = state.get("drivers", {})
    
    if not orders:
        print("\n   ⏳ No active orders - place an order in the Customer App!")
        return False
    
    if show_header:
        print(f"\n   {'Order':<12} {'Status':<12} {'Progress':<28} {'Driver':<20}")
        print("   " + "-"*70)
    
    all_delivered = True
    for order_id, order in orders.items():
        status = order["status"]
        emoji = get_status_emoji(status)
        
        if status != "delivered":
            all_delivered = False
        
        # Build progress string
        if status == "preparing":
            progress = format_progress_bar(order.get("kitchen_progress", 0))
        elif status == "on_the_way":
            progress = format_progress_bar(order.get("delivery_progress", 0))
        elif status == "delivered":
            progress = "Complete!"
        else:
            progress = status.replace("_", " ").title()
        
        # Driver info
        driver_id = order.get("driver_id")
        if driver_id and driver_id in drivers:
            driver_name = drivers[driver_id].get("name", "Unknown")
            driver_str = f"🚗 {driver_name}"
        elif status in ["pending", "preparing"] and order.get("kitchen_progress", 0) < 80:
            driver_str = "(assigning at 80%)"
        else:
            driver_str = "-"
        
        print(f"   {order_id:<12} {emoji} {status:<10} {progress:<28} {driver_str}")
    
    return all_delivered

def run_demo(interval: float = 5.0, max_steps: int = 50):
    """Run the demo simulation with realistic timing."""
    
    print_header()
    print(f"\n🚀 Starting simulation (updates every {interval}s)")
    print("   Press Ctrl+C to stop\n")
    
    step = 0
    last_status_count = 0
    
    try:
        while step < max_steps:
            step += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Run simulation step
            state = run_simulation_step()
            orders = state.get("orders", {})
            
            # Check if we have any orders
            if not orders:
                print(f"\n   [{timestamp}] Waiting for orders... (place one in Customer App)")
                time.sleep(interval)
                continue
            
            # Print status update
            print(f"\n   [{timestamp}] Step {step}")
            all_done = print_order_status(state)
            
            if all_done and orders:
                print("\n" + "="*65)
                print("   🎉 ALL ORDERS DELIVERED!")
                print("   Check the Customer App to rate the delivery.")
                print("="*65 + "\n")
                break
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n   ⏹️  Demo stopped by user\n")

def main():
    parser = argparse.ArgumentParser(
        description="Pizza Demo Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_simulation.py              # Normal speed (5s intervals)
  python demo_simulation.py --fast       # Fast demo (3s intervals)  
  python demo_simulation.py --reset      # Clear all orders first
        """
    )
    parser.add_argument("--fast", action="store_true", 
                       help="Fast mode (3 second intervals)")
    parser.add_argument("--interval", type=float, default=5.0,
                       help="Seconds between updates (default: 5)")
    parser.add_argument("--reset", action="store_true",
                       help="Reset all orders before starting")
    parser.add_argument("--steps", type=int, default=50,
                       help="Max simulation steps (default: 50)")
    
    args = parser.parse_args()
    
    if args.reset:
        print("🗑️  Resetting all orders...")
        reset_state()
        print("   Done!\n")
    
    interval = 3.0 if args.fast else args.interval
    run_demo(interval=interval, max_steps=args.steps)

if __name__ == "__main__":
    main()
