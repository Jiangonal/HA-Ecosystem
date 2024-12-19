import pandas as pd

# Load the datasets
comments_commits_df = pd.read_csv('pull_request_comments_commits_codeowners.csv')
rq2_int_df = pd.read_csv('RQ2_FEAT.csv')

# Extract pull request URLs from rq2_int_df
rq2_int_urls = rq2_int_df['URL'].unique()

# Filter the comments_commits_df based on these URLs
filtered_comments_commits_df = comments_commits_df[comments_commits_df['Pull Request URL'].isin(rq2_int_urls)]

# Save the filtered DataFrame to a new CSV file
filtered_comments_commits_df.to_csv('RQ2_FEAT_COMMENTS.csv', index=False)

