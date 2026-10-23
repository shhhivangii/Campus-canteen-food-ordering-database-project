-- Campus Canteen: SQL Server (T-SQL) version of the MySQL script
USE master;
GO
IF DB_ID('campus_canteen') IS NOT NULL
BEGIN
    ALTER DATABASE campus_canteen SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE campus_canteen;
END
GO
CREATE DATABASE campus_canteen;
GO
USE campus_canteen;
GO

CREATE TABLE customer (
    customer_id   INT IDENTITY(1,1) PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    phone         CHAR(10)     NOT NULL UNIQUE,
    customer_type VARCHAR(10)  NOT NULL DEFAULT 'Student',
    registered_on DATETIME     NOT NULL DEFAULT GETDATE(),
    CONSTRAINT chk_customer_type  CHECK (customer_type IN ('Student','Faculty','Other')),
    CONSTRAINT chk_customer_phone CHECK (LEN(phone) = 10 AND phone NOT LIKE '%[^0-9]%')
);

CREATE TABLE student (
    customer_id INT PRIMARY KEY,
    roll_no     VARCHAR(20) NOT NULL UNIQUE,
    branch      VARCHAR(50) NOT NULL,
    study_year  TINYINT     NOT NULL,
    CONSTRAINT fk_student_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
    CONSTRAINT chk_student_year CHECK (study_year BETWEEN 1 AND 4)
);

CREATE TABLE faculty (
    customer_id   INT PRIMARY KEY,
    employee_code VARCHAR(20) NOT NULL UNIQUE,
    department    VARCHAR(50) NOT NULL,
    designation   VARCHAR(50) NULL,
    CONSTRAINT fk_faculty_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE
);

CREATE TABLE canteen (
    canteen_id   INT IDENTITY(1,1) PRIMARY KEY,
    canteen_name VARCHAR(80)  NOT NULL UNIQUE,
    location     VARCHAR(120) NOT NULL,
    open_time    TIME NOT NULL,
    close_time   TIME NOT NULL,
    CONSTRAINT chk_canteen_time CHECK (close_time > open_time)
);

CREATE TABLE employee (
    emp_id        INT IDENTITY(1,1) PRIMARY KEY,
    emp_name      VARCHAR(100) NOT NULL,
    emp_role      VARCHAR(10)  NOT NULL,
    salary        DECIMAL(10,2) NOT NULL,
    hire_date     DATE NOT NULL,
    canteen_id    INT NOT NULL,
    supervisor_id INT NULL,
    CONSTRAINT chk_employee_role   CHECK (emp_role IN ('Manager','Cashier','Cook','Waiter','Cleaner')),
    CONSTRAINT chk_employee_salary CHECK (salary > 0),
    CONSTRAINT fk_employee_canteen    FOREIGN KEY (canteen_id)    REFERENCES canteen(canteen_id),
    -- SQL Server does not allow SET NULL on a self-reference, so deleting a supervisor with staff is blocked
    CONSTRAINT fk_employee_supervisor FOREIGN KEY (supervisor_id) REFERENCES employee(emp_id)
);

