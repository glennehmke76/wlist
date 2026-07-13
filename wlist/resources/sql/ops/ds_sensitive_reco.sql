-- Import birdata_records_visibility_by_user_category.csv as ds_reco_birdata

-- Import WLAB_v2_sensitive_species_140126.csv as ds_reco_wlist

alter table public.ds_reco_wlist
    add constraint ds_reco_wlist_pk
        primary key (taxon_id);

-- split legacy compound field to integer
-- Add the new columns
ALTER TABLE ds_details
    ADD COLUMN sensitivity_id INTEGER,
    ADD COLUMN breeding_sensitivity_id INTEGER;

-- Populate the columns based on ds_category parsing
UPDATE ds_details
SET
    sensitivity_id = CASE
        WHEN ds_category IS NOT NULL
             AND ds_category !~ '[bB]'
             AND ds_category ~ '^\d+$'
        THEN ds_category::INTEGER
        ELSE NULL
    END,
    breeding_sensitivity_id = CASE
        WHEN ds_category IS NOT NULL
             AND ds_category ~ '[bB]'
        THEN REGEXP_REPLACE(ds_category, '[^0-9]', '', 'g')::INTEGER
        ELSE NULL
    END;



-- find mismatches version 1
DROP VIEW IF EXISTS ds_sensitive_reco;
CREATE OR REPLACE VIEW ds_sensitive_reco AS
SELECT
    -- All ds_details fields
    w.taxon_sort,
    d.sp_id,
    d.taxon_id,
    d.taxon_name,

    -- Overall compare
    CASE
        WHEN (b.sensitivity_id IS NULL AND b.breeding_sensitivity_id IS NULL)
             AND (d.sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NULL)
        THEN 'Neither populated in either source'
        WHEN b.sensitivity_id IS NULL AND b.breeding_sensitivity_id IS NULL
        THEN 'Not in ds_birdata'
        WHEN d.sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NULL
        THEN 'Not in ds_details'
        WHEN (b.sensitivity_id = d.sensitivity_id OR (b.sensitivity_id IS NULL AND d.sensitivity_id IS NULL))
             AND (b.breeding_sensitivity_id = d.breeding_sensitivity_id OR (b.breeding_sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NULL))
        THEN 'All fields match'
        ELSE 'Has differences'
    END AS overall_comparison,

    -- OA Sensitivity
    CASE
        WHEN b.sensitivity_id IS NULL AND d.sensitivity_id IS NULL THEN 'Equal'
        WHEN b.sensitivity_id IS NULL AND d.sensitivity_id IS NOT NULL THEN 'Present in ds_details only'
        WHEN b.sensitivity_id IS NOT NULL AND d.sensitivity_id IS NULL THEN 'Present in ds_birdata only'
        WHEN b.sensitivity_id = d.sensitivity_id THEN 'Equal'
        WHEN d.sensitivity_id > b.sensitivity_id THEN 'Higher in ds_details'
        WHEN b.sensitivity_id > d.sensitivity_id THEN 'Higher in ds_birdata'
    END AS sensitivity_comparison,

    -- Breeding sensitivity
    CASE
        WHEN b.breeding_sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NULL THEN 'Equal'
        WHEN b.breeding_sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NOT NULL THEN 'Present in ds_details only'
        WHEN b.breeding_sensitivity_id IS NOT NULL AND d.breeding_sensitivity_id IS NULL THEN 'Present in ds_birdata only'
        WHEN b.breeding_sensitivity_id = d.breeding_sensitivity_id THEN 'Equal'
        WHEN d.breeding_sensitivity_id > b.breeding_sensitivity_id THEN 'Higher in ds_details'
        WHEN b.breeding_sensitivity_id > d.breeding_sensitivity_id THEN 'Higher in ds_birdata'
    END AS breeding_sensitivity_comparison,

    -- raw master fields with codes
    CASE
        WHEN d.sensitivity_id IS NOT NULL
        THEN CONCAT(ws_sens.code, ' (', d.sensitivity_id, ')')
        ELSE NULL
    END AS ds_details_sensitivity,
    CASE
        WHEN d.breeding_sensitivity_id IS NOT NULL
        THEN CONCAT(ws_breed.code, ' (', d.breeding_sensitivity_id, ')')
        ELSE NULL
    END AS ds_details_breeding_sensitivity,

    -- raw birdata fields with codes
    CASE
        WHEN b.sensitivity_id IS NOT NULL
        THEN CONCAT(s_sens.code, ' (', b.sensitivity_id, ')')
        ELSE NULL
    END AS birdata_sensitivity,
    CASE
        WHEN b.breeding_sensitivity_id IS NOT NULL
        THEN CONCAT(s_breed.code, ' (', b.breeding_sensitivity_id, ')')
        ELSE NULL
    END AS birdata_breeding_sensitivity,

    -- remaining master fields
    d.sensitivity,
    d.sensitivity_rationale,
    d.sensitivity_cats,
    d.exposure,
    d.exposure_rationale,
    d.exposure_cats,
    d.utility,
    d."utility rationale",
    d.ds_category,
    d.ds_rationale,
    d.ba_comments,
    d.conditions,
    d.is_suggested,
    d.cites,
    d.act,
    d.nsw,
    d.nt,
    d.qld,
    d.sa,
    d.tas,
    d.vic,
    d.wa
