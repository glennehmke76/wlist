import pandas as pd

# Path to the CSV file
csv_path = '/Users/glennehmke/MEGA/Taxonomy/2025 changes/avilist.csv'

# Read the first few rows of the CSV file
try:
    df = pd.read_csv(csv_path, nrows=5)
    
    # Print the column names
    print("CSV file columns:")
    for col in df.columns:
        print(f"- {col}")
    
    # Print the first row to see the data format
    print("\nFirst row of data:")
    print(df.iloc[0])
    
except FileNotFoundError:
    print(f"Error: The file {csv_path} was not found.")
except Exception as e:
    print(f"Error reading the CSV file: {e}")