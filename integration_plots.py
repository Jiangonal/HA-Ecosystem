import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_csv("filtered_prs.csv")

# Filter rows based on "Type of Change"
new_integration_count = df[df['Type of Change'].str.contains('New integration', case=False, na=False)].copy()
new_feature_count = df[df['Type of Change'].str.contains('New feature', case=False, na=False)].copy()

# Extract the year from the "Created At" column
new_integration_count['Year'] = pd.to_datetime(new_integration_count['Created At']).dt.year
new_feature_count['Year'] = pd.to_datetime(new_feature_count['Created At']).dt.year

# Count the number of rows per year for each type
integration_per_year = new_integration_count['Year'].value_counts().sort_index()
feature_per_year = new_feature_count['Year'].value_counts().sort_index()

# Plotting the counts as a bar graph
plt.figure(figsize=(10, 6))
plt.bar(integration_per_year.index - 0.2, integration_per_year.values, width=0.4, label='New Integration')
plt.bar(feature_per_year.index + 0.2, feature_per_year.values, width=0.4, label='New Feature')
plt.xlabel('Year')
plt.ylabel('Number of Rows')
plt.title('Number of New Integrations and New Features by Year')
plt.xticks(sorted(set(integration_per_year.index).union(set(feature_per_year.index))))
plt.legend()
plt.grid(visible=True, linestyle='--', alpha=0.5)
plt.show()
