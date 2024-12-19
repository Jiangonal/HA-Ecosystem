import re
import pandas as pd

def terms(title, stop_words):

    # Clean the title by removing stop words
    title_cleaned = re.sub(r'\b(' + '|'.join(stop_words) + r')\b', '', title.lower())
    words = re.findall(r'\b\w+\b', title_cleaned)
    # Return the cleaned meaningful terms as a string
    return " ".join(words).title() if words else "None"

file_path = 'PRs_RQ1_feat.csv'  # Update this path if needed
df = pd.read_csv(file_path)


# Define custom stop words
custom_stop_words = {'add', 'integration', 'new', 'update', 'support', 'fix', 'for'}

# Apply a function to each element
df['Query Title'] = df['Title'].apply(lambda x: terms(x, custom_stop_words))


df.to_csv('RQ3_FEAT.csv', index=False)
