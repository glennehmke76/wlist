-- Add the column
ALTER TABLE wlist
ADD COLUMN IF NOT EXISTS ssp_required SMALLINT DEFAULT NULL;

COMMENT ON COLUMN wlist.ssp_required IS 'Flag indicating subspecies mapping required: 1 = sp_id is not an ultrataxon and no subspecies row(s) exists';

-- Initial population
UPDATE wlist
SET ssp_required = 1
WHERE is_ultrataxon IS NULL
  AND NOT EXISTS (
      SELECT 1
      FROM wlist w2
      WHERE w2.sp_id = wlist.sp_id
        AND w2.taxon_level = 'ssp'
  );

-- Trigger function to maintain ssp_required
CREATE OR REPLACE FUNCTION update_ssp_required()
RETURNS TRIGGER AS $$
BEGIN
    -- Update all rows with same sp_id when relevant fields change
    UPDATE wlist
    SET ssp_required = CASE
        WHEN is_ultrataxon IS NULL
             AND NOT EXISTS (
                 SELECT 1
                 FROM wlist w2
                 WHERE w2.sp_id = wlist.sp_id
                   AND w2.taxon_level = 'ssp'
             )
        THEN 1
        ELSE NULL
    END
    WHERE sp_id = COALESCE(NEW.sp_id, OLD.sp_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trg_update_ssp_required ON wlist;

CREATE TRIGGER trg_update_ssp_required
AFTER INSERT OR UPDATE OF is_ultrataxon, taxon_level, sp_id OR DELETE ON wlist
FOR EACH ROW
EXECUTE FUNCTION update_ssp_required();
