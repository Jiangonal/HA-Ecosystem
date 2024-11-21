import requests
import pandas as pd

# GitHub API configuration
TOKEN = "" 
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Function to fetch comments
def fetch_comments(issue_url, review_url):
    issue_comments = requests.get(issue_url, headers=headers)
    review_comments = requests.get(review_url, headers=headers)
    
    comments = []
    if issue_comments.status_code == 200:
        for comment in issue_comments.json():
            comments.append({
                "Comment Type": "Issue",
                "User": comment["user"]["login"],
                "Comment": comment["body"],
                "Date": comment["created_at"]
            })
    else:
        print(f"Failed to fetch issue comments: {issue_comments.status_code}")
    
    if review_comments.status_code == 200:
        for comment in review_comments.json():
            comments.append({
                "Comment Type": "Review",
                "User": comment["user"]["login"],
                "Comment": comment["body"],
                "Date": comment["created_at"]
            })
    else:
        print(f"Failed to fetch review comments: {review_comments.status_code}")
    
    return comments

# Function to fetch basic commit details
def fetch_commit_details(commit_url):
    response = requests.get(commit_url, headers=headers)
    commit_data = []
    if response.status_code == 200:
        for commit in response.json():
            commit_data.append({
                "Commit SHA": commit["sha"],
                "Author": commit["commit"]["author"]["name"],
                "Commit Message": commit["commit"]["message"],
                "Date": commit["commit"]["author"]["date"]
            })
    else:
        print(f"Failed to fetch commit details: {response.status_code}")
    return commit_data

# Function to fetch the author of the pull request
def fetch_pr_author(pr_url):
    response = requests.get(pr_url, headers=headers)
    if response.status_code == 200:
        pr_data = response.json()
        return pr_data["user"]["login"]
    else:
        print(f"Failed to fetch PR author: {response.status_code}")
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
df = pd.read_csv('pull_requests_complex_features.csv').head(30)

# List to store all data
all_data = []

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
        all_data.append(comment)

    for commit in commits:
        commit["Pull Request URL"] = url
        commit["Author"] = author
        commit["Author Is Code Owner"] = author_is_code_owner
        all_data.append(commit)

# Save to CSV
all_data_df = pd.DataFrame(all_data)
csv_file_path = "pull_request_comments_commits_codeowners.csv"
all_data_df.to_csv(csv_file_path, index=False)

print(f"Comments and commit details with code owner information saved to {csv_file_path}")
