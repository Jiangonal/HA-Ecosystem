import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("pull_requests_filtered.csv")

# Filter rows based on "Type of Change"
new_integration_prs = df[df['Type of Change'].str.contains('New integration')]
new_feature_prs = df[df['Type of Change'].str.contains('New feature')]

# Extract the year from the "Created At" column
new_integration_prs['Year'] = pd.to_datetime(new_integration_prs['Created At']).dt.year
new_feature_prs['Year'] = pd.to_datetime(new_feature_prs['Created At']).dt.year

# Count the number of rows per year for each type
integrations_per_year = new_integration_prs['Year'].value_counts().sort_index()
features_per_year = new_feature_prs['Year'].value_counts().sort_index()

# Plotting the counts as a bar graph
plt.figure(figsize=(10, 6))
plt.bar(integrations_per_year.index - 0.2, integrations_per_year.values, width=0.4, edgecolor='black', label='New Integration')
plt.bar(features_per_year.index + 0.2, features_per_year.values, width=0.4, edgecolor='black', label='New Feature')
plt.xlabel('Year')
plt.ylabel('Number of Rows')
plt.title('Number of New Integrations and New Features by Year')
plt.xticks(sorted(set(integrations_per_year.index).union(set(features_per_year.index))))
plt.legend()
plt.grid(visible=True, linestyle='--', alpha=0.5)
plt.show()
