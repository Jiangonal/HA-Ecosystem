import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_excel('pull_requests_closed.xlsx')

fig, axes = plt.subplots(1, 3, figsize=(12, 6))
fig.suptitle('Distributions of Integration-Related PR Characteristics')

for i, col_name in enumerate(['Files Changed', 'Decision Time', 'Total Comments']):
    axes[i].hist(df[col_name], color='skyblue', edgecolor='black')
    axes[i].set_title(col_name)
    axes[i].set_xlabel(col_name)
    axes[i].set_ylabel('Frequency')
    axes[i].grid()

plt.tight_layout()
plt.show()

