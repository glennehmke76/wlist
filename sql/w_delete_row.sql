-- Procedure to delete a row from wlist and shuffle taxon_sort values to close the gap
DROP PROCEDURE IF EXISTS wlist_delete_row;
CREATE OR REPLACE PROCEDURE wlist_delete_row(
    p_taxon_id VARCHAR(20)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_deleted_taxon_sort INTEGER;
    rec RECORD;
BEGIN
    -- Get the taxon_sort of the row to be deleted
    SELECT taxon_sort INTO v_deleted_taxon_sort
    FROM wlist
    WHERE taxon_id = p_taxon_id;

    -- Check if the row exists
    IF v_deleted_taxon_sort IS NULL THEN
        RAISE EXCEPTION 'No row found with taxon_id = %', p_taxon_id;
    END IF;

    -- Delete the row
    DELETE FROM wlist
    WHERE taxon_id = p_taxon_id;

    RAISE NOTICE 'Deleted row with taxon_sort = % for taxon_id = %', v_deleted_taxon_sort, p_taxon_id;

    -- Decrement taxon_sort for all rows > the deleted position
    -- Process in ASCENDING order to avoid unique constraint violations
    FOR rec IN
        SELECT taxon_id AS tid, taxon_sort
        FROM wlist
        WHERE taxon_sort > v_deleted_taxon_sort
        ORDER BY taxon_sort ASC
    LOOP
        UPDATE wlist
        SET taxon_sort = rec.taxon_sort - 1
        WHERE taxon_id = rec.tid;
    END LOOP;

    RAISE NOTICE 'Shuffled taxon_sort values to close the gap';
END;
$$;

COMMENT ON PROCEDURE wlist_delete_row IS 'Deletes a row from wlist by taxon_id and decrements subsequent taxon_sort values to maintain contiguous ordering';

-- Example usage:
-- CALL wlist_delete_row('u756');