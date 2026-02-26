"""
Pizza Customer App - Order and track your pizza delivery.
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
    load_state, create_order, get_order, rate_order, 
    get_all_drivers, run_simulation_step, next_order_id, STORE_LAT, STORE_LON
)
from menu_data import MENU_ITEMS, DELIVERY_ZONES, STORE_NAME, DRIVERS

try:
    from shared_routes import get_route_from_osrm, get_driver_position_on_route
    ROUTES_AVAILABLE = True
except ImportError:
    ROUTES_AVAILABLE = False

st.set_page_config(
    page_title="Chicago Loop Pizza",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 3 seconds to pick up state changes
if AUTOREFRESH_AVAILABLE:
    st_autorefresh(interval=3000, limit=None, key="customer_autorefresh")

# Run simulation step on each refresh to advance orders
run_simulation_step()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f0f1a 100%);
        font-family: 'Poppins', sans-serif;
    }
    
    /* Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #FF6B35 0%, #ff8c42 50%, #FF6B35 100%);
        padding: 25px 40px;
        border-radius: 20px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 40px rgba(255, 107, 53, 0.3);
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .logo-icon {
        font-size: 50px;
        filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));
    }
    
    .logo-text h1 {
        margin: 0;
        font-size: 32px;
        font-weight: 800;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .logo-text p {
        margin: 0;
        font-size: 14px;
        color: rgba(255,255,255,0.9);
    }
    
    .promo-badge {
        background: rgba(255,255,255,0.2);
        padding: 12px 25px;
        border-radius: 30px;
        color: white;
        font-weight: 600;
        font-size: 14px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Category Pills */
    .category-container {
        display: flex;
        gap: 10px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }
    
    /* Menu Grid */
    .menu-section {
        margin-bottom: 30px;
    }
    
    .section-title {
        color: #FF6B35;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .menu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px;
    }
    
    [data-testid="stHorizontalBlock"] {
        gap: 1rem;
        align-items: stretch;
    }
    
    /* Menu Card - Digital Board Style */
    .menu-card {
        background: linear-gradient(145deg, #2a2a40 0%, #1f1f35 100%);
        border-radius: 16px;
        overflow: hidden;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,107,53,0.1);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    }
    
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(255,107,53,0.2);
        border-color: rgba(255,107,53,0.3);
    }
    
    .menu-card-image {
        width: 100%;
        height: 140px;
        object-fit: cover;
        border-bottom: 3px solid #FF6B35;
    }
    
    .menu-card-content {
        padding: 14px 16px;
    }
    
    .menu-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        gap: 8px;
    }
    
    .menu-card-name {
        font-size: 15px;
        font-weight: 700;
        color: white;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
        min-width: 0;
    }
    
    .menu-card-price {
        background: linear-gradient(135deg, #FF6B35 0%, #ff8c42 100%);
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
        box-shadow: 0 4px 15px rgba(255,107,53,0.4);
        white-space: nowrap;
        flex-shrink: 0;
    }
    
    .menu-card-desc {
        color: #a0a0b0;
        font-size: 12px;
        margin: 0;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    /* Cart Sidebar */
    .cart-panel {
        background: linear-gradient(180deg, #252538 0%, #1a1a28 100%);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255,107,53,0.2);
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
        position: sticky;
        top: 20px;
    }
    
    .cart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 2px solid rgba(255,107,53,0.2);
    }
    
    .cart-title {
        color: white;
        font-size: 20px;
        font-weight: 700;
        margin: 0;
    }
    
    .cart-count {
        background: #FF6B35;
        color: white;
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: 600;
        font-size: 14px;
    }
    
    .cart-item {
        background: rgba(255,255,255,0.05);
        padding: 12px 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .cart-item-name {
        color: white;
        font-weight: 500;
        font-size: 14px;
    }
    
    .cart-item-qty {
        color: #FF6B35;
        font-weight: 600;
    }
    
    .cart-item-price {
        color: #a0a0b0;
        font-size: 14px;
    }
    
    .cart-total-section {
        background: rgba(255,107,53,0.1);
        padding: 15px;
        border-radius: 12px;
        margin-top: 15px;
    }
    
    .cart-total-row {
        display: flex;
        justify-content: space-between;
        color: #a0a0b0;
        font-size: 14px;
        margin-bottom: 8px;
    }
    
    .cart-total-final {
        display: flex;
        justify-content: space-between;
        color: white;
        font-size: 20px;
        font-weight: 700;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Order Button */
    .order-btn {
        background: linear-gradient(135deg, #FF6B35 0%, #ff8c42 100%);
        color: white;
        padding: 18px;
        border-radius: 15px;
        font-size: 18px;
        font-weight: 700;
        text-align: center;
        margin-top: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(255,107,53,0.4);
    }
    
    .order-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(255,107,53,0.5);
    }
    
    /* Featured Banner */
    .featured-banner {
        background: linear-gradient(135deg, #FF6B35 0%, #e85a2b 100%);
        border-radius: 16px;
        padding: 20px 30px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 30px rgba(255,107,53,0.3);
    }
    
    .featured-text h3 {
        color: white;
        margin: 0;
        font-size: 22px;
        font-weight: 700;
    }
    
    .featured-text p {
        color: rgba(255,255,255,0.9);
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    
    .featured-code {
        background: white;
        color: #FF6B35;
        padding: 12px 25px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 16px;
    }
    
    /* Quick Info Bar */
    .info-bar {
        display: flex;
        gap: 30px;
        margin-bottom: 25px;
        padding: 15px 25px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
    }
    
    .info-item {
        display: flex;
        align-items: center;
        gap: 10px;
        color: white;
    }
    
    .info-icon {
        font-size: 20px;
    }
    
    .info-text {
        font-size: 14px;
    }
    
    .info-text span {
        color: #FF6B35;
        font-weight: 600;
    }
    
    /* Tracking */
    .tracking-card {
        background: linear-gradient(145deg, #2a2a40 0%, #1f1f35 100%);
        border-radius: 20px;
        padding: 30px;
        border: 1px solid rgba(255,107,53,0.2);
    }
    
    .status-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
    }
    
    .status-preparing { background: #FFC107; color: #000; }
    .status-ready { background: #17A2B8; color: white; }
    .status-onway { background: #007BFF; color: white; }
    .status-delivered { background: #28A745; color: white; }
    
    /* Empty Cart */
    .empty-cart {
        text-align: center;
        padding: 40px 20px;
        color: #a0a0b0;
    }
    
    .empty-cart-icon {
        font-size: 50px;
        margin-bottom: 15px;
        opacity: 0.5;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

MENU = MENU_ITEMS
DELIVERY_ADDRESSES = DELIVERY_ZONES

if "cart" not in st.session_state:
    st.session_state.cart = {}
if "view" not in st.session_state:
    st.session_state.view = "menu"
if "active_order_id" not in st.session_state:
    st.session_state.active_order_id = None
if "customer_name" not in st.session_state:
    st.session_state.customer_name = "Alex Johnson"
if "customer_phone" not in st.session_state:
    st.session_state.customer_phone = "555-1234"
if "selected_address" not in st.session_state:
    st.session_state.selected_address = 0
if "selected_tip" not in st.session_state:
    st.session_state.selected_tip = 3


def add_to_cart(item_name, price):
    if item_name in st.session_state.cart:
        st.session_state.cart[item_name]["qty"] += 1
    else:
        st.session_state.cart[item_name] = {"price": price, "qty": 1}


def remove_from_cart(item_name):
    if item_name in st.session_state.cart:
        if st.session_state.cart[item_name]["qty"] > 1:
            st.session_state.cart[item_name]["qty"] -= 1
        else:
            del st.session_state.cart[item_name]


def get_cart_total():
    return sum(item["price"] * item["qty"] for item in st.session_state.cart.values())


def get_cart_count():
    return sum(item["qty"] for item in st.session_state.cart.values())


@st.cache_data(ttl=300)
def get_cached_route(start_lon, start_lat, end_lon, end_lat):
    """Get actual road route - cached version."""
    if ROUTES_AVAILABLE:
        coords, _, _ = get_route_from_osrm(start_lon, start_lat, end_lon, end_lat)
        return coords
    return [[start_lon, start_lat], [end_lon, end_lat]]


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


def get_traffic_zones_for_map():
    """Get active traffic zones with colors for map display."""
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
    
    traffic_zones = []
    for hotspot in active:
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
    
    return traffic_zones


def render_header():
    st.markdown(f"""
    <div class="header-banner">
        <div class="logo-section">
            <div class="logo-icon">🍕</div>
            <div class="logo-text">
                <h1>{STORE_NAME}</h1>
                <p>Fresh • Hot • Delivered Fast</p>
            </div>
        </div>
        <div class="promo-badge">🔥 FREE DELIVERY on orders $25+</div>
    </div>
    """, unsafe_allow_html=True)


def render_info_bar():
    st.markdown("""
    <div class="info-bar">
        <div class="info-item">
            <span class="info-icon">🕐</span>
            <span class="info-text">Delivery: <span>25-35 min</span></span>
        </div>
        <div class="info-item">
            <span class="info-icon">📍</span>
            <span class="info-text">Chicago Loop Area</span>
        </div>
        <div class="info-item">
            <span class="info-icon">⭐</span>
            <span class="info-text">Rating: <span>4.8</span> (2.3k reviews)</span>
        </div>
        <div class="info-item">
            <span class="info-icon">🚗</span>
            <span class="info-text">Min Order: <span>$12</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_featured():
    st.markdown("""
    <div class="featured-banner">
        <div class="featured-text">
            <h3>🎉 Weekend Special!</h3>
            <p>Get 20% off on all Supreme Pizzas this weekend only</p>
        </div>
        <div class="featured-code">SUPREME20</div>
    </div>
    """, unsafe_allow_html=True)


