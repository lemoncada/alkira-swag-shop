import os
import json
import time
import resend

from flask import Flask, render_template, jsonify, request
from database import get_db, init_db, seed_products

app = Flask(__name__)

# ── ENV VAR VALIDATION ────────────────────────────────────────
_resend_api_key = os.environ.get("RESEND_API_KEY")
if _resend_api_key:
    resend.api_key = _resend_api_key
    print("[EMAIL] RESEND_API_KEY loaded.")
else:
    print("[EMAIL] WARNING: RESEND_API_KEY is not set. Emails will be skipped.")

if not os.environ.get("DATABASE_URL"):
    print("[DB] WARNING: DATABASE_URL is not set. Database calls will fail.")

# Initialize DB with retries (only in production/gunicorn)
if __name__ != "__main__":
    for attempt in range(5):
        try:
            init_db()
            seed_products()
            print("[DB] Initialized successfully.")
            break
        except Exception as e:
            print(f"[DB] Attempt {attempt + 1}/5 failed: {e}")
            if attempt < 4:
                time.sleep(3)
            else:
                raise

# ── EMAIL FUNCTION ─────────────────────────────────────────────
def send_order_email(order_data):
    if not os.environ.get("RESEND_API_KEY"):
        print("[EMAIL] Skipping email — RESEND_API_KEY is not configured.")
        return
    try:
        from datetime import datetime
        items = order_data.get("items", [])
        if isinstance(items, str):
            items = json.loads(items)

        items_rows = "".join(
            f"""<tr>
                  <td style="padding:8px 12px;border-bottom:1px solid #eee;">{item.get('name','—')}</td>
                  <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:center;">{item.get('qty', item.get('quantity', 1))}</td>
                  <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;">${item.get('price', 0):.2f}</td>
                </tr>"""
            for item in items
        )

        order_date = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
        total = order_data.get("total", 0)
        ref = order_data.get("order_ref", "N/A")

        response = resend.Emails.send({
            "from": "Alkira Swag <onboarding@resend.dev>",
            "to": ["luis.moncada@alkira.net"],
            "subject": f"🛒 New Swag Order — {order_data.get('first_name')} {order_data.get('last_name')} ({order_data.get('department')})",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#222;">

              <div style="background:#1a1a2e;padding:24px 32px;border-radius:8px 8px 0 0;">
                <h1 style="color:#fff;margin:0;font-size:22px;">🛒 New Swag Order</h1>
                <p style="color:#aaa;margin:4px 0 0;">Order Ref: <strong style="color:#fff;">{ref}</strong> &nbsp;|&nbsp; {order_date}</p>
              </div>

              <div style="background:#f9f9f9;padding:24px 32px;">

                <h3 style="margin:0 0 12px;border-bottom:2px solid #1a1a2e;padding-bottom:6px;">👤 Customer Details</h3>
                <table style="width:100%;border-collapse:collapse;font-size:15px;">
                  <tr><td style="padding:5px 0;color:#555;width:140px;">Name</td><td><strong>{order_data.get('first_name')} {order_data.get('last_name')}</strong></td></tr>
                  <tr><td style="padding:5px 0;color:#555;">Email</td><td>{order_data.get('email')}</td></tr>
                  <tr><td style="padding:5px 0;color:#555;">Department</td><td>{order_data.get('department')}</td></tr>
                  <tr><td style="padding:5px 0;color:#555;">Purpose</td><td>{order_data.get('purpose') or '—'}</td></tr>
                </table>

                <h3 style="margin:24px 0 12px;border-bottom:2px solid #1a1a2e;padding-bottom:6px;">📦 Ship To</h3>
                <p style="margin:0;font-size:15px;line-height:1.6;">{(order_data.get('address') or '—').replace(chr(10), '<br>')}</p>

                <h3 style="margin:24px 0 12px;border-bottom:2px solid #1a1a2e;padding-bottom:6px;">🧾 Items Ordered</h3>
                <table style="width:100%;border-collapse:collapse;font-size:15px;">
                  <thead>
                    <tr style="background:#1a1a2e;color:#fff;">
                      <th style="padding:8px 12px;text-align:left;">Item</th>
                      <th style="padding:8px 12px;text-align:center;">Qty</th>
                      <th style="padding:8px 12px;text-align:right;">Price</th>
                    </tr>
                  </thead>
                  <tbody>{items_rows}</tbody>
                  <tfoot>
                    <tr style="background:#eee;">
                      <td colspan="2" style="padding:10px 12px;font-weight:bold;text-align:right;">Total</td>
                      <td style="padding:10px 12px;font-weight:bold;text-align:right;">${total:.2f}</td>
                    </tr>
                  </tfoot>
                </table>

                {"<h3 style='margin:24px 0 12px;border-bottom:2px solid #1a1a2e;padding-bottom:6px;'>📝 Notes</h3><p style='margin:0;font-size:15px;'>" + order_data.get('notes') + "</p>" if order_data.get('notes') else ""}

              </div>

              <div style="background:#1a1a2e;padding:18px 32px;border-radius:0 0 8px 8px;text-align:center;">
                <p style="color:#fff;margin:0;font-size:14px;">✅ This is a verified order from the <strong>Alkira Swag Shop</strong></p>
                <p style="color:#aaa;margin:6px 0 0;font-size:12px;">Cheers, The Alkira Swag System 🎉 &nbsp;|&nbsp; alkira-swag-shop.onrender.com</p>
              </div>

            </div>
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
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    cur.execute("SELECT * FROM products WHERE active = 1 ORDER BY type, category, name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/orders", methods=["POST"])
def api_orders():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (order_ref, first_name, last_name, email,
                            department, purpose, address, items, total, notes, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')
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
    cur.close()
    conn.close()

    send_order_email(data)
    return jsonify({"status": "ok"})

# ── Admin panel ───────────────────────────────────────────────
@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/admin/products", methods=["GET"])
def admin_products():
    conn = get_db()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    cur.execute("SELECT * FROM products ORDER BY type, name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/admin/products/<int:pid>", methods=["POST"])
def admin_update_product(pid):
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE products
        SET type=%s, category=%s, name=%s, description=%s, price=%s, active=%s, image_url=%s, sizes=%s
        WHERE id=%s
    """, (
        data["type"], data["category"], data["name"],
        data["description"], data["price"], data["active"],
        data.get("image_url", ""), data.get("sizes", ""),
        pid
    ))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/admin/products/new", methods=["POST"])
def admin_new_product():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (type, category, name, description, price, icon, active, image_url, sizes)
        VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s)
    """, (
        data["type"], data["category"], data["name"],
        data["description"], data["price"], data.get("icon", "📦"),
        data.get("image_url", ""), data.get("sizes", "")
    ))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/admin/orders")
def admin_orders():
    conn = get_db()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
def admin_order_status(oid):
    data = request.json
    new_status = data.get("status", "pending")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, oid))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"})
