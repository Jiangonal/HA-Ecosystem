import requests
import pandas as pd
import json
import os
from google.cloud import bigquery
from dotenv import load_dotenv

# Initialize BigQuery client
client = bigquery.Client(project='masters-444801')

# Stack Overflow BigQuery request function
def fetch_stackoverflow_data_bq(query='python', limit=10):
    query_text = f"""
        SELECT Id, Title, creation_date
        FROM `bigquery-public-data.stackoverflow.posts_questions`
        WHERE LOWER(Title) LIKE '%{query.lower()}%'
        LIMIT {limit}
    """
    query_job = client.query(query_text)
    return query_job.result().to_dataframe()

# Test the function
if __name__ == "__main__":
    result_df = fetch_stackoverflow_data_bq()
    print(result_df.head())