def render_cart_panel():
    cart_count = get_cart_count()
    
    st.markdown(f"""
    <div class="cart-header">
        <h3 class="cart-title">🛒 Your Order</h3>
        <span class="cart-count">{cart_count} items</span>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.cart:
        st.markdown("""
        <div class="empty-cart">
            <div class="empty-cart-icon">🛒</div>
            <p>Your cart is empty</p>
            <p style="font-size: 12px;">Add items from the menu</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for item_name, item_data in st.session_state.cart.items():
        subtotal = item_data['price'] * item_data['qty']
        st.markdown(f"**{item_name}**")
        st.caption(f"${item_data['price']:.2f} × {item_data['qty']} = ${subtotal:.2f}")
        if st.button(f"➖ Remove one", key=f"cr_{item_name}", use_container_width=True):
            remove_from_cart(item_name)
            st.rerun()
        if st.button(f"➕ Add one", key=f"ca_{item_name}", use_container_width=True):
            add_to_cart(item_name, item_data['price'])
            st.rerun()
        st.markdown("---")
    
    subtotal = get_cart_total()
    delivery_fee = 0 if subtotal >= 25 else 3.99
    tax = subtotal * 0.1025
    total = subtotal + delivery_fee + tax
    
    st.markdown(f"""
    <div style="font-size:13px;color:#aaa;">
        Subtotal: ${subtotal:.2f}<br>
        Delivery: {'FREE' if delivery_fee == 0 else f'${delivery_fee:.2f}'}<br>
        Tax: ${tax:.2f}
    </div>
    <div style="font-size:18px;font-weight:bold;color:white;margin-top:10px;">
        Total: ${total:.2f}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("##### 👤 Your Name")
    st.session_state.customer_name = st.text_input("Name", value=st.session_state.customer_name, label_visibility="collapsed")
    
    st.markdown("##### 📍 Deliver To")
    address_labels = [addr['label'] for addr in DELIVERY_ADDRESSES]
    selected_label = st.selectbox("Address", address_labels, index=st.session_state.selected_address, label_visibility="collapsed")
    st.session_state.selected_address = address_labels.index(selected_label)
    addr = DELIVERY_ADDRESSES[st.session_state.selected_address]
    st.caption(addr['address'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🍕 Place Order", use_container_width=True, type="primary", disabled=cart_count == 0):
        order_id = next_order_id()
        items_list = [f"{data['qty']}x {name}" for name, data in st.session_state.cart.items()]
        
        # Create order in unified state - driver assigned automatically at 80% kitchen progress
        create_order(
            order_id=order_id,
            customer_name=st.session_state.customer_name,
            customer_phone=st.session_state.customer_phone,
            items=items_list,
            address=addr["address"],
            zone=addr["zone"],
            lat=addr["lat"],
            lon=addr["lon"],
            total=round(total, 2),
            special_instructions=""
        )
        
        st.session_state.active_order_id = order_id
        st.session_state.cart = {}
        st.session_state.view = "tracking"
        st.balloons()
        st.rerun()


def render_menu_item(item, category):
    image_url = item.get('image', '')
    cart_qty = st.session_state.cart.get(item['name'], {}).get('qty', 0)
    
    st.markdown(f"""
    <div class="menu-card">
        <img src="{image_url}" class="menu-card-image" onerror="this.src='https://via.placeholder.com/300x180/2a2a40/FF6B35?text=🍕'">
        <div class="menu-card-content">
            <div class="menu-card-header">
                <h4 class="menu-card-name">{item['name']}</h4>
                <span class="menu-card-price">${item['price']:.2f}</span>
            </div>
            <p class="menu-card-desc">{item['desc']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if cart_qty > 0:
        st.markdown(f"<div style='text-align:center;color:#FF6B35;font-weight:bold;padding:5px;'>{cart_qty} in cart</div>", unsafe_allow_html=True)
        if st.button(f"➖ Remove", key=f"rem_{category}_{item['name']}", use_container_width=True):
            remove_from_cart(item['name'])
            st.rerun()
        if st.button(f"➕ Add More", key=f"add_{category}_{item['name']}", use_container_width=True, type="primary"):
            add_to_cart(item['name'], item['price'])
            st.rerun()
    else:
        if st.button("Add to Cart", key=f"add_{category}_{item['name']}", use_container_width=True, type="primary"):
            add_to_cart(item['name'], item['price'])
            st.rerun()


def _suggest_party_bundle(description: str) -> str:
    """Generate a pizza bundle suggestion based on a party description using local menu data."""
    desc_lower = description.lower()

    # Estimate guest count
    guests = 4
    for word in desc_lower.split():
        if word.isdigit():
            guests = int(word)
            break
    for phrase, count in [("a few", 4), ("small group", 6), ("big group", 12), ("large", 15), ("huge", 20)]:
        if phrase in desc_lower:
            guests = count

    pizzas_needed = max(2, (guests + 2) // 3)
    is_game_day = any(w in desc_lower for w in ["game", "football", "basketball", "super bowl", "sports", "match"])
    is_kids = any(w in desc_lower for w in ["kid", "child", "birthday", "children"])

    pizzas = MENU.get("Pizzas", [])
    sides = MENU.get("Sides", [])
    drinks = MENU.get("Drinks", [])
    desserts = MENU.get("Desserts", [])

    if is_game_day:
        picks = ["Meat Lovers", "Classic Pepperoni", "BBQ Chicken", "Supreme Deluxe"]
        side_pick = "Buffalo Wings (8pc)"
    elif is_kids:
        picks = ["Classic Pepperoni", "Margherita", "Hawaiian Paradise"]
        side_pick = "Garlic Breadsticks"
    else:
        picks = ["Classic Pepperoni", "Margherita", "BBQ Chicken", "Veggie Garden"]
        side_pick = "Garlic Breadsticks"

    selected_pizzas = []
    for name in picks[:pizzas_needed]:
        item = next((p for p in pizzas if p["name"] == name), None)
        if item:
            selected_pizzas.append(item)
    while len(selected_pizzas) < pizzas_needed and pizzas:
        for p in pizzas:
            if p not in selected_pizzas:
                selected_pizzas.append(p)
                break
        else:
            break

    side_item = next((s for s in sides if s["name"] == side_pick), sides[0] if sides else None)
    drink_item = drinks[0] if drinks else None
    dessert_item = desserts[0] if desserts and (is_kids or guests >= 8) else None

    total = sum(p["price"] for p in selected_pizzas)
    lines = [f"  - **{p['name']}** — \\${p['price']:.2f}" for p in selected_pizzas]
    if side_item:
        sides_qty = max(1, guests // 4)
        total += side_item["price"] * sides_qty
        lines.append(f"  - **{side_item['name']}** x{sides_qty} — \\${side_item['price'] * sides_qty:.2f}")
    if drink_item:
        drinks_qty = max(1, guests // 4)
        total += drink_item["price"] * drinks_qty
        lines.append(f"  - **{drink_item['name']}** x{drinks_qty} — \\${drink_item['price'] * drinks_qty:.2f}")
    if dessert_item:
        total += dessert_item["price"]
        lines.append(f"  - **{dessert_item['name']}** — \\${dessert_item['price']:.2f}")

    theme = "Game Day Party Pack 🏈" if is_game_day else "Kids Birthday Bundle 🎂" if is_kids else "Party Bundle 🎉"
    return f"""**{theme}** for ~{guests} guests\n\n""" + "\n".join(lines) + f"\n\n**Bundle Total: \\${total:.2f}**"


def render_menu_page():
    render_header()
    render_info_bar()
    
    if st.session_state.active_order_id:
        order = get_order(st.session_state.active_order_id)
        if order and order["status"] == "delivered":
            st.session_state.view = "tracking"
            st.rerun()
            return
        if order and order["status"] not in ("delivered",):
            st.info(f"🚗 You have an active order: **{st.session_state.active_order_id}** - Status: **{order['status'].replace('_', ' ').title()}**")
            if st.button("📍 Track My Order", type="primary"):
                st.session_state.view = "tracking"
                st.rerun()
            st.markdown("---")
    
    render_featured()

    # Party Bundle Assistant
    with st.expander("🎉 Planning a party? Let us help!", expanded=False):
        party_input = st.text_input(
            "Describe your event and we'll suggest a bundle:",
            placeholder="e.g. Game day with 8 friends, or kids birthday party for 12",
            key="party_input",
        )
        if party_input:
            suggestion = _suggest_party_bundle(party_input)
            if suggestion:
                st.markdown(suggestion)
                st.caption("_Tap items below to add them to your cart._")

    menu_col, cart_col = st.columns([7, 2])
    
    with menu_col:
        category_icons = {"Pizzas": "🍕", "Sides": "🍟", "Drinks": "🥤", "Desserts": "🍰"}
        
        for category, items in MENU.items():
            icon = category_icons.get(category, "🍽️")
            st.markdown(f"### {icon} {category}")
            
            # Use container instead of nested columns
            for idx, item in enumerate(items):
                if idx % 4 == 0:
                    cols = st.columns(4)
                with cols[idx % 4]:
                    render_menu_item(item, category)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    with cart_col:
        render_cart_panel()


def render_tracking_page():
    order_id = st.session_state.active_order_id
    
    if not order_id:
        st.session_state.view = "menu"
        st.rerun()
        return
    
    order = get_order(order_id)
    
    if not order:
        st.error("Order not found")
        if st.button("← Back to Menu"):
            st.session_state.view = "menu"
            st.session_state.active_order_id = None
            st.rerun()
        return
    
    status = order["status"]
    
    if status == "delivered":
        render_rating_page(order)
        return
    
    render_header()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="tracking-card">
            <h2 style="color:white;margin:0;">Order {order_id}</h2>
            <p style="color:#a0a0b0;">Placed at {order['created_at'][:16].replace('T', ' ')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        steps = [
            ("📋", "Confirmed", ["pending", "preparing", "ready", "picked_up", "on_the_way", "delivered"]),
            ("👨‍🍳", "Preparing", ["preparing", "ready", "picked_up", "on_the_way", "delivered"]),
            ("✅", "Ready", ["ready", "picked_up", "on_the_way", "delivered"]),
            ("🚗", "On the Way", ["on_the_way", "delivered"]),
            ("🏠", "Delivered", ["delivered"]),
        ]
        
        cols = st.columns(5)
        for i, (icon, label, active_statuses) in enumerate(steps):
            with cols[i]:
                is_active = status in active_statuses
                is_current = (status in active_statuses and (i == len(steps) - 1 or status not in steps[i+1][2]))
                color = "#28A745" if is_active and not is_current else "#FF6B35" if is_current else "#555"
                opacity = "1" if is_active else "0.4"
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="font-size:32px;opacity:{opacity};">{icon}</div>
                    <div style="font-size:12px;color:{color};font-weight:{'bold' if is_current else 'normal'};">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        status_info = {
            "pending": ("🍕", "Order Received!", "We're getting your order ready...", "#FFC107"),
            "preparing": ("👨‍🍳", "In the Kitchen", "Your pizza is being made with love!", "#FF9800"),
            "ready": ("✅", "Ready!", "Driver is picking up your order", "#17A2B8"),
            "picked_up": ("📦", "Picked Up", "Your order is with the driver", "#17A2B8"),
            "on_the_way": ("🚗", "On the Way!", "Your driver is heading to you", "#007BFF"),
        }
        
        if status in status_info:
            icon, title, msg, color = status_info[status]
            eta = order.get("eta_minutes", 20)
            
            # Show progress bar for preparing status
            if status == "preparing":
                kitchen_progress = order.get("kitchen_progress", 0)
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{color} 0%,{color}dd 100%);padding:30px;border-radius:16px;text-align:center;color:white;">
                    <div style="font-size:60px;">{icon}</div>
                    <h2 style="margin:10px 0;">{title}</h2>
                    <p style="opacity:0.9;">{msg}</p>
                    <div style="background:rgba(255,255,255,0.3);border-radius:10px;height:20px;margin:15px 0;">
                        <div style="background:white;border-radius:10px;height:20px;width:{kitchen_progress}%;transition:width 0.5s;"></div>
                    </div>
                    <div style="font-size:24px;font-weight:bold;">{kitchen_progress}% Complete</div>
                </div>
                """, unsafe_allow_html=True)
            elif status == "on_the_way":
                delivery_progress = order.get("delivery_progress", 0)
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{color} 0%,{color}dd 100%);padding:30px;border-radius:16px;text-align:center;color:white;">
                    <div style="font-size:60px;">{icon}</div>
                    <h2 style="margin:10px 0;">{title}</h2>
                    <p style="opacity:0.9;">{msg}</p>
                    <div style="font-size:48px;font-weight:bold;">{eta} min</div>
                    <p style="opacity:0.7;">Estimated arrival</p>
                    <div style="background:rgba(255,255,255,0.3);border-radius:10px;height:10px;margin-top:15px;">
                        <div style="background:white;border-radius:10px;height:10px;width:{delivery_progress}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{color} 0%,{color}dd 100%);padding:30px;border-radius:16px;text-align:center;color:white;">
                    <div style="font-size:60px;">{icon}</div>
                    <h2 style="margin:10px 0;">{title}</h2>
                    <p style="opacity:0.9;">{msg}</p>
                    <div style="font-size:48px;font-weight:bold;">{eta} min</div>
                    <p style="opacity:0.7;">Estimated arrival</p>
                </div>
                """, unsafe_allow_html=True)
        
        show_live_map = status in ["picked_up", "on_the_way"] or (
            status in ["preparing", "ready"] and order.get("kitchen_progress", 0) >= 80 and order.get("driver_id")
        )
        
        if show_live_map:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🗺️ Live Tracking")
            
            driver_lat = order.get("driver_lat", STORE_LAT)
            driver_lon = order.get("driver_lon", STORE_LON)
            customer_lat = order["lat"]
            customer_lon = order["lon"]
            
            center_lat = (driver_lat + customer_lat) / 2
            center_lon = (driver_lon + customer_lon) / 2
            
            # Use route from unified state if available, else fetch from OSRM
            route_coords = order.get("route_coords")
            if not route_coords:
                route_coords = get_cached_route(STORE_LON, STORE_LAT, customer_lon, customer_lat)
            
            # Get active traffic zones (same as driver/ops apps)
            traffic_zones = get_traffic_zones_for_map()
            
            layers = []
            
            # Traffic zones layer (render first, behind other elements)
            if traffic_zones:
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=traffic_zones,
                    get_position=["lon", "lat"],
                    get_color="color",
                    get_radius="radius",
                    pickable=True,
                    opacity=0.3,
                ))
            
            layers.append(pdk.Layer("PathLayer", data=[{"path": route_coords, "color": [0, 122, 255, 200]}], get_path="path", get_color="color", width_scale=20, width_min_pixels=3))
            # Store marker (orange)
            layers.append(pdk.Layer("ScatterplotLayer", data=[{"lat": STORE_LAT, "lon": STORE_LON, "name": "Chicago Loop Pizza"}], get_position=["lon", "lat"], get_color=[255, 87, 51, 255], get_radius=40, pickable=True))
            # Driver marker (green)
            layers.append(pdk.Layer("ScatterplotLayer", data=[{"lat": driver_lat, "lon": driver_lon, "name": "Driver"}], get_position=["lon", "lat"], get_color=[52, 199, 89, 255], get_radius=40, pickable=True))
            # Customer marker (purple)
            layers.append(pdk.Layer("ScatterplotLayer", data=[{"lat": customer_lat, "lon": customer_lon, "name": "You"}], get_position=["lon", "lat"], get_color=[187, 134, 252, 255], get_radius=40, pickable=True))
            
            st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=13, pitch=45, bearing=0), map_style="dark", height=450), use_container_width=True, height=450)
            st.markdown("""
            <div style="display:flex;flex-wrap:wrap;gap:14px;font-size:12px;margin-top:8px;color:#ccc;">
                <span><span style="color:#FF5733;">●</span> Store</span>
                <span><span style="color:#34C759;">●</span> Driver</span>
                <span><span style="color:#BB86FC;">●</span> Your location</span>
                <span><span style="color:#007AFF;">●</span> Route</span>
                <span><span style="color:#FFC107;">◉</span> Traffic Zone</span>
            </div>
            """, unsafe_allow_html=True)
        
        elif status in ["pending", "preparing", "ready"] and not show_live_map:
            # Show delivery route preview during preparation
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🗺️ Delivery Route")
            
            customer_lat = order["lat"]
            customer_lon = order["lon"]
            
            center_lat = (STORE_LAT + customer_lat) / 2
            center_lon = (STORE_LON + customer_lon) / 2
            
            # Use route from unified state if available, else fetch from OSRM
            route_coords = order.get("route_coords")
            if not route_coords:
                route_coords = get_cached_route(STORE_LON, STORE_LAT, customer_lon, customer_lat)
            
            # Get active traffic zones
            traffic_zones = get_traffic_zones_for_map()
            
            layers = []
            
            # Traffic zones layer
            if traffic_zones:
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=traffic_zones,
                    get_position=["lon", "lat"],
                    get_color="color",
                    get_radius="radius",
                    pickable=True,
                    opacity=0.3,
                ))
            
            layers.append(pdk.Layer("PathLayer", data=[{"path": route_coords, "color": [0, 122, 255, 120]}], get_path="path", get_color="color", width_scale=20, width_min_pixels=3))
            # Store marker (orange)
            layers.append(pdk.Layer("ScatterplotLayer", data=[{"lat": STORE_LAT, "lon": STORE_LON, "name": "Chicago Loop Pizza"}], get_position=["lon", "lat"], get_color=[255, 87, 51, 255], get_radius=40, pickable=True))
            # Customer marker (purple)
            layers.append(pdk.Layer("ScatterplotLayer", data=[{"lat": customer_lat, "lon": customer_lon, "name": "Your Location"}], get_position=["lon", "lat"], get_color=[187, 134, 252, 255], get_radius=40, pickable=True))
            
            st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=13, pitch=45, bearing=0), map_style="dark", height=450), use_container_width=True, height=450)
            st.markdown("""
            <div style="display:flex;flex-wrap:wrap;gap:14px;font-size:12px;margin-top:8px;color:#ccc;">
                <span><span style="color:#FF5733;">●</span> Store</span>
                <span><span style="color:#BB86FC;">●</span> Your location</span>
                <span><span style="color:#007AFF;">●</span> Planned Route</span>
                <span><span style="color:#FFC107;">◉</span> Traffic Zone</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📦 Order Details")
        
        state = load_state()
        driver_info = state["drivers"].get(order.get("driver_id"), {}) if order.get("driver_id") else {}
        
        if order.get("driver_id") and driver_info:
            st.markdown(f"""
            <div style="background:#2a2a40;padding:15px;border-radius:12px;margin-bottom:15px;">
                <div style="color:#a0a0b0;font-size:12px;margin-bottom:5px;">YOUR DRIVER</div>
                <div style="color:white;font-weight:bold;font-size:16px;">🚗 {driver_info.get('name', 'Driver')}</div>
                <div style="color:#a0a0b0;font-size:13px;">{driver_info.get('vehicle', '')} • {driver_info.get('color', '')}</div>
                <div style="color:#FFD700;margin-top:5px;">⭐ {driver_info.get('rating', 4.8)}</div>
            </div>
            """, unsafe_allow_html=True)
        elif status in ["pending", "preparing"]:
            st.markdown("""
            <div style="background:#2a2a40;padding:15px;border-radius:12px;margin-bottom:15px;">
                <div style="color:#a0a0b0;font-size:12px;margin-bottom:5px;">DRIVER</div>
                <div style="color:white;font-size:14px;">Will be assigned when order is 80% ready</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("**Items:**")
        for item in order["items"]:
            st.markdown(f"• {item}")
        
        st.markdown(f"**Total:** ${order['total']:.2f}")
        st.markdown(f"**Address:** {order['address']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("← Back to Menu", use_container_width=True):
            st.session_state.view = "menu"
            st.rerun()
    
    # Auto-refresh is handled by st_autorefresh


def render_rating_page(order):
    st.markdown("""
    <div style="text-align:center;padding:40px;">
        <div style="font-size:100px;">🎉</div>
        <h1 style="color:white;">Order Delivered!</h1>
        <p style="color:#a0a0b0;">Your pizza has arrived. Enjoy!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if order.get("rating"):
        st.success(f"Thanks for rating! You gave {order['rating']} stars.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🍕 Order Again", use_container_width=True, type="primary"):
                st.session_state.view = "menu"
                st.session_state.active_order_id = None
                st.rerun()
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### How was your delivery?")
        rating = st.slider("Rate your experience", 1, 5, 5, format="%d ⭐")
        
        st.markdown("### Add a tip for your driver")
        tip_options = [0, 2, 3, 5, 8]
        tip_cols = st.columns(5)
        
        for i, tip in enumerate(tip_options):
            with tip_cols[i]:
                label = "No tip" if tip == 0 else f"${tip}"
                if st.button(label, key=f"tip_{tip}", use_container_width=True, type="primary" if st.session_state.selected_tip == tip else "secondary"):
                    st.session_state.selected_tip = tip
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("✅ Submit Rating", use_container_width=True, type="primary"):
            rate_order(order["order_id"], rating, st.session_state.selected_tip)
            st.balloons()
            st.success("Thanks for your feedback!")
            time.sleep(1)
            st.session_state.view = "menu"
            st.session_state.active_order_id = None
            st.rerun()
        
        if st.button("Skip", use_container_width=True):
            st.session_state.view = "menu"
            st.session_state.active_order_id = None
            st.rerun()


def main():
    if st.session_state.view == "menu":
        render_menu_page()
    elif st.session_state.view == "tracking":
        render_tracking_page()


if __name__ == "__main__":
    main()
