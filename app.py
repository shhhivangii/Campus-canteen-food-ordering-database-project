import streamlit as st
from pages_code import dashboard, entities, orders, feedback
from style import apply_style, banner

st.set_page_config(page_title="Campus Canteen", page_icon="🍽️", layout="wide")
apply_style()

PAGES = {
    "📊 Dashboard": dashboard.show,
    "🛒 Orders": orders.show,
    "👤 Customers": entities.customers,
    "🎓 Students": entities.students,
    "👨‍🏫 Faculty": entities.faculty,
    "🏪 Canteens": entities.canteens,
    "🧑‍🍳 Employees": entities.employees,
    "🗂️ Categories": entities.categories,
    "🍔 Menu Items": entities.menu_items,
    "⭐ Feedback": feedback.show,
}

st.sidebar.title("🍽️ Campus Canteen")
st.sidebar.caption("Food Ordering & Management System")
choice = st.sidebar.radio("Navigate", list(PAGES), label_visibility="collapsed")

banner("Campus Canteen", "Order food, manage the menu, and track inventory")
PAGES[choice]()