CREATE TABLE category (
    category_id   INT IDENTITY(1,1) PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE menu_item (
    item_id      INT IDENTITY(1,1) PRIMARY KEY,
    item_name    VARCHAR(80)  NOT NULL UNIQUE,
    price        DECIMAL(8,2) NOT NULL,
    is_veg       BIT NOT NULL DEFAULT 1,
    is_available BIT NOT NULL DEFAULT 1,
    category_id  INT NOT NULL,
    CONSTRAINT chk_item_price CHECK (price > 0),
    CONSTRAINT fk_item_category FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE orders (
    order_id       INT IDENTITY(1,1) PRIMARY KEY,
    customer_id    INT NOT NULL,
    canteen_id     INT NOT NULL,
    emp_id         INT NULL,
    order_datetime DATETIME NOT NULL DEFAULT GETDATE(),
    status         VARCHAR(10) NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_orders_status CHECK (status IN ('Pending','Preparing','Ready','Completed','Cancelled')),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_orders_canteen  FOREIGN KEY (canteen_id)  REFERENCES canteen(canteen_id),
    CONSTRAINT fk_orders_employee FOREIGN KEY (emp_id)      REFERENCES employee(emp_id) ON DELETE SET NULL
);

CREATE TABLE order_item (
    order_id   INT NOT NULL,
    item_id    INT NOT NULL,
    quantity   INT NOT NULL,
    unit_price DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (order_id, item_id),
    CONSTRAINT chk_oi_quantity CHECK (quantity > 0),
    CONSTRAINT chk_oi_price    CHECK (unit_price > 0),
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_oi_item  FOREIGN KEY (item_id)  REFERENCES menu_item(item_id)
);

CREATE TABLE payment (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id   INT NOT NULL UNIQUE,
    amount     DECIMAL(10,2) NOT NULL,
    method     VARCHAR(10) NOT NULL,
    pay_status VARCHAR(10) NOT NULL DEFAULT 'Pending',
    paid_at    DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT chk_payment_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_method CHECK (method IN ('Cash','UPI','Card','Wallet')),
    CONSTRAINT chk_payment_status CHECK (pay_status IN ('Pending','Paid','Refunded')),
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE feedback (
    order_id      INT NOT NULL,
    item_id       INT NOT NULL,
    rating        TINYINT NOT NULL,
    comment       VARCHAR(255) NULL,
    feedback_date DATETIME NOT NULL DEFAULT GETDATE(),
    PRIMARY KEY (order_id, item_id),
    CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_feedback_order_item FOREIGN KEY (order_id, item_id)
        REFERENCES order_item(order_id, item_id) ON DELETE CASCADE
);
GO

-- ------------------------- SAMPLE DATA -------------------------
INSERT INTO customer (first_name, last_name, email, phone, customer_type) VALUES
('Aarav','Sharma','aarav.sharma@nsut.ac.in','9810000001','Student'),
('Riya','Verma','riya.verma@nsut.ac.in','9810000002','Student'),
('Karan','Singh','karan.singh@nsut.ac.in','9810000003','Student'),
('Sneha','Gupta','sneha.gupta@nsut.ac.in','9810000004','Student'),
('Rajesh','Kumar','rajesh.kumar@nsut.ac.in','9810000005','Faculty'),
('Meena','Iyer','meena.iyer@nsut.ac.in','9810000006','Faculty'),
('Rohit','Mehra','rohit.mehra@gmail.com','9810000007','Other');

INSERT INTO student (customer_id, roll_no, branch, study_year) VALUES
(1,'2024UCS1001','CSE',2),(2,'2024UCS1002','CSE',2),(3,'2023UEC2010','ECE',3),(4,'2025UIT3005','IT',1);

INSERT INTO faculty (customer_id, employee_code, department, designation) VALUES
(5,'F1001','Computer Science','Professor'),(6,'F1002','Electronics','Assistant Professor');

INSERT INTO canteen (canteen_name, location, open_time, close_time) VALUES
('Main Canteen','Near Admin Block','08:00:00','20:00:00'),
('Safal','Near APJ Block','09:00:00','18:00:00'),
('Nescafe','Nescii Lawns','07:00:00','22:00:00');

INSERT INTO employee (emp_name, emp_role, salary, hire_date, canteen_id, supervisor_id) VALUES
('Suresh Yadav','Manager',35000.00,'2020-06-01',1,NULL),
('Pooja Rani','Cashier',18000.00,'2022-01-15',1,1),
('Ramesh Chand','Cook',22000.00,'2021-03-10',1,1),
('Anita Joshi','Manager',33000.00,'2019-08-20',2,NULL),
('Vikas Kumar','Cashier',17000.00,'2023-02-01',2,4),
('Mohan Lal','Waiter',15000.00,'2023-07-12',3,NULL);

INSERT INTO category (category_name) VALUES ('Meals'),('Snacks'),('Beverages'),('Desserts');

INSERT INTO menu_item (item_name, price, is_veg, is_available, category_id) VALUES
('Chole Bhature',80.00,1,1,1),('Rajma Chawal',70.00,1,1,1),('Chicken Biryani',120.00,0,1,1),
('Veg Sandwich',40.00,1,1,2),('Samosa',15.00,1,1,2),('Maggi',35.00,1,1,2),
('Masala Chai',10.00,1,1,3),('Cold Coffee',50.00,1,1,3),
('Gulab Jamun',30.00,1,1,4),('Ice Cream',25.00,1,0,4);

INSERT INTO orders (customer_id, canteen_id, emp_id, order_datetime, status) VALUES
(1,1,2,'2026-10-05T13:10:00','Completed'),
(2,1,2,'2026-10-05T13:25:00','Completed'),
(3,2,5,'2026-10-06T11:40:00','Preparing'),
(5,1,NULL,'2026-10-06T12:05:00','Pending'),
(4,3,6,'2026-10-06T19:30:00','Completed');

INSERT INTO order_item (order_id, item_id, quantity, unit_price) VALUES
(1,1,2,80.00),(1,7,2,10.00),(2,3,1,120.00),(2,8,1,50.00),
(3,4,2,40.00),(3,6,1,35.00),(4,2,1,70.00),(5,5,4,15.00),(5,9,2,30.00);

INSERT INTO payment (order_id, amount, method, pay_status, paid_at) VALUES
(1,180.00,'UPI','Paid','2026-10-05T13:12:00'),
(2,170.00,'Card','Paid','2026-10-05T13:27:00'),
(3,115.00,'Cash','Pending','2026-10-06T11:41:00'),
(5,120.00,'Cash','Paid','2026-10-06T19:35:00');

INSERT INTO feedback (order_id, item_id, rating, comment) VALUES
(1,1,5,'Best chole bhature on campus'),(1,7,4,'Chai was good'),
(2,3,3,'Biryani was a bit dry'),(5,5,5,'Crispy samosas');
GO

-- ------------------------- VIEWS -------------------------
CREATE VIEW v_order_total AS
SELECT o.order_id,
       CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
       cn.canteen_name, o.order_datetime, o.status,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_amount
FROM orders o
JOIN customer c  ON c.customer_id = o.customer_id
JOIN canteen cn  ON cn.canteen_id = o.canteen_id
LEFT JOIN order_item oi ON oi.order_id = o.order_id
GROUP BY o.order_id, c.first_name, c.last_name, cn.canteen_name, o.order_datetime, o.status;
GO

CREATE VIEW v_menu AS
SELECT m.item_id, m.item_name, cat.category_name, m.price, m.is_veg, m.is_available
FROM menu_item m JOIN category cat ON cat.category_id = m.category_id;
GO

CREATE VIEW v_item_rating AS
SELECT m.item_id, m.item_name, COUNT(f.rating) AS num_reviews,
       CAST(AVG(CAST(f.rating AS DECIMAL(5,2))) AS DECIMAL(4,2)) AS avg_rating
FROM menu_item m LEFT JOIN feedback f ON f.item_id = m.item_id
GROUP BY m.item_id, m.item_name;
GO

SELECT * FROM customer;
SELECT * FROM v_order_total;