
import csv
from dotenv import load_dotenv
from github import Github
import time
from datetime import datetime, timezone
import os

load_dotenv()

# List of tokens for rotation- can use `[os.environ.get("GITHUB_PAT_1"), os.environ.get("GITHUB_PAT_2"),...]` if using env variables
tokens = [
]
current_token_index = 0
buffer = []  # Buffer for batching PR data
BATCH_SIZE = 100  # Save every x PRs

# Initialize GitHub instance
def get_github_instance():
    global current_token_index
    g = Github(tokens[current_token_index])
    return g

# Function to rotate token when rate limit is exceeded
def rotate_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)
    print(f"Rotated to token {current_token_index + 1}")
    save_buffered_data()  # Save buffer on token rotation
    return get_github_instance()

# Function to handle rate limits by rotating tokens or waiting if all are exhausted
def handle_rate_limit(g):
    rate_limit = g.get_rate_limit().core

    if rate_limit.remaining == 0:
        reset_time = rate_limit.reset
        wait_time = (reset_time - datetime.now(timezone.utc)).total_seconds()
        print(f"Token {current_token_index + 1} rate limit exceeded.")
        
        # Rotate to the next token or wait if all tokens are exhausted
        if current_token_index == len(tokens) - 1:
            print(f"All tokens exhausted. Waiting {wait_time:.2f} seconds for reset.")
            time.sleep(wait_time)
        
        return rotate_token()
    return g

# Load last PR number from CSV if it exists, otherwise start from the beginning
def load_last_pr():
    if os.path.exists("pull_requests_all.csv"):
        with open("pull_requests_all.csv", "r", encoding="utf-8") as f:
            last_row = list(csv.reader(f))[-1]
            last_pr_number = int(last_row[0])
            print(f"Resuming from PR #{last_pr_number - 1}")
            return last_pr_number - 1
    return None  # No file exists, start fresh

# Save buffered data to CSV
def save_buffered_data():
    mode = ""
    print("Checkpoint reached.")
    if buffer:
        if os.path.exists("pull_requests_all.csv"):
            mode = "a" 
            print("Found existing file.")
        else: 
            mode = "w"
            print("Creating new file.")
        with open("pull_requests_all.csv", mode, newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if mode == "w":
                writer.writerow(["PR Number", "Title", "Created At", "Updated At", "State", 
                                 "Files Changed", "LOC Changed", "Total Comments", "Decision Time", "Closed Date", "URL"])
            writer.writerows(buffer)  # Write all buffered rows at once
        buffer.clear()  # Clear buffer after writing

# Main function to collect PR metadata
def collect_pr_metadata():
    global current_pr_number
    start_date = datetime(2021, 1, 1, tzinfo=timezone.utc)  # Set start date as timezone-aware in UTC
    end_date = datetime(2024, 10, 31, tzinfo=timezone.utc)  # Set end date as timezone-aware in UTC
    g = get_github_instance()
    repo = g.get_repo("home-assistant/core")
    
    current_pr_number = load_last_pr() or 0
    
    try:
        for pr in repo.get_pulls(state='closed', sort='created', direction='desc'):
            
            # Rotate token or wait if rate limit is exceeded
            g = handle_rate_limit(g)

            # Skip PRs created after October 2024
            if pr.created_at > end_date:
                continue
            
            # Skip PRs created before 2021
            if pr.created_at < start_date:
                save_buffered_data()  # Save any remaining data in the buffer
                return  # Exit function once we reach PRs created before 2021
            
            # Skip already processed PRs
            if (pr.number >= current_pr_number) and current_pr_number != 0:
                continue
            
            # Gather PR data
            pr_data = [
                pr.number,
                pr.title, 
                pr.created_at, 
                pr.updated_at, 
                "merged" if pr.merged else "closed", 
                pr.changed_files, 
                sum([file.changes for file in pr.get_files()]),
                len([comment for comment in pr.get_comments() + pr.get_issue_comments() if comment.user.type != "Bot"]), 
                (pr.closed_at - pr.created_at).days, 
                pr.closed_at,
                pr.html_url
            ]
            
            buffer.append(pr_data)  # Add PR data to buffer                
            # Save buffer if it reaches the BATCH_SIZE
            if len(buffer) >= BATCH_SIZE:
                save_buffered_data()


            # print(f"Processed PR #{pr.number}")
            current_pr_number = pr.number  # Update last processed PR

    except Exception as e:
        print(f"An error occurred: {e}. Saving progress and exiting.")
        save_buffered_data()  # Save remaining buffer on exception

# Run the script
if __name__ == "__main__":
    print("Starting data collection...")
    collect_pr_metadata()
    print("Data collection complete. Results saved to pull_requests_all.csv.")
