from openai import OpenAI as gpt
import pandas as pd
import re

# Initialize OpenAI API client
client = gpt(
    api_key=""
)

# Define categories and associated keywords
keywords = {
    "Bug-related": ["bug", "fix", "error", "breaking", "regression", "crash", "failure", "not working", "unexpected behavior"],
    "Overlapping Work": ["conflict", "duplicate", "dependent", "overlap", "already done", "redundant", "covered in"],
    "Unsupported Changes": ["not supported", "we don't allow", "change this", "reject", "out of scope", "invalid", "doesn't align"],
    "Complexity": ["large change", "refactor", "complex", "needs rework", "difficult", "too big", "hard to review", "unmanageable"],
    "Procedural": ["ready for review", "pull request process", "use the button", "follow the guidelines", "add a description", "missing documentation"],
    "Testing Feedback": ["tested", "works", "observations", "test results", "not working", "verify", "test coverage", "fails tests", "doesn't pass", "broken tests"],
    "Acknowledgment": ["thank you", "thanks", "great", "nice work", "appreciate", "good job", "well done", "excellent"],
    "Logistical Notes": ["tag for beta", "add to beta", "beta release", "merge this", "add milestone", "release notes", "schedule"],
    "Cross-references": ["see pr", "created a separate pr", "related pr", "integration", "linked issue", "referenced in", "duplicate pr"]
}

# Function to classify a comment based on keywords
def classify_comment(comment):
    comment = comment.lower()  # Convert comment to lowercase for case-insensitive matching
    classified = []
    
    # Check if any keyword exists in the comment for each category
    for category, words in keywords.items():
        if any(word in comment for word in words):
            classified.append(category)
    
    return ", ".join(classified) if classified else "Slow response times (default/other reasons)"

# Function to get top 3 reasons based on category counts
def classify_top_reasons(row):
    # Sort categories by their counts in descending order
    sorted_categories = row.sort_values(ascending=False)
    
    # Get non-zero categories
    valid_categories = sorted_categories[sorted_categories > 0].index.tolist()
    
    # Handle various cases
    if not valid_categories:  # If no valid categories
        return "Slow response times (default/other reasons)"  # Use this for no valid categories
    
    # If "Slow response times" or "Other" is in the valid categories, we move them to the end
    if "Slow response times (default/other reasons)" in valid_categories:
        valid_categories.remove("Slow response times (default/other reasons)")
        valid_categories.append("Slow response times (default/other reasons)")

    # Return up to 3 categories, ensuring that "Slow response times (default/other reasons)" is included if no valid categories are found
    return ', '.join(valid_categories[:3]) if valid_categories else "Slow response times (default/other reasons)"

# Load the CSV files containing comments
comments_df = pd.read_csv('pull_request_comments_commits_codeowners_integrations.csv').head(150)
comments_df = comments_df.fillna('')  # Replace NaN values with empty strings

# Process the comments and classify them
comments_df['Category'] = comments_df['Comment'].apply(classify_comment)

# Count the occurrences of each category per pull request
category_counts = comments_df.groupby(['Pull Request URL', 'Category']).size().unstack(fill_value=0)

# Apply the function to get the top 3 reasons per pull request
category_counts['Top 3 Reasons'] = category_counts.apply(classify_top_reasons, axis=1)

# Save the refined classifications to a CSV file
category_counts.reset_index(inplace=True)
category_counts.to_csv("refined_classifications1.csv", index=False)


# print(category_counts)

comments_prompt = "\n".join([f"Pull Request: {row['Pull Request URL']}\nComment: {row['Comment']}\nCategory: {row['Category']}" 
                             for _, row in comments_df.iterrows()])

final_prompt = f"""
Here are some categorized pull request comments:
{comments_prompt}

Please analyze the categories and identify any common trends or issues across them.
"""

# Request ChatGPT to interpret the trends and issues
completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant analyzing pull request comments."},
        {"role": "user", "content": final_prompt}
    ]
)
print("Query complete")

