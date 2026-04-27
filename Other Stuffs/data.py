import pandas as pd

file = "expenses_full_date.csv"

cat = pd.read_csv(file)

print(cat["Category"].unique())
