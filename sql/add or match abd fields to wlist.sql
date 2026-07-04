

-- Add the non_breeding boolean column to wlist
-- First try to match on common name (abd1)
-- For non-matches on common name, fall back to matching on scientific name (abd2)
-- Set non_breeding = TRUE where either match finds non_breeding_only = '1'

-- Add new boolean field to wlist
ALTER TABLE wlist
ADD COLUMN non_breeding boolean DEFAULT NULL;

-- Populate the field based on abd data using dual left join
UPDATE wlist
SET non_breeding = TRUE
WHERE taxon_id IN (
    -- Match by common name
    SELECT DISTINCT w.taxon_id
    FROM wlist w
    INNER JOIN abd a ON w.taxon_name = a.taxon_common_name
    WHERE a.non_breeding_only = '1'

    UNION

    -- Match by scientific name (for records without common name match)
    SELECT DISTINCT w.taxon_id
    FROM wlist w
    INNER JOIN abd a ON w.taxon_scientific_name = a.taxon_scientific_name
    WHERE a.non_breeding_only = '1'
      AND NOT EXISTS (
          -- Exclude if already matched by common name
          SELECT 1
          FROM abd a2
          WHERE w.taxon_name = a2.taxon_common_name
      )
);


