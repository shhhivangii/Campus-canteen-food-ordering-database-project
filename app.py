import streamlit as st
from pages_code import dashboard, entities, orders

st.set_page_config(page_title="Campus Canteen", page_icon="🍽️", layout="wide")
st.sidebar.title("🍽️ Campus Canteen")

PAGES = {
    "Dashboard": dashboard.show,
    "Place Order / Orders": orders.show,
    "Customers": entities.customers,
    "Customer Phones": entities.customer_phones,
    "Menu Items": entities.menu_items,
    "Categories": entities.categories,
    "Employees": entities.employees,
    "Suppliers": entities.suppliers,
    "Ingredients (Inventory)": entities.ingredients,
    "Supply Deliveries": entities.supplies,
}
choice = st.sidebar.radio("Go to", list(PAGES))
PAGES[choice]()