import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import shutil

# -------- CONFIG ----------
file = "daily_expenses.csv"

st.set_page_config(page_title="Medra Expense Tracker", layout="wide")
st.title("💰 Expense Tracker Dashboard")

# ---------------- BACKUP ----------------
if os.path.exists(file):
    shutil.copy(file, "backup_expenses.csv")

# ---------------- LOAD DATA or CREATE DATA ----------------
if os.path.exists(file):
    df=pd.read_csv(file)
else:
    df = pd.DataFrame(columns=["Date", "Item", "Amount", "Category"])

st.write("COLUMNS:", df.columns)

if "ID" not in df.columns: df["ID"] = range(1, len(df) + 1)

# ---------------- CLEAN, CONVERT, FIX DATA ----------------
if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # FIX BAD YEARS (0001 → 2026)
    df["Date"] = df["Date"].apply(
        lambda x: x.replace(year=2026) if pd.notnull(x) and x.year < 2000 else x
    )

    df["MonthYear"] = df["Date"].dt.strftime("%B %Y")
    # Temporarily on hold
    # df = df[df["Date"].notna()]

# ---------------- SIDEBAR (USER) INPUT ----------------
st.sidebar.header("➕ Add New Expense")

categories = list(df["Category"].dropna().unique()) if not df.empty else []
categories += ["Other"]

date = st.sidebar.date_input("Select Date")
item = st.sidebar.text_input("Item")
amount = st.sidebar.number_input("Amount", min_value=0)
category = st.sidebar.selectbox("Category", categories)

    # Monthly total ===== Monthly selector
selected_month = st.sidebar.selectbox("Select Month",
sorted(df["MonthYear"].dropna().unique()))

if st.sidebar.button("Add Expense"):

    if item == "" or category == "" or amount == 0:
        st.sidebar.error("❌ Please fill all fields properly")

    else:
        new_expense = {
            "ID": df["ID"].max() + 1 if not df.empty else 1,
            "Date": pd.to_datetime(date),
            "Item": item,
            "Amount": amount,
            "Category": category,
        }

    # ====== SAVING FILE ===========

        df = pd.concat([df, pd.DataFrame([new_expense])], ignore_index=True)
    
        df.to_csv(file, index=False, date_format="%Y-%m-%d")
        st.sidebar.success("✅ Expense Added!")

        st.rerun()

# ---------------- PROCESS DATA (filters, calculations) -----------
filtered_df = df[df["MonthYear"] == selected_month]


# ---------------- DISPLAY (dashboard, charts) ----------------

    # -------- dashboard ----------
