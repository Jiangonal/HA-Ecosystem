import requests
import pandas as pd
import time

# Load the CSV file
file_path = 'RQ3_SO_feat.csv'
df = pd.read_csv(file_path)

# Initialize a list to store usernames
usernames = []

# Function to fetch the username from Stack Overflow API
def fetch_username(qid):
    url = f"https://api.stackexchange.com/2.3/questions/{qid}?order=desc&sort=activity&site=stackoverflow&filter=!9_bDE(fI5"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['items']:
            return data['items'][0].get('owner', {}).get('display_name', 'Unknown')
    return 'Unknown'

# Loop through the QIDs and fetch usernames
for qid in df['StackOverflow QID']:
    username = fetch_username(qid)
    usernames.append(username)
      # To avoid hitting API rate limits

# Add the usernames to the DataFrame
df['SO Username'] = usernames

# Save the updated DataFrame back to the same file
df.to_csv(file_path, index=False)

print(f"Updated CSV saved to {file_path}")