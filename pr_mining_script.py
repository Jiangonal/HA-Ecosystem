import csv
from github import Github
import time
from datetime import datetime, timezone

# List of tokens for rotation
tokens = []
current_token_index = 0

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
    return get_github_instance()

# Function to handle rate limits by rotating tokens or waiting if all are exhausted
def handle_rate_limit(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining == 0:
        reset_time = rate_limit.reset
        wait_time = (reset_time - datetime.now(timezone.utc)).total_seconds()  # Ensure timezone awareness
        print(f"Token {current_token_index + 1} rate limit exceeded. Remaining reset wait time: {wait_time:.2f} seconds.")

        # Rotate to the next token or wait if all tokens are exhausted
        if current_token_index == len(tokens) - 1:
            print(f"All tokens exhausted. Waiting {wait_time:.2f} seconds for reset.")
            time.sleep(wait_time)
            return get_github_instance()  # Reset token rotation after wait
        else:
            return rotate_token()  # Rotate to the next token if available
    return g

# Main function to collect PR metadata
def collect_pr_metadata():
    start_date = datetime(2021, 1, 1, tzinfo=timezone.utc)  # Set start date as timezone-aware in UTC
    g = get_github_instance()
    repo = g.get_repo("home-assistant/core")

    with open("pull_requests_metadata.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["PR Number", "Title", "Created At", "Updated At", "State", "Files Changed", 
                         "Total Comments", "Decision Time", "URL"])

        while True:
            try:
                for pr in repo.get_pulls(state='closed', sort='created', direction='desc'):
                    # Rotate token or wait if rate limit is exceeded
                    g = handle_rate_limit(g)
                    
                    # Skip PRs created before 2021
                    if pr.created_at < start_date:
                        return  # Exit function once we reach PRs created before 2021
                    
                    pr_data = {
                        "PR Number": pr.number,
                        "Title": pr.title,
                        "Created At": pr.created_at,
                        "Updated At": pr.updated_at,
                        "State": pr.state,
                        "Files Changed": pr.changed_files,
                        "Total Comments": pr.comments,
                        "Decision Time": (pr.closed_at - pr.created_at).total_seconds() if pr.closed_at else None,
                        "URL": pr.html_url
                    }
                    
                    writer.writerow(pr_data.values())
                    print(pr_data)
                    time.sleep(0.5)  # Avoid rapid requests
                
                break  # Exit the loop once all PRs are processed

            except Exception as e:
                print(f"Error occurred: {e}")
                g = rotate_token()
                time.sleep(1)  # Small delay before retrying

# Run the script
if __name__ == "__main__":
    print("Starting data collection...")
    collect_pr_metadata()
    print("Data collection complete. Results saved to pull_requests_metadata.csv.")
