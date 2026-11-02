"""Reusable CRUD page for one table. Works with single or composite primary keys."""
import datetime
import re
import pandas as pd
import streamlit as st
from db import fetch_all, execute

CHECK_MESSAGES = {
    "chk_customer_phone": "Phone must be exactly 10 digits.",
    "chk_customer_email": "Please enter a valid email address.",
    "chk_customer_names": "First and last name cannot be empty.",
    "chk_student_year": "Year must be between 1 and 4.",
    "chk_canteen_time": "Opening and closing time cannot be the same.",
    "chk_employee_salary": "Salary must be above 0.",
    "chk_employee_not_self": "An employee cannot supervise themselves.",
    "chk_cm_price": "Price must be above 0.",
    "chk_feedback_rating": "Rating must be between 1 and 5.",
    "chk_oi_quantity": "Quantity must be between 1 and 50.",
}


def friendly(e):
    """Turn a long SQL Server error into one readable sentence."""
    msg = str(e)
    if "[SQL Server]" in msg:
        msg = msg.split("[SQL Server]")[-1]
    msg = re.sub(r"\s*\(\d+\)\s*\(SQL\w+\).*$", "", msg).strip()
    low = msg.lower()
    if "check constraint" in low:
        m = re.search(r'CHECK constraint "([^"]+)"', msg)
        name = m.group(1) if m else ""
        return CHECK_MESSAGES.get(name, f"A database rule was broken ({name}).")
    if "primary key constraint" in low or "unique key constraint" in low or "duplicate key" in low:
        return "That value already exists (it must be unique)."
    if "reference constraint" in low:
        return "Other records depend on this one, so this change is not allowed."
    if "foreign key constraint" in low:
        return "A linked record does not exist."
    if "cannot insert the value null" in low:
        return "A required value is missing."
    return msg


def done(msg):
    """Remember a success message, then reload so every tab shows fresh data."""
    st.session_state["flash"] = msg
    st.rerun()


def _widget(f, key, default=None):
    t, label = f["type"], f["label"]
    if t == "text":
        return st.text_input(label, default or "", key=key)
    if t == "number":
        return st.number_input(label, min_value=0.0, value=float(default or 0), key=key)
    if t == "date":
        return st.date_input(label, value=default or datetime.date.today(),
                             min_value=datetime.date(1940, 1, 1), key=key)
    if t == "time":
        if isinstance(default, datetime.timedelta):
            default = (datetime.datetime.min + default).time()
        return st.time_input(label, value=default or datetime.time(9, 0), key=key)
    if t == "bool":
        return st.checkbox(label, value=bool(default) if default is not None else True, key=key)
    if t == "choice":
        opts = f["options"]
        idx = opts.index(default) if default in opts else 0
        return st.selectbox(label, opts, index=idx, key=key)
    if t == "fk":
        rows = fetch_all(f["sql"])              # query must return columns: id, label
        ids = [r["id"] for r in rows]
        names = {r["id"]: r["label"] for r in rows}
        if f.get("optional"):
            ids = [None] + ids
            names[None] = "-- none --"
        idx = ids.index(default) if default in ids else 0
        return st.selectbox(label, ids, index=idx, format_func=lambda i: names[i], key=key)


def crud_page(title, table, pk, fields, view_sql=None, custom_add=None,
              list_sql=None, lock_on_update=()):
    """pk: a column name, or a list of column names (composite key).
    list_sql: query for the dropdowns in Update/Delete; must return all table columns plus a 'label' column.
    lock_on_update: field names that cannot be edited in the Update tab (keys)."""
    pk_cols = [pk] if isinstance(pk, str) else list(pk)
    where = " AND ".join(f"{c}=%s" for c in pk_cols)
    st.header(title)
    t_add, t_view, t_upd, t_del = st.tabs(["➕ Add", "📋 View", "✏️ Update", "🗑️ Delete"])

    # ---------- CREATE ----------
    with t_add:
        if custom_add:
            custom_add()
        else:
            st.subheader("Add a new record")
            st.caption("Fill in the details below and press Save.")
            with st.form(f"{table}_add"):
                vals = {f["name"]: _widget(f, f"{table}_add_{f['name']}") for f in fields}
                ok = st.form_submit_button("Save")
            if ok:
                empty = [f["label"] for f in fields
                         if f["type"] == "text" and not f.get("optional") and not str(vals[f["name"]]).strip()]
                if empty:
                    st.error(f"Required: {', '.join(empty)}")
                else:
                    try:
                        cols = ", ".join(vals)
                        marks = ", ".join(["%s"] * len(vals))
                        execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", tuple(vals.values()))
                        done("Record added!")
                    except Exception as e:
                        st.error(f"Could not save: {friendly(e)}")

    # ---------- READ ----------
    with t_view:
        st.subheader("All records")
        q = st.text_input("🔍 Search", key=f"{table}_search")
        try:
            df = pd.DataFrame(fetch_all(view_sql or f"SELECT * FROM {table}"))
            if q and not df.empty:
                mask = df.astype(str).apply(lambda c: c.str.contains(q, case=False)).any(axis=1)
                df = df[mask]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(df)} record(s) found")
        except Exception as e:
            st.error(f"Could not load data: {friendly(e)}")

    rows = fetch_all(list_sql or f"SELECT * FROM {table}")
    label_of = lambda r: r["label"] if "label" in r else " | ".join(str(r[k]) for k in list(r)[:3])
    key_of = lambda r: "_".join(str(r[c]) for c in pk_cols)

    # ---------- UPDATE ----------
    with t_upd:
        st.subheader("Edit an existing record")
        if not rows:
            st.info("Nothing to update yet.")
        else:
            row = st.selectbox("Select record", rows, format_func=label_of, key=f"{table}_usel")
            new = {}
            for f in fields:
                if f["name"] in lock_on_update:
                    st.caption(f"🔒 {f['label']} cannot be changed here.")
                else:
                    new[f["name"]] = _widget(f, f"{table}_u_{f['name']}_{key_of(row)}", row[f["name"]])
            if st.button("Update", key=f"{table}_ubtn"):
                try:
                    sets = ", ".join(f"{c}=%s" for c in new)
                    execute(f"UPDATE {table} SET {sets} WHERE {where}",
                            tuple(new.values()) + tuple(row[c] for c in pk_cols))
                    done("Record updated!")
                except Exception as e:
                    st.error(f"Could not update: {friendly(e)}")

    # ---------- DELETE ----------
    with t_del:
        st.subheader("Delete a record")
        st.caption("This cannot be undone. Records that other data depends on are protected by the database.")
        if not rows:
            st.info("Nothing to delete.")
        else:
            row = st.selectbox("Record to delete", rows, format_func=label_of, key=f"{table}_dsel")
            sure = st.checkbox("I confirm I want to delete this record", key=f"{table}_dchk")
            if st.button("Delete", key=f"{table}_dbtn"):
                if not sure:
                    st.warning("Tick the confirmation box first.")
                else:
                    try:
                        execute(f"DELETE FROM {table} WHERE {where}", tuple(row[c] for c in pk_cols))
                        done("Record deleted.")
                    except Exception as e:
                        st.error(f"Cannot delete: {friendly(e)}")