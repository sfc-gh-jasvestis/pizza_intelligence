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
            "image": "https://media.istockphoto.com/id/521403691/photo/hot-homemade-pepperoni-pizza.jpg?s=612x612&w=0&k=20&c=PaISuuHcJWTEVoDKNnxaHy7L2BTUkyYZ06hYgzXmTbo=",
        },
        {
            "name": "Margherita",
            "desc": "Fresh mozzarella, tomatoes, basil",
            "price": 16.99,
            "prep_time": 10,
            "image": "https://media.istockphoto.com/id/917527628/photo/pizza-margherita.jpg?s=612x612&w=0&k=20&c=b4vJDgO9BJeVGSqjJVyge4_irqVA26ubp7FwDF2fkA4=",
        },
        {
            "name": "BBQ Chicken",
            "desc": "Grilled chicken, BBQ sauce, red onions",
            "price": 21.99,
            "prep_time": 14,
            "image": "https://media.istockphoto.com/id/1287923350/photo/pizza-with-chicken-and-barbeque-sauce-italian-pizza-on-dark-grey-black-slate-background.jpg?s=612x612&w=0&k=20&c=x4YFBWQfEWOMzbtPFJxj5_7RezyQYqo44d9DuwRnnvY=",
        },
        {
            "name": "Veggie Garden",
            "desc": "Fresh vegetables and feta cheese",
            "price": 17.99,
            "prep_time": 11,
            "image": "https://media.istockphoto.com/id/1354893222/photo/colorful-garden.jpg?s=612x612&w=0&k=20&c=3-wO5OS_TTJTXvos1QMPilTsF7HAqQM7jT0n0qp0XqQ=",
        },
        {
            "name": "Meat Lovers",
            "desc": "Pepperoni, sausage, bacon, ham",
            "price": 23.99,
            "prep_time": 15,
            "image": "https://media.istockphoto.com/id/1248287329/photo/savory-homemade-meat-lovers-pizza.jpg?s=612x612&w=0&k=20&c=ozXnuE1wYhYHJ75jwR9dLIodSbM2CFupeA9sxhAqtjY=",
        },
        {
            "name": "Hawaiian Paradise",
            "desc": "Ham, pineapple, mozzarella cheese",
            "price": 18.99,
            "prep_time": 11,
            "image": "https://media.istockphoto.com/id/537640710/photo/homemade-pineapple-and-ham-hawaiian-pizza.jpg?s=612x612&w=0&k=20&c=j2aAIbK9Emya9FHhBgBXG38DhC0vVGSdqK5FcsbZDHY=",
        },
        {
            "name": "Supreme Deluxe",
            "desc": "Pepperoni, sausage, peppers, onions, olives",
            "price": 22.99,
            "prep_time": 14,
            "image": "https://media.istockphoto.com/id/1151447052/photo/tasty-supreme-pizza-with-olives-peppers-onions-and-sausage.jpg?s=612x612&w=0&k=20&c=6m17pHx7VmeR2jCYmgbVCMTUgejpzFsB4Sx654fPBnM=",
        },
        {
            "name": "Truffle Mushroom",
            "desc": "Wild mushrooms, truffle oil, fontina cheese",
            "price": 24.99,
            "prep_time": 14,
            "image": "https://media.istockphoto.com/id/2160147074/photo/truffle-pizza.jpg?s=612x612&w=0&k=20&c=GjrtjUb9iCGDN2A2B3MlQOMhB9aKVQAkj8Etf4eLec8=",
        },
        {
            "name": "Buffalo Chicken",
            "desc": "Spicy buffalo chicken, ranch drizzle",
            "price": 21.99,
            "prep_time": 13,
            "image": "https://media.istockphoto.com/id/1215802218/photo/homemade-buffalo-chicken-pizza.jpg?s=612x612&w=0&k=20&c=ijUGukTPx-R2ODa4UoLpD3_6rCrqABf4he1aK81ArH8=",
        },
        {
            "name": "Four Cheese",
            "desc": "Mozzarella, cheddar, parmesan, gorgonzola",
            "price": 19.99,
            "prep_time": 11,
            "image": "https://media.istockphoto.com/id/1443706910/video/cutting-with-cutter-four-cheese-pizza-on-wooden-background.avif?s=640x640&k=20&c=BFe8EULYw_ZTu7qTMkfNmGJ7zfGYlZGTnBZv3q6aiAQ=",
        },
    ],
    "Sides": [
        {
            "name": "Garlic Breadsticks",
            "desc": "Toasted garlic ciabatta bread served on a wood board",
            "price": 6.99,
            "prep_time": 5,
            "image": "https://media.istockphoto.com/id/1334915216/photo/garlic-bread.jpg?s=612x612&w=0&k=20&c=OcBsBjYfmp3_XPQdxHyfDN5YabSEb-U4n-n-V3fruhY=",
        },
        {
            "name": "Buffalo Wings (8pc)",
            "desc": "Crispy wings with buffalo sauce",
            "price": 11.99,
            "prep_time": 12,
            "image": "https://images.unsplash.com/photo-1608039755401-742074f0548d?w=400&q=80",
        },
        {
            "name": "Caesar Salad",
            "desc": "Romaine, parmesan, croutons, caesar dressing",
            "price": 8.99,
            "prep_time": 3,
            "image": "https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400&q=80",
        },
        {
            "name": "Stuffed Cheesy Bread",
            "desc": "Warm bread stuffed with melted cheese and herbs",
            "price": 7.99,
            "prep_time": 7,
            "image": "https://images.unsplash.com/photo-1745031601360-b189f522ea90?w=400&q=80",
        },
        {
            "name": "Mozzarella Sticks (6pc)",
            "desc": "Golden fried mozzarella with marinara dip",
            "price": 8.99,
            "prep_time": 6,
            "image": "https://images.unsplash.com/photo-1734774924912-dcbb467f8599?w=400&q=80",
        },
        {
            "name": "Potato Wedges",
            "desc": "Seasoned crispy potato wedges with sour cream",
            "price": 6.49,
            "prep_time": 8,
            "image": "https://images.unsplash.com/photo-1623238913973-21e45cced554?w=400&q=80",
        },
        {
            "name": "Chicken Tenders (5pc)",
            "desc": "Crispy breaded chicken strips with honey mustard",
            "price": 9.99,
            "prep_time": 10,
            "image": "https://images.unsplash.com/photo-1605291581926-df4bf7ee3e89?w=400&q=80",
        },
        {
            "name": "Mac & Cheese Bites",
            "desc": "Creamy homemade macaroni and cheese",
            "price": 7.49,
            "prep_time": 6,
            "image": "https://media.istockphoto.com/id/1313740916/photo/homemade-creamy-macaroni-and-cheese-pasta.jpg?s=612x612&w=0&k=20&c=zwK-1q5ih1lFUrg4SlGURcsiW4KGs8IKsdE8kJG9Kps=",
        },
        {
            "name": "Onion Rings",
            "desc": "Beer-battered crispy onion rings",
            "price": 6.99,
            "prep_time": 6,
            "image": "https://images.unsplash.com/photo-1639024471283-03518883512d?w=400&q=80",
        },
    ],
    "Drinks": [
        {
            "name": "Coca-Cola (2L)",
            "desc": "Classic Coke",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/458709281/photo/two-liter-bottle-of-coca-cola.jpg?s=612x612&w=0&k=20&c=uOvqKDJ_lg35QtyTJf9Pc5yVLzOJLC-Qvbt8J3PMudc=",
        },
        {
            "name": "Sprite (2L)",
            "desc": "Lemon-flavored soda",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/459032317/photo/bottle-of-sprite.jpg?s=612x612&w=0&k=20&c=IdtYIIvrnJ7JY6RpV1jVGHcRv_kfniiWrLPxIDfMSmQ=",
        },
        {
            "name": "Fanta Orange (2L)",
            "desc": "Orange-flavored soda",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/458581151/photo/fanta-bottle-isolated-on-white-background.jpg?s=612x612&w=0&k=20&c=OHTMnI-BHCpQRuQW8vITpbMpIqbAYwEszZNQlFSRcX0=",
        },
        {
            "name": "Dr Pepper (2L)",
            "desc": "23 flavors of deliciousness",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/530939199/photo/dr-pepper-soft-drink-bottle.jpg?s=612x612&w=0&k=20&c=aCWD3_0KNlRF6rKHAp-1Ji-duARQJ0-G1NoE97xt0Xg=",
        },
        {
            "name": "Lemonade",
            "desc": "Freshley squeezed lemons with soda water",
            "price": 4.49,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/1164372498/photo/lemonade-in-a-jar.jpg?s=612x612&w=0&k=20&c=n2xxx71r1362I6ByJn6rnG4KEsTuF8rUwENvSZNlbYo=",
        },
        {
            "name": "Lemon Iced Tea",
            "desc": "Fresh iced tea with lemon",
            "price": 3.49,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/690507630/photo/mason-jar-glass-of-iced-tea-with-straw-isolated-on-white.jpg?s=612x612&w=0&k=20&c=IQft93o9oxBZeJrCqfuaWD9PxQ23N8jtEFFQhu5MJ40=",
        },
        {
            "name": "Bottled Water",
            "desc": "Still spring water 500ml",
            "price": 1.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/1032678242/photo/water-in-plastic-bottle-on-isolated-white-background.jpg?s=612x612&w=0&k=20&c=w4IhYJwKsaCJmjOqnBlqmdpu0skqNuTpkluUqe1-7vs=",
        },
        {
            "name": "Root Beer (2L)",
            "desc": "Cold refreshing root beer soda in a glass",
            "price": 3.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/1372804127/photo/cold-refreshing-root-beer-soda.jpg?s=612x612&w=0&k=20&c=XzXrVcyaLP5i6fjfyd_iFq_3Are6M-NhRzJFyTiDlqQ=",
        },
    ],
    "Desserts": [
        {
            "name": "Chocolate Lava Cake",
            "desc": "Molten lava cake with ice cream and fresh berries",
            "price": 7.99,
            "prep_time": 8,
            "image": "https://media.istockphoto.com/id/1346128287/photo/chocolate-fondant-cake-molten-lava-cake.jpg?s=612x612&w=0&k=20&c=zX5BNyWrbrBLKqEehMfIXej0hLz8a8eGEPT2naOPHuk=",
        },
        {
            "name": "Cinnamon Twists",
            "desc": "Crispy twists with cinnamon sugar",
            "price": 5.99,
            "prep_time": 5,
            "image": "https://images.unsplash.com/photo-1771677751270-2e7ce50c8716?w=400&q=80",
        },
        {
            "name": "New York Cheesecake",
            "desc": "Strawberry cheesecake with fresh berries",
            "price": 6.99,
            "prep_time": 0,
            "image": "https://media.istockphoto.com/id/179640507/photo/strawberry-cheesecake.jpg?s=612x612&w=0&k=20&c=VKRS8I0OgwWseIXTOP_2_DwRBKgHVHyaAtQl2rDCxeY=",
        },
        {
            "name": "Brownie Bites (6pc)",
            "desc": "Rich fudge brownies dusted with powdered sugar",
            "price": 6.49,
            "prep_time": 0,
            "image": "https://images.unsplash.com/photo-1636743715220-d8f8dd900b87?w=400&q=80",
        },
        {
            "name": "Cookie Dough Bites",
            "desc": "Chocolate chip cookies with chocolate drops",
            "price": 7.49,
            "prep_time": 5,
            "image": "https://media.istockphoto.com/id/526137752/photo/chocolate-chip-cookies-with-mint-and-chocolate-drops.jpg?s=612x612&w=0&k=20&c=obTpor6hPxJH4P_kRLw6O6P2KIRAIC2_4oIf2mMRAiM=",
        },
        {
            "name": "Churros (4pc)",
            "desc": "Churros with a cup of hot chocolate",
            "price": 5.99,
            "prep_time": 5,
            "image": "https://media.istockphoto.com/id/939303754/photo/traditional-spanish-dessert-churros.jpg?s=612x612&w=0&k=20&c=S9AxY35E3feZP-KTDyXLykRuoL7PyhLRAFRukmOTC24=",
        },
        {
            "name": "Apple Pie Bites",
            "desc": "Mini apple pie bites",
            "price": 5.49,
            "prep_time": 4,
            "image": "https://media.istockphoto.com/id/174877838/photo/mini-apple-pie-with-bite-taken-out.jpg?s=612x612&w=0&k=20&c=qQxthC3MBCngz2AOmxVNVjZBfo5IgD2nSwy3YwOZ5HM=",
        },
    ],
}

