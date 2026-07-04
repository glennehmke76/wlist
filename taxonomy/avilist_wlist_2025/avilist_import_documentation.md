# Avilist CSV Import Documentation

## Overview
This document describes the process of importing the avilist.csv file into a new table called 'avilist_aust' in the birdata_plus.public schema. The import process includes making field names PostgreSQL compliant and matching field names to the 'wlist' table where possible.

## Files
- **import_avilist.py**: The main script that performs the import process.
- **/Users/glennehmke/MEGA/Taxonomy/2025 changes/avilist.csv**: The source CSV file containing the avilist data.

## Import Process
The import process consists of the following steps:

1. Connect to the birdata_plus database.
2. Retrieve the structure of the 'wlist' table to understand what field names to match.
3. Read the avilist.csv file using pandas.
4. Transform the CSV column names to be PostgreSQL compliant:
   - Replace spaces, dots, and other non-alphanumeric characters with underscores.
   - Convert to lowercase.
   - Ensure column names don't start with a number.
   - Handle unnamed columns.
5. Match the compliant column names to 'wlist' field names where possible:
   - sequence_avilist -> taxon_sort
   - taxon_rank -> taxon_level
   - taxonid_wlab -> taxon_id
   - taxonname_wlab4 -> taxon_name
   - scientific_name -> taxon_scientific_name
   - family -> family_name
   - family_english_name -> family_scientific_name
   - order -> t_order
   - australian_population -> population
6. Drop the existing 'avilist_aust' table if it exists.
7. Create a new 'avilist_aust' table with the appropriate column names and data types.
8. Import the data from the CSV file into the new table using the COPY command.
9. Verify the import by counting the rows in the new table.

## Results
The import process successfully imported 2022 rows into the 'avilist_aust' table in the birdata_plus.public schema. The table has the following columns:

- changes
- change_explaination
- taxon_sort (matched to wlist.taxon_sort)
- taxon_level (matched to wlist.taxon_level)
- taxon_id (matched to wlist.taxon_id)
- taxon_name (matched to wlist.taxon_name)
- avibaseid
- t_order (matched to wlist.t_order)
- family_name (matched to wlist.family_name)
- family_scientific_name (matched to wlist.family_scientific_name)
- taxon_scientific_name (matched to wlist.taxon_scientific_name)
- english_name_avilist
- english_name_clements_v2024
- english_name_birdlife_v9
- extinct_or_possibly_extinct
- iucn_red_list_category
- population (matched to wlist.population)
- australian_iucn_redliststatus_2020
- extra_unnamed__18
- extra_unnamed__19

## How to Run the Script
To run the script, use the following command:
```
python /Users/glennehmke/MEGA/py_proj/range/import_avilist.py
```

The script will output information about the import process, including the column name mapping, the SQL used to create the table, and the number of rows imported.

## Notes
- The script handles duplicate column names by ensuring that each column name is unique in the CREATE TABLE statement and the COPY command.
- The script determines appropriate PostgreSQL data types based on the pandas data types.
- The script uses the COPY command for efficient bulk loading of data.