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
        CREATE TABLE IF NOT EXISTS expenses (
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
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()
create_categories_table()

def create_budget_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            month TEXT PRIMARY KEY,
            amount REAL
        )
    """)
    conn.commit()
    conn.close()
create_budget_table()

# ---------- CATEGORY ----------
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
    for cat in df["category"].dropna().unique():
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    conn.commit()
    conn.close()

# ---------- CRUD ----------
def add_expense(date, item, amount, category):
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (date, item, amount, category) VALUES (?, ?, ?, ?)",
        (date, item, amount, category)
    )
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
        SET item=?, amount=?, category=?, date=?
        WHERE id=?
    """, (item, amount, category, date, id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()

def save_budget(month, amount):
    conn = connect_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO budget VALUES (?, ?)", (month, amount))
    conn.commit()
    conn.close()

def get_budget(month):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT amount FROM budget WHERE month=?", (month,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ---------- APP ----------
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Expense Tracker Dashboard")

# ---------- SIDEBAR ----------
st.sidebar.header("➕ Add Expense")

# ===== CSV UPLOAD (FIXED) =====
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        csv_df = pd.read_csv(uploaded_file)
        csv_df.columns = [c.lower().strip() for c in csv_df.columns]

        required = {"date", "item", "amount", "category"}
        if not required.issubset(csv_df.columns):
            st.sidebar.error(f"CSV must contain {required}")
        else:
            csv_df["date"] = pd.to_datetime(csv_df["date"], errors="coerce")
            csv_df["amount"] = pd.to_numeric(csv_df["amount"], errors="coerce")

            csv_df = csv_df.dropna(subset=["date", "amount", "item", "category"])

            sync_categories_from_df(csv_df)

            for _, row in csv_df.iterrows():
                add_expense(str(row["date"]), row["item"], row["amount"], row["category"])

            st.sidebar.success(f"✅ Uploaded {len(csv_df)} rows")

            # 🔥 CRITICAL FIX
            st.session_state["file_uploaded"] = True
            st.rerun()

    except Exception as e:
        st.sidebar.error(f"❌ Upload failed: {e}")

if "file_uploaded" in st.session_state:
    del st.session_state["file_uploaded"]

# ---------- LOAD DATA ----------
df = load_data()

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["Month"] = df["date"].dt.to_period("M")

# ---------- MANUAL INPUT ----------
categories = get_categories()

date = st.sidebar.date_input("Date")
item = st.sidebar.text_input("Item")
amount = st.sidebar.number_input("Amount", min_value=0.0)
category = st.sidebar.selectbox("Category", categories)

if st.sidebar.button("Add Expense"):
    if item and amount > 0:
        add_expense(str(date), item, amount, category)
        st.rerun()

# ---------- MONTH FILTER ----------
if not df.empty:
    months = sorted(df["Month"].dropna().unique())
    labels = [m.strftime("%B %Y") for m in months]

    selected_label = st.sidebar.selectbox("Select Month", labels)
    selected_month = months[labels.index(selected_label)]

    filtered_df = df[df["Month"] == selected_month]
else:
    filtered_df = df

# ---------- DASHBOARD ----------
if not filtered_df.empty:

    total = filtered_df["amount"].sum()
    avg = filtered_df["amount"].mean()

    col1, col2 = st.columns(2)
    col1.metric("Total", total)
    col2.metric("Average", f"{avg:.2f}")

    # Chart
    st.subheader("Spending by Category")
    cat = filtered_df.groupby("category")["amount"].sum()

    fig, ax = plt.subplots()
    cat.plot(kind="bar", ax=ax)
    st.pyplot(fig)

    # Table
    st.subheader("All Expenses")
    df_display = filtered_df.copy()
    df_display["date"] = df_display["date"].dt.strftime("%d %b %Y")
    st.dataframe(df_display)

else:
    st.info("No data yet")