import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

file_path = 'pull_requests_filtered.csv'
df = pd.read_csv(file_path)
dev_prs = df[df['Type of Change'].str.contains('New integration', case=False, na=False)]
feat_prs = df[df['Type of Change'].str.contains('New feature', case=False, na=False)]
# Calculate the 75th percentile for each numeric column
percentiles = dev_prs[['Files Changed', 'Total Comments', 'Decision Time', 'LOC Changed']].quantile(0.75)

# Filter rows where any metric exceeds the 75th percentile
complex_entries_dev = dev_prs[
    ((dev_prs['Files Changed'] >= percentiles['Files Changed']) |
    (dev_prs['Total Comments'] >= percentiles['Total Comments']) |
    (dev_prs['LOC Changed'] >= percentiles['LOC Changed'])) &
    (dev_prs['Decision Time'] >= percentiles['Decision Time']) 
]

complex_entries_dev.to_csv('PRs_RQ1_dev.csv', index=False)

percentiles = feat_prs[['Files Changed', 'Total Comments', 'Decision Time', 'LOC Changed']].quantile(0.75)

# Filter rows where any metric exceeds the 75th percentile
complex_entries_feat = feat_prs[
    ((feat_prs['Files Changed'] >= percentiles['Files Changed']) |
    (feat_prs['Total Comments'] >= percentiles['Total Comments']) |
    (feat_prs['LOC Changed'] >= percentiles['LOC Changed'])) &
    (feat_prs['Decision Time'] >= percentiles['Decision Time']) 
]

complex_entries_feat.to_csv('PRs_RQ1_feat.csv', index=False)





