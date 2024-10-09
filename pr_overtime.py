
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Configuration
ACCESS_TOKEN = ''  # Replace with your GitHub access token
REPO_OWNER = 'home-assistant'  # Organization name
REPO_NAME = 'core'  # Repository name within the Home Assistant organization

# Function to get the number of pull requests for a specific date range using the GitHub Search API
def get_pull_requests_count(since_date, until_date):
    url = 'https://api.github.com/search/issues'
    headers = {'Authorization': f'token {ACCESS_TOKEN}'}
    params = {
        'q': f'repo:{REPO_OWNER}/{REPO_NAME} is:pr created:{since_date.strftime("%Y-%m-%d")}..{until_date.strftime("%Y-%m-%d")}',
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['total_count']
    else:
        print(f"Error fetching data: {response.status_code}")
        return 0

# Generate data points for every 1 year from the beginning of the project
start_date = datetime(2013, 9, 17)  # Approximate start date of the Home Assistant project
end_date = datetime.now()
data_points = []
dates = []

while start_date < end_date:
    next_date = start_date + timedelta(days=365)  # 1-year interval
    pr_count = get_pull_requests_count(start_date, next_date)
    data_points.append(pr_count)
    dates.append(start_date.strftime('%Y'))
    start_date = next_date

# Plotting the data
plt.figure(figsize=(12, 6))
plt.plot(dates, data_points, marker='o')
plt.title(f'Number of Pull Requests in {REPO_NAME} Every Year (From Project Start to Present)')
plt.xlabel('Year')
plt.ylabel('Number of Pull Requests')
plt.xticks(rotation=45)
plt.grid(True)

# Annotate the graph with the values
for i, value in enumerate(data_points):
    plt.text(dates[i], value, str(value), ha='center', va='bottom')

plt.tight_layout()
plt.show()
