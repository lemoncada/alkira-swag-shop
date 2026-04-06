import sqlite3

DB = "swag.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # Create base tables if they don't exist yet
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            icon TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_ref TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            department TEXT,
            purpose TEXT,
            address TEXT,
            items TEXT,
            total REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Migrations: safely add new columns to existing databases ──
    prod_cols = [row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()]
    if 'image_url' not in prod_cols:
        conn.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
    if 'sizes' not in prod_cols:
        conn.execute("ALTER TABLE products ADD COLUMN sizes TEXT")

    order_cols = [row[1] for row in conn.execute("PRAGMA table_info(orders)").fetchall()]
    if 'status' not in order_cols:
        conn.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending'")

    conn.commit()
    conn.close()

def seed_products():
    """Run once to load your existing products into the DB."""
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    products = [
        ('hq',     'Apparel',     'Classic Alkira T-Shirt',   'Soft 100% cotton tee with embroidered Alkira logo. Available S–3XL.',       15,  '👕'),
        ('hq',     'Apparel',     'Zip-Up Hoodie',            'Heavyweight fleece hoodie with chest logo and sleeve wordmark.',             45,  '🧥'),
        ('hq',     'Accessories', 'Structured Baseball Cap',  'Six-panel structured cap with embroidered Alkira logo.',                     20,  '🧢'),
        ('hq',     'Drinkware',   'Insulated Water Bottle',   '20oz stainless steel. Keeps cold 24h, hot 12h. Alkira branded.',             25,  '🧴'),
        ('hq',     'Accessories', 'Canvas Tote Bag',          'Heavy-duty natural canvas with Alkira screen print.',                        18,  '🛍'),
        ('hq',     'Stationery',  'Sticker Pack (10 pcs)',    'Die-cut Alkira stickers, perfect for laptops and bottles.',                   5,  '🏷'),
        ('vendor', 'Apparel',     'Performance Polo',         'Moisture-wicking polo with embroidered Alkira logo. Great for events.',      35,  '👔'),
        ('vendor', 'Tech',        'Laptop Sleeve 15"',        'Neoprene sleeve with Alkira branding and accessory pocket.',                 40,  '💻'),
        ('vendor', 'Stationery',  'Hardcover Notebook',       'A5 hardcover, 192 ruled pages, debossed Alkira cover.',                      15,  '📓'),
        ('vendor', 'Tech',        'Wireless Charging Pad',    '10W Qi pad with engraved Alkira logo. USB-C powered.',                       55,  '🔋'),
        ('vendor', 'Accessories', 'Tech Organizer',           'Cable and gadget travel bag with Alkira branding.',                          65,  '🎒'),
        ('vendor', 'Accessories', 'Branded Umbrella',         'Auto-open windproof umbrella with full-panel Alkira print.',                 30,  '☂️'),
    ]
    conn.executemany(
        "INSERT INTO products (type, category, name, description, price, icon) VALUES (?,?,?,?,?,?)",
        products
    )
    conn.commit()
    conn.close()