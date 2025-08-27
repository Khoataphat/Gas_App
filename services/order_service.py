import sqlite3
import time
from database import get_db

def create_new_order(customer_id, staff_id, product_ids, numbers, prices):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Bước 1: Tạo đơn hàng mới với giá ban đầu là 0
        cursor.execute("INSERT INTO orders (customer_id, staff_id, full_price, created_at) VALUES (?, ?, ?, ?)", 
                       (customer_id, staff_id, 0, int(time.time())))
        order_id = cursor.lastrowid

        total_price = 0
        
        # Bước 2: Lặp qua từng sản phẩm trong đơn hàng
        for i in range(len(product_ids)):
            product_id = product_ids[i]
            number = int(numbers[i])
            price = float(prices[i])

            # Thêm giá vào bảng lịch sử giá
            cursor.execute("INSERT INTO prices_history (product_id, price, time) VALUES (?, ?, ?)", 
                           (product_id, price, int(time.time())))
            price_history_id = cursor.lastrowid
            
            # Lấy inventory_id của sản phẩm
            inventory_row = cursor.execute("SELECT inventory_id FROM inventory WHERE product_id = ?", (product_id,)).fetchone()
            
            if inventory_row:
                inventory_id = inventory_row['inventory_id']
                
                # Thêm chi tiết đơn hàng
                cursor.execute("INSERT INTO order_detail (order_id, inventory_id, number, time, price_history_id) VALUES (?, ?, ?, ?, ?)", 
                               (order_id, inventory_id, number, int(time.time()), price_history_id))
                
                total_price += number * price

        # Bước 3: Cập nhật tổng giá cho đơn hàng
        cursor.execute("UPDATE orders SET full_price = ? WHERE order_id = ?", (total_price, order_id))
        conn.commit()