from dotenv import load_dotenv
from os import environ
import os
import json
import pandas as pd
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import concurrent.futures
from time import sleep
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load environment variables and GitHub token
load_dotenv()
TOKEN = ''
headers = {"Authorization": f"Bearer {TOKEN}"}

# GitHub repository details
owner = 'home-assistant'
repo = 'core'
STATE = 'closed'
pulls_url = f'https://api.github.com/repos/{owner}/{repo}/pulls'

# Temporary files for checkpointing
PROGRESS_FILE = "progress_checkpoint.json"  # Tracks last processed page
TEMP_DATA_FILE = "temp_pull_requests.csv"   # Stores processed PRs incrementally

# Set up a requests session with retry strategy
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Load the last processed page from checkpoint, if exists
def load_last_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f).get("last_page", 1)
    return 1

# Save the current page to a checkpoint file
def save_progress(last_page):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_page": last_page}, f)

# Fetch pull requests with no page limit (until all pages are retrieved)
def get_pull_requests(start_page=1):
    all_pull_requests = []
    page = start_page
    while True:
        print(f"Fetching page {page}")
        response = session.get(
            pulls_url,
            headers=headers,
            params={'state': STATE, 'sort': 'created', 'direction': 'desc', 'per_page': 100, 'page': page}
        )
        if response.status_code == 200:
            pull_requests = response.json()
            # Stop if there are no more pull requests
            if not pull_requests:
                break
            
            # Filter to keep pull requests created from 2021 onward
            all_pull_requests.extend([pr for pr in pull_requests if datetime.fromisoformat(pr['created_at']).replace(tzinfo=timezone.utc) >= datetime(2021, 1, 1, tzinfo=timezone.utc)])
            page += 1
            save_progress(page - 1)  # Save the current page as a checkpoint
            sleep(0.5)  # Short delay to avoid hitting rate limits
        else:
            print(f"Error fetching page {page}: {response.status_code}")
            break
    return all_pull_requests


# Fetch additional data for each PR (e.g., files changed, comments, decision time, type of change)
def fetch_pr_details(pr):
    pr_number = pr['number']
    review_comments_count, files_changed_count, pr_checkbox_data = 0, 0, None
    
    # Use multithreading for concurrent requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            "review_comments": executor.submit(get_review_comments, pr_number),
            "files_changed": executor.submit(get_files_changed, pr_number),
            "checkbox_data": executor.submit(get_pr_checkbox_data, pr['html_url'])
        }
        for key, future in futures.items():
            try:
                if key == "review_comments":
                    review_comments_count = future.result()
                elif key == "files_changed":
                    files_changed_count = future.result()
                elif key == "checkbox_data":
                    pr_checkbox_data = future.result()
            except Exception as e:
                print(f"Error in {key}: {e}")
    
    # Collect all required fields
    labels = [label['name'] for label in pr.get('labels', [])]
    created_date = datetime.fromisoformat(pr['created_at'])
    closed_date = datetime.fromisoformat(pr['closed_at'])
    days_to_close = (closed_date - created_date).days if closed_date else 'N/A'
    
    return {
        'PR Number': pr['number'],
        'Title': pr['title'],
        'Labels': ', '.join(labels),
        'Created At': pr['created_at'],
        'Updated At': pr['updated_at'],
        'State': 'merged' if pr.get('merged_at') else 'closed',
        'Files Changed': files_changed_count,
        'Total Comments': pr.get('comments', 0) + review_comments_count,
        'Decision Time': days_to_close,
        'Type of Change': pr_checkbox_data,
        'URL': pr['html_url']
    }

# Process PR data and save it incrementally
def process_and_save_data(pull_requests):
    processed_data = []
    for pr in pull_requests:
        pr_data = fetch_pr_details(pr)
        if pr_data:
            processed_data.append(pr_data)
    
    # Convert to DataFrame and append to CSV
    df = pd.DataFrame(processed_data)
    if os.path.exists(TEMP_DATA_FILE):
        df.to_csv(TEMP_DATA_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(TEMP_DATA_FILE, mode='w', header=True, index=False)

# Main function with checkpointing enabled
def main():
    start_page = load_last_progress()  # Resume from last saved page
    print(f"Resuming from page {start_page}")
    pull_requests = get_pull_requests(start_page=start_page)
    process_and_save_data(pull_requests)


    print(f"Data saved to {TEMP_DATA_FILE}.")

# Supporting functions to get comments and file changes
def get_review_comments(pr_number):
    urls = [
        f"{pulls_url}/{pr_number}/comments",
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    ]
    total_comments = 0
    for url in urls:
        response = session.get(url, headers=headers)
        if response.status_code == 200:
            comments = response.json()
            if "issues" in url:
                total_comments += sum(1 for comment in comments if comment['user']['type'] != 'Bot')
            else:
                total_comments += len(comments)
        sleep(0.2)
    return total_comments

def get_files_changed(pr_number: int) -> int:
    files_changed_url = f"{pulls_url}/{pr_number}/files"
    total_files_changed = 0
    page = 1

    while True:
        res = requests.get(files_changed_url, headers=headers, params={'page': page, 'per_page': 100})
        if res.status_code == requests.codes.ok:
            files = res.json()
            total_files_changed += len(files)
            if len(files) < 100:
                break
            page += 1
            sleep(0.2)
        else:
            print(f"Error: Unable to fetch file changes for PR #{pr_number} (status code: {res.status_code})")
            break

    return total_files_changed

def get_pr_checkbox_data(pr_html_url):
    response = session.get(pr_html_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        section = soup.find('ul', class_='contains-task-list')
        if section:
            checked_items = [li.text.strip() for li in section.find_all('li') if li.find('input', checked=True)]
            if any('New integration' in item or 'New feature' in item for item in checked_items):
                return ", ".join(checked_items)
    return None

# Run the main function
main()
