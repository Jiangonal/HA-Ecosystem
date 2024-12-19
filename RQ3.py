import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()
key = os.getenv("SO_KEY")

# Stack Overflow API request function
def fetch_stackoverflow_data(query, from_date, to_date, pagesize=100, api_key=key):
    url = "https://api.stackexchange.com/2.3/search"
    params = {
        "order": "desc",
        "sort": "relevance",
        "intitle": query,
        "site": "stackoverflow",
        "fromdate": from_date,
        "todate": to_date,
        "pagesize": pagesize,
        "key": api_key
    }
    response = requests.get(url, params=params)
    
    data = response.json().get("items", [])
    return pd.DataFrame(data)

# Check if a fuzzy match exists
def is_fuzzy_match(comment_text, so_title, threshold=80):
    score = fuzz.token_set_ratio(comment_text.lower(), so_title.lower())
    return score >= threshold
def convert_unix_to_readable(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Filter PRs from CSV and search Stack Overflow
def map_prs_from_csv(csv_file='RQ3_DEV.csv'):
    prs_data = pd.read_csv(csv_file)
    matches = []
    
    for _, pr_row in prs_data.iterrows():
        pr_query = pr_row['Query Title']
        pr_title = pr_row['Title']
        created_at = pr_row['Created At']
        updated_at = pr_row['Updated At']

        # Handle full datetime parsing while ignoring timezone offsets
        from_date = int(datetime.strptime(created_at.split("+")[0], "%Y-%m-%d %H:%M:%S").timestamp())
        to_date = int(datetime.strptime(updated_at.split("+")[0], "%Y-%m-%d %H:%M:%S").timestamp())

        so_data = fetch_stackoverflow_data(pr_query, from_date, to_date)
        
        if not so_data.empty:
            for _, so_row in so_data.iterrows():
                
                if is_fuzzy_match(pr_query, so_row['title']):
                    matches.append((pr_row['PR Number'], pr_title, so_row['owner']['display_name'],  so_row['question_id'], so_row['title'], so_row['tags'], so_row['creation_date'], so_row['last_activity_date'], so_row['link']))
    
    return pd.DataFrame(matches, columns=['GitHub PR Number', 'GitHub PR Title', 'Post Owner', 'StackOverflow QID', 'StackOverflow Title', 'SO tags', 'SO Creation Date', 'SO Last Activity Date', 'SO link'])


mapped_data_csv = map_prs_from_csv()
mapped_data_csv['SO Creation Date'] = mapped_data_csv['SO Creation Date'].apply(convert_unix_to_readable)
mapped_data_csv['SO Last Activity Date'] = mapped_data_csv['SO Last Activity Date'].apply(convert_unix_to_readable)

mapped_data_csv.to_csv('RQ3_SO_dev.csv', index=False)

