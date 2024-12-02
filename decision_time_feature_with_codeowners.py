import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# change path back
with open('CODEOWNERS.txt') as file:
    lines = file.readlines()
    codeowners = [line.strip() for line in lines if line.strip() and not line.startswith('#')]

df = pd.read_csv("pull_requests_filtered.csv")
new_feature_prs = df[df['Type of Change'].str.contains('New feature')]
decision_times = new_feature_prs['Decision Time']

codeowner_map = {}
for line in codeowners:
    parts = line.split()  # format: "/homeassistant/components/<integration_name>/ @codeowner1 @codeowner2 @..."
    path = parts[0]
    owners = parts[1:]  # possible to have multiple codeowners per integration
    cleaned_owners = [username.lstrip('@') for username in owners]

    if path.startswith("/homeassistant/components/"):
        integration = path.split('/')[3]  # isolate integration name
        codeowner_map[integration] = set(cleaned_owners)

def is_code_owner(row):
    integration = row["Integration"]
    author = row["Author"]

    if integration in codeowner_map:
        return author in codeowner_map[integration]
    return False

df["Author is Codeowner"] = df.apply(is_code_owner, axis=1)     # axis=1 applies function to each row

upper_limit = df['Decision Time'].quantile(0.95)
df = df[df['Decision Time'] <= upper_limit]

plt.figure(figsize=(10, 6))
ax = sns.boxplot(x='Author is Codeowner', y='Decision Time', data=df, linewidth=1.2, palette={True: 'skyblue', False: 'salmon'}, hue='Author is Codeowner', legend=False)

medians = df.groupby('Author is Codeowner')['Decision Time'].median()
for tick, median in zip(ax.get_xticks(), medians):
    ax.text(tick, median + 1.5, f'{int(median)}', horizontalalignment='center', size=10, color='white')

counts = df['Author is Codeowner'].value_counts()
plt.legend(title='Data Points', loc='upper left', labels=[counts.get(False), counts.get(True)])

plt.xlabel('Author is Codeowner')
plt.ylabel('Decision Time (days)')
plt.title('Decision Times for PRs: Author as Codeowner vs Not')

plt.savefig('plot-images/decision_time_with_codeowners.png')
plt.show()
