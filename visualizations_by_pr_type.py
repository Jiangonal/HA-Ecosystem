import pandas as pd
import matplotlib.pyplot as plt

merged_df = pd.read_csv('pull_requests_filtered_merged.csv')

# get two possible column values to make grouping easier (remove permutations with 'Bugfix' or 'Dependency' along with 'New feature')
merged_df['Type of Change'] = merged_df['Type of Change'].apply(lambda value: 'New feature' if 'New feature' in value else 'New integration')
merged_df = merged_df.groupby('Type of Change')

fig, axes = plt.subplots(2, 2, figsize=(9, 9))
axes = axes.ravel()

# for i, col_name in enumerate(['Files Changed', 'Decision Time', 'Total Comments', 'LOC Changed']):    don't have LOC Changed currently
for i, col_name in enumerate(['Files Changed', 'Decision Time', 'Total Comments']):
    axes[i].hist(merged_df.get_group('New integration')[col_name], bins=20, color='salmon', edgecolor='black', alpha=0.5, label='New integration')
    axes[i].hist(merged_df.get_group('New feature')[col_name], bins=20, color='skyblue', edgecolor='black', alpha=0.5, label='New feature')

    axes[i].set_title(col_name)
    axes[i].set_xlabel(col_name)
    axes[i].set_ylabel('Frequency')
    axes[i].grid()

handles, labels = axes[0].get_legend_handles_labels()
labels[0] = f"New integration ({len(merged_df.get_group('New integration'))} data points)"
labels[1] = f"New feature ({len(merged_df.get_group('New feature'))} data points)"
fig.legend(handles, labels, loc='upper left')
fig.suptitle('Distributions of Integration-Related Merged PR Characteristics')

plt.tight_layout(pad=2)
plt.show()

