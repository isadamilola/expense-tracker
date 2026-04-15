import pandas as pd
import os

file = "daily_expenses.csv"

# Load or create a file
if os.path.exists(file):
    df = pd.read_csv(file)
else:
    df = pd.DataFrame(columns=["Date", "Item", "Amount", "Category"])

while True:
    print("\n==== EXPENSE TRACKER ===")
    print("1. Add Expenses")
    print("2. View Dashboard")
    print("3. Filter by Category")
    print("4. View Charts")
    print("5. Exit")

    choice = input("Choose option: ")

    if choice == "1":
        date = input('Enter date (e.g. 9 November 2026): ')
        item = input("Enter item: ")
        amount = int(input("Enter amount: "))
        category = input("Enter category: ")

        new_expense = {
            "Date": date,
            "Item": item,
            "Amount": amount,
            "Category": category,
        }
        
        df = pd.concat(
            [df, pd.DataFrame([new_expense])], ignore_index=True
        )

        df["Date"] = pd.to_datetime(df["Date"], format="%d %B %Y")
        df = df.sort_values(by="Date")
        df["Date"] = df["Date"].dt.strftime("%d %B %Y")

        df.to_csv(file, index = False)

        print("✔✅Expense added!")

    elif choice == "2":
        print("\n" + "="*35)
        print("\n📊 DASHBOARD")
        print("="*35)

        
        total_spent = df["Amount"].sum()
        max_expenses = df["Amount"].max()
        min_expenses = df["Amount"].min()
        avg = df["Amount"].mean()

        # Category analysis
        category_totals = df.groupby("Category")["Amount"].sum()
        top_category = category_totals.idxmax()
        top_amount = category_totals.max()

        # Row of highest expense
        max_row = df[df["Amount"] == max_expenses].iloc[0]
        max_item = max_row["Item"]

        
        print(f"💰 Total Spent   :   {total_spent}")
        print(f"😢  Highest Expense: {max_expenses} ({max_item})")
        print(f"📉   Lowest spending  :  {min_expenses}")
        print(f"📊  Average Spending   :   {avg:2f}")
        
        print("\n📂 Category Breakdown:")
        for cat, amt in category_totals.items():
            print(f"  ➡  {cat:<15}: {amt}")

        print(f"\n🏆 Most Expensive Category:  {top_category} ({top_amount})")


    elif choice == "3":
        cat = input("Enter category: ")
        print(df[df["Category"] == cat])

    elif choice == "4":
        import matplotlib.pyplot as plt

        category_totals = df.groupby("Category")["Amount"].sum()

        plt.figure(figsize=(12,5))

        # Bar Chart
        plt.subplot(1,2,1)
        category_totals.plot(kind="bar")
        plt.title("Expenses by Category")
        plt.xlabel("Category")
        plt.ylabel("Amount")

        # Pie Chart
        plt.subplot(1, 2, 2)
        category_totals.plot(kind="pie", autopct="%1.1f%%")
        plt.title("Expense Distribution")
        plt.ylabel("")

        plt.tight_layout()
        plt.show()


    elif choice == "5":
        print("👋🏼 Goodbye! 😊")
        break
    else:
        print("❌Invalid option")