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

def setup_db():
    with get_db() as conn:
        # Create all tables if they do not exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "products" (
                "product_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "name" TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "prices_history" (
                "price_history_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "product_id" INTEGER,
                "time" INTEGER,
                "price" REAL,
                FOREIGN KEY("product_id") REFERENCES "products"("product_id")
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "warehouses" (
                "warehouses_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "name" TEXT NOT NULL,
                "address" TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "inventory" (
                "inventory_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "product_id" INTEGER,
                "warehouse_id" INTEGER,
                "full_qty" INTEGER,
                "empty_qty" INTEGER,
                "updated_at" INTEGER,
                FOREIGN KEY("product_id") REFERENCES "products"("product_id"),
                FOREIGN KEY("warehouse_id") REFERENCES "warehouses"("warehouses_id")
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "staffs" (
                "staff_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "name" TEXT,
                "phone" TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "customers" (
                "customer_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "name" TEXT,
                "phone" TEXT,
                "address" TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "orders" (
                "order_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "customer_id" INTEGER,
                "staff_id" INTEGER,
                "full_price" REAL,
                "created_at" INTEGER,
                FOREIGN KEY("customer_id") REFERENCES "customers"("customer_id"),
                FOREIGN KEY("staff_id") REFERENCES "staffs"("staff_id")
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS "order_detail" (
                "order_detail_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "order_id" INTEGER,
                "inventory_id" INTEGER,
                "number" INTEGER,
                "time" INTEGER,
                "price_history_id" INTEGER,
                FOREIGN KEY("order_id") REFERENCES "orders"("order_id"),
                FOREIGN KEY("inventory_id") REFERENCES "inventory"("inventory_id"),
                FOREIGN KEY("price_history_id") REFERENCES "prices_history"("price_history_id")
            )
        """)
        conn.commit()

# --- Routes cho Dashboard chính (GET) ---
@app.route('/')
def index():
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
        warehouses = conn.execute("SELECT * FROM warehouses").fetchall()
        staffs = conn.execute("SELECT * FROM staffs").fetchall()
        customers = conn.execute("SELECT * FROM customers").fetchall()
        
        inventory = conn.execute("""
            SELECT 
                i.inventory_id,
                p.name AS product_name,
                w.name AS warehouse_name,
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
                c.name AS customer_name,
                s.name AS staff_name,
                o.full_price,
                o.created_at
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN staffs s ON o.staff_id = s.staff_id
            ORDER BY o.order_id DESC
        """).fetchall()

        prices_history = conn.execute("""
            SELECT
                ph.price_history_id,
                p.name AS product_name,
                ph.price,
                ph.time
            FROM prices_history ph
            JOIN products p ON ph.product_id = p.product_id
            ORDER BY ph.time DESC
        """).fetchall()
    
    return render_template("index.html", products=products, warehouses=warehouses, inventory=inventory, staffs=staffs, customers=customers, orders=orders, prices_history=prices_history)

# --- Routes cho Sản phẩm ---
@app.route('/add_product', methods=["POST"])
def add_product():
    name = request.form["name"]
    type = request.form["type"]
    with get_db() as conn:
        conn.execute("INSERT INTO products (name, type) VALUES (?, ?)", (name,type))
        conn.commit()
    return redirect("/")

@app.route('/edit_product/<int:product_id>', methods=["POST"])
def edit_product(product_id):
    name = request.form["name"]
    with get_db() as conn:
        conn.execute("UPDATE products SET name = ? WHERE product_id = ?", (name, product_id))
        conn.commit()
    return redirect("/")

@app.route('/delete_product/<int:product_id>', methods=["POST"])
def delete_product(product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
    return redirect("/")

@app.route('/add_price_history/<int:product_id>', methods=["POST"])
def add_price_history(product_id):
    price = request.form["price"]
    current_time = int(time.time())
    with get_db() as conn:
        conn.execute("INSERT INTO prices_history (product_id, price, time) VALUES (?, ?, ?)", (product_id, price, current_time))
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
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Step 1: Insert new order
        cursor.execute("INSERT INTO orders (customer_id, staff_id, full_price, created_at) VALUES (?, ?, ?, ?)", (customer_id, staff_id, 0, int(time.time())))
        order_id = cursor.lastrowid

        # Step 2: Handle product details and total price
        product_ids = request.form.getlist("product_id[]")
        numbers = request.form.getlist("number[]")
        prices = request.form.getlist("price[]")
        
        total_price = 0

        for i in range(len(product_ids)):
            product_id = product_ids[i]
            number = int(numbers[i])
            price = float(prices[i])

            # Get the inventory_id, full_qty, and empty_qty for the product
            inventory_row = cursor.execute("SELECT i.inventory_id, i.full_qty, i.empty_qty, p.type FROM inventory i JOIN products p ON i.product_id = p.product_id WHERE i.product_id = ?", (product_id,)).fetchone()
            # BƯỚC MỚI: Kiểm tra giá trong tháng hiện tại
            check_price_row = cursor.execute("""
                    SELECT price 
                    FROM prices_history 
                    WHERE product_id = ? 
                    AND strftime('%Y-%m', time, 'unixepoch') = strftime('%Y-%m', 'now')
                    ORDER BY time DESC 
                    LIMIT 1
                """, (product_id,)).fetchone()

            if inventory_row:
                inventory_id = inventory_row['inventory_id']
                current_qty = inventory_row['full_qty']
                current_empty_qty = inventory_row['empty_qty']
                product_type = inventory_row['type']
                
                # So sánh và chèn giá
                price_history_id = None
                # Nếu chưa có giá nào trong tháng hoặc giá hiện tại khác với giá cũ nhất
                if check_price_row is None or check_price_row['price'] != price:
                    # Insert giá mới
                    cursor.execute("INSERT INTO prices_history (product_id, price, time) VALUES (?, ?, ?)", (product_id, price, int(time.time())))
                    price_history_id = cursor.lastrowid
                """else:
                    # Nếu giá không đổi, lấy ID của bản ghi giá hiện có
                    price_history_id = cursor.execute("SELECT price_history_id FROM prices_history WHERE product_id = ? ORDER BY time DESC LIMIT 1", (product_id,)).fetchone()['price_history_id']"""

                # Insert order detail
                cursor.execute("INSERT INTO order_detail (order_id, inventory_id, number, time, price_history_id) VALUES (?, ?, ?, ?, ?)", (order_id, inventory_id, number, int(time.time()), price_history_id))
                
                total_price += number * price
                
                if product_type == 'Gas':
                    # Tính toán số lượng mới
                    new_qty = current_qty - number
                    new_empty_qty = current_empty_qty + number
                    
                    # Cập nhật cả hai cột full_qty và empty_qty trong bảng tồn kho
                    # Lỗi đã được sửa: Thay "AND" bằng dấu phẩy "," và dùng biến "new_empty_qty" đã được tính toán
                    cursor.execute("UPDATE inventory SET full_qty = ?, empty_qty = ? WHERE inventory_id = ?", (new_qty, new_empty_qty, inventory_id))
                else: # Áp dụng cho bếp gas, phụ kiện...
                    new_full_qty = current_qty - number
                    cursor.execute("UPDATE inventory SET full_qty = ? WHERE inventory_id = ?", (new_full_qty, inventory_id))
        # Step 3: Update the order with the final total price
        cursor.execute("UPDATE orders SET full_price = ? WHERE order_id = ?", (total_price, order_id))
        conn.commit()
    return redirect("/")

@app.route('/api/order_details/<int:order_id>')
def api_order_details(order_id):
    with get_db() as conn:
        cursor = conn.cursor()

        order = cursor.execute("""
            SELECT
                o.order_id,
                o.full_price,
                o.created_at,
                c.name AS customer_name,
                s.name AS staff_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN staffs s ON o.staff_id = s.staff_id
            WHERE o.order_id = ?
        """, (order_id,)).fetchone()

        if order is None:
            return jsonify({"error": "Order not found"}), 404

        products = cursor.execute("""
            SELECT
                od.number,
                p.name AS product_name,
                ph.price AS unit_price
            FROM order_detail od
            JOIN inventory i ON od.inventory_id = i.inventory_id
            JOIN products p ON i.product_id = p.product_id
            LEFT JOIN prices_history ph ON od.price_history_id = ph.price_history_id
            WHERE od.order_id = ?
        """, (order_id,)).fetchall()

        products_list = [dict(p) for p in products]

        return jsonify({
            "order": dict(order),
            "products": products_list
        })

@app.route('/delete_order/<int:order_id>', methods=["POST"])
def delete_order(order_id):
    with get_db() as conn:
        conn.execute("DELETE FROM order_detail WHERE order_id = ?", (order_id,))
        conn.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
    return redirect("/")

#===Route chuyển trang===#
@app.route('/import')
def import_page():
    return render_template('import.html')

if __name__ == "__main__":
    setup_db()
    app.run(debug=True)