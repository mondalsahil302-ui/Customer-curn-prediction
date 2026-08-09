import pandas as pd

# Load the CSV file
df = pd.read_csv("Telco_customer_churn.csv")
print("CSV Loaded Successfully!")
print("Rows and Columns:", df.shape)
print(df.head())