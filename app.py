from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import time
import datetime

app = Flask(__name__)

# Register the custom strftime filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(timestamp, fmt='%Y-%m-%d %H:%M:%S'):
    if not isinstance(timestamp, (int, float)):
        return ''
    return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)

DATABASE = "gas.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Routes cho Dashboard chính (GET) ---
@app.route('/')
def index():
    with get_db() as conn:
        # Fetch all data for the dashboard
        products = conn.execute("SELECT * FROM products").fetchall()
        warehouses = conn.execute("SELECT * FROM warehouses").fetchall()
        staffs = conn.execute("SELECT * FROM staffs").fetchall()
        customers = conn.execute("SELECT * FROM customers").fetchall()
        
        inventory = conn.execute("""
            SELECT 
                i.inventory_id,
                p.name AS name,
                w.name AS name,
                i.full_qty,
                i.empty_qty,
                i.updated_at
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN warehouses w ON i.warehouse_id = w.warehouses_id
        """).fetchall()

        orders = conn.execute("""
            SELECT
                o.order_id,
                c.name AS name,
                s.name AS name,
                o.full_price,
                od.order_detail_id
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN staffs s ON o.staff_id = s.staff_id
            JOIN order_detail od ON od.order_detail_id = o.order_detail_id
            ORDER BY o.order_id DESC
        """).fetchall()
    
    return render_template("index.html", products=products, warehouses=warehouses, inventory=inventory, staffs=staffs, customers=customers, orders=orders)

# --- Routes cho Sản phẩm ---
@app.route('/add_product', methods=["POST"])
def add_product():
    name = request.form["name"]
    price = request.form["price"]
    with get_db() as conn:
        conn.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
        conn.commit()
    return redirect("/")

@app.route('/edit_product/<int:product_id>', methods=["POST"])
def edit_product(product_id):
    name = request.form["name"]
    price = request.form["price"]
    with get_db() as conn:
        conn.execute("UPDATE products SET name = ?, price = ? WHERE product_id = ?", (name, price, product_id))
        conn.commit()
    return redirect("/")

@app.route('/delete_product/<int:product_id>', methods=["POST"])
def delete_product(product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
    return redirect("/")

# --- Routes cho Kho hàng (Warehouses) ---
@app.route('/add_warehouse', methods=["POST"])
def add_warehouse():
    name = request.form["name"]
    address = request.form["address"]
    with get_db() as conn:
        conn.execute("INSERT INTO warehouses (name, address) VALUES (?, ?)", (name, address))
        conn.commit()
    return redirect("/")

@app.route('/edit_warehouse/<int:warehouse_id>', methods=["POST"])
def edit_warehouse(warehouse_id):
    name = request.form["name"]
    address = request.form["address"]
    with get_db() as conn:
        conn.execute("UPDATE warehouses SET name = ?, address = ? WHERE warehouses_id = ?", (name, address, warehouse_id))
        conn.commit()
    return redirect("/")

@app.route('/delete_warehouse/<int:warehouse_id>', methods=["POST"])
def delete_warehouse(warehouse_id):
    with get_db() as conn:
        conn.execute("DELETE FROM warehouses WHERE warehouses_id = ?", (warehouse_id,))
        conn.commit()
    return redirect("/")

# --- Routes cho Tồn kho (Inventory) ---
@app.route('/add_inventory', methods=["POST"])
def add_inventory():
    product_id = request.form["product_id"]
    warehouse_id = request.form["warehouse_id"]
    full_qty = request.form["full_qty"]
    empty_qty = request.form["empty_qty"]
    updated_at = int(time.time())
    
    with get_db() as conn:
        existing_inventory = conn.execute("SELECT * FROM inventory WHERE product_id = ? AND warehouse_id = ?", (product_id, warehouse_id)).fetchone()
        
        if existing_inventory:
            conn.execute("UPDATE inventory SET full_qty = ?, empty_qty = ?, updated_at = ? WHERE product_id = ? AND warehouse_id = ?", (full_qty, empty_qty, updated_at, product_id, warehouse_id))
        else:
            conn.execute("INSERT INTO inventory (product_id, warehouse_id, full_qty, empty_qty, updated_at) VALUES (?, ?, ?, ?, ?)", (product_id, warehouse_id, full_qty, empty_qty, updated_at))
        conn.commit()
    return redirect("/")

@app.route('/delete_inventory/<int:inventory_id>', methods=["POST"])
def delete_inventory(inventory_id):
    with get_db() as conn:
        conn.execute("DELETE FROM inventory WHERE inventory_id = ?", (inventory_id,))
        conn.commit()
    return redirect("/")

# --- Routes cho Khách hàng (Customers) ---
@app.route('/add_customer', methods=["POST"])
def add_customer():
    name = request.form["name"]
    phone = request.form["phone"]
    address = request.form["address"]
    with get_db() as conn:
        conn.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", (name, phone, address))
        conn.commit()
    return redirect("/")

@app.route('/delete_customer/<int:customer_id>', methods=["POST"])
def delete_customer(customer_id):
    with get_db() as conn:
        conn.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        conn.commit()
    return redirect("/")

# --- Routes cho Nhân viên (Staffs) ---
@app.route('/add_staff', methods=["POST"])
def add_staff():
    name = request.form["name"]
    phone = request.form["phone"]
    with get_db() as conn:
        conn.execute("INSERT INTO staffs (name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
    return redirect("/")

@app.route('/delete_staff/<int:staff_id>', methods=["POST"])
def delete_staff(staff_id):
    with get_db() as conn:
        conn.execute("DELETE FROM staffs WHERE staff_id = ?", (staff_id,))
        conn.commit()
    return redirect("/")

# --- Routes cho Đơn hàng (Orders) và Chi tiết Đơn hàng (Order Details) ---
@app.route('/add_order', methods=["POST"])
def add_order():
    customer_id = request.form["customer_id"]
    staff_id = request.form["staff_id"]
    full_price = request.form["full_price"]
    created_at = int(time.time())
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (customer_id, staff_id, full_price) VALUES (?, ?, ?, ?)", (customer_id, staff_id, full_price, created_at))
        order_id = cursor.lastrowid
        
        # Thêm chi tiết đơn hàng
        product_id = request.form["product_id"]
        number = request.form["number"]
        
        # Lấy inventory_id từ product_id
        inventory_id = cursor.execute("SELECT inventory_id FROM inventory WHERE product_id = ?", (product_id,)).fetchone()
        
        if inventory_id:
            cursor.execute("INSERT INTO order_detail (order_id, inventory_id, number, time) VALUES (?, ?, ?, ?)", (order_id, inventory_id['inventory_id'], number, created_at))
        
        conn.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)