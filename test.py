import pandas as pd

# Define file paths
file1_path = 'category_totals_feats_json.csv'
file2_path = 'category_totals_Json.csv'


# Load both CSV files
df1 = pd.read_csv(file1_path)
df2 = pd.read_csv(file2_path)
top1 = df1.nlargest(11, 'Total Count')
top2 = df2.nlargest(11, 'Total Count')


print(top1)
print(top2)