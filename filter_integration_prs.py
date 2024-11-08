import pandas as pd

df = pd.read_csv("pull_requests_all_with_checkbox_data.csv")
df = df[df['Type of Change'].isin(['New feature (which adds functionality to an existing integration)', 'New integration (thank you!)'])]
df = df.reset_index(drop=True)
print(df.head())
df.to_csv("pull_requests_filtered.csv", index=False)
