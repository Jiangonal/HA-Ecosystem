import pandas as pd
import requests
from openai import OpenAI
from dotenv import load_dotenv
from os import environ
from pydantic import BaseModel
from collections import defaultdict
import os

# Load environment variables
load_dotenv()

# Set up API keys
GITHUB_API_KEY = environ.get("GITHUB_PAT_2")
client = OpenAI()  # Automatically loads OPENAI_API_KEY from .env

# Read the JSON file
df_json = pd.read_json('formatted_pull_requests_int.json')
pd.set_option('display.max_colwidth', None)

# Define response model
class CommentCategoriesExtraction(BaseModel):
    categories: list[str]

# Initialize totals dictionary
category_totals = defaultdict(int)
output_file = 'category_totals_json.csv'

# If the CSV exists, load it to resume progress
if os.path.exists(output_file):
    existing_df = pd.read_csv(output_file)
    category_totals.update(existing_df.set_index('Category')['Total Count'].to_dict())

# Process PRs
batch_size = 5

for start_idx in range(0, len(df_json), batch_size):
    for idx in range(start_idx, min(start_idx + batch_size, len(df_json))):
        test = df_json.iloc[idx]
        pr_number = test['pull_request_url'].split('/')[-1]

        # Fetch issue comments
        issue_comments_url = f"https://api.github.com/repos/home-assistant/core/issues/{pr_number}/comments"
        response = requests.get(issue_comments_url, headers={"Authorization": f"Bearer {GITHUB_API_KEY}"})
        issue_comment_data = response.json()

        # Filter out bot comments
        issue_comment_bodies = [comment['body'] for comment in issue_comment_data if comment['user']['type'] != 'Bot']

        # Fetch review comments
        review_comments_url = f"https://api.github.com/repos/home-assistant/core/pulls/{pr_number}/comments"
        response = requests.get(review_comments_url, headers={"Authorization": f"Bearer {GITHUB_API_KEY}"})
        review_comment_data = response.json()

        # Extract review comment bodies
        review_comment_bodies = [comment['body'] for comment in review_comment_data]

        # Prepare the input for the OpenAI API
        body = f"ISSUE COMMENT BODIES: \n{issue_comment_bodies}\n\nREVIEW COMMENT BODIES: \n{review_comment_bodies}"

        # Send the request to the OpenAI API
        chat_response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes pull request comments within the Home Assistant repository to categorize challenges faced when developing device integrations, and returns a list of them. If not categorizable, use 'Other'."},
                {"role": "user", "content": f"{body}"},
                {"role": "assistant", "content": "categories=['Testing Issues', 'Naming/ID Issues', 'Code Structure Issues', 'Communication Issues', 'Review Process Issues', 'Other']"},
                {"role": "user", "content": f"Can you make sure any Home Assistant/Smart home specific concepts are captured: {body}"}
            ],
            response_format=CommentCategoriesExtraction
        )

        # Update category totals
        extracted_categories = chat_response.choices[0].message.parsed.categories
        for category in extracted_categories:
            category_totals[category] += 1

    # Save progress to the CSV file every 5 PRs
    totals_df = pd.DataFrame.from_dict(category_totals, orient='index', columns=['Total Count']).reset_index()
    totals_df.columns = ['Category', 'Total Count']
    totals_df.to_csv(output_file, index=False)

    print(f"Batch {start_idx // batch_size + 1} processed and saved to {output_file}.\n")

print(f"Processing completed. Results saved to {output_file}.")
