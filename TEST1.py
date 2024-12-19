import json
json_file='RQ2_FEAT_WORKING_part1.json'
with open(json_file, 'r') as f:
    github_data = json.load(f)
    
print(github_data[0].get('comments', ''))