FROM ds_details d
FULL OUTER JOIN ds_reco_birdata b ON d.taxon_id = b.taxon_id
-- Join wlist_v2 for ordering
LEFT JOIN wlist_v2 w ON COALESCE(d.taxon_id, b.taxon_id) = w.taxon_id
-- Lookups for ds_details (wlist_sensitivity)
LEFT JOIN wlist_sensitivity ws_sens ON d.sensitivity_id = ws_sens.id
LEFT JOIN wlist_sensitivity ws_breed ON d.breeding_sensitivity_id = ws_breed.id
-- Lookups for birdata (sensitivity)
LEFT JOIN sensitivity s_sens ON b.sensitivity_id = s_sens.id
LEFT JOIN sensitivity s_breed ON b.breeding_sensitivity_id = s_breed.id
WHERE
    (b.sensitivity_id IS DISTINCT FROM d.sensitivity_id)
    OR (b.breeding_sensitivity_id IS DISTINCT FROM d.breeding_sensitivity_id)
ORDER BY w.taxon_sort NULLS LAST;




-- find mismatches version 2 - excludes birdata restricted cat comparisons
DROP VIEW IF EXISTS ds_sensitive_reco;
CREATE OR REPLACE VIEW ds_sensitive_reco AS
WITH code_values AS (
    -- Convert wlist_sensitivity codes to decimal values (NULL if contains non-numeric characters)
    SELECT
        id,
        CASE
            WHEN code ~ '^[0-9]+(\.[0-9]+)?$'
            THEN code::DECIMAL
            ELSE NULL
        END AS code_value
    FROM wlist_sensitivity
),
birdata_code_values AS (
    -- Convert sensitivity codes to decimal values (NULL if contains non-numeric characters)
    SELECT
        id,
        CASE
            WHEN code ~ '^[0-9]+(\.[0-9]+)?$'
            THEN code::DECIMAL
            ELSE NULL
        END AS code_value
    FROM sensitivity
)
SELECT
    -- Core fields
    w.taxon_sort,
    d.sp_id,
    d.taxon_id,
    d.taxon_name,

    -- Overall compare (using code values)
    CASE
        WHEN (bcv_sens.code_value IS NULL AND bcv_breed.code_value IS NULL)
             AND (wcv_sens.code_value IS NULL AND wcv_breed.code_value IS NULL)
        THEN 'Neither populated in either source'
        WHEN bcv_sens.code_value IS NULL AND bcv_breed.code_value IS NULL
        THEN 'Not in ds_birdata'
        WHEN wcv_sens.code_value IS NULL AND wcv_breed.code_value IS NULL
        THEN 'Not in ds_details'
        WHEN (bcv_sens.code_value = wcv_sens.code_value OR (bcv_sens.code_value IS NULL AND wcv_sens.code_value IS NULL))
             AND (bcv_breed.code_value = wcv_breed.code_value OR (bcv_breed.code_value IS NULL AND wcv_breed.code_value IS NULL))
        THEN 'All fields match'
        ELSE 'Has differences'
    END AS overall_comparison,

    -- OA Sensitivity comparison (using code values)
    CASE
        WHEN bcv_sens.code_value IS NULL AND wcv_sens.code_value IS NULL THEN 'Equal'
        WHEN bcv_sens.code_value IS NULL AND wcv_sens.code_value IS NOT NULL THEN 'Present in ds_details only'
        WHEN bcv_sens.code_value IS NOT NULL AND wcv_sens.code_value IS NULL THEN 'Present in ds_birdata only'
        WHEN bcv_sens.code_value = wcv_sens.code_value THEN 'Equal'
        WHEN wcv_sens.code_value > bcv_sens.code_value THEN 'Higher in ds_details'
        WHEN bcv_sens.code_value > wcv_sens.code_value THEN 'Higher in ds_birdata'
    END AS sensitivity_comparison,

    -- Breeding sensitivity comparison (using code values)
    CASE
        WHEN bcv_breed.code_value IS NULL AND wcv_breed.code_value IS NULL THEN 'Equal'
        WHEN bcv_breed.code_value IS NULL AND wcv_breed.code_value IS NOT NULL THEN 'Present in ds_details only'
        WHEN bcv_breed.code_value IS NOT NULL AND wcv_breed.code_value IS NULL THEN 'Present in ds_birdata only'
        WHEN bcv_breed.code_value = wcv_breed.code_value THEN 'Equal'
        WHEN wcv_breed.code_value > bcv_breed.code_value THEN 'Higher in ds_details'
        WHEN bcv_breed.code_value > wcv_breed.code_value THEN 'Higher in ds_birdata'
    END AS breeding_sensitivity_comparison,

    -- raw sensitivity code values
    wcv_sens.code_value AS ds_details_sensitivity,
    bcv_sens.code_value AS birdata_sensitivity,

    -- raw breeding sensitivity code values
    wcv_breed.code_value AS ds_details_breeding_sensitivity,
    bcv_breed.code_value AS birdata_breeding_sensitivity,

    -- remaining master fields
    d.sensitivity,
    d.sensitivity_rationale,
    d.sensitivity_cats,
    d.exposure,
    d.exposure_rationale,
    d.exposure_cats,
    d.utility,
    d."utility rationale",
    d.ds_category,
    d.ds_rationale,
    d.ba_comments,
    d.conditions,
    d.is_suggested,
    d.cites,
    d.act,
    d.nsw,
    d.nt,
    d.qld,
    d.sa,
    d.tas,
    d.vic,
    d.wa
