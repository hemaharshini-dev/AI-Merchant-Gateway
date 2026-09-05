import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal, engine
from models.models import Base, Merchant, Product, AIBuyer

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Merchant).first():
        print("Database already seeded.")
        db.close()
        return

    # --- Merchant ---
    merchant = Merchant(
        id="merchant_techkart",
        name="TechKart",
        currency="INR",
        policies={
            "max_transaction_amount": 10000,
            "daily_spending_limit": 30000,
            "max_quantity": 5,
            "allowed_categories": ["Electronics", "Office Equipment"],
            "max_discount_percent": 10,
            "human_approval_threshold": 7500
        }
    )
    db.add(merchant)

    # --- AI Buyer ---
    buyer = AIBuyer(
        id="buyer_office_agent",
        name="Office Procurement Agent",
        spending_limits={"per_transaction": 10000, "daily": 30000},
        permitted_categories=["Electronics", "Office Equipment"]
    )
    db.add(buyer)

    # --- Products ---
    products = [
        # Keyboards
        Product(id="prod_kb_001", merchant_id="merchant_techkart", name="MechPro Wireless Keyboard", description="Mechanical wireless keyboard with RGB backlight", category="Office Equipment", price=2499, inventory=25, attributes={"type": "mechanical", "connectivity": "wireless", "backlight": "RGB"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["keyboard", "wireless", "mechanical"]),
        Product(id="prod_kb_002", merchant_id="merchant_techkart", name="SlimType Wireless Keyboard", description="Slim membrane wireless keyboard", category="Office Equipment", price=1299, inventory=40, attributes={"type": "membrane", "connectivity": "wireless", "backlight": "none"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["keyboard", "wireless", "membrane"]),
        Product(id="prod_kb_003", merchant_id="merchant_techkart", name="TypeMaster Wired Keyboard", description="Full-size wired mechanical keyboard", category="Office Equipment", price=1799, inventory=30, attributes={"type": "mechanical", "connectivity": "wired", "backlight": "white"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["keyboard", "wired", "mechanical"]),
        Product(id="prod_kb_004", merchant_id="merchant_techkart", name="ErgoFlex Ergonomic Keyboard", description="Split ergonomic wireless keyboard", category="Office Equipment", price=3999, inventory=15, attributes={"type": "ergonomic", "connectivity": "wireless", "backlight": "none"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["keyboard", "wireless", "ergonomic"]),

        # Mice
        Product(id="prod_ms_001", merchant_id="merchant_techkart", name="SilentClick Wireless Mouse", description="Silent wireless optical mouse", category="Office Equipment", price=899, inventory=50, attributes={"connectivity": "wireless", "dpi": "1600", "silent": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["mouse", "wireless", "silent"]),
        Product(id="prod_ms_002", merchant_id="merchant_techkart", name="PrecisionPro Gaming Mouse", description="High-DPI gaming mouse with RGB", category="Electronics", price=1999, inventory=20, attributes={"connectivity": "wired", "dpi": "16000", "rgb": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["mouse", "wired", "gaming"]),
        Product(id="prod_ms_003", merchant_id="merchant_techkart", name="ErgoGrip Vertical Mouse", description="Ergonomic vertical wireless mouse", category="Office Equipment", price=1499, inventory=18, attributes={"connectivity": "wireless", "dpi": "2400", "ergonomic": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["mouse", "wireless", "ergonomic"]),

        # Mouse Pads
        Product(id="prod_mp_001", merchant_id="merchant_techkart", name="DeskMate XL Mouse Pad", description="Extra-large desk mouse pad", category="Office Equipment", price=499, inventory=60, attributes={"size": "XL", "material": "cloth"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["mousepad", "accessories", "desk"]),
        Product(id="prod_mp_002", merchant_id="merchant_techkart", name="HardSurface Pro Mouse Pad", description="Hard surface precision mouse pad", category="Office Equipment", price=699, inventory=35, attributes={"size": "medium", "material": "hard"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["mousepad", "accessories"]),

        # Monitors
        Product(id="prod_mn_001", merchant_id="merchant_techkart", name="ViewPro 24\" FHD Monitor", description="24 inch Full HD IPS monitor", category="Electronics", price=8999, inventory=10, attributes={"size": "24 inch", "resolution": "1920x1080", "panel": "IPS", "refresh_rate": "75Hz"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="14 days", tags=["monitor", "display", "FHD"]),
        Product(id="prod_mn_002", merchant_id="merchant_techkart", name="ViewPro 27\" QHD Monitor", description="27 inch Quad HD IPS monitor", category="Electronics", price=14999, inventory=8, attributes={"size": "27 inch", "resolution": "2560x1440", "panel": "IPS", "refresh_rate": "144Hz"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["monitor", "display", "QHD"]),
        Product(id="prod_mn_003", merchant_id="merchant_techkart", name="UltraWide 29\" Monitor", description="29 inch ultrawide curved monitor", category="Electronics", price=18999, inventory=5, attributes={"size": "29 inch", "resolution": "2560x1080", "panel": "VA", "curved": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore"]}, return_policy="14 days", tags=["monitor", "display", "ultrawide"]),

        # Laptops
        Product(id="prod_lp_001", merchant_id="merchant_techkart", name="SwiftBook Pro 15", description="15.6 inch laptop with 16GB RAM, 512GB SSD", category="Electronics", price=64999, inventory=7, attributes={"ram": "16GB", "storage": "512GB SSD", "processor": "Intel i7", "display": "15.6 inch FHD"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["laptop", "computer"]),
        Product(id="prod_lp_002", merchant_id="merchant_techkart", name="SwiftBook Air 13", description="13.3 inch ultrabook with 8GB RAM, 256GB SSD", category="Electronics", price=44999, inventory=12, attributes={"ram": "8GB", "storage": "256GB SSD", "processor": "Intel i5", "display": "13.3 inch FHD"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["laptop", "computer", "ultrabook"]),
        Product(id="prod_lp_003", merchant_id="merchant_techkart", name="PowerDesk 16 Workstation", description="16 inch workstation laptop with 32GB RAM", category="Electronics", price=89999, inventory=4, attributes={"ram": "32GB", "storage": "1TB SSD", "processor": "Intel i9", "display": "16 inch 4K"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="7 days", tags=["laptop", "workstation", "computer"]),

        # Headphones
        Product(id="prod_hp_001", merchant_id="merchant_techkart", name="FocusSound ANC Headphones", description="Active noise cancelling wireless headphones", category="Electronics", price=3499, inventory=22, attributes={"connectivity": "wireless", "anc": True, "battery": "30 hours"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["headphones", "wireless", "anc", "audio"]),
        Product(id="prod_hp_002", merchant_id="merchant_techkart", name="ClearVoice USB Headset", description="USB headset with microphone for calls", category="Office Equipment", price=1299, inventory=35, attributes={"connectivity": "USB", "microphone": True, "type": "on-ear"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["headset", "microphone", "usb", "calls"]),
        Product(id="prod_hp_003", merchant_id="merchant_techkart", name="BassMax Wireless Earbuds", description="True wireless earbuds with charging case", category="Electronics", price=1999, inventory=28, attributes={"connectivity": "bluetooth", "battery": "6 hours", "case_battery": "24 hours"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["earbuds", "wireless", "bluetooth", "audio"]),

        # Webcams
        Product(id="prod_wc_001", merchant_id="merchant_techkart", name="ClearCam 1080p Webcam", description="Full HD webcam with built-in microphone", category="Office Equipment", price=1799, inventory=20, attributes={"resolution": "1080p", "fps": "30", "microphone": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["webcam", "camera", "video calls"]),
        Product(id="prod_wc_002", merchant_id="merchant_techkart", name="ProStream 4K Webcam", description="4K webcam with autofocus and ring light", category="Office Equipment", price=4999, inventory=10, attributes={"resolution": "4K", "fps": "30", "autofocus": True, "ring_light": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["webcam", "camera", "4K", "streaming"]),

        # USB Hubs & Docks
        Product(id="prod_uh_001", merchant_id="merchant_techkart", name="PortExpand 7-in-1 USB Hub", description="USB-C hub with HDMI, USB-A, SD card reader", category="Office Equipment", price=1499, inventory=30, attributes={"ports": 7, "usb_c": True, "hdmi": True, "sd_card": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["usb hub", "accessories", "usb-c"]),
        Product(id="prod_uh_002", merchant_id="merchant_techkart", name="DeskDock Pro 12-in-1", description="Full docking station with dual HDMI", category="Office Equipment", price=3999, inventory=12, attributes={"ports": 12, "dual_hdmi": True, "ethernet": True, "usb_c_pd": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["dock", "accessories", "usb-c", "dual monitor"]),

        # Chargers & Power
        Product(id="prod_ch_001", merchant_id="merchant_techkart", name="FastCharge 65W GaN Charger", description="65W GaN USB-C charger, 3-port", category="Electronics", price=1299, inventory=45, attributes={"wattage": "65W", "ports": 3, "technology": "GaN"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["charger", "usb-c", "accessories"]),
        Product(id="prod_ch_002", merchant_id="merchant_techkart", name="PowerBank Ultra 20000mAh", description="20000mAh power bank with fast charging", category="Electronics", price=1999, inventory=25, attributes={"capacity": "20000mAh", "fast_charge": True, "ports": 3}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["powerbank", "accessories", "charging"]),

        # Desk Accessories
        Product(id="prod_da_001", merchant_id="merchant_techkart", name="AdjustDesk Monitor Stand", description="Adjustable monitor riser with storage", category="Office Equipment", price=899, inventory=20, attributes={"adjustable": True, "material": "aluminium", "storage": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["monitor stand", "desk", "accessories"]),
        Product(id="prod_da_002", merchant_id="merchant_techkart", name="LaptopRise Aluminium Stand", description="Portable aluminium laptop stand", category="Office Equipment", price=1199, inventory=28, attributes={"material": "aluminium", "foldable": True, "adjustable": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["laptop stand", "desk", "accessories"]),
        Product(id="prod_da_003", merchant_id="merchant_techkart", name="CableOrganizer Pro Kit", description="Cable management kit for desk setup", category="Office Equipment", price=399, inventory=55, attributes={"pieces": 20, "reusable": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["cable management", "desk", "accessories"]),
        Product(id="prod_da_004", merchant_id="merchant_techkart", name="WristRest Keyboard Pad", description="Memory foam wrist rest for keyboard", category="Office Equipment", price=499, inventory=40, attributes={"material": "memory foam", "size": "full"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["wrist rest", "keyboard", "accessories", "ergonomic"]),

        # Printers
        Product(id="prod_pr_001", merchant_id="merchant_techkart", name="PrintMate Inkjet Printer", description="Wireless inkjet printer for home office", category="Office Equipment", price=5999, inventory=8, attributes={"type": "inkjet", "connectivity": "wireless", "color": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="14 days", tags=["printer", "office"]),
        Product(id="prod_pr_002", merchant_id="merchant_techkart", name="LaserJet Compact Printer", description="Compact monochrome laser printer", category="Office Equipment", price=7999, inventory=6, attributes={"type": "laser", "connectivity": "USB", "color": False}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["printer", "laser", "office"]),

        # Tablets
        Product(id="prod_tb_001", merchant_id="merchant_techkart", name="TabPro 10 Drawing Tablet", description="10 inch graphics drawing tablet", category="Electronics", price=3999, inventory=14, attributes={"size": "10 inch", "pressure_levels": 8192, "wireless": False}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["tablet", "drawing", "graphics"]),

        # Networking
        Product(id="prod_nw_001", merchant_id="merchant_techkart", name="DualBand WiFi Router", description="AC1200 dual band wireless router", category="Electronics", price=2499, inventory=15, attributes={"speed": "AC1200", "bands": 2, "antennas": 4}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="14 days", tags=["router", "networking", "wifi"]),
        Product(id="prod_nw_002", merchant_id="merchant_techkart", name="USB WiFi Adapter 600Mbps", description="Compact USB WiFi adapter", category="Electronics", price=699, inventory=35, attributes={"speed": "600Mbps", "bands": 2, "usb": "USB 3.0"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["wifi adapter", "networking", "usb"]),

        # Storage
        Product(id="prod_st_001", merchant_id="merchant_techkart", name="PortableSSD 1TB", description="USB-C portable SSD 1TB", category="Electronics", price=5999, inventory=18, attributes={"capacity": "1TB", "interface": "USB-C", "speed": "540MB/s"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi"]}, return_policy="7 days", tags=["ssd", "storage", "portable"]),
        Product(id="prod_st_002", merchant_id="merchant_techkart", name="USB Flash Drive 64GB", description="USB 3.0 flash drive 64GB", category="Electronics", price=399, inventory=70, attributes={"capacity": "64GB", "interface": "USB 3.0"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["flash drive", "storage", "usb"]),
        Product(id="prod_st_003", merchant_id="merchant_techkart", name="NAS Drive 4TB", description="4TB network attached storage drive", category="Electronics", price=8499, inventory=6, attributes={"capacity": "4TB", "interface": "ethernet", "raid": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["nas", "storage", "network"]),

        # Speakers
        Product(id="prod_sp_001", merchant_id="merchant_techkart", name="DeskSound Bluetooth Speaker", description="Compact Bluetooth speaker for desk", category="Electronics", price=1499, inventory=22, attributes={"connectivity": "bluetooth", "battery": "12 hours", "waterproof": False}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["speaker", "bluetooth", "audio"]),
        Product(id="prod_sp_002", merchant_id="merchant_techkart", name="StudioMonitor 2.1 Speakers", description="2.1 channel desktop studio speakers", category="Electronics", price=3999, inventory=10, attributes={"channels": "2.1", "connectivity": "3.5mm + USB", "wattage": "40W"}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai"]}, return_policy="14 days", tags=["speaker", "studio", "audio", "desktop"]),

        # Smart Devices
        Product(id="prod_sd_001", merchant_id="merchant_techkart", name="SmartPlug WiFi 16A", description="WiFi smart plug with energy monitoring", category="Electronics", price=799, inventory=40, attributes={"ampere": "16A", "wifi": True, "energy_monitor": True}, shipping={"available": True, "cities": ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai"]}, return_policy="7 days", tags=["smart plug", "smart home", "wifi"]),
    ]

    db.add_all(products)
    db.commit()
    db.close()
    print(f"Seeded: 1 merchant, {len(products)} products, 1 AI buyer.")

if __name__ == "__main__":
    seed()
