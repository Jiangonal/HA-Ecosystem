import pandas as pd
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
df_json = pd.read_json('RQ2_FEAT.json')
pd.set_option('display.max_colwidth', None)

# Define response model
class CommentCategoriesExtraction(BaseModel):
    categories: list[str]

# Initialize totals dictionary
category_totals = defaultdict(int)
output_file = 'category_totals_feats_json.csv'

# If the CSV exists, load it to resume progress
if os.path.exists(output_file):
    existing_df = pd.read_csv(output_file)
    category_totals.update(existing_df.set_index('Category')['Total Count'].to_dict())

# Process PRs
batch_size = 10

# Process PRs directly from the JSON file
for idx, test in df_json.iterrows():
    pr_number = test['pull_request_url'].split('/')[-1]

    # Extract issue comments (excluding bots)
    issue_comment_bodies = [
        comment['comment'] for comment in test['comments']
        if comment['comment_type'] == 'Issue' and 'bot' not in comment['user'].lower()
    ]

    # Extract review comments
    review_comment_bodies = [
        comment['comment'] for comment in test['comments']
        if comment['comment_type'] == 'Review'
    ]

    # Prepare the input for the OpenAI API
    body = f"ISSUE COMMENT BODIES: \n{issue_comment_bodies}\n\nREVIEW COMMENT BODIES: \n{review_comment_bodies}"

    try:
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

    except Exception as e:
        print(f"Error processing PR #{pr_number}: {e}")

    # Save progress to the CSV file every batch_size PRs
    if (idx + 1) % batch_size == 0:
        totals_df = pd.DataFrame.from_dict(category_totals, orient='index', columns=['Total Count']).reset_index()
        totals_df.columns = ['Category', 'Total Count']
        totals_df.to_csv(output_file, index=False)
        print(f"Batch {idx // batch_size + 1} processed and saved to {output_file}.\n")

# Final save after processing all PRs
totals_df = pd.DataFrame.from_dict(category_totals, orient='index', columns=['Total Count']).reset_index()
totals_df.columns = ['Category', 'Total Count']
totals_df.to_csv(output_file, index=False)

print(f"Processing completed. Results saved to {output_file}.")