FROM ds_details d
FULL OUTER JOIN ds_reco_birdata b ON d.taxon_id = b.taxon_id
-- Join wlist_v2 for ordering
LEFT JOIN wlist_v2 w ON COALESCE(d.taxon_id, b.taxon_id) = w.taxon_id
-- Join CTE for ds_details code values (wlist_sensitivity)
LEFT JOIN code_values wcv_sens ON d.sensitivity_id = wcv_sens.id
LEFT JOIN code_values wcv_breed ON d.breeding_sensitivity_id = wcv_breed.id
-- Join CTE for birdata code values (sensitivity)
LEFT JOIN birdata_code_values bcv_sens ON b.sensitivity_id = bcv_sens.id
LEFT JOIN birdata_code_values bcv_breed ON b.breeding_sensitivity_id = bcv_breed.id
WHERE
    (bcv_sens.code_value IS DISTINCT FROM wcv_sens.code_value)
    OR (bcv_breed.code_value IS DISTINCT FROM wcv_breed.code_value)
ORDER BY w.taxon_sort NULLS LAST;


-- v3
-- find mismatches version 2 - with two-pass comparison (numeric then string)
DROP VIEW IF EXISTS ds_sensitive_reco;
CREATE OR REPLACE VIEW ds_sensitive_reco AS
WITH code_values AS (
    -- Convert wlist_sensitivity codes to decimal values (NULL if contains non-numeric characters)
    -- Also retain the original string code for fallback comparison
    SELECT
        id,
        code AS code_string,
        CASE
            WHEN code ~ '^[0-9]+(\.[0-9]+)?$'
            THEN code::DECIMAL
            ELSE NULL
        END AS code_value
    FROM wlist_sensitivity
),
birdata_code_values AS (
    -- Convert sensitivity codes to decimal values (NULL if contains non-numeric characters)
    -- Also retain the original string code for fallback comparison
    SELECT
        id,
        code AS code_string,
        CASE
            WHEN code ~ '^[0-9]+(\.[0-9]+)?$'
            THEN code::DECIMAL
            ELSE NULL
        END AS code_value
    FROM sensitivity
)
SELECT
    -- Core fields
    w.taxon_sort,
    d.sp_id,
    d.taxon_id,
    d.taxon_name,

    -- Overall compare (two-pass: numeric first, then string fallback)
    CASE
        -- Both sources have no data
        WHEN (b.sensitivity_id IS NULL AND b.breeding_sensitivity_id IS NULL)
             AND (d.sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NULL)
        THEN 'Neither populated in either source'
        -- Birdata has no data
        WHEN b.sensitivity_id IS NULL AND b.breeding_sensitivity_id IS NULL
        THEN 'Not in ds_birdata'
        -- ds_details has no data
        WHEN d.sensitivity_id IS NULL AND d.breeding_sensitivity_id IS NULL
        THEN 'Not in ds_details'
        -- Numeric comparison succeeds for both fields
        WHEN (bcv_sens.code_value = wcv_sens.code_value OR (bcv_sens.code_value IS NULL AND wcv_sens.code_value IS NULL AND bcv_sens.code_string IS NULL AND wcv_sens.code_string IS NULL))
             AND (bcv_breed.code_value = wcv_breed.code_value OR (bcv_breed.code_value IS NULL AND wcv_breed.code_value IS NULL AND bcv_breed.code_string IS NULL AND wcv_breed.code_string IS NULL))
        THEN 'All fields match'
        -- String fallback comparison when numeric is NULL
        WHEN (bcv_sens.code_value IS NULL OR wcv_sens.code_value IS NULL)
             AND (bcv_sens.code_string = wcv_sens.code_string OR (bcv_sens.code_string IS NULL AND wcv_sens.code_string IS NULL))
             AND (bcv_breed.code_value IS NULL OR wcv_breed.code_value IS NULL)
             AND (bcv_breed.code_string = wcv_breed.code_string OR (bcv_breed.code_string IS NULL AND wcv_breed.code_string IS NULL))
        THEN 'All fields match (string comparison)'
        ELSE 'Has differences'
    END AS overall_comparison,

    -- OA Sensitivity comparison (two-pass)
    CASE
        -- Both NULL (no data)
        WHEN bcv_sens.code_value IS NULL AND wcv_sens.code_value IS NULL
             AND bcv_sens.code_string IS NULL AND wcv_sens.code_string IS NULL
        THEN 'Equal'
        -- Numeric comparison
        WHEN bcv_sens.code_value IS NOT NULL AND wcv_sens.code_value IS NOT NULL THEN
            CASE
                WHEN bcv_sens.code_value = wcv_sens.code_value THEN 'Equal'
                WHEN wcv_sens.code_value > bcv_sens.code_value THEN 'Higher in ds_details'
                WHEN bcv_sens.code_value > wcv_sens.code_value THEN 'Higher in ds_birdata'
            END
        -- String fallback when one or both are non-numeric
        WHEN bcv_sens.code_string IS NULL AND wcv_sens.code_string IS NOT NULL THEN 'Present in ds_details only'
        WHEN bcv_sens.code_string IS NOT NULL AND wcv_sens.code_string IS NULL THEN 'Present in ds_birdata only'
        WHEN bcv_sens.code_string = wcv_sens.code_string THEN 'Equal (string match)'
        ELSE 'String mismatch: ' || COALESCE(wcv_sens.code_string, 'NULL') || ' vs ' || COALESCE(bcv_sens.code_string, 'NULL')
    END AS sensitivity_comparison,

    -- Breeding sensitivity comparison (two-pass)
    CASE
        -- Both NULL (no data)
        WHEN bcv_breed.code_value IS NULL AND wcv_breed.code_value IS NULL
             AND bcv_breed.code_string IS NULL AND wcv_breed.code_string IS NULL
        THEN 'Equal'
        -- Numeric comparison
        WHEN bcv_breed.code_value IS NOT NULL AND wcv_breed.code_value IS NOT NULL THEN
            CASE
                WHEN bcv_breed.code_value = wcv_breed.code_value THEN 'Equal'
                WHEN wcv_breed.code_value > bcv_breed.code_value THEN 'Higher in ds_details'
                WHEN bcv_breed.code_value > wcv_breed.code_value THEN 'Higher in ds_birdata'
            END
        -- String fallback when one or both are non-numeric
        WHEN bcv_breed.code_string IS NULL AND wcv_breed.code_string IS NOT NULL THEN 'Present in ds_details only'
        WHEN bcv_breed.code_string IS NOT NULL AND wcv_breed.code_string IS NULL THEN 'Present in ds_birdata only'
        WHEN bcv_breed.code_string = wcv_breed.code_string THEN 'Equal (string match)'
        ELSE 'String mismatch: ' || COALESCE(wcv_breed.code_string, 'NULL') || ' vs ' || COALESCE(bcv_breed.code_string, 'NULL')
    END AS breeding_sensitivity_comparison,

    -- ds_details sensitivity values (numeric or string fallback)
    COALESCE(wcv_sens.code_value::TEXT, wcv_sens.code_string) AS ds_details_sensitivity,
    COALESCE(wcv_breed.code_value::TEXT, wcv_breed.code_string) AS ds_details_breeding_sensitivity,

    -- birdata sensitivity values (numeric or string fallback)
    COALESCE(bcv_sens.code_value::TEXT, bcv_sens.code_string) AS birdata_sensitivity,
    COALESCE(bcv_breed.code_value::TEXT, bcv_breed.code_string) AS birdata_breeding_sensitivity,

    -- remaining master fields
    d.sensitivity,
    d.sensitivity_rationale,
    d.sensitivity_cats,
    d.exposure,
    d.exposure_rationale,
    d.exposure_cats,
    d.utility,
    d."utility rationale",
    d.ds_category,
    d.ds_rationale,
    d.ba_comments,
    d.conditions,
    d.is_suggested,
    d.cites,
    d.act,
    d.nsw,
    d.nt,
    d.qld,
    d.sa,
    d.tas,
    d.vic,
    d.wa
