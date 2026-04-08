import resend
resend.api_key = os.environ.get("re_KJCqmhWT_AkQT9pprww9kpCE2wWPru7mX")
import os

from flask import Flask, render_template, jsonify, request
from database import get_db, init_db, seed_products

app = Flask(__name__)

# Initialize DB (only in production)
if __name__ != "__main__":
    init_db()
    seed_products()

# ── EMAIL FUNCTION ─────────────────────────────────────────────
def send_order_email(order_data):
    try:
        response = resend.Emails.send({
            "from": "<onboarding@resend.dev>",
            "to": ["luis.moncada@alkira.net"],  # <-- PUT YOUR EMAIL HERE
            "subject": "🛒 New Swag Order",
            "html": f"""
                <h2>New Alkira Swag Order 🚀</h2>

                <p><strong>Name:</strong> {order_data.get("first_name")} {order_data.get("last_name")}</p>
                <p><strong>Email:</strong> {order_data.get("email")}</p>
                <p><strong>Department:</strong> {order_data.get("department")}</p>

                <p><strong>Items:</strong> {order_data.get("items")}</p>
                <p><strong>Total:</strong> {order_data.get("total")}</p>
            """
        })

        print("✅ Email sent:", response)

    except Exception as e:
        print("❌ Email failed:", e)

# ── Public shop ───────────────────────────────────────────────
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

    # ✅ SEND EMAIL AFTER ORDER
    send_order_email(data)

    return jsonify({"status": "ok"})

# ── Admin panel ───────────────────────────────────────────────
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
    data = request.json
    new_status = data.get("status", "pending")
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, oid))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})