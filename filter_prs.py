import pandas as pd


df = pd.read_csv("pull_requests_all_with_checkbox_data.csv")
df = df[df['Type of Change'].isin(['New feature (which adds functionality to an existing integration)', 'New integration (thank you!)'])]
df = df.drop_duplicates()
df = df.reset_index(drop=True)

df.to_csv("pull_requests_filtered.csv", index=False)

# Get 'complex' pull requests for new integrations and new features, and shuffle entries
complex_prs = df[df['Decision Time'] >= 7]
complex_prs_integration = complex_prs[complex_prs['Type of Change'].str.contains('New integration')].sample(frac=1)
complex_prs_feature = complex_prs[complex_prs['Type of Change'].str.contains('New feature')].sample(frac=1)

complex_prs_integration.to_csv("pull_requests_complex_integrations.csv", index=False)
complex_prs_feature.to_csv("pull_requests_complex_features.csv", index=False)