FROM ds_details d
FULL OUTER JOIN ds_reco_birdata b ON d.taxon_id = b.taxon_id
-- Join wlist_v2 for ordering
LEFT JOIN wlist_v2 w ON COALESCE(d.taxon_id, b.taxon_id) = w.taxon_id
-- Join CTE for ds_details code values (wlist_sensitivity)
LEFT JOIN code_values wcv_sens ON d.sensitivity_id = wcv_sens.id
LEFT JOIN code_values wcv_breed ON d.breeding_sensitivity_id = wcv_breed.id
-- Join CTE for birdata code values (sensitivity)
LEFT JOIN birdata_code_values bcv_sens ON b.sensitivity_id = bcv_sens.id
LEFT JOIN birdata_code_values bcv_breed ON b.breeding_sensitivity_id = bcv_breed.id
WHERE
    -- Numeric mismatch
    (bcv_sens.code_value IS DISTINCT FROM wcv_sens.code_value)
    OR (bcv_breed.code_value IS DISTINCT FROM wcv_breed.code_value)
    -- String mismatch (when numeric is NULL)
    OR (bcv_sens.code_value IS NULL AND wcv_sens.code_value IS NULL
        AND bcv_sens.code_string IS DISTINCT FROM wcv_sens.code_string)
    OR (bcv_breed.code_value IS NULL AND wcv_breed.code_value IS NULL
        AND bcv_breed.code_string IS DISTINCT FROM wcv_breed.code_string)
ORDER BY w.taxon_sort NULLS LAST
;


Here's the updated view that performs a two-pass comparison - first using numeric code values, then falling back to string comparison when codes are non-numeric:
### Key Features:

| Comparison Type | Logic |
| --- | --- |
| **Numeric first** | If both codes are numeric, compare as decimals |
| **String fallback** | If either code is non-numeric (e.g., "3b", "restricted"), compare as strings |
| **Mismatch output** | Shows `String mismatch: X vs Y` when string values differ |
### Output Examples:

| sensitivity_comparison | ds_details_sensitivity | birdata_sensitivity |
| --- | --- | --- |
| `Equal` | `2` | `2` |
| `Higher in ds_details` | `3` | `2` |
| `Equal (string match)` | `3b` | `3b` |
| `String mismatch: 3b vs restricted` | `3b` | `restricted` |
| `Present in ds_details only` | `2` | `NULL` |