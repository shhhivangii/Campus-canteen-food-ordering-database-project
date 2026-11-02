import pandas as pd
import streamlit as st
from db import fetch_all


def show():
    st.title("📊 Dashboard")
    n_orders = fetch_all("SELECT COUNT(*) AS n FROM orders")[0]["n"]
    open_orders = fetch_all("SELECT COUNT(*) AS n FROM orders WHERE status IN ('Pending','Preparing','Ready')")[0]["n"]
    revenue = fetch_all("SELECT ISNULL(SUM(amount),0) AS r FROM payment WHERE pay_status='Paid'")[0]["r"]
    refunded = fetch_all("SELECT ISNULL(SUM(refund_amount),0) AS r FROM refund")[0]["r"]
    custs = fetch_all("SELECT COUNT(*) AS n FROM customer WHERE is_active=1")[0]["n"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total orders", n_orders)
    c2.metric("Open orders", open_orders)
    c3.metric("Revenue (paid)", f"₹{revenue}")
    c4.metric("Refunded", f"₹{refunded}")
    c5.metric("Active customers", custs)

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
    pp = pd.DataFrame(fetch_all("SELECT order_id, amount, method FROM payment WHERE pay_status='Pending'"))
    st.dataframe(pp, hide_index=True, use_container_width=True) if not pp.empty else st.success("No pending payments.")

    st.subheader("🛡️ Data-quality check")
    issues = pd.DataFrame(fetch_all("SELECT issue, ref_id FROM v_integrity_issues"))
    if issues.empty:
        st.success("All business rules are satisfied.")
    else:
        st.warning("Some records need attention (for example, draft orders with no payment yet):")
        st.dataframe(issues, hide_index=True, use_container_width=True)