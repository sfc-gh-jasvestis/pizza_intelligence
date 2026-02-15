"""
Shared menu data for Pizza Demo Apps.
Ensures consistency across Customer App, Driver App, Ops Assistant, and Snowflake Intelligence.
Data aligned with PIZZA_INTELLIGENCE.ANALYTICS.DIM_PRODUCTS
"""

STORE_NAME = "Chicago Loop Pizza"
STORE_LAT = 41.8827
STORE_LON = -87.6233

MENU_ITEMS = {
    "Pizzas": [
        {
            "name": "Classic Pepperoni",
            "desc": "Classic pepperoni with mozzarella cheese",
            "price": 18.99,
            "prep_time": 12,
            "image": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400&q=80",
        },
        {
            "name": "Margherita",
            "desc": "Fresh mozzarella, tomatoes, basil",
            "price": 16.99,
            "prep_time": 10,
            "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&q=80",
        },
        {
            "name": "BBQ Chicken",
            "desc": "Grilled chicken, BBQ sauce, red onions",
            "price": 21.99,
            "prep_time": 14,
            "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&q=80",
        },
        {
            "name": "Veggie Garden",
            "desc": "Mushrooms, peppers, onions, olives, tomatoes",
            "price": 17.99,
            "prep_time": 11,
            "image": "https://images.unsplash.com/photo-1511689660979-10d2b1aada49?w=400&q=80",
        },
        {
            "name": "Meat Lovers",
            "desc": "Pepperoni, sausage, bacon, ham",
            "price": 23.99,
            "prep_time": 15,
            "image": "https://images.unsplash.com/photo-1594007654729-407eedc4be65?w=400&q=80",
        },
        {
            "name": "Hawaiian Paradise",
            "desc": "Ham, pineapple, mozzarella cheese",
            "price": 18.99,
            "prep_time": 11,
            "image": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=400&q=80",
        },
        {
            "name": "Supreme Deluxe",
            "desc": "Pepperoni, sausage, peppers, onions, olives",
            "price": 22.99,
            "prep_time": 14,
            "image": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&q=80",
        },
    ],
    "Sides": [
        {
            "name": "Garlic Breadsticks",
            "desc": "Toasted with garlic butter and herbs",
            "price": 6.99,
            "prep_time": 5,
            "image": "https://images.unsplash.com/photo-1619535860434-ba1d8fa12536?w=400&q=80",
        },
        {
            "name": "Buffalo Wings (8pc)",
            "desc": "Crispy wings with buffalo sauce",
            "price": 11.99,
            "prep_time": 12,
            "image": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400&q=80",
        },
        {
            "name": "Caesar Salad",
            "desc": "Romaine, parmesan, croutons, caesar dressing",
            "price": 8.99,
            "prep_time": 3,
            "image": "https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400&q=80",
        },
    ],
    "Drinks": [
        {
            "name": "Coca-Cola (2L)",
            "desc": "Classic Coke",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=400&q=80",
        },
        {
            "name": "Sprite (2L)",
            "desc": "Lemon-lime soda",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=400&q=80",
        },
    ],
    "Desserts": [
        {
            "name": "Chocolate Lava Cake",
            "desc": "Warm chocolate cake with molten center",
            "price": 7.99,
            "prep_time": 8,
            "image": "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400&q=80",
        },
        {
            "name": "Cinnamon Twists",
            "desc": "Crispy twists with cinnamon sugar",
            "price": 5.99,
            "prep_time": 5,
            "image": "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&q=80",
        },
    ],
}

DELIVERY_ZONES = [
    {"label": "Home", "address": "456 Oak Ave, River North", "zone": "River North", "lat": 41.8925, "lon": -87.6340},
    {"label": "Work", "address": "789 State St, West Loop", "zone": "West Loop", "lat": 41.8827, "lon": -87.6474},
    {"label": "Downtown", "address": "321 Wacker Dr, Loop", "zone": "Loop", "lat": 41.8869, "lon": -87.6368},
    {"label": "Streeterville", "address": "654 Michigan Ave, Streeterville", "zone": "Streeterville", "lat": 41.8951, "lon": -87.6244},
]

DRIVERS = {
    "DRV001": {"name": "Mike Rodriguez", "phone": "555-0101", "rating": 4.8, "vehicle": "Honda Civic", "color": "Silver"},
    "DRV002": {"name": "Sarah Chen", "phone": "555-0102", "rating": 4.9, "vehicle": "Toyota Prius", "color": "Blue"},
    "DRV003": {"name": "James Wilson", "phone": "555-0103", "rating": 4.7, "vehicle": "Ford Focus", "color": "Red"},
    "DRV004": {"name": "Emma Thompson", "phone": "555-0104", "rating": 4.9, "vehicle": "Hyundai Elantra", "color": "White"},
}

def get_all_pizza_items():
    """Get flat list of all pizza items for order simulation."""
    return MENU_ITEMS["Pizzas"]

def get_item_by_name(name):
    """Get menu item by name."""
    for category, items in MENU_ITEMS.items():
        for item in items:
            if item["name"] == name:
                return item
    return None
