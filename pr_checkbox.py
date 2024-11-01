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
BATCH_SIZE = 100  # Save every x PRs

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
    print("Checkpoint reached (every", BATCH_SIZE, "PRs)")
    if buffer:
        mode = "a" if os.path.exists("pull_requests_with_checkbox_data.csv") else "w"
        with open("pull_requests_with_checkbox_data.csv", mode, newline="", encoding="utf-8") as file:
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

# Handle rate limits by rotating tokens or waiting
def handle_rate_limit(pr_number):
    save_progress(pr_number)  # Save progress on token exhaustion
    if current_token_index == len(tokens) - 1:
        reset_time = datetime.now(timezone.utc) + timedelta(hours=1)
        wait_time = (reset_time - datetime.now(timezone.utc)).total_seconds()
        print(f"All tokens exhausted. Waiting {wait_time:.2f} seconds for reset.")
        time.sleep(wait_time)
        global current_token_index
        current_token_index = 0  # Reset token rotation
    else:
        rotate_token()

# Scrape type of change checkboxes from PR HTML
def get_pr_checkbox_data(pr_html_url, pr_number):
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
    elif response.status_code == 403:
        print(f"Rate limit hit for {pr_html_url}.")
        handle_rate_limit(pr_number)
        return get_pr_checkbox_data(pr_html_url, pr_number)
    else:
        print(f"Failed to retrieve {pr_html_url}. Status code: {response.status_code}")
        return None

# Load last PR number from progress file if it exists
def get_last_processed_pr():
    try:
        with open("progress_checkbox.txt", "r") as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return None

# Process PRs and add checkbox data
def add_checkbox_data():
    last_pr = get_last_processed_pr()

    with open("pull_requests_metadata.csv", mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            pr_number = int(row["PR Number"])
            if last_pr and pr_number <= last_pr:
                continue

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

                print(f"Processed PR #{pr_number}: {type_of_change}")
                save_progress(pr_number)  # Save progress after each PR
                time.sleep(1)
            
            except Exception as e:
                print(f"Error occurred: {e}")
                save_progress(pr_number)
                rotate_token()
                time.sleep(1)

    # Final save after all processing
    save_buffered_data()

if __name__ == "__main__":
    print("Starting Part 2: Adding checkbox data to PR metadata...")
    add_checkbox_data()
    print("Checkbox data added. Results saved to pull_requests_with_checkbox_data.csv.")
