import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone, timedelta
import os

# List of tokens for rotation
tokens = []
current_token_index = 0
buffer = []  # Buffer for batching PR data
BATCH_SIZE = 10  # Save every x PRs

# Get authorization headers for requests
def get_headers():
    global current_token_index
    return {"Authorization": f"token {tokens[current_token_index]}"}

# Rotate the token
def rotate_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)
    print(f"Rotating to token {current_token_index + 1}")
    save_buffered_data()  # Save buffer on token rotation

# Save buffered data to CSV
def save_buffered_data():
    print("Checkpoint reached")
    mode = ""
    if buffer:
        if os.path.exists("pull_requests_all_with_checkbox_data.csv"):
            mode = "a"  
            print("Found existing file.")
        else:
            mode = "w"
        with open("pull_requests_all_with_checkbox_data.csv", mode, newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if mode == "w":
                writer.writerow(["PR Number", "Title", "Created At", "Updated At", "State", 
                                 "Files Changed", "Total Comments", "Decision Time", "URL", "Type of Change"])
            writer.writerows(buffer)  # Write all buffered rows at once
        buffer.clear()  # Clear buffer after writing

# Save progress to a file
def save_progress(pr_number):
    with open("progress_checkbox.txt", "w") as file:
        file.write(str(pr_number))

# Scrape type of change checkboxes from PR HTML
def get_pr_checkbox_data(pr_html_url):
    response = requests.get(pr_html_url, headers=get_headers())
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        type_of_change_section = soup.find('ul', class_='contains-task-list')
        if not type_of_change_section:
            return None

        checked_items = []
        for li in type_of_change_section.find_all('li'):
            checkbox = li.find('input', {'type': 'checkbox'})
            label = li.text.strip()
            if checkbox and checkbox.has_attr('checked'):
                checked_items.append(label)

        return ", ".join(checked_items) if checked_items else None
    else:
        print(f"Failed to retrieve {pr_html_url}. Status code: {response.status_code}")
        return None


# Load last PR number from output CSV if it exists, otherwise fallback to progress file
def get_last_processed_pr():
    last_pr = None
    
    # Check if the output CSV exists and get the last PR number if it does
    if os.path.exists("pull_requests_all_with_checkbox_data.csv"):
        with open("pull_requests_all_with_checkbox_data.csv", mode="r", encoding="utf-8") as outfile:
            reader = csv.DictReader(outfile)
            rows = list(reader)
            if rows:
                last_pr = int(rows[-1]["PR Number"])  # Get the PR Number from the last row in the CSV

    # Fallback to progress file if output CSV doesn't exist
    if last_pr is None:
        try:
            with open("progress_checkbox.txt", "r") as file:
                last_pr = int(file.read().strip())
        except FileNotFoundError:
            last_pr = None

    return last_pr


# Process PRs and add checkbox data
def add_checkbox_data():
    last_pr = get_last_processed_pr()
    
    # Read the CSV into a list and sort in descending order of PR numbers
    with open("pull_requests_all.csv", mode="r", encoding="utf-8") as infile:
        reader = list(csv.DictReader(infile))
        reader.sort(key=lambda row: int(row["PR Number"]), reverse=True)

    start_processing = False

    for row in reader:
        pr_number = int(row["PR Number"])

        # Find the next smallest PR after `last_pr` to start processing
        if not last_pr:
            last_pr = pr_number  # Set last_pr if it's not set
        else:
            if pr_number < last_pr:
                start_processing = True

        # Start processing from the next smallest PR after `last_pr`
        if start_processing:

            # Collect PR data and checkbox data
            try:
                type_of_change = get_pr_checkbox_data(row["URL"], pr_number)
                pr_data = [
                    pr_number,
                    row["Title"],
                    row["Created At"],
                    row["Updated At"],
                    row["State"],
                    row["Files Changed"],
                    row["Total Comments"],
                    row["Decision Time"],
                    row["URL"],
                    type_of_change
                ]
                buffer.append(pr_data)  # Add PR data to buffer

                # Save buffer if it reaches the BATCH_SIZE
                if len(buffer) >= BATCH_SIZE:
                    save_buffered_data()

                # Save progress after each PR
                save_progress(pr_number)
                time.sleep(0.5)
            
            except Exception as e:
                print(f"Error occurred: {e}")
                save_progress(pr_number)
                time.sleep(0.5)

    # Final save after all processing
    save_buffered_data()
    os.remove("progress_checkbox.txt")

if __name__ == "__main__":
    print("Starting Part 2: Adding checkbox data to PR metadata...")
    add_checkbox_data()
    print("Checkbox data added. Results saved to pull_requests_all_with_checkbox_data.csv.")
