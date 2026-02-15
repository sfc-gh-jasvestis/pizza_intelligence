"""
Pizza Customer App - Order and track your pizza delivery.
Part of the Pizza Ops Demo ecosystem powered by Snowflake.
"""

import streamlit as st
import pydeck as pdk
import time
from datetime import datetime
import random

from shared_state import (
    load_state, save_state, create_order, get_order, 
    rate_order, get_all_active_orders, assign_driver
)
from menu_data import MENU_ITEMS, DELIVERY_ZONES, STORE_NAME, STORE_LAT, STORE_LON, DRIVERS

st.set_page_config(
    page_title="Chicago Loop Pizza",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
    }
    .hero-header {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #FF6B35 100%);
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }
    .menu-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 0;
        margin-bottom: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .menu-card-content {
        padding: 15px;
    }
    .price-tag {
        background: linear-gradient(135deg, #FF6B35, #F7931E);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 18px;
    }
    .cart-item {
        background: #2d2d44;
        padding: 12px 15px;
        border-radius: 10px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .order-status {
        text-align: center;
        padding: 30px;
        border-radius: 16px;
        margin: 15px 0;
    }
    .status-preparing {
        background: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
    }
    .status-on-way {
        background: linear-gradient(135deg, #17A2B8 0%, #138496 100%);
    }
    .status-delivered {
        background: linear-gradient(135deg, #28A745 0%, #1E7E34 100%);
    }
    .eta-display {
        font-size: 48px;
        font-weight: bold;
        color: white;
    }
    .tracking-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
    }
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
    }
    .step {
        text-align: center;
        flex: 1;
    }
    .step-icon {
        font-size: 24px;
        margin-bottom: 5px;
    }
    .step-active {
        color: #FF6B35;
        font-weight: bold;
    }
    .step-done {
        color: #28A745;
    }
    .step-pending {
        color: #aaa;
    }
    .category-tab {
        background: #2d2d44;
        padding: 12px 20px;
        border-radius: 25px;
        margin: 5px;
        cursor: pointer;
        color: white;
        border: none;
    }
    .category-tab-active {
        background: linear-gradient(135deg, #FF6B35, #F7931E);
    }
    .quantity-btn {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: none;
        font-size: 18px;
        font-weight: bold;
    }
    .rating-star {
        font-size: 40px;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .rating-star:hover {
        transform: scale(1.2);
    }
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
    st.session_state.customer_name = "Demo Customer"
if "customer_phone" not in st.session_state:
    st.session_state.customer_phone = "555-1234"
if "selected_address" not in st.session_state:
    st.session_state.selected_address = 0
if "category" not in st.session_state:
    st.session_state.category = "Pizzas"


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


def render_menu():
    st.markdown(f"""
    <div class="hero-header">
        <h1 style="margin: 0; font-size: 28px;">🍕 {STORE_NAME}</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Fresh from our oven to your door</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    categories = list(MENU.keys())
    
    for i, cat in enumerate(categories):
        with [col1, col2, col3, col4][i]:
            if st.button(
                f"{cat}", 
                key=f"cat_{cat}",
                use_container_width=True,
                type="primary" if st.session_state.category == cat else "secondary"
            ):
                st.session_state.category = cat
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    items = MENU[st.session_state.category]
    cols = st.columns(2)
    
    for idx, item in enumerate(items):
        with cols[idx % 2]:
            with st.container():
                image_url = item.get('image', '')
                st.markdown(f"""
                <div class="menu-card">
                    <div style="width: 100%; height: 140px; overflow: hidden;">
                        <img src="{image_url}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none'">
                    </div>
                    <div class="menu-card-content">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <strong style="font-size: 16px;">{item['name']}</strong>
                            <span class="price-tag">${item['price']:.2f}</span>
                        </div>
                        <p style="color: #666; margin: 8px 0; font-size: 13px;">{item['desc']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                cart_qty = st.session_state.cart.get(item['name'], {}).get('qty', 0)
                
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1:
                    if cart_qty > 0:
                        if st.button("➖", key=f"rem_{item['name']}", use_container_width=True):
                            remove_from_cart(item['name'])
                            st.rerun()
                with c2:
                    if cart_qty > 0:
                        st.markdown(f"<div style='text-align: center; padding: 8px; color: white; font-weight: bold;'>{cart_qty} in cart</div>", unsafe_allow_html=True)
                with c3:
                    if st.button("➕", key=f"add_{item['name']}", use_container_width=True, type="primary"):
                        add_to_cart(item['name'], item['price'])
                        st.rerun()
    
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    
    cart_count = get_cart_count()
    if cart_count > 0:
        cart_total = get_cart_total()
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div style="background: #2d2d44; padding: 15px; border-radius: 12px;">
                <span style="color: white; font-size: 16px;">🛒 {cart_count} items</span>
                <span style="color: #FF6B35; font-size: 20px; font-weight: bold; float: right;">${cart_total:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("View Cart →", use_container_width=True, type="primary"):
                st.session_state.view = "cart"
                st.rerun()


def render_cart():
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <h2 style="color: white; margin: 0;">🛒 Your Cart</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Menu"):
        st.session_state.view = "menu"
        st.rerun()
    
    if not st.session_state.cart:
        st.markdown("""
        <div style="text-align: center; padding: 60px; color: #aaa;">
            <div style="font-size: 64px;">🛒</div>
            <h3>Your cart is empty</h3>
            <p>Add some delicious items from our menu!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("### Items")
    for item_name, item_data in st.session_state.cart.items():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"<span style='color: white; font-size: 16px;'>{item_name}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color: #aaa;'>${item_data['price']:.2f}</span>", unsafe_allow_html=True)
        with col3:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("−", key=f"cart_rem_{item_name}"):
                    remove_from_cart(item_name)
                    st.rerun()
            with c2:
                st.markdown(f"<div style='text-align: center; color: white;'>{item_data['qty']}</div>", unsafe_allow_html=True)
            with c3:
                if st.button("+", key=f"cart_add_{item_name}"):
                    add_to_cart(item_name, item_data['price'])
                    st.rerun()
        with col4:
            subtotal = item_data['price'] * item_data['qty']
            st.markdown(f"<span style='color: #FF6B35; font-weight: bold;'>${subtotal:.2f}</span>", unsafe_allow_html=True)
        st.divider()
    
    st.markdown("### Delivery Address")
    address_options = [f"{addr['label']} - {addr['address']}" for addr in DELIVERY_ADDRESSES]
    selected = st.selectbox("Select address", address_options, index=st.session_state.selected_address, label_visibility="collapsed")
    st.session_state.selected_address = address_options.index(selected)
    
    st.markdown("### Special Instructions")
    instructions = st.text_input("Any special requests?", placeholder="e.g., Ring doorbell, extra napkins...", label_visibility="collapsed")
    
    st.markdown("---")
    
    subtotal = get_cart_total()
    delivery_fee = 3.99
    tax = subtotal * 0.1025
    total = subtotal + delivery_fee + tax
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<span style='color: #aaa;'>Subtotal</span>", unsafe_allow_html=True)
        st.markdown("<span style='color: #aaa;'>Delivery Fee</span>", unsafe_allow_html=True)
        st.markdown("<span style='color: #aaa;'>Tax</span>", unsafe_allow_html=True)
        st.markdown("<span style='color: white; font-weight: bold; font-size: 20px;'>Total</span>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span style='color: white; text-align: right; display: block;'>${subtotal:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: white; text-align: right; display: block;'>${delivery_fee:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: white; text-align: right; display: block;'>${tax:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: #FF6B35; font-weight: bold; font-size: 20px; text-align: right; display: block;'>${total:.2f}</span>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🍕 Place Order", use_container_width=True, type="primary"):
        addr = DELIVERY_ADDRESSES[st.session_state.selected_address]
        order_id = f"ORD-{random.randint(10000, 99999)}"
        
        items_list = [f"{data['qty']}x {name}" for name, data in st.session_state.cart.items()]
        
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
            special_instructions=instructions
        )
        
        driver_id = random.choice(list(DRIVERS.keys()))
        assign_driver(order_id, driver_id)
        
        st.session_state.active_order_id = order_id
        st.session_state.cart = {}
        st.session_state.view = "tracking"
        st.rerun()


def render_tracking():
    order_id = st.session_state.active_order_id
    
    if not order_id:
        st.session_state.view = "menu"
        st.rerun()
        return
    
    order = get_order(order_id)
    
    if not order:
        st.error("Order not found")
        st.session_state.view = "menu"
        st.session_state.active_order_id = None
        return
    
    status = order["status"]
    
    if status == "delivered":
        render_rating(order)
        return
    
    st.markdown(f"""
    <div class="hero-header">
        <h2 style="margin: 0;">Order {order_id}</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Placed at {order['created_at'][:16].replace('T', ' ')}</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            is_current = (status in active_statuses and 
                         (i == len(steps) - 1 or status not in steps[i+1][2]))
            
            color = "#28A745" if is_active and not is_current else "#FF6B35" if is_current else "#555"
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 28px; opacity: {'1' if is_active else '0.4'};">{icon}</div>
                <div style="font-size: 12px; color: {color}; font-weight: {'bold' if is_current else 'normal'};">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    status_messages = {
        "pending": ("🍕", "Order Received!", "We're preparing your order...", "#FFC107"),
        "preparing": ("👨‍🍳", "In the Kitchen", "Your pizza is being made with love!", "#FF9800"),
        "ready": ("✅", "Ready for Pickup", "Driver is on the way to pick up your order", "#17A2B8"),
        "picked_up": ("📦", "Picked Up!", "Your order is with the driver", "#17A2B8"),
        "on_the_way": ("🚗", "On the Way!", "Your driver is heading to you", "#007BFF"),
    }
    
    if status in status_messages:
        icon, title, message, color = status_messages[status]
        
        eta = order.get("eta_minutes", 20)
        st.markdown(f"""
        <div class="order-status" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); color: white;">
            <div style="font-size: 48px;">{icon}</div>
            <h2 style="margin: 10px 0;">{title}</h2>
            <p style="opacity: 0.9;">{message}</p>
            <div class="eta-display">{eta} min</div>
            <p style="opacity: 0.7; margin-top: 5px;">Estimated arrival</p>
        </div>
        """, unsafe_allow_html=True)
    
    if status in ["picked_up", "on_the_way"]:
        st.markdown("### 🗺️ Live Tracking")
        
        driver_lat = order.get("driver_lat", STORE_LAT)
        driver_lon = order.get("driver_lon", STORE_LON)
        customer_lat = order["lat"]
        customer_lon = order["lon"]
        
        center_lat = (driver_lat + customer_lat) / 2
        center_lon = (driver_lon + customer_lon) / 2
        
        driver_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"lat": driver_lat, "lon": driver_lon, "name": "Driver"}],
            get_position=["lon", "lat"],
            get_color=[41, 181, 232, 255],
            get_radius=100,
            pickable=True,
        )
        
        customer_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"lat": customer_lat, "lon": customer_lon, "name": "You"}],
            get_position=["lon", "lat"],
            get_color=[40, 167, 69, 255],
            get_radius=100,
            pickable=True,
        )
        
        route_layer = pdk.Layer(
            "PathLayer",
            data=[{
                "path": [[driver_lon, driver_lat], [customer_lon, customer_lat]],
                "color": [255, 107, 53]
            }],
            get_path="path",
            get_color="color",
            width_scale=20,
            width_min_pixels=3,
        )
        
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=13,
            pitch=0,
        )
        
        st.pydeck_chart(pdk.Deck(
            layers=[route_layer, driver_layer, customer_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v10",
        ), use_container_width=True)
        
        state = load_state()
        driver_info = state["drivers"].get(order["driver_id"], {})
        st.markdown(f"""
        <div style="background: #2d2d44; padding: 15px; border-radius: 12px; margin-top: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: white; font-size: 16px;">🚗 {driver_info.get('name', 'Driver')}</strong><br>
                    <span style="color: #aaa;">{driver_info.get('vehicle', '')} • {driver_info.get('color', '')}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: #FFD700; font-size: 18px;">⭐ {driver_info.get('rating', 4.8)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📞 Call Driver", use_container_width=True):
                st.info(f"Calling {driver_info.get('name', 'Driver')}...")
        with col2:
            if st.button("💬 Message", use_container_width=True):
                st.info("Opening chat...")
    
    st.markdown("### 📦 Order Details")
    with st.expander("View items", expanded=False):
        for item in order["items"]:
            st.markdown(f"• {item}")
        st.markdown(f"**Total: ${order['total']:.2f}**")
        st.markdown(f"**Delivering to:** {order['address']}")
        if order.get("special_instructions"):
            st.markdown(f"**Note:** {order['special_instructions']}")
    
    if status not in ["delivered"]:
        time.sleep(3)
        st.rerun()


def render_rating(order):
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <div style="font-size: 80px;">🎉</div>
        <h1 style="color: white;">Order Delivered!</h1>
        <p style="color: #aaa;">Your pizza has arrived. Enjoy!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if order.get("rating"):
        st.success(f"Thanks for rating! You gave {order['rating']} stars.")
        if st.button("Order Again 🍕", use_container_width=True, type="primary"):
            st.session_state.view = "menu"
            st.session_state.active_order_id = None
            st.rerun()
        return
    
    st.markdown("### How was your delivery?")
    
    rating = st.slider("Rate your experience", 1, 5, 5, format="%d ⭐")
    
    st.markdown("### Add a tip for your driver")
    tip_options = [0, 2, 3, 5, 8]
    tip_cols = st.columns(5)
    
    if "selected_tip" not in st.session_state:
        st.session_state.selected_tip = 3
    
    for i, tip in enumerate(tip_options):
        with tip_cols[i]:
            label = "No tip" if tip == 0 else f"${tip}"
            if st.button(label, key=f"tip_{tip}", use_container_width=True,
                        type="primary" if st.session_state.selected_tip == tip else "secondary"):
                st.session_state.selected_tip = tip
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Submit Rating", use_container_width=True, type="primary"):
        rate_order(order["order_id"], rating, st.session_state.selected_tip)
        st.balloons()
        st.success("Thanks for your feedback!")
        time.sleep(2)
        st.rerun()
    
    if st.button("Skip", use_container_width=True):
        st.session_state.view = "menu"
        st.session_state.active_order_id = None
        st.rerun()


def check_for_active_orders():
    if st.session_state.active_order_id:
        order = get_order(st.session_state.active_order_id)
        if order and order["status"] != "delivered":
            return True
        elif order and order["status"] == "delivered" and not order.get("rating"):
            return True
    return False


def main():
    with st.sidebar:
        st.markdown("### 👤 Account")
        st.session_state.customer_name = st.text_input("Name", st.session_state.customer_name)
        st.session_state.customer_phone = st.text_input("Phone", st.session_state.customer_phone)
        
        st.divider()
        
        if st.session_state.active_order_id:
            if st.button("📍 Track Order", use_container_width=True):
                st.session_state.view = "tracking"
                st.rerun()
        
        if st.button("🍕 Menu", use_container_width=True):
            st.session_state.view = "menu"
            st.rerun()
        
        st.divider()
        
        st.caption("Demo Controls")
        if st.button("🎬 Simulate Delivery", use_container_width=True):
            if st.session_state.active_order_id:
                from shared_state import update_order_status
                order = get_order(st.session_state.active_order_id)
                if order:
                    status_flow = ["pending", "preparing", "ready", "picked_up", "on_the_way", "delivered"]
                    current_idx = status_flow.index(order["status"]) if order["status"] in status_flow else 0
                    if current_idx < len(status_flow) - 1:
                        update_order_status(st.session_state.active_order_id, status_flow[current_idx + 1])
                        st.rerun()
    
    if check_for_active_orders() and st.session_state.view == "menu":
        st.info(f"📍 You have an active order: {st.session_state.active_order_id}")
        if st.button("Track Order →"):
            st.session_state.view = "tracking"
            st.rerun()
        st.divider()
    
    if st.session_state.view == "menu":
        render_menu()
    elif st.session_state.view == "cart":
        render_cart()
    elif st.session_state.view == "tracking":
        render_tracking()


if __name__ == "__main__":
    main()
