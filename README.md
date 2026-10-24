# Campus-canteen-food-ordering-database-project

A database project with a web interface for managing a campus canteen: customers, menu, orders, payments, employees and feedback.

**Team:** [Name 1], [Name 2], [Name 3], [Name 4]
**Course:** [Course name] | **College:** [College name]

## Features

- Create, Read, Update and Delete (CRUD) on every main table
- Place an order with a cart, which saves the order, its items and the payment together as one transaction
- Customers are split into Students and Faculty (specialization)
- Employees have supervisors (recursive relationship)
- Feedback and ratings for items that were actually ordered
- Dashboard with totals, top-selling items, orders per canteen, best-rated dishes and pending payments
- Search box on every View tab
- Database rules shown clearly in the UI (for example, a phone number must be 10 digits, and a record cannot be deleted while other records depend on it)

## Technologies

| Part | Tool |
|---|---|
| Database | Microsoft SQL Server (Express) |
| Backend | Python 3 with pyodbc |
| User interface | Streamlit |
| Data tables | pandas |

## Project structure

```
canteen_app/
├── app.py                      Main file, sidebar menu
├── db.py                       Database connection
├── style.py                    Colours and design
├── test_db.py                  Checks the database connection
├── campus_canteen_mssql.sql    Creates the database, tables, sample data and views
├── .streamlit/config.toml      Theme settings
└── pages_code/
    ├── crud.py                 Reusable Add / View / Update / Delete page
    ├── entities.py             Customers, Students, Faculty, Canteens, Employees, Categories, Menu Items
    ├── orders.py               Place order, view, update status, delete
    ├── feedback.py             Feedback page
    └── dashboard.py            Dashboard
```

## Database tables

`customer`, `student`, `faculty`, `canteen`, `employee`, `category`, `menu_item`, `orders`, `order_item`, `payment`, `feedback`
