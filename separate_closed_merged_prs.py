import csv
import pandas as pd

pr_csv = pd.read_csv('pull_requests_filtered.csv')
grouped = pr_csv.groupby(['State'])
grouped.get_group('merged').to_csv("pull_requests_filtered_merged.csv", index=False)
grouped.get_group('closed').to_csv("pull_requests_filtered_closed.csv", index=False)
