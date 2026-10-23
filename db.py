import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD",
        database="canteen_db"
    )

def fetch_all(query, params=None):
    """Use for SELECT. Returns a list of dicts."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def execute(query, params=None):
    """Use for INSERT / UPDATE / DELETE."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    new_id = cur.lastrowid
    cur.close(); conn.close()
    return new_id