import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("expenses2.csv")
df.columns = df.columns.str.strip().str.lower()
print(df.columns)

print("Your Raw Data:")
print(df)

#Total spent
total_spent =df["amount"].sum()
print("\nTotal Spent:", total_spent)

# Group by category
category_totals = df.groupby("category")["amount"].sum()

print("\nSpending by Category:")
print(category_totals)

# Plot
category_totals.plot(kind="bar")
plt.title("Spending by Category")
plt.xlabel("Category")
plt.ylabel("amount")
plt.show()