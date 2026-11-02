"""One function per table of campus_canteen. Edit names here if the schema changes."""
import streamlit as st
from db import get_connection
from pages_code.crud import crud_page, done, friendly

CANTEEN_FK = "SELECT canteen_id AS id, canteen_name AS label FROM canteen"


def _add_customer():
    """Registers a customer through the stored procedures, so a Student/Faculty
    always gets its detail record in the SAME transaction."""
    st.subheader("Add a new customer")
    st.caption("Students and Faculty get their extra details saved together with the customer.")
    ctype = st.selectbox("Customer type", ["Student", "Faculty", "Other"], key="newcust_type")
    with st.form("add_customer_full"):
        a, b = st.columns(2)
        first = a.text_input("First name")
        last = b.text_input("Last name")
        email = a.text_input("Email")
        phone = b.text_input("Phone (10 digits)")
        extra = {}
        if ctype == "Student":
            extra["roll_no"] = a.text_input("Roll no")
            extra["branch"] = b.text_input("Branch")
            extra["study_year"] = a.selectbox("Year", [1, 2, 3, 4])
        elif ctype == "Faculty":
            extra["employee_code"] = a.text_input("Employee code")
            extra["department"] = b.text_input("Department")
            extra["designation"] = a.text_input("Designation (optional)")
        ok = st.form_submit_button("Save")
    if not ok:
        return
    needed = [first, last, email, phone] + [v for k, v in extra.items() if k != "designation"]
    if any(not str(v).strip() for v in needed):
        st.error("Please fill in all the required fields.")
        return

    conn = get_connection()
    cur = conn.cursor()
    saved, cid = False, None
    try:
        if ctype == "Student":
            cur.execute("SET NOCOUNT ON; DECLARE @id INT; "
                        "EXEC dbo.sp_register_student ?,?,?,?,?,?,?, @id OUTPUT; SELECT @id;",
                        (first, last, email, phone, extra["roll_no"], extra["branch"], int(extra["study_year"])))
        elif ctype == "Faculty":
            cur.execute("SET NOCOUNT ON; DECLARE @id INT; "
                        "EXEC dbo.sp_register_faculty ?,?,?,?,?,?,?, @id OUTPUT; SELECT @id;",
                        (first, last, email, phone, extra["employee_code"], extra["department"],
                         extra["designation"] or None))
        else:
            cur.execute("SET NOCOUNT ON; DECLARE @id INT; "
                        "EXEC dbo.sp_register_other ?,?,?,?, @id OUTPUT; SELECT @id;",
                        (first, last, email, phone))
        cid = cur.fetchone()[0]
        conn.commit()
        saved = True
    except Exception as e:
        conn.rollback()
        st.error(f"Could not save (nothing was stored): {friendly(e)}")
    finally:
        cur.close(); conn.close()
    if saved:
        done(f"{ctype} customer added with ID {cid}.")


def customers():
    crud_page("Customers", "customer", "customer_id", [
        {"name": "first_name", "label": "First name", "type": "text"},
        {"name": "last_name", "label": "Last name", "type": "text"},
        {"name": "email", "label": "Email", "type": "text"},
        {"name": "phone", "label": "Phone (10 digits)", "type": "text"},
        {"name": "customer_type", "label": "Type", "type": "choice", "options": ["Student", "Faculty", "Other"]},
        {"name": "is_active", "label": "Active (untick to deactivate instead of deleting)", "type": "bool"},
    ], custom_add=_add_customer,
        list_sql="SELECT *, CONCAT(first_name,' ',last_name) AS label FROM customer")


def students():
    crud_page("Students (specialization of Customer)", "student", "customer_id", [
        {"name": "customer_id", "label": "Customer (type Student, no record yet)", "type": "fk",
         "sql": "SELECT customer_id AS id, CONCAT(first_name,' ',last_name) AS label FROM customer "
                "WHERE customer_type='Student' AND customer_id NOT IN (SELECT customer_id FROM student)"},
        {"name": "roll_no", "label": "Roll no", "type": "text"},
        {"name": "branch", "label": "Branch", "type": "text"},
        {"name": "study_year", "label": "Year", "type": "choice", "options": [1, 2, 3, 4]},
    ], view_sql="SELECT s.customer_id, CONCAT(c.first_name,' ',c.last_name) AS name, "
                "s.roll_no, s.branch, s.study_year FROM student s "
                "JOIN customer c ON c.customer_id = s.customer_id",
        list_sql="SELECT s.*, CONCAT(c.first_name,' ',c.last_name,' (',s.roll_no,')') AS label "
                 "FROM student s JOIN customer c ON c.customer_id = s.customer_id",
        lock_on_update=["customer_id"])


