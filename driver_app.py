"""
Pizza Driver App - Delivery execution interface for drivers.
Part of the Pizza Ops Demo ecosystem powered by Snowflake.
"""

import streamlit as st
import pydeck as pdk
import time
from datetime import datetime
import random
import requests

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

from unified_state import (
    load_state, get_driver_orders, get_driver_info, get_order,
    driver_pickup, start_delivery, advance_delivery, run_simulation_step, STORE_LAT, STORE_LON
)
from menu_data import STORE_NAME, DRIVERS

try:
    from shared_routes import get_route_from_osrm, get_driver_position_on_route
    ROUTES_AVAILABLE = True
except ImportError:
    ROUTES_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Pizza Driver",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 3 seconds to pick up state changes
if AUTOREFRESH_AVAILABLE:
    st_autorefresh(interval=3000, limit=None, key="driver_autorefresh")

# Run simulation step on each refresh to advance orders
run_simulation_step()

# Custom CSS for mobile-friendly driver interface
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .driver-header {
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
        padding: 15px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .order-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        color: #333333;
    }
    .status-btn {
        padding: 15px 30px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 12px;
        width: 100%;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 15px;
        color: white;
        text-align: center;
    }
    .item-list {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        color: #333333;
    }
    .big-text {
        font-size: 28px;
        font-weight: bold;
    }
    .eta-badge {
        background: #28a745;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Store location (Chicago Loop Pizza)
# Store location imported from menu_data

# Chicago Loop Traffic Hotspots - areas drivers should avoid
TRAFFIC_HOTSPOTS = {
    "always": [
        {"name": "I-90/94 Junction", "lat": 41.8756, "lon": -87.6244, "radius": 350, "reason": "Highway interchange"},
        {"name": "Michigan & Wacker", "lat": 41.8870, "lon": -87.6245, "radius": 250, "reason": "Tourist congestion"},
    ],
    "rush_hour": [
        {"name": "Lake Shore Dr & Ohio", "lat": 41.8920, "lon": -87.6130, "radius": 300, "reason": "Commuter backup"},
        {"name": "Congress Pkwy", "lat": 41.8754, "lon": -87.6290, "radius": 280, "reason": "Highway merge"},
        {"name": "Chicago & State", "lat": 41.8967, "lon": -87.6280, "radius": 200, "reason": "Transit hub"},
        {"name": "Clark & Division", "lat": 41.9040, "lon": -87.6315, "radius": 220, "reason": "Nightlife district"},
    ],
    "lunch": [
        {"name": "Randolph & Michigan", "lat": 41.8846, "lon": -87.6246, "radius": 200, "reason": "Millennium Park lunch rush"},
        {"name": "Adams & Wacker", "lat": 41.8792, "lon": -87.6370, "radius": 180, "reason": "Willis Tower lunch crowd"},
        {"name": "Hubbard & Clark", "lat": 41.8898, "lon": -87.6310, "radius": 180, "reason": "River North restaurants"},
    ],
    "weekend": [
        {"name": "Navy Pier area", "lat": 41.8917, "lon": -87.6059, "radius": 400, "reason": "Tourist attraction"},
        {"name": "Magnificent Mile", "lat": 41.8950, "lon": -87.6245, "radius": 300, "reason": "Shopping traffic"},
    ],
}

# Zone-specific delivery tips
DELIVERY_ZONES = {
    "Gold Coast": {"risk_level": "high", "alternate_route": "Use Lake Shore Dr → Oak St exit"},
    "Magnificent Mile": {"risk_level": "high", "alternate_route": "Use State St → Chicago Ave → Rush St"},
    "West Loop": {"risk_level": "high", "alternate_route": "Use Adams St → Halsted St"},
    "River North": {"risk_level": "high", "alternate_route": "Park on Hubbard St, walk 1 block"},
    "Loop": {"risk_level": "medium", "alternate_route": "Avoid Michigan Ave during rush hour"},
    "Streeterville": {"risk_level": "medium", "alternate_route": "Use Illinois St instead of Grand Ave"},
}


def get_active_traffic_hotspots():
    """Get currently active traffic hotspots based on time of day."""
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    
    active = list(TRAFFIC_HOTSPOTS["always"])
    
    if 7 <= hour <= 9 or 16 <= hour <= 19:
        active.extend(TRAFFIC_HOTSPOTS["rush_hour"])
    
    if 11 <= hour <= 14:
        active.extend(TRAFFIC_HOTSPOTS["lunch"])
    
    if weekday >= 5:  # Saturday or Sunday
        active.extend(TRAFFIC_HOTSPOTS["weekend"])
    
    return active


# Initialize session state
if "driver_id" not in st.session_state:
    st.session_state.driver_id = None
if "simulation_active" not in st.session_state:
    st.session_state.simulation_active = False
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0


def simulate_driver_movement(order):
    """Simulate driver moving towards customer."""
    if order["status"] == "on_the_way":
        current_lat = order.get("driver_lat", STORE_LAT)
        current_lon = order.get("driver_lon", STORE_LON)
        target_lat = order["lat"]
        target_lon = order["lon"]
        
        # Move 10% closer each update
        new_lat = current_lat + (target_lat - current_lat) * 0.15
        new_lon = current_lon + (target_lon - current_lon) * 0.15
        
        # Calculate ETA based on distance
        distance = ((target_lat - new_lat)**2 + (target_lon - new_lon)**2) ** 0.5
        eta = max(1, int(distance * 500))  # Rough ETA calculation
        
        update_driver_location(order["order_id"], new_lat, new_lon, eta)
        return new_lat, new_lon, eta
    return order.get("driver_lat"), order.get("driver_lon"), order.get("eta_minutes")


@st.cache_data(ttl=300)
def get_cached_route(start_lon, start_lat, end_lon, end_lat):
    """Get actual road route - cached version."""
    if ROUTES_AVAILABLE:
        coords, duration, distance = get_route_from_osrm(start_lon, start_lat, end_lon, end_lat)
        return coords, duration, distance
    return [[start_lon, start_lat], [end_lon, end_lat]], 0, 0


def render_order_map(order):
    """Render map showing route from driver to customer with traffic conditions."""
    driver_lat = order.get("driver_lat", STORE_LAT)
    driver_lon = order.get("driver_lon", STORE_LON)
    customer_lat = order["lat"]
    customer_lon = order["lon"]
    order_zone = order.get("zone", "Loop")
    
    # Center map between driver and customer
    center_lat = (driver_lat + customer_lat) / 2
    center_lon = (driver_lon + customer_lon) / 2
    
    # Use route from unified state if available, else fetch from OSRM
    route_coords = order.get("route_coords")
    if not route_coords:
        route_result = get_cached_route(STORE_LON, STORE_LAT, customer_lon, customer_lat)
        route_coords = route_result[0] if isinstance(route_result, tuple) else route_result
    
    # Get active traffic hotspots
    active_hotspots = get_active_traffic_hotspots()
    
    # Build traffic zones data with colors
    traffic_zones = []
    for hotspot in active_hotspots:
        if hotspot in TRAFFIC_HOTSPOTS["always"]:
            color = [244, 67, 54, 100]  # Red
        else:
            color = [255, 193, 7, 80]   # Yellow
        
        traffic_zones.append({
            "name": hotspot["name"],
            "lat": hotspot["lat"],
            "lon": hotspot["lon"],
            "radius": hotspot["radius"],
            "color": color,
            "reason": hotspot["reason"],
        })
    
    layers = []
    
    # Traffic zones layer (render first, behind other elements)
    if traffic_zones:
        traffic_layer = pdk.Layer(
            "ScatterplotLayer",
            data=traffic_zones,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            pickable=True,
            opacity=0.3,
        )
        layers.append(traffic_layer)
    
    # Route line following actual roads
    route_color = [76, 175, 80, 200]  # Green for normal
    
    # Check if route passes through traffic zones
    route_has_traffic = False
    for coord in route_coords[::max(1, len(route_coords)//10)]:
        for hotspot in active_hotspots:
            dlat = (coord[1] - hotspot["lat"]) * 111
            dlon = (coord[0] - hotspot["lon"]) * 85
            dist_km = (dlat**2 + dlon**2) ** 0.5
            if dist_km < 0.3:
                route_has_traffic = True
                route_color = [255, 152, 0, 200]  # Orange for traffic
                break
        if route_has_traffic:
            break
    
    route_layer = pdk.Layer(
        "PathLayer",
        data=[{
            "path": route_coords,
            "color": route_color,
            "name": f"Route to {order.get('customer_name', 'Customer')}",
            "reason": f"Order {order['order_id']}",
        }],
        get_path="path",
        get_color="color",
        get_width=5,
        width_min_pixels=4,
        pickable=True,
    )
    layers.append(route_layer)
    
    # Store marker (orange)
    store_data = [{
        "name": "Chicago Loop Pizza",
        "reason": "Store Location",
        "lat": STORE_LAT,
        "lon": STORE_LON,
        "color": [255, 87, 51, 255],
        "size": 100,
    }]
    store_layer = pdk.Layer(
        "ScatterplotLayer",
        data=store_data,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="size",
        pickable=True,
    )
    layers.append(store_layer)
    
    # Customer marker (blue)
    customer_data = [{
        "name": order.get("customer_name", "Customer"),
        "reason": order.get("address", "Delivery destination"),
        "lat": customer_lat,
        "lon": customer_lon,
        "color": [33, 150, 243, 255],
        "size": 80,
    }]
    customer_layer = pdk.Layer(
        "ScatterplotLayer",
        data=customer_data,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="size",
        pickable=True,
    )
    layers.append(customer_layer)
    
    # Driver marker (green - current position)
    if order["status"] in ["on_the_way", "picked_up"]:
        driver_data = [{
            "name": "You",
            "reason": f"Delivering {order['order_id']}",
            "lat": driver_lat,
            "lon": driver_lon,
            "color": [52, 199, 89, 255],
            "size": 90,
        }]
        driver_layer = pdk.Layer(
            "ScatterplotLayer",
            data=driver_data,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="size",
            pickable=True,
        )
        layers.append(driver_layer)
    
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=13,
        pitch=45,
        bearing=0,
    )
    
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={
            "html": "<b>{name}</b><br/>{reason}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        },
        height=400,
    )
    
    st.pydeck_chart(deck, use_container_width=True, height=400)
    
    # Legend
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 12px; margin-top: 8px; color: #aaa;">
        <span>🟠 Store</span>
        <span>🔵 Customer</span>
        <span>🟢 You</span>
        <span style="color: #f44336;">● Traffic Zone</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Traffic alert if route affected
    if route_has_traffic:
        zone_info = DELIVERY_ZONES.get(order_zone, {})
        alt_route = zone_info.get("alternate_route", "Consider side streets")
        st.warning(f"⚠️ **Traffic Alert:** Route passes through congestion. {alt_route}")


def render_order_card(order, driver_info):
    """Render the current order details."""
    status = order["status"]
    
    # Status colors and labels
    status_config = {
        "preparing": ("🍕", "Preparing", "#FFC107"),
        "ready": ("✅", "Ready for Pickup", "#28A745"),
        "picked_up": ("📦", "Picked Up", "#17A2B8"),
        "on_the_way": ("🚗", "On The Way", "#007BFF"),
    }
    
    icon, label, color = status_config.get(status, ("📋", status.title(), "#6c757d"))
    
    st.markdown(f"""
    <div class="order-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <span style="font-size: 24px; font-weight: bold;">{order['order_id']}</span>
            <span style="background: {color}; color: white; padding: 6px 14px; border-radius: 20px; font-weight: 600;">
                {icon} {label}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Customer info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 📍 {order['customer_name']}")
        st.markdown(f"**{order['address']}**")
        st.caption(f"Zone: {order['zone']}")
    with col2:
        if order.get("eta_minutes"):
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 32px; font-weight: bold; color: #28a745;">{order['eta_minutes']}</div>
                <div style="color: #666;">min ETA</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Items
    st.markdown("#### 📦 Order Items")
    items_html = "<div class='item-list'>"
    for item in order["items"]:
        items_html += f"<div style='padding: 4px 0;'>• {item}</div>"
    items_html += "</div>"
    st.markdown(items_html, unsafe_allow_html=True)
    
    # Special instructions
    if order.get("special_instructions"):
        st.warning(f"📝 **Special Instructions:** {order['special_instructions']}")
    
    # Order total
    st.markdown(f"### 💰 Total: ${order['total']:.2f}")
    
    st.divider()
    
    # Action buttons based on status
    if status == "preparing":
        kitchen_progress = order.get("kitchen_progress", 0)
        st.info(f"⏳ Order is being prepared... {kitchen_progress}% complete")
        st.progress(kitchen_progress / 100)
    
    elif status == "ready":
        st.success("✅ Order is ready! Head to the store to pick it up.")
        if st.button("📦 PICKED UP", use_container_width=True, type="primary"):
            driver_pickup(order["order_id"])
            st.toast("Order picked up! Start your delivery.", icon="📦")
            st.rerun()
    
    elif status == "picked_up":
        st.info("📦 You have the order. Start driving to the customer!")
        if st.button("🚗 START DELIVERY", use_container_width=True, type="primary"):
            start_delivery(order["order_id"])
            st.toast("Delivery started! Drive safely.", icon="🚗")
            st.rerun()
    
    elif status == "on_the_way":
        delivery_progress = order.get("delivery_progress", 0)
        st.info(f"🚗 Delivery in progress... {delivery_progress}% of the way")
        st.progress(delivery_progress / 100)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📞 Call Customer", use_container_width=True):
                st.info(f"Calling {order['customer_name']} at {order['customer_phone']}...")
        with col2:
            if st.button("⚠️ Report Issue", use_container_width=True):
                st.warning("Issue reported to dispatch.")


def render_driver_stats(driver_info, driver_id):
    """Render driver statistics."""
    state = load_state()
    driver_data = state["drivers"].get(driver_id, {})
    
    # Get delivery history for this driver
    delivery_history = driver_data.get("delivery_history", [])
    deliveries_today = driver_data.get('deliveries_today', 0) + len(delivery_history)
    tips_today = driver_data.get('tips_today', 0) or 0
    for delivery in delivery_history:
        tip = delivery.get("tip") or 0
        tips_today += tip
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; font-weight: bold;">{deliveries_today}</div>
            <div style="font-size: 12px; opacity: 0.9;">Deliveries Today</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; font-weight: bold;">${tips_today:.2f}</div>
            <div style="font-size: 12px; opacity: 0.9;">Tips Earned</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; font-weight: bold;">⭐ {driver_data.get('rating', 4.8)}</div>
            <div style="font-size: 12px; opacity: 0.9;">Rating</div>
        </div>
        """, unsafe_allow_html=True)


def render_delivery_history(driver_id):
    """Render delivery history for the driver."""
    state = load_state()
    driver_data = state["drivers"].get(driver_id, {})
    delivery_history = driver_data.get("delivery_history", [])
    
    if not delivery_history:
        return
    
    st.markdown("### 📜 Recent Deliveries")
    
    total_earnings = 0
    for delivery in sorted(delivery_history, key=lambda x: x.get("completed_at", ""), reverse=True)[:5]:
        tip = delivery.get("tip") or 0
        total_earnings += tip
        completed = delivery.get("completed_at", "")
        if completed:
            try:
                completed_time = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                time_str = completed_time.strftime("%I:%M %p")
            except:
                time_str = "Earlier"
        else:
            time_str = "Earlier"
        
        st.markdown(f"""
        <div style="background: #2d2d44; padding: 12px; border-radius: 8px; margin: 5px 0; display: flex; justify-content: space-between;">
            <div>
                <strong style="color: white;">{delivery.get('order_id', 'Order')}</strong><br>
                <span style="color: #aaa;">{delivery.get('customer_name', 'Customer')} • {delivery.get('zone', 'Loop')}</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #4CAF50; font-weight: bold;">+${tip:.2f}</span><br>
                <span style="color: #888; font-size: 11px;">{time_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if total_earnings > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 15px; border-radius: 10px; margin-top: 15px; text-align: center;">
            <div style="font-size: 14px; color: rgba(255,255,255,0.9);">Today's Earnings</div>
            <div style="font-size: 32px; font-weight: bold; color: white;">${total_earnings:.2f}</div>
        </div>
        """, unsafe_allow_html=True)


def main():
    # Check if any driver has an active order - auto-select for demo
    state = load_state()
    drivers = state.get("drivers", {})
    
    # Find driver with active order
    active_driver = None
    for driver_id, driver in drivers.items():
        if driver.get("current_order"):
            active_driver = driver_id
            break
    
    # Auto-select driver with active order for seamless demo
    if active_driver and not st.session_state.driver_id:
        st.session_state.driver_id = active_driver
    
    # Check if currently selected driver's order was delivered - auto-reset
    if st.session_state.driver_id:
        driver_data = drivers.get(st.session_state.driver_id, {})
        current_order_id = driver_data.get("current_order")
        
        if current_order_id:
            # Driver has active order - check if it just became delivered
            order = state.get("orders", {}).get(current_order_id, {})
            if order.get("status") == "delivered":
                st.markdown("""
                <div style="text-align: center; padding: 100px 20px;">
                    <div style="font-size: 80px;">🎉</div>
                    <h2 style="color: #4CAF50;">Delivery Complete!</h2>
                    <p style="color: #aaa;">Great job! Returning to driver list...</p>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(2)
                st.session_state.driver_id = None
                st.rerun()
                return
    
    # Driver selection screen
    if not st.session_state.driver_id:
        st.markdown("""
        <div style="text-align: center; padding: 40px;">
            <h1>🚗 Pizza Driver App</h1>
            <p style="color: #aaa;">Waiting for order assignment...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show all drivers with their status
        for driver_id, driver in drivers.items():
            has_order = driver.get("current_order")
            status_badge = "🟢 Active Order" if has_order else "⚪ Available"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div style="background: {'#2d4d2d' if has_order else '#2d2d44'}; padding: 15px; border-radius: 10px; margin: 5px 0; border: {'2px solid #4CAF50' if has_order else 'none'};">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: white;">{driver['name']}</strong>
                        <span style="color: {'#4CAF50' if has_order else '#aaa'}; font-size: 12px;">{status_badge}</span>
                    </div>
                    <span style="color: #aaa;">{driver['vehicle']} • ⭐ {driver['rating']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("Select", key=f"select_{driver_id}", use_container_width=True):
                    st.session_state.driver_id = driver_id
                    st.rerun()
        
        st.divider()
        st.info("📱 Orders assigned automatically when kitchen reaches 80%")
        
        return
    
    # Get driver info
    driver_id = st.session_state.driver_id
    driver_info = get_driver_info(driver_id)
    
    if not driver_info:
        st.error("Driver not found")
        st.session_state.driver_id = None
        st.rerun()
        return
    
    # Switch driver button at top
    if st.button("🚪 Switch Driver", use_container_width=False):
        st.session_state.driver_id = None
        st.rerun()
    
    # Header
    st.markdown(f"""
    <div class="driver-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 20px; font-weight: bold;">🚗 {driver_info['name']}</div>
                <div style="font-size: 14px; opacity: 0.9;">{driver_info['vehicle']} • {driver_info['color']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 24px;">⭐ {driver_info['rating']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats
    render_driver_stats(driver_info, driver_id)
    
    st.divider()
    
    # Get current orders for this driver
    orders = get_driver_orders(driver_id)
    
    if not orders:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px;">☕</div>
            <h2 style="color: white;">No Active Orders</h2>
            <p style="color: #aaa;">Waiting for new deliveries...</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("📱 Orders assigned when kitchen reaches 80%")
        
        # Show delivery history when no active orders
        render_delivery_history(driver_id)
    else:
        # Show current order
        current_order = orders[0]
        
        # Map
        st.markdown("### 🗺️ Delivery Route")
        render_order_map(current_order)
        
        # Order details
        render_order_card(current_order, driver_info)
        
        # Queue
        if len(orders) > 1:
            st.markdown("### 📋 Up Next")
            for order in orders[1:]:
                st.markdown(f"""
                <div style="background: #2d2d44; padding: 12px; border-radius: 8px; margin: 5px 0;">
                    <strong style="color: white;">{order['order_id']}</strong> - {order['customer_name']}<br>
                    <span style="color: #aaa;">{order['zone']} • ${order['total']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
