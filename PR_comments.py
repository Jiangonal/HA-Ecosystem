import requests
import pandas as pd
import csv
import os
import time
from datetime import datetime, timezone
FIELDNAMES = [
    "Comment Type", "User", "Comment", "Date", 
    "Commit SHA", "Author", "Commit Message",  
    "Pull Request URL", "Is Code Owner", "Author Is Code Owner"
]

# List of tokens for rotation
tokens = [
]  # Replace with your tokens
current_token_index = 0

# Buffer and batch size
buffer = []  # Buffer for batching data
BATCH_SIZE = 100  # Save every 100 items

# Function to get headers with the current token
def get_headers():
    global current_token_index
    return {
        "Authorization": f"token {tokens[current_token_index]}",
        "Accept": "application/vnd.github.v3+json"
    }

# Function to rotate token
def rotate_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)
    print(f"Rotated to token {current_token_index + 1}")

# Function to handle rate limits
def handle_rate_limit(response):
    if response.status_code == 403:  # Forbidden, likely due to rate limit
        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
        wait_time = max(0, reset_time - int(time.time()))
        print(f"Rate limit exceeded. Waiting {wait_time} seconds.")
        
        # Rotate to the next token or wait if all are exhausted
        if current_token_index == len(tokens) - 1:
            time.sleep(wait_time)
        else:
            rotate_token()
        return False  # Retry after token rotation or wait
    return True  # Proceed if no rate limit

# Save buffered data to CSV
def save_buffered_data():
    if buffer:  # Only save if there's data in the buffer
        mode = 'a' if os.path.exists("pull_request_comments_commits_codeowners_integrations.csv") else 'w'
        with open("pull_request_comments_commits_codeowners_integrations.csv", mode, newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            if mode == 'w':  # Write header if creating a new file
                writer.writeheader()
            
            # Normalize dictionaries to match fieldnames
            normalized_buffer = [{key: item.get(key, None) for key in FIELDNAMES} for item in buffer]
            writer.writerows(normalized_buffer)  # Write all buffered rows
        buffer.clear()  # Clear the buffer after saving
        print("Checkpoint: Data saved.")


# Fetch functions
def fetch_comments(issue_url, review_url):
    comments = []
    for url in [issue_url, review_url]:
        while True:
            response = requests.get(url, headers=get_headers())
            if handle_rate_limit(response):
                if response.status_code == 200:
                    for comment in response.json():
                        comments.append({
                            "Comment Type": "Issue" if url == issue_url else "Review",
                            "User": comment["user"]["login"],
                            "Comment": comment["body"],
                            "Date": comment["created_at"]
                        })
                else:
                    print(f"Failed to fetch comments: {response.status_code}")
                break  # Exit loop if successful
    return comments

def fetch_commit_details(commit_url):
    while True:
        response = requests.get(commit_url, headers=get_headers())
        if handle_rate_limit(response):
            if response.status_code == 200:
                return [
                    {
                        "Commit SHA": commit["sha"],
                        "Author": commit["commit"]["author"]["name"],
                        "Commit Message": commit["commit"]["message"],
                        "Date": commit["commit"]["author"]["date"]
                    } for commit in response.json()
                ]
            else:
                print(f"Failed to fetch commit details: {response.status_code}")
            break
    return []

def fetch_pr_author(pr_url):
    while True:
        response = requests.get(pr_url, headers=get_headers())
        if handle_rate_limit(response):
            if response.status_code == 200:
                return response.json()["user"]["login"]
            else:
                print(f"Failed to fetch PR author: {response.status_code}")
            break
    return None

# Load CODEOWNERS.txt file
def load_codeowners(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

# Check if a user is a code owner
def is_code_owner(user, codeowners):
    for line in codeowners:
        if user in line:
            return True
    return False

# Load CODEOWNERS.txt
codeowners_file = "CODEOWNERS.txt"  # Replace with the path to your CODEOWNERS.txt
codeowners = load_codeowners(codeowners_file)

# Load pull requests from CSV
df = pd.read_csv('pull_requests_complex_integrations.csv')

# Iterate through pull requests
for url in df['URL']:
    # Extract pull request number from the URL
    pull_number = url.split("/")[-1]
    repo_owner = "home-assistant"  # Adjust if owner/repo can vary
    repo_name = "core"  # Adjust if owner/repo can vary

    # Generate API URLs
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}"
    issue_comments_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pull_number}/comments"
    review_comments_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}/comments"
    commit_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}/commits"

    # Fetch PR author, comments, and commit details
    author = fetch_pr_author(pr_url)
    comments = fetch_comments(issue_comments_url, review_comments_url)
    commits = fetch_commit_details(commit_url)

    # Check if author and commenters are code owners
    author_is_code_owner = is_code_owner(author, codeowners)
    for comment in comments:
        comment["Is Code Owner"] = is_code_owner(comment["User"], codeowners)
        comment["Pull Request URL"] = url
        comment["Author"] = author
        comment["Author Is Code Owner"] = author_is_code_owner
        buffer.append(comment)
        if len(buffer) >= BATCH_SIZE:
            save_buffered_data()

    for commit in commits:
        commit["Pull Request URL"] = url
        commit["Author"] = author
        commit["Author Is Code Owner"] = author_is_code_owner
        buffer.append(commit)
        if len(buffer) >= BATCH_SIZE:
            save_buffered_data()

# Save remaining data in the buffer
save_buffered_data()
print(f"Comments and commit details with code owner information saved to pull_request_comments_commits_codeowners.csv")