DELIVERY_ZONES = [
    {"label": "River North", "address": "456 Oak Ave, River North", "zone": "River North", "lat": 41.8925, "lon": -87.6340},
    {"label": "West Loop", "address": "789 State St, West Loop", "zone": "West Loop", "lat": 41.8827, "lon": -87.6474},
    {"label": "Loop", "address": "321 Wacker Dr, Loop", "zone": "Loop", "lat": 41.8869, "lon": -87.6368},
    {"label": "Streeterville", "address": "654 Michigan Ave, Streeterville", "zone": "Streeterville", "lat": 41.8951, "lon": -87.6244},
    {"label": "Gold Coast", "address": "875 N Michigan Ave, Gold Coast", "zone": "Gold Coast", "lat": 41.8988, "lon": -87.6234},
    {"label": "South Loop", "address": "1501 S State St, South Loop", "zone": "South Loop", "lat": 41.8610, "lon": -87.6275},
    {"label": "Old Town", "address": "1540 N Wells St, Old Town", "zone": "Old Town", "lat": 41.9105, "lon": -87.6345},
    {"label": "Lincoln Park", "address": "2400 N Lincoln Ave, Lincoln Park", "zone": "Lincoln Park", "lat": 41.9260, "lon": -87.6490},
]

DRIVERS = {
    "DRV001": {"name": "Mike Rodriguez", "phone": "555-0101", "rating": 4.8, "vehicle": "Honda Civic", "color": "Silver"},
    "DRV002": {"name": "Sarah Chen", "phone": "555-0102", "rating": 4.9, "vehicle": "Toyota Prius", "color": "Blue"},
    "DRV003": {"name": "James Wilson", "phone": "555-0103", "rating": 4.7, "vehicle": "Ford Focus", "color": "Red"},
    "DRV004": {"name": "Emma Thompson", "phone": "555-0104", "rating": 4.9, "vehicle": "Hyundai Elantra", "color": "White"},
}

DRIVER_COLORS = {
    "DRV001": {"emoji": "🔴", "rgba": [255, 59, 48, 255], "hex": "#FF3B30"},
    "DRV002": {"emoji": "🔵", "rgba": [0, 122, 255, 255], "hex": "#007AFF"},
    "DRV003": {"emoji": "🟡", "rgba": [255, 204, 0, 255], "hex": "#FFCC00"},
    "DRV004": {"emoji": "🟢", "rgba": [52, 199, 89, 255], "hex": "#34C759"},
}

DRIVER_COLOR_DEFAULT = {"emoji": "⚪", "rgba": [200, 200, 200, 255], "hex": "#C8C8C8"}

def get_driver_color(driver_id):
    return DRIVER_COLORS.get(driver_id, DRIVER_COLOR_DEFAULT)

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
