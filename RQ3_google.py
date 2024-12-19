import requests
import pandas as pd
import json
import os
from google.cloud import bigquery
from dotenv import load_dotenv
from datetime import datetime
from fuzzywuzzy import fuzz
import time

# Initialize BigQuery client
client = bigquery.Client(project='masters-444801')

# Stack Overflow BigQuery request function
def fetch_stackoverflow_data_bq(query, limit=100):
    query_text = f"""
        SELECT Id, Title, creation_date
        FROM `bigquery-public-data.stackoverflow.posts_questions`
        WHERE LOWER(Title) LIKE r'''%{query.replace("'", "''").lower()}%'''
        LIMIT {limit}
    """
    # print(query_text)
    query_job = client.query(query_text)
    
    return query_job.result().to_dataframe()

# Check if a fuzzy match exists
def is_fuzzy_match(comment_text, so_title, threshold=80):
    score = fuzz.token_set_ratio(comment_text.lower(), so_title.lower())
    return score >= threshold

# Filter PRs by inclusive dates and search Stack Overflow using combined comments from the JSON file
def map_prs_from_json(json_file='RQ2_FEAT_WORKING_part1.json'):
    with open(json_file, 'r') as f:
        github_data = json.load(f)

    matches = []

    for pr_row in github_data:
        pr_title = pr_row.get('title', '')

        # Combine all comments into a single query
        combined_comments = " ".join(
            str(comment.get('comment', '')).strip() for comment in pr_row.get('comments', []) if isinstance(comment.get('comment', ''), str)
        )

        if not combined_comments:
            continue

        so_data = fetch_stackoverflow_data_bq(combined_comments)

        for _, so_row in so_data.iterrows():
            if is_fuzzy_match(combined_comments, so_row['Title']):
                matches.append((pr_row['pull_request_url'], pr_title, so_row['Id'], so_row['Title'], so_row['CreationDate']))
                df = pd.DataFrame(matches, columns=['GitHub PR Number', 'GitHub PR Title', 'StackOverflow QID', 'StackOverflow Title', 'SO Creation Date'])
                if not os.path.isfile('mapped_data_feat_json.csv'):
                    # If the file doesn't exist, create it
                    df.to_csv('mapped_data_feat_json.csv', index=False)
                else:
                    # If the file exists, append without writing the header again
                    df.to_csv('mapped_data_feat_json.csv', mode='a', header=False, index=False)


    return pd.DataFrame(matches, columns=['GitHub PR URL', 'GitHub PR Title', 'StackOverflow QID', 'StackOverflow Title', 'SO Creation Date'])

# Filter PRs from CSV and search Stack Overflow
def map_prs_from_csv(csv_file='PRs_RQ1_feat.csv'):
    prs_data = pd.read_csv(csv_file)[600:700]
    matches = []

    for _, pr_row in prs_data.iterrows():
        pr_title = pr_row['Title']
        
        so_data = fetch_stackoverflow_data_bq(pr_title)

        for _, so_row in so_data.iterrows():
            if is_fuzzy_match(pr_title, so_row['Title']):
                matches.append((pr_row['PR Number'], pr_title, so_row['Id'], so_row['Title'], so_row['CreationDate']))
                df = pd.DataFrame(matches, columns=['GitHub PR Number', 'GitHub PR Title', 'StackOverflow QID', 'StackOverflow Title', 'SO Creation Date'])
                if not os.path.isfile('mapped_data_feat_csv.csv'):
                    # If the file doesn't exist, create it
                    df.to_csv('mapped_data_feat_csv.csv', index=False)
                else:
                    # If the file exists, append without writing the header again
                    df.to_csv('mapped_data_feat_csv.csv', mode='a', header=False, index=False)



# Perform the mapping

mapped_data_csv = map_prs_from_csv()
# mapped_data_json = map_prs_from_json()
# Save results to CSV files
# mapped_data_json.to_csv('mapped_data_feat_json.csv', index=False)
# mapped_data_csv.to_csv('mapped_data_feat_csv.csv', index=False)

# Print confirmation
print("done")
