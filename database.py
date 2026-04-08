import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            icon TEXT,
            active INTEGER DEFAULT 1,
            image_url TEXT,
            sizes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
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
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def seed_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    existing = cur.fetchone()[0]
    if existing > 0:
        cur.close()
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
    cur.executemany(
        "INSERT INTO products (type, category, name, description, price, icon) VALUES (%s,%s,%s,%s,%s,%s)",
        products
    )
    conn.commit()
    cur.close()
    conn.close()
