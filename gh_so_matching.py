import pandas as pd
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load Data
so_posts = pd.read_csv('RQ3_SO_dev.csv')
pr_data = pd.read_csv('PRs_RQ1_dev.csv')
with open('RQ2_DEV_WORKING.json', 'r') as f:
    pr_comments = json.load(f)


prs_titles = list(so_posts['GitHub PR Title'].unique())
prs = pr_data[pr_data['Title'].isin(prs_titles)]


pr_urls = set(prs['URL'].unique())
pr_dis = [c for c in pr_comments if c['pull_request_url'] in pr_urls]


users = []
authors = []
for i in range(len(pr_dis)):
    auth = {'url': pr_dis[i]['pull_request_url'], 'author': pr_dis[i]['comments'][i]['author']}
    authors.append(auth)
    u = []
    use = {'url': pr_dis[i]['pull_request_url'], 'users': u}
    for j in range(len(pr_dis[i]['comments'])):
        if pr_dis[i]['comments'][j]['user'] not in u and pr_dis[i]['comments'][j]['user'] not in ['homeassistant', 'github-actions[bot]', 'home-assistant[bot]'] and type(pr_dis[i]['comments'][j]['user']) is str :
            u.append(pr_dis[i]['comments'][j]['user'])
    users.append(use)
            

users_df = pd.DataFrame(users)
authors_df = pd.DataFrame(authors)

prs_1 = pd.merge(users_df, authors_df, on='url', how='inner')
prs = pd.merge(prs, prs_1, left_on='URL', right_on = 'url' ,how='inner')

prs.to_csv('rq3dev.csv',index=False)
def clean_text(text):
    if isinstance(text, str):
        return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    return ''

def extract_links(text):
    return re.findall(r'https?://\S+', text) if isinstance(text, str) else []

# Merge Datasets by Matching Titles
merged_df = pd.merge(
    prs, so_posts,
    left_on=prs['Title'].apply(clean_text),
    right_on=so_posts['GitHub PR Title'].apply(clean_text),
    suffixes=('_pr', '_so')
)
print(merged_df)
# Matching Logic
results = []
for _, row in merged_df.iterrows():
    pr_url = row['url']
    pr_author = row['author']
    pr_users = eval(row['users']) if isinstance(row['users'], str) else []
    so_title = clean_text(row['StackOverflow Title'])
    pr_title = clean_text(row['Title'])

    # Matching Calculations
    keyword_score = cosine_similarity(
        TfidfVectorizer(stop_words='english').fit_transform([f"{so_title}", pr_title])
    )[0, 1]

    author_match = pr_author in pr_users

    if keyword_score > 0 or author_match:
        results.append({
            'PR URL': pr_url,
            'PR Title': row['Title'],
            'SO Title': row['StackOverflow Title'],
            'Keyword Score': keyword_score,
            'Author Match': author_match
        })

# Save Results
results_df = pd.DataFrame(results)
results_df.to_csv('rq3_dev_titles.csv')
print(results_df)