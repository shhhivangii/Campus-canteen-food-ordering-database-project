import pyodbc

# ---- CHANGE THIS to the server name you see in SSMS's "Connect" window ----
SERVER = r"SIMMI\SQLEXPRESS"
DATABASE = "campus_canteen"


def _driver():
    found = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not found:
        raise RuntimeError("No SQL Server ODBC driver found. Install 'ODBC Driver 18 for SQL Server'.")
    newest = sorted([d for d in found if d.startswith("ODBC Driver")], reverse=True)
    return (newest or found)[0]


def get_connection():
    conn_str = (f"DRIVER={{{_driver()}}};SERVER={SERVER};DATABASE={DATABASE};"
                "Trusted_Connection=yes;TrustServerCertificate=yes;")
    return pyodbc.connect(conn_str)


def fetch_all(query, params=None):
    """For SELECT. Returns a list of dictionaries. (%s is converted to ? for SQL Server)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query.replace("%s", "?"), params or ())
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def execute(query, params=None):
    """For INSERT / UPDATE / DELETE."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query.replace("%s", "?"), params or ())
    conn.commit()
    n = cur.rowcount
    cur.close(); conn.close()
    return n