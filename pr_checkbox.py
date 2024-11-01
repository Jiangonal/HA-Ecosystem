import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone,timedelta

tokens = []
current_token_index = 0

def get_headers():
    global current_token_index
    return {"Authorization": f"token {tokens[current_token_index]}"}

def rotate_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)
    print(f"Rotating to token {current_token_index + 1}")

def save_progress(pr_number):
    with open("progress_checkbox.txt", "w") as file:
        file.write(str(pr_number))

def handle_rate_limit(pr_number):
    save_progress(pr_number)  # Save progress on token exhaustion
    if current_token_index == len(tokens) - 1:
        reset_time = datetime.now(timezone.utc) + timedelta(hours=1)  # Make reset_time timezone-aware
        wait_time = (reset_time - datetime.now(timezone.utc)).total_seconds()
        print(f"All tokens exhausted. Waiting {wait_time:.2f} seconds for reset.")
        time.sleep(wait_time)
        global current_token_index
        current_token_index = 0  # Reset token rotation
    else:
        rotate_token()

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

def get_last_processed_pr():
    try:
        with open("progress_checkbox.txt", "r") as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return None

def add_checkbox_data():
    last_pr = get_last_processed_pr()

    with open("pull_requests_metadata.csv", mode="r", encoding="utf-8") as infile, \
         open("pull_requests_with_checkbox_data.csv", mode="a", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["Type of Change"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        if last_pr is None:
            writer.writeheader()

        for row in reader:
            pr_number = int(row["PR Number"])
            if last_pr and pr_number <= last_pr:
                continue

            try:
                type_of_change = get_pr_checkbox_data(row["URL"], pr_number)
                row["Type of Change"] = type_of_change
                writer.writerow(row)
                print(f"Processed PR #{pr_number}: {type_of_change}")
                save_progress(pr_number)  # Save progress after each PR
                time.sleep(1)
            
            except Exception as e:
                print(f"Error occurred: {e}")
                save_progress(pr_number)
                rotate_token()
                time.sleep(1)

if __name__ == "__main__":
    print("Starting Part 2: Adding checkbox data from URLs...")
    add_checkbox_data()
    print("Checkbox data added. Results saved to pull_requests_with_checkbox_data.csv.")
