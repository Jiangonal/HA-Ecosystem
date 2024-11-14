import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_csv("pull_requests_filtered.csv")

merged_prs = df[df['State'] == 'merged']
closed_prs = df[df['State'] == 'closed']

fig, axes = plt.subplots(2, 2, figsize=(9, 9))
axes = axes.ravel()
fig.suptitle('Distributions of Integration-Related PR Characteristics')

for i, col_name in enumerate(['Files Changed', 'Decision Time', 'Total Comments', 'LOC Changed']):

    # Take 98th percentile as upper limit to avoid extreme outliers making the scale unreasonable
    upper_limit = np.percentile(
        pd.concat([merged_prs[col_name], closed_prs[col_name]]), 
        98 
    )
    bins = np.linspace(0, upper_limit, 20)

    axes[i].hist(merged_prs[col_name], bins=bins, color='skyblue', edgecolor='black', alpha=0.5, label='Merged PRs')
    axes[i].hist(closed_prs[col_name], bins=bins, color='salmon', edgecolor='black', alpha=0.5, label='Closed PRs')

    axes[i].set_title(col_name)
    axes[i].set_xlabel(col_name)
    axes[i].set_ylabel('Frequency')
    axes[i].set_xlim()
    axes[i].grid(visible=True, linestyle='--', alpha=0.5)

handles, labels = axes[0].get_legend_handles_labels()
labels[0] = f"Merged PRs ({len(merged_prs)} data points)"
labels[1] = f"Closed PRs ({len(closed_prs)} data points)"
fig.legend(handles, labels, loc='upper left')
plt.tight_layout(pad=2)
plt.show()