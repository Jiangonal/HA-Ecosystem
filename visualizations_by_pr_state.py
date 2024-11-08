import pandas as pd
import matplotlib.pyplot as plt

merged_df = pd.read_csv('pull_requests_filtered_merged.csv')
closed_df = pd.read_csv('pull_requests_filtered_closed.csv')

fig, axes = plt.subplots(2, 2, figsize=(9, 9))
axes = axes.ravel()
fig.suptitle('Distributions of Integration-Related PR Characteristics')

# for i, col_name in enumerate(['Files Changed', 'Decision Time', 'Total Comments', 'LOC Changed']):    currently don't have LOC changed
for i, col_name in enumerate(['Files Changed', 'Decision Time', 'Total Comments']):
    axes[i].hist(merged_df[col_name], bins=20, color='skyblue', edgecolor='black', alpha=0.5, label='Merged PRs')
    axes[i].hist(closed_df[col_name], bins=20, color='salmon', edgecolor='black', alpha=0.5, label='Closed PRs')

    axes[i].set_title(col_name)
    axes[i].set_xlabel(col_name)
    axes[i].set_ylabel('Frequency')
    axes[i].grid()

handles, labels = axes[0].get_legend_handles_labels()
labels[0] = f"Merged PRs ({len(merged_df)} data points)"
labels[1] = f"Closed PRs ({len(closed_df)} data points)"
fig.legend(handles, labels, loc='upper left')
plt.tight_layout(pad=2)
plt.show()

