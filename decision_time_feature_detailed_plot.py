import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

SECONDARY_CHARACTERISTIC = 'LOC Changed'   # replace with 'Files Changed', 'Total Comments', 'LOC Changed' etc

df = pd.read_csv("pull_requests_filtered.csv")
new_feature_prs = df[df['Type of Change'].str.contains('New feature')]
decision_times = new_feature_prs['Decision Time']
secondary_characteristic = new_feature_prs[SECONDARY_CHARACTERISTIC]

bins = [0, 3, 7, 30, np.percentile(df['Decision Time'], 98)]

bin_indices = np.digitize(decision_times, bins)  # assign each PR to its bin index

secondary_characteristic_by_bin = [
    secondary_characteristic[bin_indices == i]
    for i in range(1, len(bins))
]
capped_secondary_characteristic_by_bin = [
    np.clip(bin_data, None, np.percentile(secondary_characteristic, 98))    # stop outliers making axes huge by taking 98th percentile cutoff
    for bin_data in secondary_characteristic_by_bin
]

plt.figure(figsize=(12, 8))
fig, ax = plt.subplots(figsize=(12, 8))
hist_counts, bin_edges, _ = ax.hist(
    decision_times, bins=bins, edgecolor='black', alpha=0.7, label='PR Count', align='mid'
)
plt.xscale('log')

# create secondary y-axis for the box plots
ax2 = ax.twinx()

log_bins = np.log10(bins[1:])
log_bins = np.insert(log_bins, 0, [0])

# add box plots for each bin
bin_centers = [10 ** (((log_bins[i] + log_bins[i + 1])) / 2) for i in range(len(log_bins) - 1)]  # center positions for box plots
for i, secondary_characteristic_data in enumerate(capped_secondary_characteristic_by_bin):
    ax2.boxplot(
        secondary_characteristic_data,
        positions=[bin_centers[i]],  # place the box plot at the bin center
        widths=(bins[i + 1] - bins[i]) * 0.2,  # adjust width to match bin size
        vert=True,
        patch_artist=True,
        boxprops=dict(facecolor="lightblue", color="black"),
    )

ax.set_xticks([1] + bins[1:], [str(int(b)) for b in bins])      # log scale, so use 1 as first value as log(1) = 0 for first tick

plt.title('Distribution of Decision Time for New Feature PRs')
ax.set_xlabel('Decision Time (days)')
ax.set_ylabel('Number of PRs')
ax2.set_ylabel(SECONDARY_CHARACTERISTIC)
plt.grid(visible=True, linestyle='--', alpha=0.5)

plt.savefig(f'plot-images/decision_time_with_{'_'.join(SECONDARY_CHARACTERISTIC.lower().split())}.png')
plt.show()

