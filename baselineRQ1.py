import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
file_path = 'pull_requests_filtered.csv'
df = pd.read_csv(file_path)

# columns_of_interest = ['Files Changed', 'Total Comments', 'Decision Time', 'LOC Changed']

# # Filter DataFrames for new device and new feature integrations
# new_integration_prs = df[df['Type of Change'].str.contains('New integration', case=False, na=False)][columns_of_interest]
# new_feature_prs = df[df['Type of Change'].str.contains('New feature', case=False, na=False)][columns_of_interest]

# # Generate summary statistics for both
# dev_stats = new_integration_prs.describe()
# feat_stats = new_feature_prs.describe()

# # Print the statistics
# print("New Device PRs Summary Statistics:\n", dev_stats)
# print("\nNew Feature PRs Summary Statistics:\n", feat_stats)


def feat_vs_int(df):
    new_integration_prs = df[df['Type of Change'].str.contains('New integration')]
    new_feature_prs = df[df['Type of Change'].str.contains('New feature')]

    # Count the total number of rows for each type
    total_integrations = new_integration_prs.shape[0]
    total_features = new_feature_prs.shape[0]

    # Count the number of merged PRs for each type
    merged_integrations = new_integration_prs[new_integration_prs['State'] == 'merged'].shape[0]
    merged_features = new_feature_prs[new_feature_prs['State'] == 'merged'].shape[0]

    # Categories and counts
    categories = ['New Integration', 'New Feature']
    totals = [total_integrations, total_features]
    merged = [merged_integrations, merged_features]

    # -------------------- First Plot: Bar Graph --------------------
    plt.figure(figsize=(10, 6))
    x = range(len(categories))  # x positions for the bars

    # Plot total PRs
    bars1 = plt.bar([pos - 0.2 for pos in x], totals, width=0.4, color='blue', edgecolor='black', label='Total PRs')

    # Plot merged PRs
    bars2 = plt.bar([pos + 0.2 for pos in x], merged, width=0.4, color='orange', edgecolor='black', label='Merged PRs')

    # Labeling and title
    plt.xlabel('Type of Change')
    plt.ylabel('Number of PRs')
    plt.title('Total and Merged New Integration and New Feature PRs')
    plt.xticks(x, categories)
    plt.legend()
    plt.grid(visible=True, linestyle='--', alpha=0.5)

    # Add labels on top of the bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height + 2, f'{height}', ha='center', va='bottom', fontsize=12)

    plt.tight_layout()
    plt.show()

    # -------------------- Second Plot: Numerical Display --------------------
    plt.figure(figsize=(8, 5))

    # Display totals and merged as text
    table_data = [
        ['New Integration', total_integrations, merged_integrations],
        ['New Feature', total_features, merged_features]
    ]

    # Convert to pandas DataFrame for tabular visualization
    table_df = pd.DataFrame(table_data, columns=['Type of Change', 'Total PRs', 'Merged PRs'])
    print(table_df)

    # Display the table as part of the graph
    plt.axis('tight')
    plt.axis('off')
    plt.table(cellText=table_df.values, colLabels=table_df.columns, loc='center', cellLoc='center')
    plt.title('Summary of PR Counts')
    plt.tight_layout()
    plt.show()



def correlation(df):
    # Calculate correlation matrix for numeric columns
    correlation_matrix = df[['Files Changed', 'Total Comments', 'Decision Time', 'LOC Changed']].corr()
    print(correlation_matrix)
    # Plot the correlation matrix
    plt.figure(figsize=(8, 6))
    plt.matshow(correlation_matrix, cmap='coolwarm', fignum=1)
    plt.colorbar()
    plt.title("Correlation Matrix", pad=20)
    plt.show()




# def plots_stats(df):
#     # Filter rows based on "Type of Change"
#     dev_prs = df[df['Type of Change'].str.contains('New device')]
#     feat_prs = df[df['Type of Change'].str.contains('New feature')]

#     def create_histogram(decision_times, bins, title_label):
#         # Create histogram
#         fig, ax = plt.subplots(figsize=(12, 8))
#         ax.hist(decision_times, bins=bins, edgecolor='black', alpha=0.7, label='PR Count', align='mid', color='blue')
       
#         ax.set_xlabel('Decision Time (days)')
#         ax.set_ylabel('Number of PRs')
#         ax.grid(visible=True, linestyle='--', alpha=0.5)

#         # Custom x-axis labels for bins
#         bin_medians = [
#             np.median(decision_times[(decision_times >= bins[i]) & (decision_times < bins[i + 1])])
#             if len(decision_times[(decision_times >= bins[i]) & (decision_times < bins[i + 1])]) > 0 else 0
#             for i in range(len(bins) - 1)
#         ]
#         x_labels = [f"{int(bins[i])}-{int(bins[i + 1])}\n(Median: {int(median)})"
#                     for i, median in enumerate(bin_medians)]
#         ax.set_xticks([(bins[i] + bins[i + 1]) / 2 for i in range(len(bins) - 1)])
#         ax.set_xticklabels(x_labels, rotation=45, ha='right')

#         plt.title(f'{title_label} vs Decision Time')
#         plt.tight_layout()
#         plt.show()

#     # Define bins for decision times using percentiles
#     percentiles = np.percentile(df['Decision Time'], [0, 25, 50, 75, 100])
#     bins = list(percentiles)

#     # Generate separate plots for Integration and Feature PRs
#     create_histogram(int_prs['Decision Time'], bins, "New Device Integration PRs")
#     create_histogram(feat_prs['Decision Time'], bins, "New Feature PRs")

# plots_stats(df)
