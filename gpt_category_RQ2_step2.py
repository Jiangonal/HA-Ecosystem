from openai import OpenAI
from dotenv import load_dotenv
from os import environ
import pandas as pd
import ast

# Load environment variables
load_dotenv()

# Initialize API client
client = OpenAI()  # Automatically loads OPENAI_API_KEY from .env


df = pd.read_csv('all_cat_totals.csv')

# Convert to a compact dictionary-like string
categories_text = df.set_index('Category')['Total Count'].to_dict()
categories_text_str = str(categories_text)

# Create a chat prompt and request dictionary output from GPT-4
chat_response = client.chat.completions.create(
    model="gpt-4",
    temperature=0.1,  # Reduce randomness
    messages=[
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that analyzes pull request comments within the Home Assistant repository "
                "to categorize challenges faced when developing device integrations into no more than 10 categories, "
                "with an 11th category named 'Other' for anything that doesn't fit. "
                "Please output the response as a dictionary in valid Python format, without extra text."
            ),
        },
        # {"role": "assistant", "content": "categories={'Testing Issues': ['Testing bug', 'Incorrect output', 'Did not pass unit test'], 'Naming Issues' : ['Wrong variable name','Invalid variable call']}"},
        {
            "role": "user",
            "content": (
                f"Here are some software development issue categories. Please organize them into no more than 10 "
                f"general categories, with an additional 'Other' category:\n\n{categories_text}"
            ),
        },
    ],
)

# Extract and clean the response
response_text = chat_response.choices[0].message.content

# Remove unwanted formatting like triple backticks and prefix text
cleaned_text = response_text.replace("```python", "").replace("```", "").strip()

# Attempt to parse the cleaned dictionary
try:
    categories_dict = ast.literal_eval(cleaned_text)
except (SyntaxError, ValueError) as e:
    raise ValueError(f"Failed to parse API response. Error: {e}")

# Convert to DataFrame
formatted_df = pd.DataFrame(
    [(category, ", ".join(examples)) for category, examples in categories_dict.items()],
    columns=["challenge", "examples"],
)

# Save to CSV
output_file = "general_categories_formatted.csv"
formatted_df.to_csv(output_file, index=False)

print(f"\nCategorization completed. Results saved to '{output_file}'.")
