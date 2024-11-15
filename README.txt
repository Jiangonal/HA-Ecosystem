Setup:

1. Create a virtual environment into a folder called '.venv', and install required dependencies:
    Run `python -m venv .venv` to create venv
    Run `source .venv/bin/activate` to active venv
    Run `pip install -r requirements.txt` to install required packages  

2. Create a '.env' file, containing a key GITHUB_PAT and value corresponding to your Github personal access token
e.g. GITHUB_PAT="my_access_token"

3. Usage:
   --> Run `python scrape_all_prs.py` to get all pull requests (can take multiple hours)
   --> Run `python scrape_pr_checkbox_data.py` to get associated checked boxes for each pull request (can take multiple hours)
   --> Run `python filter_prs.py` to filter down to integration related PRs