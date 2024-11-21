import pandas as pd
import re

# Load the CSV file
file_path = 'pull_request_comments_commits_codeowners.csv'  # Replace with your file path
data = pd.read_csv(file_path)

# Convert the 'Date' column to datetime for time gap analysis
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

# Define the refined keyword categories
refined_keyword_categories = {
    "Bug-related": [
        "bug", "fix", "error", "breaking", "regression", "crash", "failure", "not working", "unexpected behavior"
    ],
    "Overlapping Work": [
        "conflict", "duplicate", "dependent", "overlap", "already done", "redundant", "covered in"
    ],
    "Unsupported Changes": [
        "not supported", "we don't allow", "change this", "reject", "out of scope", "invalid", "doesn't align"
    ],
    "Complexity": [
        "large change", "refactor", "complex", "needs rework", "difficult", "too big", "hard to review", "unmanageable"
    ],
    "Procedural": [
        "ready for review", "pull request process", "use the button", "follow the guidelines", "add a description",
        "missing documentation"
    ],
    "Testing Feedback": [
        "tested", "works", "observations", "test results", "not working", "verify", "test coverage", "fails tests",
        "doesn't pass", "broken tests"
    ],
    "Acknowledgment": [
        "thank you", "thanks", "great", "nice work", "appreciate", "good job", "well done", "excellent"
    ],
    "Logistical Notes": [
        "tag for beta", "add to beta", "beta release", "merge this", "add milestone", "release notes", "schedule"
    ],
    "Cross-references": [
        "see pr", "created a separate pr", "related pr", "integration", "linked issue", "referenced in", "duplicate pr"
    ]
}

# Function to classify comments based on refined keywords
def classify_comment(comment, keyword_categories):
    for category, keywords in keyword_categories.items():
        for keyword in keywords:
            if re.search(rf"\b{keyword}\b", str(comment).lower()):
                return category
    return "Other"

# Classify comments using the refined categories
data["Refined Reason"] = data["Comment"].apply(lambda x: classify_comment(x, refined_keyword_categories))

# Count reasons per pull request
refined_reason_counts = data.groupby(["Pull Request URL", "Refined Reason"]).size().unstack(fill_value=0)

# Calculate time gaps between comments
time_gaps = data.sort_values(['Pull Request URL', 'Date']).groupby('Pull Request URL')['Date'].diff()
data['Time Gap (Hours)'] = time_gaps.dt.total_seconds() / 3600

# Align data for correlation analysis
review_comment_counts = data[data["Refined Reason"] == "Procedural"].groupby("Pull Request URL").size()
avg_time_gaps = data.groupby('Pull Request URL')['Time Gap (Hours)'].mean()

aligned_data = pd.DataFrame({
    "Review Comments": review_comment_counts,
    "Average Time Gap (Hours)": avg_time_gaps
}).dropna()

code_owner_involvement = data.groupby('Pull Request URL').agg({
    'Is Code Owner': 'sum'
}).rename(columns={'Is Code Owner': 'Code Owner Comments'})

aligned_owner_data = pd.DataFrame({
    "Code Owner Comments": code_owner_involvement["Code Owner Comments"],
    "Review Comments": review_comment_counts
}).dropna()

# Save the correlation data to CSV
aligned_data.to_csv("review_comments_vs_time_gaps.csv", index=False)
aligned_owner_data.to_csv("code_owner_comments_vs_review_comments.csv", index=False)

# Save refined classifications for user review
refined_reason_counts.reset_index(inplace=True)
refined_reason_counts.to_csv("refined_classifications.csv", index=False)

print("Refined classifications and correlation insights have been saved to CSV files.")
