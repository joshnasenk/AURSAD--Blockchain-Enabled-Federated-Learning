import pandas as pd

df = pd.read_csv("data/aursad.csv")
print("Label counts:")
print(df.iloc[:, -1].value_counts())
print("\nSample rows:")
print(df.head())
