from dotenv import load_dotenv
from os import environ
import os
import json
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
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

# Check rate limit and return reset time if limit is reached
def check_rate_limit():
    response = session.get("https://api.github.com/rate_limit", headers=headers)
    rate_limit_info = response.json()
    remaining = rate_limit_info['resources']['core']['remaining']
    reset_timestamp = rate_limit_info['resources']['core']['reset']
    reset_time = datetime.utcfromtimestamp(reset_timestamp)
    return remaining, reset_time

# Wait until rate limit resets, then resume
def wait_until_reset():
    remaining, reset_time = check_rate_limit()
    if remaining == 0:
        wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
        print(f"Rate limit reached. Waiting until {reset_time} (in {wait_seconds} seconds).")
        sleep(wait_seconds + 1)  # Wait until limit resets
    else:
        print(f"Remaining requests: {remaining}")
def get_total_comments(pr_number):
    # URLs for issue comments and review comments
    issue_comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    review_comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    
    total_comments = 0
    
    try:
        # Fetch issue comments
        issue_response = session.get(issue_comments_url, headers=headers)
        if issue_response.status_code == 200:
            issue_comments = issue_response.json()
            # Filter out bot comments in issue comments
            filtered_issue_comments = [
                comment for comment in issue_comments 
                if comment['user']['type'] != 'Bot' and 'bot' not in comment['user']['login'].lower()
            ]
            total_comments += len(filtered_issue_comments)
        else:
            print(f"Failed to fetch issue comments for PR #{pr_number}: {issue_response.status_code}")
        
        # Fetch review comments
        review_response = session.get(review_comments_url, headers=headers)
        if review_response.status_code == 200:
            review_comments = review_response.json()
            # Filter out bot comments in review comments
            filtered_review_comments = [
                comment for comment in review_comments 
                if comment['user']['type'] != 'Bot' and 'bot' not in comment['user']['login'].lower()
            ]
            total_comments += len(filtered_review_comments)
        else:
            print(f"Failed to fetch review comments for PR #{pr_number}: {review_response.status_code}")

    except Exception as e:
        print(f"Error fetching comments for PR #{pr_number}: {e}")
    
    return total_comments


# Function to get the number of files changed for a PR
def get_files_changed(pr_number):
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    try:
        response = session.get(files_url, headers=headers)
        if response.status_code == 200:
            files = response.json()
            return len(files)  # Number of files changed
        else:
            print(f"Failed to fetch files for PR #{pr_number}: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error fetching files for PR #{pr_number}: {e}")
        return 0

# Function to get checkbox data from the PR page (if needed)
def get_pr_checkbox_data(pr_html_url):
    # Fetch the PR webpage
    response = requests.get(pr_html_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the "Type of change" section by locating the <ul> with class "contains-task-list"
        type_of_change_section = soup.find('ul', class_='contains-task-list')

        if not type_of_change_section:
            return None

        # Iterate over all list items within the "Type of change" section
        checked_items = []
        for li in type_of_change_section.find_all('li'):
            checkbox = li.find('input', {'type': 'checkbox'})
            label = li.text.strip()

            # If the checkbox is checked, store the corresponding label text
            if checkbox and checkbox.has_attr('checked'):
                checked_items.append(label)

        # We care about PRs that have "New integration" or "New feature"
        if any('New integration' in item for item in checked_items) or any('New feature' in item for item in checked_items):
            return ", ".join(checked_items)  # Return all checked items
        else:
            return None  # Ignore PRs that don't have "New integration" or "New feature"
    else:
        print(f"Error: Unable to fetch PR page {pr_html_url} (status code: {response.status_code})")
        return None

# Fetch pull requests with no page limit (until all pages are retrieved)
def get_pull_requests(start_page=1):
    all_pull_requests = []
    page = start_page
    save_interval = 50  # Checkpoint interval: save every 50 pages
    
    while True:
        print(f"Fetching page {page}")
        remaining, reset_time = check_rate_limit()
        if remaining == 0:
            wait_until_reset()
        
        response = session.get(
            pulls_url,
            headers=headers,
            params={'state': STATE, 'sort': 'created', 'direction': 'desc', 'per_page': 100, 'page': page}
        )
        
        if response.status_code == 200:
            pull_requests = response.json()
            if not pull_requests:
                break
            
            # Filter pull requests based on the creation date and "integration" label
            for pr in pull_requests:
                created_date = datetime.fromisoformat(pr['created_at']).replace(tzinfo=None)
                labels = [label['name'] for label in pr.get('labels', [])]
                
                # Apply both filters
                if created_date >= datetime(2021, 1, 1) and any("integration" in label.lower() for label in labels):
                    all_pull_requests.append(pr)
            
            # Save progress and write to CSV every 50 pages
            if page % save_interval == 0:
                save_progress(page)
                process_and_save_data(all_pull_requests)  # Write data to CSV every 50 pages
                all_pull_requests = []  # Reset list after saving to reduce memory usage
            
            page += 1
            sleep(0.5)  # Short delay to avoid hitting rate limits
        else:
            print(f"Error fetching page {page}: {response.status_code}")
            break

    # Save remaining data if any
    if all_pull_requests:
        process_and_save_data(all_pull_requests)

    return all_pull_requests



# Fetch additional data for each PR (e.g., files changed, comments, decision time, type of change)
def fetch_pr_details(pr):
    pr_number = pr['number']
    total_comments_count, files_changed_count, pr_checkbox_data = 0, 0, None
    
    # Use multithreading for concurrent requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            "total_comments": executor.submit(get_total_comments, pr_number),
            "files_changed": executor.submit(get_files_changed, pr_number),
            "checkbox_data": executor.submit(get_pr_checkbox_data, pr['html_url'])
        }
        for key, future in futures.items():
            try:
                if key == "total_comments":
                    total_comments_count = future.result()
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
    if pr_checkbox_data:
        return {
            'PR Number': pr['number'],
            'Title': pr['title'],
            'Labels': ', '.join(labels),
            'Created At': pr['created_at'],
            'Updated At': pr['updated_at'],
            'State': 'merged' if pr.get('merged_at') else 'closed',
            'Files Changed': files_changed_count,
            'Total Comments': total_comments_count,  # Now uses the combined total comments count
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

# Run the main function
main()