def faculty():
    crud_page("Faculty (specialization of Customer)", "faculty", "customer_id", [
        {"name": "customer_id", "label": "Customer (type Faculty, no record yet)", "type": "fk",
         "sql": "SELECT customer_id AS id, CONCAT(first_name,' ',last_name) AS label FROM customer "
                "WHERE customer_type='Faculty' AND customer_id NOT IN (SELECT customer_id FROM faculty)"},
        {"name": "employee_code", "label": "Employee code", "type": "text"},
        {"name": "department", "label": "Department", "type": "text"},
        {"name": "designation", "label": "Designation", "type": "text", "optional": True},
    ], view_sql="SELECT f.customer_id, CONCAT(c.first_name,' ',c.last_name) AS name, "
                "f.employee_code, f.department, f.designation FROM faculty f "
                "JOIN customer c ON c.customer_id = f.customer_id",
        list_sql="SELECT f.*, CONCAT(c.first_name,' ',c.last_name,' (',f.employee_code,')') AS label "
                 "FROM faculty f JOIN customer c ON c.customer_id = f.customer_id",
        lock_on_update=["customer_id"])


def canteens():
    crud_page("Canteens", "canteen", "canteen_id", [
        {"name": "canteen_name", "label": "Canteen name", "type": "text"},
        {"name": "location", "label": "Location", "type": "text"},
        {"name": "open_time", "label": "Opens at", "type": "time"},
        {"name": "close_time", "label": "Closes at (can be after midnight)", "type": "time"},
    ])


def employees():
    crud_page("Employees", "employee", "emp_id", [
        {"name": "emp_name", "label": "Name", "type": "text"},
        {"name": "emp_role", "label": "Role", "type": "choice",
         "options": ["Manager", "Cashier", "Cook", "Waiter", "Cleaner"]},
        {"name": "salary", "label": "Salary (₹)", "type": "number"},
        {"name": "hire_date", "label": "Hire date", "type": "date"},
        {"name": "canteen_id", "label": "Canteen", "type": "fk", "sql": CANTEEN_FK},
        {"name": "supervisor_id", "label": "Supervisor (a Manager of the same canteen)", "type": "fk",
         "optional": True,
         "sql": "SELECT e.emp_id AS id, CONCAT(e.emp_name,' - ',c.canteen_name) AS label FROM employee e "
                "JOIN canteen c ON c.canteen_id = e.canteen_id WHERE e.emp_role='Manager' AND e.is_active=1"},
        {"name": "is_active", "label": "Active", "type": "bool"},
    ], view_sql="SELECT e.emp_id, e.emp_name, e.emp_role, e.salary, e.hire_date, "
                "c.canteen_name, s.emp_name AS supervisor, e.is_active FROM employee e "
                "JOIN canteen c ON c.canteen_id = e.canteen_id "
                "LEFT JOIN employee s ON s.emp_id = e.supervisor_id",
        list_sql="SELECT *, CONCAT(emp_name,' (',emp_role,')') AS label FROM employee")


def categories():
    crud_page("Categories", "category", "category_id", [
        {"name": "category_name", "label": "Category name", "type": "text"},
    ])


def menu_items():
    crud_page("Menu Items (the dish catalogue)", "menu_item", "item_id", [
        {"name": "item_name", "label": "Item name", "type": "text"},
        {"name": "is_veg", "label": "Vegetarian", "type": "bool"},
        {"name": "is_active", "label": "Active (untick if the dish is discontinued)", "type": "bool"},
        {"name": "category_id", "label": "Category", "type": "fk",
         "sql": "SELECT category_id AS id, category_name AS label FROM category"},
    ], view_sql="SELECT m.item_id, m.item_name, c.category_name, m.is_veg, m.is_active "
                "FROM menu_item m JOIN category c ON c.category_id = m.category_id",
        list_sql="SELECT *, item_name AS label FROM menu_item")


def canteen_menu():
    st.info("💰 Prices live here: each canteen sets its own price for each dish. "
            "To change a price, open the Update tab.")
    crud_page("Canteen Menu & Prices", "canteen_menu", ["canteen_id", "item_id"], [
        {"name": "canteen_id", "label": "Canteen", "type": "fk", "sql": CANTEEN_FK},
        {"name": "item_id", "label": "Menu item", "type": "fk",
         "sql": "SELECT item_id AS id, item_name AS label FROM menu_item WHERE is_active=1"},
        {"name": "price", "label": "Price (₹)", "type": "number"},
        {"name": "is_available", "label": "Available at this canteen", "type": "bool"},
    ], view_sql="SELECT canteen_name, item_name, category_name, price, is_veg, is_available "
                "FROM v_menu ORDER BY canteen_name, item_name",
        list_sql="SELECT cm.*, CONCAT(c.canteen_name,' - ',m.item_name) AS label FROM canteen_menu cm "
                 "JOIN canteen c ON c.canteen_id = cm.canteen_id "
                 "JOIN menu_item m ON m.item_id = cm.item_id ORDER BY label",
        lock_on_update=["canteen_id", "item_id"])