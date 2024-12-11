import pandas as pd
import matplotlib.pyplot as plt

file_path = 'pull_requests_filtered.csv'
df = pd.read_csv(file_path)

# Calculate correlation matrix for numeric columns
correlation_matrix = df[['Files Changed', 'Total Comments', 'Decision Time', 'LOC Changed']].corr()
print(correlation_matrix)
# Plot the correlation matrix
plt.figure(figsize=(8, 6))
plt.matshow(correlation_matrix, cmap='coolwarm', fignum=1)
plt.colorbar()
plt.title("Correlation Matrix", pad=20)
plt.show()

# Calculate the 75th percentile for each numeric column
percentiles = df[['Files Changed', 'Total Comments', 'Decision Time', 'LOC Changed']].quantile(0.75)
print(percentiles)
# Filter rows where any metric exceeds the 75th percentile
complex_entries = df[
    ((df['Files Changed'] >= percentiles['Files Changed']) |
    (df['Total Comments'] >= percentiles['Total Comments']) |
    (df['LOC Changed'] >= percentiles['LOC Changed'])) &
    (df['Decision Time'] >= percentiles['Decision Time']) 
]

# Display the filtered entries
complex_entries.to_csv('PRs_RQ1_2.csv', index=False)
# print("Filtered entries saved to 'complex_pull_requests1.csv'")