import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from os import environ
from pydantic import BaseModel
from collections import defaultdict
import os

# Load environment variables
load_dotenv()

client = OpenAI()  # Automatically loads OPENAI_API_KEY from .env

# Read the JSON file
df_json = pd.read_json('RQ2_DEV_WORKING.json')
pd.set_option('display.max_colwidth', None)

# Define response model
class CommentCategoriesExtraction(BaseModel):
    categories: list[str]

# Initialize totals dictionary
category_totals = defaultdict(int)
pr_labels_file = 'DEV_PR_LABELS.csv'
category_counts_file = 'DEV_CATEGORY_COUNTS.csv'

# Initialize CSV files if not exist
if not os.path.exists(pr_labels_file):
    pd.DataFrame(columns=['PR Number', 'Category']).to_csv(pr_labels_file, index=False)

if not os.path.exists(category_counts_file):
    pd.DataFrame(columns=['Category', 'Total Count']).to_csv(category_counts_file, index=False)

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
            model="gpt-4o",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes pull request comments within the Home Assistant repository to categorize challenges faced when developing device integrations, and returns PR numbers with corresponding challenge categories. Normalize similar terms/challenges to avoid duplicates and similar entries. Consider timestamps to identify slow response time. If a pull request is marked as stale, count it as a response time challenge. Use 'Other' only if no specific category applies."},

                {"role": "assistant", "content": "categories=['Bug-Related', 'Logic Issues', 'Testing/Validation Issues', 'Code Structure/Design Issues', 'Communication/Collaboration Issues', 'Slow Response', 'Other']"},

                {"role": "user", "content": f"Here are the pull requests: {body}"}
            ],
            response_format=CommentCategoriesExtraction
        )

        # Extract and save categories
        extracted_categories = chat_response.choices[0].message.parsed.categories

        with open(pr_labels_file, 'a', newline='') as file:
            for category in extracted_categories:
                file.write(f"{pr_number},{category}\n")
                category_totals[category] += 1

    except Exception as e:
        print(f"Error processing PR #{pr_number}: {e}")

    # Save progress every batch_size PRs
    if (idx + 1) % batch_size == 0:
        totals_df = pd.DataFrame.from_dict(category_totals, orient='index', columns=['Total Count']).reset_index()
        totals_df.columns = ['Category', 'Total Count']
        totals_df.to_csv(category_counts_file, index=False)
        print(f"Batch {idx // batch_size + 1} processed and saved.\n")

# Final save after processing all PRs
totals_df = pd.DataFrame.from_dict(category_totals, orient='index', columns=['Total Count']).reset_index()
totals_df.columns = ['Category', 'Total Count']
totals_df.to_csv(category_counts_file, index=False)

print(f"Processing completed. Results saved to {pr_labels_file} and {category_counts_file}.")
