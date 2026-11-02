import pandas as pd
import streamlit as st
from db import fetch_all, get_connection
from pages_code.crud import done, friendly

METHODS = ["Cash", "UPI", "Card", "Wallet"]
SERVE_ROLES = "('Cashier','Waiter','Manager')"
# Allowed order-status moves (the database enforces the same rule with a trigger)
NEXT_STATUS = {"Pending": ["Preparing", "Cancelled"], "Preparing": ["Ready", "Cancelled"],
               "Ready": ["Completed", "Cancelled"], "Completed": [], "Cancelled": []}


def _run(statements):
    """Run (sql, params) pairs in ONE transaction: all succeed or none."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        for query, params in statements:
            cur.execute(query, params or ())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()


def _checkout(cur, order_id, method, paid):
    """Creates the payment record (amount is computed by the database) and optionally marks it Paid."""
    cur.execute("SET NOCOUNT ON; DECLARE @pid INT; EXEC dbo.sp_checkout_order ?, ?, @pid OUTPUT; SELECT @pid;",
                (order_id, method))
    pid = cur.fetchone()[0]
    if paid:
        cur.execute("EXEC dbo.sp_confirm_payment ?", (pid,))


def place_order(customer_id, canteen_id, emp_id, cart, method, mode):
    """orders + items (+ payment) in ONE transaction. mode: 'paid' | 'pending' | 'draft'."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SET NOCOUNT ON; INSERT INTO orders (customer_id, canteen_id, emp_id) VALUES (?,?,?); "
                    "SELECT CAST(SCOPE_IDENTITY() AS INT);", (customer_id, canteen_id, emp_id))
        order_id = cur.fetchone()[0]
        for c in cart:                      # the procedure copies the canteen's current price
            cur.execute("EXEC dbo.sp_add_order_item ?, ?, ?", (order_id, c["item_id"], c["qty"]))
        if mode != "draft":
            _checkout(cur, order_id, method, paid=(mode == "paid"))
        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()


