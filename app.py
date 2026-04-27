import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

# ---------- DATABASE ----------
def connect_db():
    return sqlite3.connect("expenses.db", check_same_thread=False)

def create_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS
        expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            item TEXT,
            amount REAL,
            category TEXT
            )
              """)
    conn.commit()
    conn.close()
create_table()

def create_categories_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS
        categories(
              id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE
                )
            """)
    conn.commit()
    conn.close()
create_categories_table()    

def create_budget_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS
              budget (month TEXT PRIMARY KEY, amount REAL)
""")
    conn.commit()
    conn.close()
create_budget_table()

# ---------- CALLLING CAT TABLE FUNCTION ----------
def insert_default_categories():
    conn = connect_db()
    c = conn.cursor()

    default_categories = ["Food", "Transport", "Rent", "Bills", "Other"]
    for cat in default_categories:
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES(?)", (cat,))
    conn.commit()
    conn.close()
insert_default_categories()

def get_categories():
    conn = connect_db()
    df = pd.read_sql_query("SELECT name FROM categories", conn)
    conn.close()
    return df["name"].tolist()

def insert_category(name):
    conn = connect_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def sync_categories_from_df(df):
    conn = connect_db()
    c = conn.cursor()

    unique_cats = df["category"].dropna().unique()

    for cat in unique_cats:
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    conn.commit()
    conn.close()


# ---------- CRUD FUNCTIONS ----------
def add_expense(date, item, amount, category):
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO expenses (date, item, amount, category)
        VALUES (?, ?, ?, ?)""",
        (date, item, amount, category))
    conn.commit()
    conn.close()

def load_data():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    return df

def update_expense(id, date, item, amount, category):
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        UPDATE expenses
        SET item = ?, amount = ?, category = ?, date = ?
        WHERE id = ?""", (item, amount, category, date, id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

def save_budget(month, amount):
    conn = connect_db()
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO budget (month, amount) VALUES (?, ?)""", (month, amount))
    conn.commit()
    conn.close()

def get_budget(month):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT amount FROM budget WHERE month = ?", (month,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ---------- APP ----------
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Expense Tracker Dashboard")

# ---------------- SIDEBAR (USER INPUT) ----------------
st.sidebar.header("➕ Add Expense")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key="csv_uploader")
if uploaded_file is not None:
    file_id = uploaded_file.name

    if st.session_state.get("last_uploaded") != file_id:
        try:
            csv_df = pd.read_csv(uploaded_file)
            csv_df.columns = [col.strip().lower() for col in csv_df.columns]
            csv_df["date"] = pd.to_datetime(csv_df["date"], format="%d-%B-%Y", errors="coerce")
            csv_df = csv_df.dropna(subset=["date", "amount", "item", "category"])

            sync_categories_from_df(csv_df)

            for _, row in csv_df.iterrows():
                add_expense(row["date"].strftime("%Y-%m-%d"), row["item"], float(row["amount"]), row["category"])

            st.session_state["last_uploaded"] = file_id
            st.sidebar.success("CSV Uploaded Successfully!")
            st.rerun()

        except Exception as e:
            st.sidebar.error(f"Upload failed: {e}")

    if st.sidebar.button("Reset Upload"):
        st.session_state.pop("last_uploaded", None)
        st.rerun()

df = load_data()

# ---------- CLEAN DATA ----------
if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors = "coerce")
    df["Month"] = df["date"].dt.to_period("M")

categories = get_categories()

date = st.sidebar.date_input("Date")
item = st.sidebar.text_input("Item")
amount = st.sidebar.number_input("Amount", min_value=0.0)
category = st.sidebar.selectbox("Category", categories)

st.sidebar.subheader("Add New Category")
new_cat = st.sidebar.text_input("New Category")

if st.sidebar.button("Add Category"):
    if new_cat:
        insert_category(new_cat)
        st.sidebar.success("Category added!")
        st.rerun()

if st.sidebar.button("Add Expense"):
    if item and amount > 0:
        add_expense(str(date), item, amount, category)
        st.sidebar.success("✅ Expense Added!")
        st.rerun()
    else:
        st.sidebar.error("❌ Fill all fields properly")

# ---------- MONTH FILTER ----------
if not df.empty:
    months = sorted(df["Month"].dropna().unique())
    month_labels = [m.strftime("%B %Y") for m in months]

    selected_label = st.sidebar.selectbox("Select Month", month_labels)

    selected_month = months[month_labels.index(selected_label)]

    filtered_df = df[df["Month"] == selected_month]
else:
    filtered_df = df

