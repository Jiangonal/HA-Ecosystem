import csv
import requests
from bs4 import BeautifulSoup
import time

# List of tokens for rotation
tokens = []
current_token_index = 0

# Function to get headers with the current token
def get_headers():
    global current_token_index
    headers = {"Authorization": f"token {tokens[current_token_index]}"}
    return headers

# Rotate tokens
def rotate_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)
    print(f"Rotating to token {current_token_index + 1}")

# Function to fetch checkbox data from PR HTML page
def get_pr_checkbox_data(pr_html_url):
    response = requests.get(pr_html_url, headers=get_headers())
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the section that contains task list items (checkboxes)
        type_of_change_section = soup.find('ul', class_='contains-task-list')
        if not type_of_change_section:
            return None

        # Collect checked items from the list
        checked_items = []
        for li in type_of_change_section.find_all('li'):
            checkbox = li.find('input', {'type': 'checkbox'})
            label = li.text.strip()
            if checkbox and checkbox.has_attr('checked'):
                checked_items.append(label)

        return ", ".join(checked_items) if checked_items else None
    elif response.status_code == 403:
        # Rotate token on rate limit or permission error
        print(f"Rate limit hit or access forbidden for {pr_html_url}. Rotating token...")
        rotate_token()
        return get_pr_checkbox_data(pr_html_url)
    else:
        print(f"Failed to retrieve {pr_html_url}. Status code: {response.status_code}")
        return None

# Read the metadata CSV and add checkbox data to a new CSV
def add_checkbox_data():
    with open("pull_requests_metadata.csv", mode="r", encoding="utf-8") as infile, \
         open("pull_requests_with_checkbox_data.csv", mode="w", newline="", encoding="utf-8") as outfile:
        
        # Set up CSV reader and writer
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["Type of Change"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each PR and add checkbox data
        for row in reader:
            type_of_change = get_pr_checkbox_data(row["URL"])
            row["Type of Change"] = type_of_change
            writer.writerow(row)
            print(f"Processed PR #{row['PR Number']}: {type_of_change}")
            time.sleep(1)  # Delay to avoid hitting GitHub's server too rapidly

# Run the script
if __name__ == "__main__":
    print("Starting Part 2: Adding checkbox data from URLs...")
    add_checkbox_data()
    print("Checkbox data added. Results saved to pull_requests_with_checkbox_data.csv.")