def show():
    st.header("Orders")
    t_new, t_view, t_upd, t_del = st.tabs(["🛒 Place Order", "📋 View Orders", "✏️ Update Order", "🗑️ Delete Draft"])
    if "cart" not in st.session_state:
        st.session_state.cart = []

    # ---------- CREATE ----------
    with t_new:
        st.subheader("Create a new order")
        custs = fetch_all("SELECT c.customer_id, c.first_name, c.last_name FROM customer c "
                          "WHERE dbo.fn_customer_profile_ok(c.customer_id) = 1 ORDER BY c.first_name")
        canteens = fetch_all("SELECT canteen_id, canteen_name FROM canteen")
        if not custs or not canteens:
            st.info("Add at least one active customer and one canteen first.")
        else:
            a, b = st.columns(2)
            cust = a.selectbox("Customer", custs, format_func=lambda x: f"{x['first_name']} {x['last_name']}")
            canteen = b.selectbox("Canteen", canteens, format_func=lambda x: x["canteen_name"])
            if st.session_state.get("cart_canteen") != canteen["canteen_id"]:
                st.session_state.cart = []          # a cart belongs to one canteen
                st.session_state.cart_canteen = canteen["canteen_id"]

            staff = [None] + fetch_all(
                f"SELECT emp_id, emp_name, emp_role FROM employee WHERE canteen_id=%s AND is_active=1 "
                f"AND emp_role IN {SERVE_ROLES}", (canteen["canteen_id"],))
            emp = st.selectbox("Served by (needed before the order can progress)", staff,
                               format_func=lambda x: "-- none --" if x is None else f"{x['emp_name']} ({x['emp_role']})")

            items = fetch_all(
                "SELECT m.item_id, m.item_name, cm.price FROM canteen_menu cm "
                "JOIN menu_item m ON m.item_id = cm.item_id "
                "WHERE cm.canteen_id=%s AND cm.is_available=1 AND m.is_active=1 ORDER BY m.item_name",
                (canteen["canteen_id"],))

            st.markdown("**Add items** (only items this canteen sells are listed, at its own prices)")
            if not items:
                st.warning("This canteen has no available items. Add some on the Canteen Menu page.")
            else:
                c1, c2, c3 = st.columns([3, 1, 1])
                item = c1.selectbox("Item", items, format_func=lambda i: f"{i['item_name']} (₹{i['price']})")
                qty = c2.number_input("Qty", min_value=1, max_value=50, value=1, step=1)
                if c3.button("Add to cart"):
                    for line in st.session_state.cart:
                        if line["item_id"] == item["item_id"]:
                            line["qty"] = min(50, line["qty"] + int(qty))
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
                mode_label = p1.selectbox("Payment", ["Pay now (Paid)", "Pay later (payment Pending)",
                                                      "Save as draft (no payment record yet)"])
                method = p2.selectbox("Method", METHODS)
                mode = {"Pay now (Paid)": "paid", "Pay later (payment Pending)": "pending"}.get(mode_label, "draft")
                b1, b2 = st.columns(2)
                if b1.button("✅ Place Order"):
                    try:
                        oid = place_order(cust["customer_id"], canteen["canteen_id"],
                                          emp["emp_id"] if emp else None, cart, method, mode)
                        st.session_state.cart = []
                        done(f"Order #{oid} placed. Total ₹{df['subtotal'].sum():.2f}")
                    except Exception as e:
                        st.error(f"Order failed, nothing was saved: {friendly(e)}")
                if b2.button("Clear cart"):
                    st.session_state.cart = []
                    st.rerun()
            else:
                st.info("Cart is empty.")

    # ---------- READ ----------
    with t_view:
        st.subheader("All orders")
        st.dataframe(pd.DataFrame(fetch_all(
            "SELECT order_id, customer_name, canteen_name, order_datetime, status, total_amount, method, pay_status "
            "FROM v_order_total ORDER BY order_id DESC")), use_container_width=True, hide_index=True)
        oid = st.number_input("Show items of order #", min_value=0, step=1)
        if oid:
            st.dataframe(pd.DataFrame(fetch_all(
                "SELECT m.item_name, oi.quantity, oi.unit_price, oi.quantity*oi.unit_price AS subtotal "
                "FROM order_item oi JOIN menu_item m ON m.item_id=oi.item_id WHERE oi.order_id=%s",
                (int(oid),))), hide_index=True)
        st.subheader("Refunds")
        st.dataframe(pd.DataFrame(fetch_all(
            "SELECT r.refund_id, p.order_id, r.refund_amount, r.refunded_at, r.reason, e.emp_name AS processed_by "
            "FROM refund r JOIN payment p ON p.payment_id = r.payment_id "
            "JOIN employee e ON e.emp_id = r.processed_by ORDER BY r.refund_id DESC")),
            use_container_width=True, hide_index=True)

    orders = fetch_all("SELECT o.order_id, o.canteen_id, o.status, o.emp_id, p.payment_id, p.pay_status "
                       "FROM orders o LEFT JOIN payment p ON p.order_id = o.order_id ORDER BY o.order_id DESC")
    order_label = lambda x: f"#{x['order_id']}  (order: {x['status']}, payment: {x['pay_status'] or 'none yet'})"

    # ---------- UPDATE ----------
    with t_upd:
        st.subheader("Update an order")
        if not orders:
            st.info("No orders yet.")
        else:
            o = st.selectbox("Order", orders, key="uo", format_func=order_label)
            oid = o["order_id"]

            st.markdown("**1. Order status and staff**")
            options = NEXT_STATUS[o["status"]]
            if not options:
                st.info(f"This order is {o['status']}, so it is final and cannot be changed.")
            else:
                eligible = [None] + fetch_all(
                    f"SELECT emp_id, emp_name, emp_role FROM employee WHERE canteen_id=%s AND is_active=1 "
                    f"AND emp_role IN {SERVE_ROLES}", (o["canteen_id"],))
                idx = next((i for i, s in enumerate(eligible) if s and s["emp_id"] == o["emp_id"]), 0)
                emp = st.selectbox("Served by", eligible, index=idx, key=f"emp_{oid}",
                                   format_func=lambda x: "-- none --" if x is None else f"{x['emp_name']} ({x['emp_role']})")
                new_status = st.selectbox("Order status", [o["status"]] + options, key=f"os_{oid}")
                if st.button("Update order", key=f"ub_{oid}"):
                    try:
                        _run([("UPDATE orders SET status=?, emp_id=? WHERE order_id=?",
                               (new_status, emp["emp_id"] if emp else None, oid))])
                        done("Order updated.")
                    except Exception as e:
                        st.error(friendly(e))

            st.markdown("**2. Payment**")
            if o["payment_id"] is None:
                st.caption("This order has no payment record yet (draft).")
                m = st.selectbox("Method", METHODS, key=f"pm_{oid}")
                paid_now = st.checkbox("Mark as Paid now", key=f"pn_{oid}")
                if st.button("Create payment record", key=f"pb_{oid}"):
                    conn = get_connection(); cur = conn.cursor()
                    try:
                        _checkout(cur, oid, m, paid_now)
                        conn.commit()
                        ok = True
                    except Exception as e:
                        conn.rollback(); ok = False
                        st.error(friendly(e))
                    finally:
                        cur.close(); conn.close()
                    if ok:
                        done("Payment record created.")
            elif o["pay_status"] == "Pending":
                if st.button("Mark payment as Paid", key=f"pp_{oid}"):
                    try:
                        _run([("EXEC dbo.sp_confirm_payment ?", (o["payment_id"],))])
                        done("Payment marked as Paid.")
                    except Exception as e:
                        st.error(friendly(e))
            elif o["pay_status"] == "Paid":
                st.caption("To cancel a paid order, refund it first, then cancel the order.")
                staff_all = fetch_all("SELECT emp_id, emp_name, emp_role FROM employee WHERE is_active=1")
                who = st.selectbox("Refund processed by", staff_all, key=f"rw_{oid}",
                                   format_func=lambda x: f"{x['emp_name']} ({x['emp_role']})")
                reason = st.text_input("Reason for refund", key=f"rr_{oid}")
                if st.button("Refund full amount", key=f"rb_{oid}"):
                    if not reason.strip():
                        st.error("Please give a reason.")
                    else:
                        try:
                            _run([("EXEC dbo.sp_refund_payment ?, ?, ?", (o["payment_id"], reason.strip(), who["emp_id"]))])
                            done("Payment refunded.")
                        except Exception as e:
                            st.error(friendly(e))
            else:
                st.info("This payment has been refunded. Records of money are permanent.")

    # ---------- DELETE ----------
    with t_del:
        st.subheader("Delete a draft order")
        st.caption("Only draft orders (Pending, with no payment record) can be deleted. "
                   "Any other order should be Cancelled in the Update tab, because money records are permanent.")
        drafts = [x for x in orders if x["status"] == "Pending" and x["payment_id"] is None]
        if not drafts:
            st.info("There are no draft orders. Place an order with 'Save as draft' to try this.")
        else:
            d = st.selectbox("Draft order", drafts, key="do", format_func=order_label)
            sure = st.checkbox("I confirm deleting this draft order and its items")
            if st.button("Delete draft order"):
                if sure:
                    try:
                        _run([("DELETE FROM order_item WHERE order_id=?", (d["order_id"],)),
                              ("DELETE FROM orders WHERE order_id=?", (d["order_id"],))])
                        done("Draft order deleted.")
                    except Exception as e:
                        st.error(f"Cannot delete: {friendly(e)}")
                else:
                    st.warning("Tick the confirmation box first.")