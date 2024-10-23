from dotenv import load_dotenv
from os import environ
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import concurrent.futures

# Import Github token from .env
load_dotenv()
TOKEN = environ.get("GITHUB_PAT")

# Set up headers for the GitHub API request
headers = {"Authorization": f"Bearer {TOKEN}"}

# GitHub repository details
owner = 'home-assistant'
repo = 'core'

STATE = 'closed'

# Correct GitHub API URL to fetch pull requests
pulls_url = f'https://api.github.com/repos/{owner}/{repo}/pulls'

# Function to get all pull requests from the GitHub API with pagination
def get_pull_requests():
    all_pull_requests = []
    page = 1
    # control how many results to fetch 
    PAGE_LIMIT = 10
    while page <= PAGE_LIMIT:
        # Fetch each page of pull requests
        response = requests.get(pulls_url, headers=headers, params={'page': page, 'per_page': 100, 'state': STATE})
        if response.status_code == 200:
            pull_requests = response.json()
            if not pull_requests:
                # If there are no more pull requests, stop pagination
                break
            all_pull_requests.extend(pull_requests)
            page += 1
        else:
            print(f"Error: Unable to fetch pull requests (status code: {response.status_code})")
            break
    return all_pull_requests

# Function to get review comments for a specific pull request
def get_review_comments(pull_number: int):
    review_comments_url = f"{pulls_url}/{pull_number}/comments"
    response = requests.get(review_comments_url, headers=headers, params={'per_page': 100})
    if response.status_code == 200:
        return len(response.json())  # Return the number of review comments
    else:
        print(f"Error: Unable to fetch review comments for PR #{pull_number} (status code: {response.status_code})")
        return 0
    
# Function to get number of files changed in PR
def get_files_changed(pr_number: int) -> int:
    files_changed_url = f"{pulls_url}/{pr_number}/files"
    res = requests.get(files_changed_url, headers=headers)
    if res.status_code == requests.codes.ok:
        return len(res.json())

    print(f"Error: Unable to fetch file changes for PR #{pr_number} (status code: {res.status_code})")
    return 0

# Function to scrape the PR page for checkbox data (e.g., "Type of change")
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

# Function to process the pull request and extract required data
def process_pr(pr):
    labels = [label['name'] for label in pr.get('labels', [])]
    created_date = datetime.fromisoformat(pr['created_at']).replace(tzinfo=None)
    
    # Filter by creation date: Only include PRs created from 2021 onwards
    if created_date >= datetime(2021, 1, 1):
        if any("integration" in label for label in labels):
            # Fetch review comments for this PR
            review_comments_count = get_review_comments(pr['number'])
            
            # Calculate the total number of comments (issue comments + review comments)
            total_comments = pr.get('comments', 0) + review_comments_count  # Issue comments + Review comments

            files_changed_count = get_files_changed(pr['number'])

            closed_date = datetime.fromisoformat(pr['closed_at']).replace(tzinfo=None)
            days_to_close = (closed_date - created_date).days

            # Scrape the PR page for checkbox data (e.g., "Type of change")
            pr_checkbox_data = get_pr_checkbox_data(pr['html_url'])

            # Only process PRs if they relate to "New integration"
            if pr_checkbox_data:
                pr_data = {
                    'PR Number': pr['number'],
                    'Title': pr['title'],
                    'Labels': ', '.join(labels),
                    'Created At': pr['created_at'],
                    'Updated At': pr['updated_at'],
                    'State': pr['state'],
                    'Files Changed': files_changed_count,
                    'Total Comments': total_comments,
                    'Decision Time': days_to_close if STATE == 'closed' else 'N/A',
                    'URL': pr['html_url'],
                    'Type of Change': pr_checkbox_data  # Include checkbox data for type of change
                }
                return pr_data
    return None

print("Fetching pull requests")

# Fetch all pull requests
pull_requests = get_pull_requests()

# Process the pull requests using multithreading for speed
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
    results = list(executor.map(process_pr, pull_requests))

print("Filtering")

# Filter out None values (PRs that didn't match our criteria)
data = [pr_data for pr_data in results if pr_data is not None]

# Convert the filtered data into a Pandas DataFrame
df = pd.DataFrame(data)

# Select only the columns of interest, including 'Type of Change'
df_filtered = df[['PR Number', 'Title', 'Labels', 'Created At', 'Updated At', 'State', 'Files Changed', 'Total Comments'] + ['Decision Time' if STATE == 'closed' else []]+ ['Type of Change', 'URL']]

print("Writing to Excel")

# Optionally, save the DataFrame to an Excel file
df_filtered.to_excel("pull_requests_" + STATE + "_test.xlsx", index=False)


