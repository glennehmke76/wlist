


-- Convert all fields in ala_taxon_list to code compliant naming
alter table public.ala_taxon_list
    drop column species;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Species" TO species;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Species Name" TO taxon_scientific_name_original;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Scientific Name Authorship" TO scientific_name_authorship;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Taxon Rank" TO taxon_rank;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Kingdom" TO kingdom;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Phylum" TO phylum;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Class" TO class;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Order" TO taxonomic_order;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Family" TO family;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Genus" TO genus;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Vernacular Name" TO taxon_name;
ALTER TABLE ala_taxon_list
RENAME COLUMN "Subspecies" TO subspecies;


-- remove parenthetical content
ALTER TABLE ala_taxon_list
ADD COLUMN taxon_scientific_name TEXT;

UPDATE ala_taxon_list
SET taxon_scientific_name = TRIM(
    REGEXP_REPLACE(
        taxon_scientific_name_original,
        '\s*\([^)]*\)\s*',
        ' ',
        'g'
    )
);

-- clean-up spaces
UPDATE ala_taxon_list
SET taxon_scientific_name = REGEXP_REPLACE(
    taxon_scientific_name,
    '\s+',
    ' ',
    'g'
);





alter table public.ala_taxon_list
    drop column sp_id;
alter table public.ala_taxon_list
    drop column taxon_id;

alter table public.ala_taxon_list
    add sp_id integer;

alter table public.ala_taxon_list
    add taxon_id varchar(50);




-- Add the matched_on field
ALTER TABLE ala_taxon_list
ADD COLUMN matched_on VARCHAR(50);

-- Update based on vernacular names first
UPDATE ala_taxon_list
SET
    taxon_id = wlist.taxon_id,
    sp_id = wlist.sp_id,
    matched_on = 'taxon_name'
FROM wlist
WHERE wlist.taxon_name = ala_taxon_list.taxon_name;

-- Then, update unmatched rows based on scientific names
UPDATE ala_taxon_list
SET
    taxon_id = wlist.taxon_id,
    sp_id = wlist.sp_id,
    matched_on = 'taxon_scientific_name'
FROM wlist
WHERE wlist.taxon_scientific_name = ala_taxon_list.taxon_scientific_name
AND ala_taxon_list.taxon_id IS NULL;


-- Update remaining unmatched rows by matching first two words of scientific name
UPDATE ala_taxon_list
SET
    taxon_id = wlist.taxon_id,
    sp_id = wlist.sp_id,
    matched_on = 'taxon_scientific_name_partial'
FROM wlist
WHERE wlist.taxon_level = 'sp'
AND ala_taxon_list.sp_id IS NULL
AND SPLIT_PART(wlist.taxon_scientific_name, ' ', 1) || ' ' || SPLIT_PART(wlist.taxon_scientific_name, ' ', 2) =
    SPLIT_PART(ala_taxon_list.taxon_scientific_name, ' ', 1) || ' ' || SPLIT_PART(ala_taxon_list.taxon_scientific_name, ' ', 2);





SELECT
    taxonomic_order,
    family,
    COUNT(CASE WHEN matched_on = 'taxon_name' THEN 1 END) AS taxon_name,
    COUNT(CASE WHEN matched_on = 'taxon_scientific_name' THEN 1 END) AS taxon_scientific_name,
    COUNT(CASE WHEN matched_on = 'taxon_scientific_name_partial' THEN 1 END) AS taxon_scientific_name_partial,
    COUNT(CASE WHEN matched_on IS NULL THEN 1 END) AS unmatched,
    COUNT(*) AS total
FROM ala_taxon_list
GROUP BY "taxonomic_order", family
ORDER BY "taxonomic_order", family
;


SELECT
  CASE
    WHEN matched_on IS NULL AND GROUPING(matched_on) = 0 THEN 'Unmatched'
    WHEN GROUPING(matched_on) = 1 THEN 'Total'
    ELSE matched_on
  END as matched_on,
  count(*) as num
FROM ala_taxon_list
GROUP BY ROLLUP(matched_on)
ORDER BY
  CASE
    WHEN GROUPING(matched_on) = 1 THEN 2  -- Total last
    WHEN matched_on IS NULL AND GROUPING(matched_on) = 0 THEN 1  -- Unmatched second to last
    ELSE 0  -- All other values first
  END,
  matched_on



-- Add the taxon_level field to ala_taxon_list
ALTER TABLE ala_taxon_list
ADD COLUMN taxon_level VARCHAR;

-- Update ala_taxon_list with taxon_level from wlist based on taxon_id
UPDATE ala_taxon_list
SET taxon_level = wlist.taxon_level
FROM wlist
WHERE wlist.taxon_id = ala_taxon_list.taxon_id
AND ala_taxon_list.taxon_id IS NOT NULL;