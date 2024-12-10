import pandas as pd
import json

# Load CSV file
file_path = 'pull_request_comments_commits_codeowners_integrations.csv'
df = pd.read_csv(file_path)

# Group by Pull Request URL
grouped_data = []
for url, group in df.groupby('Pull Request URL'):
    pull_request_data = {
        'pull_request_url': url,
        'comments': []
    }
    
    for _, row in group.iterrows():
        comment_data = {
            'comment_type': row['Comment Type'],
            'user': row['User'],
            'comment': row['Comment'],
            'date': row['Date'],
            'commit_sha': row['Commit SHA'] if pd.notna(row['Commit SHA']) else None,
            'author': row['Author'],
            'commit_message': row['Commit Message'] if pd.notna(row['Commit Message']) else None,
            'is_code_owner': row['Is Code Owner'],
            'author_is_code_owner': row['Author Is Code Owner']
        }
        pull_request_data['comments'].append(comment_data)
    
    grouped_data.append(pull_request_data)

# Save to JSON
output_file = 'formatted_pull_requests_int.json'
with open(output_file, 'w') as f:
    json.dump(grouped_data, f, indent=4)

print(f"Data formatted and saved to {output_file}")
