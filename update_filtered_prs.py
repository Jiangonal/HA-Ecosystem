import pandas as pd
import requests

df = pd.read_csv("pull_requests_filtered.csv")

# List of GitHub personal access tokens
GITHUB_TOKENS = []
token_index = 0

# Function to get the next token in the cycle
def get_next_token():
    global token_index
    token = GITHUB_TOKENS[token_index]
    token_index = (token_index + 1) % len(GITHUB_TOKENS)
    return token

# Function to fetch the closed date of a PR using GitHub API with token cycling
def fetch_data_with_token_cycle(pr_url):
    try:
        # Extract owner, repo, and PR number from the URL
        parts = pr_url.split("/")
        owner = parts[3]
        repo = parts[4]
        pr_number = parts[-1]

        # Construct the API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

        # Headers for authentication using the next token in the cycle
        headers = {"Authorization": f"token {get_next_token()}"}

        # Make the request
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            pr_data = response.json()
            additions = pr_data.get("additions", 0)
            deletions = pr_data.get("deletions", 0)
            loc = additions + deletions
            close = pr_data.get("closed_at", None)
            return loc, close
        else:
            return None
    except Exception as e:
        return None


# Apply the function to the 'URL' column and add a new 'Closed Date (API)' column
df[["LOC Changed", "Closed Date"]] = pd.DataFrame(
    df["URL"].apply(fetch_data_with_token_cycle).tolist(), index=df.index
)

print(df.head())

# add lines of code


df.to_csv("pull_requests_filtered_1.csv", index=False)
