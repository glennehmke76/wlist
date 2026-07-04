import sys
sys.path.append('/Users/glennehmke/MEGA/py_proj/range/base_plots')
from db_connection import connect_to_database, execute_query

# Connect to the database
conn = connect_to_database(dbname="birdata_plus")

# Get the column names and data types from the wlist table
query = """
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'wlist'
ORDER BY ordinal_position;
"""

columns = execute_query(conn, query)

# Print the column names and data types
print("Columns in the 'wlist' table:")
for col in columns:
    print(f"{col[0]} - {col[1]}")

# Close the connection
conn.close()