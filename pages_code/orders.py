import pandas as pd
import streamlit as st
from db import fetch_all, execute, get_connection

STATUSES = ["Pending", "Preparing", "Ready", "Completed", "Cancelled"]


def place_order(customer_id, canteen_id, emp_id, cart, method, pay_status):
    """Insert into orders + order_item + payment as ONE transaction."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO orders (customer_id, canteen_id, emp_id) OUTPUT INSERTED.order_id "
                    "VALUES (?,?,?)", (customer_id, canteen_id, emp_id))
        order_id = cur.fetchone()[0]
        total = 0
        for c in cart:
            cur.execute("INSERT INTO order_item (order_id, item_id, quantity, unit_price) VALUES (?,?,?,?)",
                        (order_id, c["item_id"], c["qty"], c["price"]))
            total += c["qty"] * c["price"]
        cur.execute("INSERT INTO payment (order_id, amount, method, pay_status) VALUES (?,?,?,?)",
                    (order_id, total, method, pay_status))
        conn.commit()
        return order_id, total
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()


def show():
    st.header("Orders")
    t_new, t_view, t_upd, t_del = st.tabs(["🛒 Place Order", "📋 View Orders", "✏️ Update Status", "🗑️ Delete Order"])
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # ---------- CREATE ----------
    with t_new:
        custs = fetch_all("SELECT customer_id, first_name, last_name FROM customer")
        canteens = fetch_all("SELECT canteen_id, canteen_name FROM canteen")
        emps = [None] + fetch_all("SELECT emp_id, emp_name, emp_role FROM employee")
        items = fetch_all("SELECT item_id, item_name, price FROM menu_item WHERE is_available = 1")

        a, b, c = st.columns(3)
        cust = a.selectbox("Customer", custs, format_func=lambda x: f"{x['first_name']} {x['last_name']}")
        canteen = b.selectbox("Canteen", canteens, format_func=lambda x: x["canteen_name"])
        emp = c.selectbox("Served by (optional)", emps,
                          format_func=lambda x: "-- none --" if x is None else f"{x['emp_name']} ({x['emp_role']})")

        st.markdown("**Add items**")
        c1, c2, c3 = st.columns([3, 1, 1])
        item = c1.selectbox("Item", items, format_func=lambda i: f"{i['item_name']} (₹{i['price']})")
        qty = c2.number_input("Qty", min_value=1, value=1, step=1)
        if c3.button("Add to cart"):
            for line in st.session_state.cart:          # same item twice -> merge (PK is order_id+item_id)
                if line["item_id"] == item["item_id"]:
                    line["qty"] += int(qty)
                    break
            else:
                st.session_state.cart.append({"item_id": item["item_id"], "name": item["item_name"],
                                              "qty": int(qty), "price": float(item["price"])})

        cart = st.session_state.cart
        if cart:
            df = pd.DataFrame(cart)
            df["subtotal"] = df["qty"] * df["price"]
            st.dataframe(df[["name", "qty", "price", "subtotal"]], hide_index=True, use_container_width=True)
            st.metric("Total", f"₹{df['subtotal'].sum():.2f}")
            p1, p2 = st.columns(2)
            method = p1.selectbox("Payment method", ["Cash", "UPI", "Card", "Wallet"])
            pay_status = p2.selectbox("Payment status", ["Paid", "Pending"])
            b1, b2 = st.columns(2)
            if b1.button("✅ Place Order"):
                try:
                    oid, total = place_order(cust["customer_id"], canteen["canteen_id"],
                                             emp["emp_id"] if emp else None, cart, method, pay_status)
                    st.session_state.cart = []
                    st.success(f"Order #{oid} placed. Total ₹{total:.2f}")
                except Exception as e:
                    st.error(f"Order failed, nothing was saved: {e}")
            if b2.button("Clear cart"):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info("Cart is empty.")

    # ---------- READ ----------
    with t_view:
        rows = fetch_all(
            "SELECT v.order_id, v.customer_name, v.canteen_name, v.order_datetime, v.status, "
            "v.total_amount, p.method, p.pay_status FROM v_order_total v "
            "LEFT JOIN payment p ON p.order_id = v.order_id ORDER BY v.order_id DESC")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        oid = st.number_input("Show items of order #", min_value=0, step=1)
        if oid:
            st.dataframe(pd.DataFrame(fetch_all(
                "SELECT m.item_name, oi.quantity, oi.unit_price, oi.quantity*oi.unit_price AS subtotal "
                "FROM order_item oi JOIN menu_item m ON m.item_id=oi.item_id WHERE oi.order_id=%s",
                (int(oid),))), hide_index=True)

    orders = fetch_all("SELECT order_id, status FROM orders ORDER BY order_id DESC")

    # ---------- UPDATE ----------
    with t_upd:
        if orders:
            o = st.selectbox("Order", orders, format_func=lambda x: f"#{x['order_id']} ({x['status']})", key="uo")
            status = st.selectbox("Order status", STATUSES, index=STATUSES.index(o["status"]), key=f"os_{o['order_id']}")
            pay = st.selectbox("Payment status", ["Pending", "Paid", "Refunded"], key=f"ps_{o['order_id']}")
            if st.button("Update"):
                try:
                    execute("UPDATE orders SET status=%s WHERE order_id=%s", (status, o["order_id"]))
                    execute("UPDATE payment SET pay_status=%s WHERE order_id=%s", (pay, o["order_id"]))
                    st.success("Updated! Check View Orders.")
                except Exception as e:
                    st.error(f"Could not update: {e}")

    # ---------- DELETE ----------
    with t_del:
        if orders:
            o = st.selectbox("Order", orders, format_func=lambda x: f"#{x['order_id']} ({x['status']})", key="do")
            sure = st.checkbox("I confirm deleting this order (its items, payment and feedback too)")
            if st.button("Delete order"):
                if sure:
                    execute("DELETE FROM orders WHERE order_id=%s", (o["order_id"],))
                    st.success("Order deleted.")
                else:
                    st.warning("Tick the confirmation box first.")