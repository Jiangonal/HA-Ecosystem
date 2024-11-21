import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = 'refined_classifications.csv'  # Replace with your file path
refined_classifications = pd.read_csv(file_path)

# Combine relevant categories to focus on delay-related issues
delay_related_categories = [
    "Bug-related", "Procedural", "Testing Feedback", 
    "Unsupported Changes", "Complexity"
]

# Aggregate delay-related counts
delay_related_totals = refined_classifications[delay_related_categories].sum()

# Bar plot for delay-related categories
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
