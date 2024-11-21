import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = 'refined_classifications.csv'  # Replace with your file path
refined_classifications = pd.read_csv(file_path)

# Ensure all relevant columns (excluding 'Pull Request URL') are numeric
numeric_columns = refined_classifications.columns.difference(['Pull Request URL'])
refined_classifications[numeric_columns] = refined_classifications[numeric_columns].apply(pd.to_numeric, errors='coerce')

# Add a new column for adaptive top reasons classification
def classify_top_reasons(row):
    # Exclude 'Pull Request URL' column
    classifications = row.drop(labels=["Pull Request URL"])
    # Sort categories by their counts in descending order
    sorted_categories = classifications.sort_values(ascending=False)
    # Get non-zero and non-"Other" categories
    valid_categories = sorted_categories[sorted_categories > 0].index.tolist()
    # Handle various cases
    if not valid_categories:  # If no valid categories
        return "Slow response times (default/other)"
    if "Other" in valid_categories:  # Move "Other" to the end
        valid_categories.remove("Other")
        valid_categories.append("Other")
    # Return up to 3 categories
    return ', '.join(valid_categories[:3])

# Apply the classification logic to each row
refined_classifications['Top Reasons'] = refined_classifications.apply(classify_top_reasons, axis=1)

# Save the updated DataFrame to a new CSV file
output_file_path = "refined_classifications.csv"
refined_classifications.to_csv(output_file_path, index=False)

# Plot for delay-related categories
delay_related_categories = [
    "Bug-related", "Procedural", "Testing Feedback", 
    "Unsupported Changes", "Complexity"
]

# Aggregate delay-related counts
delay_related_totals = refined_classifications[delay_related_categories].sum()

plt.figure(figsize=(10, 5))
delay_related_totals.sort_values(ascending=False).plot(kind="bar", color="orange")
plt.title("Delay-Related Reasons for Pull Request Duration")
plt.xlabel("Delay Reason Category")
plt.ylabel("Total Count")
plt.xticks(rotation=45, ha="right")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig("distribution.png")
plt.show()

print(f"Updated classifications with top reasons saved to: {output_file_path}")