# -------- DASHBOARD ----------
if not filtered_df.empty:

    filtered_df = filtered_df.copy()
    filtered_df["weekday"] = filtered_df["date"].dt.day_name()
    weekday_spend = filtered_df.groupby("weekday")["amount"].sum()
    top_day = weekday_spend.idxmax()

    total = filtered_df["amount"].sum()
    avg = filtered_df["amount"].mean()

    Transaction_days = len(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Spending", total)
    col2.metric("📊 Average Spending", f"{avg:.2f}")
    col3.metric("Transactions", Transaction_days)

    # --- Top Category ---
    if not filtered_df.empty:
        top_cat = filtered_df.groupby("category")["amount"].sum().idxmax()
    else:
        top_cat = "N/A"
    col4.metric("🥇 Top Category", top_cat)
    st.divider()

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        daily = filtered_df.groupby("date")["amount"].sum()
        max_day = daily.idxmax()
        max_value = daily.max()

        st.metric("📆 Highest Spending Day", max_day.strftime("%d %b"), f"{max_value:.2f}")

    with col6:
        if len(months) > 1:
            current_total = filtered_df["amount"].sum()
            months_sorted = sorted(months)
            current_index = months_sorted.index(selected_month)
            if current_index > 0:
                prev_month = months_sorted[current_index - 1]
                prev_df = df[df["Month"] == prev_month]
                prev_total = prev_df["amount"].sum()
                diff = current_total - prev_total
                st.metric("📈 vs Last Month", f"{diff:.2f}")
            else:
                st.metric("📈 vs Last Month", "N/A")

    with col7:
        no_of_days = filtered_df["date"].nunique()
        avg_daily = total/no_of_days if no_of_days > 0 else 0
        st.metric("Average Daily Spending", avg_daily)

    with col8:
        st.write("Top 3 expenses this month")

        if not filtered_df.empty:
            Top3 = filtered_df.sort_values(by="amount", ascending=False).head(3)
            st.dataframe(Top3, use_container_width=True)
        else:
            st.info("No data available")


    # ---------- CHARTS ----------
    col1, col2, col3 = st.columns(3)

    # --- Category Chart ---
    with col1:
        st.subheader("Category Breakdown")

        cat = filtered_df.groupby("category")["amount"].sum()

        fig, ax = plt.subplots(figsize=(5,3))
        cat.plot(kind="bar", ax=ax)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=False)

    # --- Daily Trend ---
    with col2:
        st.subheader("Daily Spending")
        daily = filtered_df.groupby("date")["amount"].sum().sort_index()
        fig2, ax2 = plt.subplots(figsize=(5,3))
        daily.plot(kind="line", marker = "o", ax=ax2)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2, use_container_width=False)
    st.divider()

    with col3:
        st.subheader("Spending per month")
        month_spending = df.groupby("Month")["amount"].sum()

        fig3, ax3 = plt.subplots(figsize=(5,3))
        month_spending.plot(kind="bar", ax=ax3)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig3, use_container_width=False)

    # ---------- TABLE ----------
    st.subheader("All Expenses")

    df_display = filtered_df.copy()
    df_display["date"] = df_display["date"].dt.strftime("%d %b %Y")
    st.dataframe(df_display, use_container_width=True)
    st.divider()

    # ---------- DELETE & EDIT ----------
    col1, col2 = st.columns(2)

    # ---------- DELETE ----------
    with col1:
        st.subheader("🧺 Delete Expenses")

        selected_ids = st.multiselect(
            "Select to delete", options=filtered_df["id"],
            format_func = lambda x: filtered_df[filtered_df["id"] == x]["item"].values[0])

        if st.button("Delete Selected"):
            if selected_ids:
                for i in selected_ids:
                    delete_expense(i)
                st.success("Deleted!")
                st.rerun()
            else:
                st.warning("No item selected")


    # ---------- EDIT ----------
    with col2:
        st.subheader("🖊 Edit Expense")

        edit_id = st.selectbox(
            "Select expense", filtered_df["id"],
            format_func= lambda x: filtered_df[filtered_df["id"] == x]["item"].values[0]
        )

        row = filtered_df[filtered_df["id"] == edit_id].iloc[0]
        
        new_date = st.date_input("Date", value= row["date"])
        new_item = st.text_input("Item", value= row["item"])
        new_amount = st.number_input("Amount", value= float(row["amount"]))

        if row["category"] in categories:
            idx = categories.index(row["category"])
        else:
            idx = 0
        new_category = st.selectbox("Category", categories, index= idx)

        if st.button("💾 Update Expense"):
            update_expense(edit_id, str(new_date), new_item, new_amount, new_category)
            st.success("✔ Expense Updated")
            st.rerun()
    st.divider()

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button("Download CSV", csv, "expenses.csv", "text/csv")

    # ---------- BUDGET ----------
    st.subheader("Budget Tracker")

    month_str = str(selected_month)

    existing_budget = get_budget(month_str)

    budget = st.number_input("Enter budget", value=float(existing_budget), min_value=0.0)

    if st.button("Save Budget"):
        save_budget(month_str, budget)
        st.success("Budget Saved!")

    if budget > 0:
        spending = filtered_df["amount"].sum()
        progress = min(spending / budget, 1.0)

        st.write(f"💸 Spending: {spending}")
        st.write(f"📉 Remaining: {budget - spending}")
        st.progress(progress)

        if spending > budget:
            st.error("❌ Exceeded budget!")
        elif spending > 0.8 * budget:
            st.warning("⚠ Close to limit")
        else:
            st.success("👍🏼 Within budget")
else:
    st.info("No data yet")