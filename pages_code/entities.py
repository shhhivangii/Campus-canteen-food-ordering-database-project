"""One function per table of campus_canteen. Edit names here if the schema changes."""
from pages_code.crud import crud_page

CUSTOMER_FK = "SELECT customer_id AS id, CONCAT(first_name,' ',last_name) AS label FROM customer"
CANTEEN_FK = "SELECT canteen_id AS id, canteen_name AS label FROM canteen"


def customers():
    crud_page("Customers", "customer", "customer_id", [
        {"name": "first_name", "label": "First name", "type": "text"},
        {"name": "last_name", "label": "Last name", "type": "text"},
        {"name": "email", "label": "Email", "type": "text"},
        {"name": "phone", "label": "Phone (10 digits)", "type": "text"},
        {"name": "customer_type", "label": "Type", "type": "choice", "options": ["Student", "Faculty", "Other"]},
    ])


def students():
    crud_page("Students (specialization of Customer)", "student", "customer_id", [
        {"name": "customer_id", "label": "Customer (type Student)", "type": "fk",
         "sql": CUSTOMER_FK + " WHERE customer_type='Student'"},
        {"name": "roll_no", "label": "Roll no", "type": "text"},
        {"name": "branch", "label": "Branch", "type": "text"},
        {"name": "study_year", "label": "Year", "type": "choice", "options": [1, 2, 3, 4]},
    ], view_sql="SELECT s.customer_id, CONCAT(c.first_name,' ',c.last_name) AS name, "
                "s.roll_no, s.branch, s.study_year FROM student s "
                "JOIN customer c ON c.customer_id = s.customer_id")


def faculty():
    crud_page("Faculty (specialization of Customer)", "faculty", "customer_id", [
        {"name": "customer_id", "label": "Customer (type Faculty)", "type": "fk",
         "sql": CUSTOMER_FK + " WHERE customer_type='Faculty'"},
        {"name": "employee_code", "label": "Employee code", "type": "text"},
        {"name": "department", "label": "Department", "type": "text"},
        {"name": "designation", "label": "Designation", "type": "text", "optional": True},
    ], view_sql="SELECT f.customer_id, CONCAT(c.first_name,' ',c.last_name) AS name, "
                "f.employee_code, f.department, f.designation FROM faculty f "
                "JOIN customer c ON c.customer_id = f.customer_id")


def canteens():
    crud_page("Canteens", "canteen", "canteen_id", [
        {"name": "canteen_name", "label": "Canteen name", "type": "text"},
        {"name": "location", "label": "Location", "type": "text"},
        {"name": "open_time", "label": "Opens at", "type": "time"},
        {"name": "close_time", "label": "Closes at", "type": "time"},
    ])


def employees():
    crud_page("Employees", "employee", "emp_id", [
        {"name": "emp_name", "label": "Name", "type": "text"},
        {"name": "emp_role", "label": "Role", "type": "choice",
         "options": ["Manager", "Cashier", "Cook", "Waiter", "Cleaner"]},
        {"name": "salary", "label": "Salary (₹)", "type": "number"},
        {"name": "hire_date", "label": "Hire date", "type": "date"},
        {"name": "canteen_id", "label": "Canteen", "type": "fk", "sql": CANTEEN_FK},
        {"name": "supervisor_id", "label": "Supervisor", "type": "fk", "optional": True,
         "sql": "SELECT emp_id AS id, emp_name AS label FROM employee"},
    ], view_sql="SELECT e.emp_id, e.emp_name, e.emp_role, e.salary, e.hire_date, "
                "c.canteen_name, s.emp_name AS supervisor FROM employee e "
                "JOIN canteen c ON c.canteen_id = e.canteen_id "
                "LEFT JOIN employee s ON s.emp_id = e.supervisor_id")


def categories():
    crud_page("Categories", "category", "category_id", [
        {"name": "category_name", "label": "Category name", "type": "text"},
    ])


def menu_items():
    crud_page("Menu Items", "menu_item", "item_id", [
        {"name": "item_name", "label": "Item name", "type": "text"},
        {"name": "price", "label": "Price (₹)", "type": "number"},
        {"name": "is_veg", "label": "Vegetarian", "type": "bool"},
        {"name": "is_available", "label": "Available", "type": "bool"},
        {"name": "category_id", "label": "Category", "type": "fk",
         "sql": "SELECT category_id AS id, category_name AS label FROM category"},
    ], view_sql="SELECT * FROM v_menu")