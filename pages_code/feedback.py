import pandas as pd
import streamlit as st
from db import fetch_all, execute


def show():
    st.header("Feedback")
    t_add, t_view, t_upd, t_del = st.tabs(["➕ Add", "📋 View", "✏️ Update", "🗑️ Delete"])

    # ---------- CREATE ----------
    with t_add:
        pairs = fetch_all(
            "SELECT oi.order_id, oi.item_id, m.item_name FROM order_item oi "
            "JOIN menu_item m ON m.item_id = oi.item_id "
            "WHERE NOT EXISTS (SELECT 1 FROM feedback f WHERE f.order_id=oi.order_id AND f.item_id=oi.item_id) "
            "ORDER BY oi.order_id")
        if not pairs:
            st.info("Every ordered item already has feedback.")
        else:
            with st.form("fb_add"):
                p = st.selectbox("Ordered item", pairs,
                                 format_func=lambda x: f"Order #{x['order_id']} - {x['item_name']}")
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_input("Comment (optional)")
                ok = st.form_submit_button("Save")
            if ok:
                try:
                    execute("INSERT INTO feedback (order_id, item_id, rating, comment) VALUES (%s,%s,%s,%s)",
                            (p["order_id"], p["item_id"], rating, comment or None))
                    st.success("Feedback saved!")
                except Exception as e:
                    st.error(f"Could not save: {e}")

    # ---------- READ ----------
    with t_view:
        st.subheader("All feedback")
        st.dataframe(pd.DataFrame(fetch_all(
            "SELECT f.order_id, m.item_name, CONCAT(c.first_name,' ',c.last_name) AS customer, "
            "f.rating, f.comment, f.feedback_date FROM feedback f "
            "JOIN menu_item m ON m.item_id=f.item_id "
            "JOIN orders o ON o.order_id=f.order_id "
            "JOIN customer c ON c.customer_id=o.customer_id ORDER BY f.feedback_date DESC")),
            use_container_width=True, hide_index=True)
        