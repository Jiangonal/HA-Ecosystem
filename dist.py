import pandas as pd

# Load the CSV files

df = pd.read_csv('RQ3_SO_feat.csv')
df1 = pd.read_csv('rq3_feat_rel.csv')
print(df,df1)
# Merge the DataFrames based on matching titles
merged_df = df1.merge(df[['StackOverflow Title', 'SO link','SO Creation Date','SO Last Activity Date']], left_on='SO Title', right_on='StackOverflow Title', how='left')

# Save the merged DataFrame to a new CSV file
print(merged_df)
merged_df.to_csv('updated_rq3_feat.csv', index=False)

