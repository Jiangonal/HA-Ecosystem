import pandas as pd
import requests

# Your GitHub personal access token
TOKEN = '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'  # Replace with your actual token

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

# Function to get issue comments for a specific pull request
def get_issue_comments(issue_number):
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    response = requests.get(comments_url, headers=headers)
    if response.status_code == 200:
        return response.json()  # return the JSON response
    else:
        print(f"Error: Unable to fetch comments for PR #{issue_number} (status code: {response.status_code})")
        return []

# Function to get review comments for a specific pull request
def get_review_comments(pull_number):
    review_comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments"
    response = requests.get(review_comments_url, headers=headers)
    if response.status_code == 200:
        return response.json()  # return the JSON response
    else:
        print(f"Error: Unable to fetch review comments for PR #{pull_number} (status code: {response.status_code})")
        return []

# Fetch all pull requests
pull_requests = get_pull_requests()

# List to store pull requests data
data = []

# Loop through each pull request and fetch details including comments
for pr in pull_requests:
    # Fetch the labels for each PR
    labels = [label['name'] for label in pr.get('labels', [])]

    # Only include PRs with any label containing the word "integration"
    if any("integration" in label for label in labels):  # Check for "integration" in labels
        # Fetch issue comments for this PR
        issue_comments = get_issue_comments(pr['number'])
        comments_text = "\n".join([comment['body'] for comment in issue_comments])

        # Fetch review comments for this PR
        review_comments = get_review_comments(pr['number'])
        review_comments_text = "\n".join([comment['body'] for comment in review_comments])

        # Count the number of issue and review comments
        num_issue_comments = len(issue_comments)
        num_review_comments = len(review_comments)
        total_comments = num_issue_comments + num_review_comments

        # Create a dictionary with all the relevant PR data, excluding 'User', 'Issue Comments', 'Review Comments'
        pr_data = {
            'PR Number': pr['number'],
            'Title': pr['title'],
            'Labels': ', '.join(labels),
            'Created At': pr['created_at'],
            'Updated At': pr['updated_at'],
            'State': pr['state'],
            'Total Comments': total_comments,  # New column for total number of comments
            'URL': pr['html_url']
        }
    
        # Append this PR's data to the list
        data.append(pr_data)

# Convert the data into a Pandas DataFrame
df = pd.DataFrame(data)

# Optionally, save the DataFrame to an Excel file
df.to_excel("pull_requests_" + state + ".xlsx", index=False)
