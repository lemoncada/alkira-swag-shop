import json
from flask import Flask, render_template, jsonify, request
from database import get_db, init_db, seed_products

app = Flask(__name__)

init_db()
seed_products()

# ── Public shop ───────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/products")
def api_products():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM products WHERE active = 1 ORDER BY type, category, name"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/orders", methods=["POST"])
def api_orders():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO orders (order_ref, first_name, last_name, email,
                            department, purpose, address, items, total, notes, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,'pending')
    """, (
        data.get("order_ref"),
        data.get("first_name"),
        data.get("last_name"),
        data.get("email"),
        data.get("department"),
        data.get("purpose"),
        data.get("address"),
        json.dumps(data.get("items", [])),
        data.get("total"),
        data.get("notes"),
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# ── Admin panel ───────────────────────────────────────────────────────────────
@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/admin/products", methods=["GET"])
def admin_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY type, name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/admin/products/<int:pid>", methods=["POST"])
def admin_update_product(pid):
    data = request.json
    conn = get_db()
    conn.execute("""
        UPDATE products
        SET type=?, category=?, name=?, description=?, price=?, active=?, image_url=?, sizes=?
        WHERE id=?
    """, (
        data["type"], data["category"], data["name"],
        data["description"], data["price"], data["active"],
        data.get("image_url", ""), data.get("sizes", ""),
        pid
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/admin/products/new", methods=["POST"])
def admin_new_product():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO products (type, category, name, description, price, icon, active, image_url, sizes)
        VALUES (?,?,?,?,?,?,1,?,?)
    """, (
        data["type"], data["category"], data["name"],
        data["description"], data["price"], data.get("icon", "📦"),
        data.get("image_url", ""), data.get("sizes", "")
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/admin/orders")
def admin_orders():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
def admin_order_status(oid):
    """Update order status: pending | fulfilled | archived"""
    data = request.json
    new_status = data.get("status", "pending")
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, oid))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5001)