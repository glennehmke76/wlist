import sys
import pandas as pd
import re
sys.path.append('/Users/glennehmke/MEGA/py_proj/range/base_plots')
from db_connection import connect_to_database, execute_query, execute_update

def make_pg_compliant(name):
    """Convert a column name to be PostgreSQL compliant."""
    # Replace spaces, dots, and other non-alphanumeric chars with underscores
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Ensure it doesn't start with a number
    if name[0].isdigit():
        name = 'col_' + name
    # Handle unnamed columns
    if name.startswith('unnamed_'):
        name = 'extra_' + name
    return name

def map_to_wlist_fields(csv_field, wlist_fields, used_fields):
    """Map CSV field names to wlist field names where possible."""
    # Direct mappings based on the field names we've seen
    mapping = {
        'sequence_avilist': 'taxon_sort',
        'taxon_rank': 'taxon_level',
        'taxonid_wlab': 'taxon_id',
        'taxonname_wlab4': 'taxon_name',
        'scientific_name': 'taxon_scientific_name',
        'family': 'family_name',
        'family_english_name': 'family_scientific_name',
        'order': 't_order',
        'australian_population': 'population',
        'english_name_avilist': 'common_name',  # Changed to avoid duplicate with taxon_name
    }

    # Check if there's a direct mapping
    if csv_field in mapping and mapping[csv_field] in wlist_fields:
        mapped_field = mapping[csv_field]
        # Check if this field name has already been used
        if mapped_field in used_fields:
            # If already used, keep the original compliant name
            return csv_field
        return mapped_field

    # If no direct mapping, keep the original (but compliant) name
    return csv_field

def main():
    # Path to the CSV file
    csv_path = '/Users/glennehmke/MEGA/Taxonomy/2025 changes/avilist.csv'

    # Connect to the database
    conn = connect_to_database(dbname="birdata_plus")

    # Get the wlist table structure
    wlist_query = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'wlist'
    ORDER BY ordinal_position;
    """
    wlist_columns = execute_query(conn, wlist_query)
    wlist_fields = [col[0] for col in wlist_columns]

    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Create a mapping of original column names to PostgreSQL compliant names
    original_to_compliant = {}
    compliant_to_wlist = {}
    used_wlist_fields = set()

    for col in df.columns:
        compliant_name = make_pg_compliant(col)
        original_to_compliant[col] = compliant_name

        # Try to map to wlist field names
        wlist_name = map_to_wlist_fields(compliant_name, wlist_fields, used_wlist_fields)
        compliant_to_wlist[compliant_name] = wlist_name
        used_wlist_fields.add(wlist_name)

    # Rename the DataFrame columns to be PostgreSQL compliant
    df.rename(columns=original_to_compliant, inplace=True)

    # Print the mapping for reference
    print("Column name mapping:")
    for orig, comp in original_to_compliant.items():
        wlist_name = compliant_to_wlist[comp]
        print(f"Original: {orig} -> Compliant: {comp} -> Wlist: {wlist_name}")

    # Drop the table if it exists
    drop_table_sql = "DROP TABLE IF EXISTS public.avilist_aust;"
    print("\nDropping existing table if it exists...")
    execute_update(conn, drop_table_sql)

    # Create the table in the database
    create_table_sql = "CREATE TABLE public.avilist_aust (\n"

    # Track columns to ensure no duplicates
    added_columns = set()

    # Add columns based on the DataFrame
    for col in df.columns:
        # Get the mapped column name
        mapped_col = compliant_to_wlist[col]

        # Skip if this column name has already been added
        if mapped_col in added_columns:
            print(f"Warning: Skipping duplicate column {mapped_col}")
            continue

        # Determine the PostgreSQL data type based on the pandas dtype
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            pg_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            pg_type = "NUMERIC"
        else:
            pg_type = "TEXT"

        create_table_sql += f"    {mapped_col} {pg_type},\n"
        added_columns.add(mapped_col)

    # Remove the trailing comma and newline, and close the statement
    create_table_sql = create_table_sql.rstrip(",\n") + "\n);"

    print("\nCreating table with SQL:")
    print(create_table_sql)

    # Execute the create table statement
    execute_update(conn, create_table_sql)

    # Import the data
    print("\nImporting data...")

    # Create a new DataFrame with the correct column names
    # This ensures the columns in the CSV match the columns in the table
    new_df = pd.DataFrame()

    # Get the unique mapped column names in the order they appear
    unique_columns = []
    seen_columns = set()
    column_mapping = {}  # Maps unique columns to original columns

    for col in df.columns:
        mapped_col = compliant_to_wlist[col]
        if mapped_col not in seen_columns:
            unique_columns.append(mapped_col)
            seen_columns.add(mapped_col)
            column_mapping[mapped_col] = col

    # Copy data to the new DataFrame with the correct column names
    for mapped_col in unique_columns:
        original_col = column_mapping[mapped_col]
        new_df[mapped_col] = df[original_col]

    # Save the new DataFrame to a temporary CSV file
    temp_csv = '/tmp/avilist_temp.csv'
    new_df.to_csv(temp_csv, index=False, header=False)

    # Create the column string for the COPY command
    columns_str = ', '.join(unique_columns)

    print(f"Columns being imported: {columns_str}")

    # Use the psycopg2 copy_expert method for the COPY command
    with open(temp_csv, 'r') as f:
        with conn.cursor() as cur:
            cur.copy_expert(f"COPY public.avilist_aust ({columns_str}) FROM STDIN WITH CSV", f)

    # Commit the transaction
    conn.commit()

    # Verify the import
    count_query = "SELECT COUNT(*) FROM public.avilist_aust;"
    count = execute_query(conn, count_query)
    print(f"\nImported {count[0][0]} rows into public.avilist_aust")

    # Close the connection
    conn.close()

    print("\nImport completed successfully!")

if __name__ == "__main__":
    main()
