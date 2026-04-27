import pandas as pd
import requests

df = pd.read_csv("data.csv")

predicted_ages = []

for name in df["Name"]:
    url = f"https://api.agify.io/?name={name}"

    response = requests.get(url)
    data = response.json()

    predicted_ages.append(data["age"])

df["Predicted_Age"] = predicted_ages
df["Testing"] = {'uno':1, 'cutro':2, 'side':5, 'bal': 8, 'coo': 7}

print(df)
if data["age"] is not None:
    predicted_ages.append(data["age"])
else:
    predicted_ages.append(0)

df.to_csv("final_data.csv", index=False)