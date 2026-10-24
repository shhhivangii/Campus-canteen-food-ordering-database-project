import pandas as pd
import streamlit as st
from db import fetch_all


def show():
    st.title("📊 Dashboard")
    n_orders = fetch_all("SELECT COUNT(*) AS n FROM orders")[0]["n"]
    pending = fetch_all("SELECT COUNT(*) AS n FROM orders WHERE status IN ('Pending','Preparing')")[0]["n"]
    revenue = fetch_all("SELECT ISNULL(SUM(amount),0) AS r FROM payment WHERE pay_status='Paid'")[0]["r"]
    custs = fetch_all("SELECT COUNT(*) AS n FROM customer")[0]["n"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total orders", n_orders)
    c2.metric("Open orders", pending)
    c3.metric("Revenue (paid)", f"₹{revenue}")
    c4.metric("Customers", custs)

    left, right = st.columns(2)
    with left:
        st.subheader("Top-selling items")
        top = pd.DataFrame(fetch_all(
            "SELECT TOP 5 m.item_name, SUM(oi.quantity) AS sold FROM order_item oi "
            "JOIN menu_item m ON m.item_id=oi.item_id GROUP BY m.item_name ORDER BY sold DESC"))
        st.bar_chart(top.set_index("item_name")) if not top.empty else st.info("No orders yet.")
    with right:
        st.subheader("Orders by canteen")
        by = pd.DataFrame(fetch_all(
            "SELECT cn.canteen_name, COUNT(*) AS orders FROM orders o "
            "JOIN canteen cn ON cn.canteen_id=o.canteen_id GROUP BY cn.canteen_name"))
        st.bar_chart(by.set_index("canteen_name")) if not by.empty else st.info("No orders yet.")

    st.subheader("⭐ Best-rated dishes")
    rt = pd.DataFrame(fetch_all(
        "SELECT TOP 5 item_name, num_reviews, avg_rating FROM v_item_rating WHERE num_reviews > 0 "
        "ORDER BY avg_rating DESC"))
    st.dataframe(rt, hide_index=True, use_container_width=True) if not rt.empty else st.info("No feedback yet.")

    st.subheader("🕒 Pending payments")
    pp = pd.DataFrame(fetch_all(
        "SELECT order_id, amount, method FROM payment WHERE pay_status='Pending'"))
    st.dataframe(pp, hide_index=True, use_container_width=True) if not pp.empty else st.success("No pending payments.")