-- Procedure to add a new row to wlist and shuffle taxon_sort values accordingly
DROP PROCEDURE IF EXISTS wlist_add_row;
CREATE OR REPLACE PROCEDURE wlist_add_row(
    -- This is the row below which the new entry will be added
    p_taxon_sort_target     INTEGER,
    -- Required field (NOT NULL in schema) — auto-generated for ultrataxons if not provided
    p_taxon_id              VARCHAR(20) DEFAULT NULL,
    -- Required: must be 1 (ultrataxon) or 0 (not ultrataxon). NULL will halt the procedure.
    p_is_ultrataxon         SMALLINT DEFAULT NULL,
    -- Optional fields
    p_taxon_level           VARCHAR(50) DEFAULT NULL,
    p_sp_id                 SMALLINT DEFAULT NULL,
    p_taxon_name            VARCHAR(255) DEFAULT NULL,
    p_taxon_scientific_name VARCHAR(255) DEFAULT NULL,
    p_family_name           VARCHAR(255) DEFAULT NULL,
    p_family_scientific_name VARCHAR(255) DEFAULT NULL,
    p_t_order               VARCHAR(255) DEFAULT NULL,
    p_population            VARCHAR(255) DEFAULT NULL,
    p_aust_rli_1990         SMALLINT DEFAULT NULL,
    p_aust_rli_2000         SMALLINT DEFAULT NULL,
    p_aust_rli_2010         SMALLINT DEFAULT NULL,
    p_aust_rli              SMALLINT DEFAULT NULL,
    p_bird_group         VARCHAR(255) DEFAULT NULL,
    p_supplementary         SMALLINT DEFAULT NULL,
    p_avibase_id            VARCHAR(255) DEFAULT NULL,
    p_reference             TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_new_taxon_sort INTEGER;
    v_max_taxon_sort INTEGER;
    v_sp_id          SMALLINT;
    v_taxon_id       VARCHAR(20);
    rec RECORD;
BEGIN
    -- ====================================================================
    -- Validate p_is_ultrataxon — must be explicitly provided
    -- ====================================================================
    IF p_is_ultrataxon IS NULL THEN
        RAISE EXCEPTION
            'p_is_ultrataxon must not be NULL. '
            'Please provide p_is_ultrataxon (1 = ultrataxon, 0 = not ultrataxon) '
            'and a full p_taxon_id string.';
    END IF;

    -- ====================================================================
    -- Resolve sp_id: use provided value or auto-assign next available in 5001–7999
    -- ====================================================================
    IF p_sp_id IS NOT NULL THEN
        v_sp_id := p_sp_id;
    ELSE
        SELECT (COALESCE(MAX(sp_id), 5000) + 1)::SMALLINT
        INTO v_sp_id
        FROM wlist
        WHERE sp_id > 5000 AND sp_id < 8000;

        IF v_sp_id >= 8000 THEN
            RAISE EXCEPTION
                'Cannot auto-assign sp_id: all values in range 5001–7999 are exhausted.';
        END IF;

        RAISE NOTICE 'Auto-assigned sp_id = %', v_sp_id;
    END IF;

    -- ====================================================================
    -- Resolve taxon_id: use provided value, or auto-generate for ultrataxons
    -- ====================================================================
    IF p_taxon_id IS NOT NULL THEN
        v_taxon_id := p_taxon_id;
    ELSIF p_is_ultrataxon = 1 THEN
        -- Ultrataxon: prefix sp_id with 'u'
        v_taxon_id := ('u' || v_sp_id)::VARCHAR(20);
        RAISE NOTICE 'Auto-generated taxon_id = % (ultrataxon)', v_taxon_id;
    ELSE
        RAISE EXCEPTION
            'p_taxon_id must be provided when p_is_ultrataxon is not 1. '
            'Please supply a full taxon_id string.';
    END IF;

    -- ====================================================================
    -- Calculate the new taxon_sort value (target + 1)
    -- ====================================================================
    v_new_taxon_sort := p_taxon_sort_target + 1;

    -- Get the maximum taxon_sort value that needs to be updated
    SELECT MAX(taxon_sort) INTO v_max_taxon_sort
    FROM wlist
    WHERE taxon_sort >= v_new_taxon_sort;

    -- Increment taxon_sort for all rows >= the new position
    -- Process in DESCENDING order to avoid unique constraint violations
    IF v_max_taxon_sort IS NOT NULL THEN
        FOR rec IN
            SELECT taxon_id, taxon_sort
            FROM wlist
            WHERE taxon_sort >= v_new_taxon_sort
            ORDER BY taxon_sort DESC
        LOOP
            UPDATE wlist
            SET taxon_sort = rec.taxon_sort + 1
            WHERE taxon_id = rec.taxon_id;
        END LOOP;
    END IF;

    -- ====================================================================
    -- Insert the new row
    -- ====================================================================
    INSERT INTO wlist (
        taxon_sort,
        is_ultrataxon,
        taxon_level,
        sp_id,
        taxon_id,
        taxon_name,
        taxon_scientific_name,
        family_name,
        family_scientific_name,
        t_order,
        population,
        aust_rli_1990,
        aust_rli_2000,
        aust_rli_2010,
        aust_rli,
        bird_group ,
        supplementary,
        avibase_id,
        reference
    ) VALUES (
        v_new_taxon_sort,
        p_is_ultrataxon,
        p_taxon_level,
        v_sp_id,
        v_taxon_id,
        p_taxon_name,
        p_taxon_scientific_name,
        p_family_name,
        p_family_scientific_name,
        p_t_order,
        p_population,
        p_aust_rli_1990,
        p_aust_rli_2000,
        p_aust_rli_2010,
        p_aust_rli,
        p_bird_group ,
        p_supplementary,
        p_avibase_id,
        p_reference
    );

    RAISE NOTICE 'Inserted new row with taxon_sort = %, taxon_id = %, sp_id = %',
                 v_new_taxon_sort, v_taxon_id, v_sp_id;
END;
$$;

COMMENT ON PROCEDURE wlist_add_row IS
    'Adds a new row to wlist below the specified taxon_sort position and increments '
    'subsequent taxon_sort values to maintain uniqueness. '
    'sp_id defaults to the next available value in 5001–7999. '
    'taxon_id is auto-generated as ''u'' || sp_id for ultrataxons (p_is_ultrataxon = 1). '
    'p_is_ultrataxon must be explicitly set; NULL will halt execution.';

CALL wlist_add_row(
    p_taxon_sort_target     := 1729,
    p_taxon_id              := 'u790'::VARCHAR(20),
    p_is_ultrataxon         := 1::SMALLINT,
    p_taxon_level           := 'ssp'::VARCHAR(50),
    p_sp_id                 := 790::SMALLINT,
    p_taxon_name            := 'Common Redpoll (ssp)'::VARCHAR(255),
    p_taxon_scientific_name := 'Acanthis flammea cabaret'::VARCHAR(255),
    p_family_name           := 'Old World Finches'::VARCHAR(255),
    p_family_scientific_name := 'Fringillidae'::VARCHAR(255),
    p_t_order               := 'Passeriformes'::VARCHAR(255),
    p_population            := 'Introduced'::VARCHAR(255),
    p_bird_group         := NULL::VARCHAR(255),
    p_aust_rli_1990         := NULL::SMALLINT,
    p_aust_rli_2000         := NULL::SMALLINT,
    p_aust_rli_2010         := NULL::SMALLINT,
    p_aust_rli              := NULL::SMALLINT,
    p_reference             := NULL::TEXT
);