"""Reusable CRUD page. Every entity page is built from this one function."""
import datetime
import pandas as pd
import streamlit as st
from db import fetch_all, execute


def _widget(f, key, default=None):
    t, label = f["type"], f["label"]
    if t == "text":
        return st.text_input(label, default or "", key=key)
    if t == "number":
        return st.number_input(label, min_value=0.0, value=float(default or 0), key=key)
    if t == "int":
        return st.number_input(label, min_value=0, step=1, value=int(default or 0), key=key)
    if t == "date":
        return st.date_input(label, value=default or datetime.date.today(),
                             min_value=datetime.date(1940, 1, 1), key=key)
    if t == "choice":
        opts = f["options"]
        idx = opts.index(default) if default in opts else 0
        return st.selectbox(label, opts, index=idx, key=key)
    if t == "fk":   # dropdown filled from another table
        rows = fetch_all(f["sql"])              # needs columns: id, label
        ids = [r["id"] for r in rows]
        names = {r["id"]: r["label"] for r in rows}
        if f.get("optional"):
            ids = [None] + ids
            names[None] = "-- none --"
        idx = ids.index(default) if default in ids else 0
        return st.selectbox(label, ids, index=idx, format_func=lambda i: names[i], key=key)


def crud_page(title, table, pk, fields, view_sql=None):
    st.header(title)
    t_add, t_view, t_upd, t_del = st.tabs(["➕ Add", "📋 View", "✏️ Update", "🗑️ Delete"])

    # ---------- CREATE ----------
    with t_add:
        with st.form(f"{table}_add"):
            vals = {f["name"]: _widget(f, f"{table}_add_{f['name']}") for f in fields}
            ok = st.form_submit_button("Save")
        if ok:
            first = fields[0]["name"]
            if first and fields[0]["type"] == "text" and not str(vals[first]).strip():
                st.error(f"{fields[0]['label']} is required.")
            else:
                try:
                    cols = ", ".join(vals)
                    marks = ", ".join(["%s"] * len(vals))
                    execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", tuple(vals.values()))
                    st.success("Record added!")
                except Exception as e:
                    st.error(f"Could not save: {e}")

    # ---------- READ ----------
    with t_view:
        q = st.text_input("🔍 Search", key=f"{table}_search")
        try:
            df = pd.DataFrame(fetch_all(view_sql or f"SELECT * FROM {table}"))
            if q and not df.empty:
                mask = df.astype(str).apply(lambda c: c.str.contains(q, case=False)).any(axis=1)
                df = df[mask]
            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not load data: {e}")

    rows = fetch_all(f"SELECT * FROM {table}")
    label_of = lambda r: " | ".join(str(r[k]) for k in list(r)[:3])

    # ---------- UPDATE ----------
    with t_upd:
        if not rows:
            st.info("Nothing to update yet.")
        else:
            row = st.selectbox("Select record", rows, format_func=label_of, key=f"{table}_usel")
            new = {f["name"]: _widget(f, f"{table}_u_{f['name']}_{row[pk]}", row[f["name"]])
                   for f in fields}
            if st.button("Update", key=f"{table}_ubtn"):
                try:
                    sets = ", ".join(f"{c}=%s" for c in new)
                    execute(f"UPDATE {table} SET {sets} WHERE {pk}=%s", tuple(new.values()) + (row[pk],))
                    st.success("Record updated! Open the View tab to see it.")
                except Exception as e:
                    st.error(f"Could not update: {e}")

    # ---------- DELETE ----------
    with t_del:
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
                        execute(f"DELETE FROM {table} WHERE {pk}=%s", (row[pk],))
                        st.success("Record deleted.")
                    except Exception:
                        st.error("Cannot delete: other records depend on this one (foreign key protection).")