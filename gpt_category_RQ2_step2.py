from openai import OpenAI
from dotenv import load_dotenv
from os import environ
import pandas as pd
import ast

# Load environment variables
load_dotenv()

# Initialize API client
client = OpenAI()  # Automatically loads OPENAI_API_KEY from .env


df = pd.read_csv('category_totals_json.csv')

# Convert to a compact dictionary-like string
categories_text = df.set_index('Category')['Total Count'].to_dict()
categories_text_str = str(categories_text)
# print(categories_text)
# # Create a chat prompt and request dictionary output from GPT-4
chat_response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.1,
    messages=[
    {
        "role": "system",
        "content": (
            "You are a helpful assistant that organizes unique software development topics "
            "into distinct categories and subcategories, ensuring no repeated entries. "
            "Respond only with a valid Python dictionary."
        ),
    },
    {
        "role": "user",
        "content": (
            "Here are some software development issue categories. Please organize them into "
            "distinct categories with at least 5 relevant subcategories and moderately specifc challenges and their descriptions. For the 'Other' category, include at least 7 subcategories."
            " Ensure each subcategory is unique.  Categories: Bug-Related Issues, Integration and Compatibility, Documentation and Support, "
            "Performance and Optimization, Security and Compliance, Other."
        ),
    },
]


)

# Extract and clean the response
response_text = chat_response.choices[0].message.content

# Remove unwanted formatting like triple backticks and prefix text
cleaned_text = response_text.replace("```python", "").replace("```", "").strip()
with open("cleaned_response1.txt", "w") as file:
    file.write(cleaned_text)