if len(df) > 0:

    total = filtered_df["Amount"].sum()
    avg = filtered_df["Amount"].mean()
    max_exp = filtered_df["Amount"].max()
    min_exp = filtered_df["Amount"].min()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total", total)
    col2.metric("📊 Average", f"{avg:.2f}")
    col3.metric("🔥 Highest", max_exp)
    col4.metric("📉 Lowest", min_exp)

    st.divider()

    # -------- CATEGORY SUMMARY (Charts) --------
    category_totals = filtered_df.groupby("Category")["Amount"].sum()

    if not category_totals.empty:

        col5, col6 = st.columns(2)

        # Bar Chart
        with col5:
            st.subheader("📊 Expenses by Category")
            fig, ax = plt.subplots()
            category_totals.plot(kind="bar", ax=ax)
            st.pyplot(fig)

        # Pie Chart
        with col6:
            st.subheader("🥧 Distribution")
            fig2, ax2 = plt.subplots()
            category_totals.plot(kind="pie", autopct="%1.1f%%", ax=ax2)
            ax2.set_ylabel("")
            st.pyplot(fig2)

    else:
        st.warning("No category data to display charts yet")

        # Line Chart
    st.subheader("💹 Daily Spending Trend")

    daily_total = filtered_df.groupby("Date")["Amount"].sum()
    daily_total = daily_total.sort_index()

    fig, ax = plt.subplots()
    daily_total.plot(kind="line", marker="o", ax=ax)

    ax.set_title("Daily Spending")
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")

    st.pyplot(fig)

    # -------- Cleaner display (don't know what to call it yet, buh I think that's what it's for)
    st.divider()

    df_display = df.copy()
    df_display["Date"] = df_display["Date"].dt.strftime("%d %B %Y")

    st.dataframe(df_display)

    # ------ MONTHLY TREND ---------
    st.subheader("📊 Monthly Spending Trend")

    monthly_total = df.groupby("MonthYear")["Amount"].sum()

    monthly_total = monthly_total.sort_index()

    fig, ax = plt.subplots()
    monthly_total.plot(kind="line", marker ="o", ax=ax)

    ax.set_title("Monthly Spending")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount")

    st.pyplot(fig)

    # -------- Highest Expenses ------
    st.subheader("🏆 Top 5 Highest Expenses")

    top5 = filtered_df.sort_values(by="Amount", ascending=False).head(5)
    top5_display = top5.copy()
    top5_display["Date"] = top5_display["Date"].dt.strftime("%d %B %Y")

    st.dataframe(top5_display)

    # -------- TABLE --------
    st.subheader("📋 All Expenses (Select to Delete)")

    df_display = df.copy()
    df_display["Date"] = df_display["Date"].dt.strftime("%d %B %Y")

    # checkbox selection
    selected_ids = st.multiselect(
        "Select expenses to delete", options=df_display["ID"], format_func=lambda x:
        df_display[df_display["ID"] == x]["Item"].values[0]
    )

    st.dataframe(df_display, use_container_width=True)

    # Delete  button
    if st.button("🧺 Delete Selected Items"):
        if selected_ids:
            df = df[~df["ID"].isin(selected_ids)]
            df.to_csv(file, index=False)
            st.success("🧺 Selected expenses deleted!")
            st.rerun()
        else:
            st.warning("No items selected")

    # Editing data
    st.subheader("🖊 Edit Expense")

    # I need a clear button or clear field after update expense cos all the edits remain after
    edit_id = st.selectbox(
        "Select expense to edit", df["ID"],
        format_func= lambda x: df[df["ID"] == x]["Item"].values[0]
    )
    edit_row = df[df["ID"] == edit_id].iloc[0]
    
    edit_date = st.date_input("Edit Date", value= edit_row["Date"])
    edit_item = st.text_input("Edit Item", value=edit_row["Item"], key="edit_item")
    edit_amount = st.number_input("Edit Amount", value= edit_row["Amount"])
    edit_category = st.selectbox("Edit Category", df["Category"].dropna().unique(),
                                 
    index= list(df["Category"].dropna().unique()).index(edit_row["Category"]))


    if st.button("💾 Update Expense"):
        df.loc[df["ID"] == edit_id, "Date"] = pd.to_datetime(edit_date)
        df.loc[df["ID"] == edit_id, "Item"] = edit_item
        df.loc[df["ID"] == edit_id, "Amount"] = edit_amount
        df.loc[df["ID"] == edit_id, "Category"] = edit_category

        df.to_csv(file, index=False)
        st.success("✔ Expense updated")

        st.rerun()

    # Budget Tracker 1
    st.subheader("Budget Tracker")
    budget = st.number_input("Enter budget amount", min_value=0)

    # Avoid division error
    if budget > 0:

        total_spending = filtered_df["Amount"].sum()
        remaining = budget - total_spending

        st.write(f"💲 Budget: {budget}")
        st.write(f"💸 Spending: {total_spending}")
        st.write(f"📉 Remaining: {remaining}")

        # Progress calculation and display
        progress = total_spending / budget
        progress = min(progress, 1.0)
        st.progress(progress)

        # Status message
        if total_spending < budget:
            st.success("✅ You're within budget. Good job!")
        elif total_spending == budget:
            st.warning("⚠ You've reached your budget limit")
        elif total_spending >= 0.8 * budget:
            st.warning("⚠ You're close to your budget limit!")
        else:
            st.error("❌ You've exceeded your budget!")


else:
    st.info("No data yet. Add your first expense 👈🏼")
