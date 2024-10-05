import pandas as pd
import requests
import datetime
from bs4 import BeautifulSoup
import concurrent.futures

# Your GitHub personal access token
TOKEN = '' # Replace with your actual token

# Set up headers for the GitHub API request
headers = {"Authorization": f"token {TOKEN}"}

# GitHub repository details
owner = 'home-assistant'
repo = 'core'

state = 'open'

# Correct GitHub API URL to fetch pull requests
pulls_url = f'https://api.github.com/repos/{owner}/{repo}/pulls'

# Function to get all pull requests from the GitHub API with pagination
def get_pull_requests():
    all_pull_requests = []
    page = 1
    while True:
        # Fetch each page of pull requests
        response = requests.get(pulls_url, headers=headers, params={'page': page, 'per_page': 100, 'state': state})
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
def get_review_comments(pull_number):
    review_comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments"
    response = requests.get(review_comments_url, headers=headers)
    if response.status_code == 200:
        return len(response.json())  # Return the number of review comments
    else:
        print(f"Error: Unable to fetch review comments for PR #{pull_number} (status code: {response.status_code})")
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
    pr_creation_date = datetime.datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    
    # Filter by creation date: Only include PRs created from 2021 onwards
    if pr_creation_date >= datetime.datetime(2021, 1, 1):
        if any("integration" in label for label in labels):
            # Fetch review comments for this PR
            review_comments_count = get_review_comments(pr['number'])
            
            # Calculate the total number of comments (issue comments + review comments)
            total_comments = pr.get('comments', 0) + review_comments_count  # Issue comments + Review comments

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
                    'Total Comments': total_comments,
                    'URL': pr['html_url'],
                    'Type of Change': pr_checkbox_data  # Include checkbox data for type of change
                }
                return pr_data
    return None

print("Fetching pull requests")

# Fetch all pull requests
pull_requests = get_pull_requests()

# Process the pull requests using multithreading for speed
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_pr, pull_requests))

print("Filtering")

# Filter out None values (PRs that didn't match our criteria)
data = [pr_data for pr_data in results if pr_data is not None]

# Convert the filtered data into a Pandas DataFrame
df = pd.DataFrame(data)

# Select only the columns of interest, including 'Type of Change'
df_filtered = df[['PR Number', 'Title', 'Labels', 'Created At', 'Updated At', 'State', 'Total Comments', 'Type of Change', 'URL']]

print("Writing to Excel")

# Optionally, save the DataFrame to an Excel file
df_filtered.to_excel("pull_requests_" + state + "_test.xlsx", index=False)


