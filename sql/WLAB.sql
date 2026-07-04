-- wlist v4 (PostGres)

-- take /Users/glennehmke/MEGAsync/Taxonomy/wlist_v4.xlsx and...
  -- F&R 'u' in UltrataxonID to 1s
  -- TRIM cells
  -- delete non-main fields and openoffice saveas wlist_dump.csv

-- create table
  DROP VIEW IF EXISTS wlist_range_inventory_species;
  DROP VIEW IF EXISTS wlist_range_inventory_ultrataxa;
  DROP VIEW IF EXISTS wlist_sp;
  DROP TABLE IF EXISTS wlist;
  CREATE TABLE wlist (
    taxon_sort int DEFAULT NULL, -- index
    is_ultrataxon smallint DEFAULT NULL,
    taxon_level varchar(50) DEFAULT NULL,
    sp_id smallint DEFAULT NULL, -- index
    taxon_id varchar(20) DEFAULT NOT NULL, -- primary key
    taxon_name varchar(255) DEFAULT NULL,
    taxon_scientific_name varchar(255) DEFAULT NULL,
    family_name varchar(255) DEFAULT NULL,
    family_scientific_name varchar(255) DEFAULT NULL,
    t_order varchar(255) DEFAULT NULL,
    population varchar(255) DEFAULT NULL,
    rli_1990 smallint DEFAULT NULL, -- refer to lut_rli for categories
    rli_2000 smallint DEFAULT NULL, -- refer to lut_rli for categories
    rli_2010 smallint DEFAULT NULL, -- refer to lut_rli for categories
    rli_2020 smallint DEFAULT NULL, -- refer to lut_rli for categories
    bird_group varchar(255) DEFAULT NULL,
    bird_sub_group varchar(255) DEFAULT NULL,
    supplementary smallint DEFAULT NULL,
    avibase_id varchar(255) DEFAULT NULL
  );

  copy wlist FROM '/Users/glennehmke/MEGAsync/Taxonomy/wlist_dump.csv' DELIMITER ',' CSV HEADER;

  ALTER TABLE wlist
      ADD CONSTRAINT wlist_pkey PRIMARY KEY (taxon_id);

  CREATE UNIQUE INDEX idx_taxon_sort
      ON wlist USING btree
      (taxon_sort ASC NULLS LAST)
      INCLUDE(taxon_sort);
  CREATE INDEX IF NOT EXISTS idx_wlist_sp_id
  ON wlist (sp_id);

-- add timestamps


-- create species only subset numbers
  CREATE VIEW wlist_sp AS
  SELECT
    *
  FROM wlist
  WHERE taxon_level = 'sp';

-- wlist_range
  DROP TABLE IF EXISTS wlist_range;
  CREATE TABLE wlist_range (
    sp_id smallint DEFAULT NULL,
    taxon_id_r varchar(50) DEFAULT NULL,
    taxon_id varchar(50) DEFAULT NULL,
    is_hybrid smallint DEFAULT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_wlist_range_sp_id
    ON public.wlist_range USING btree
    (sp_id ASC NULLS LAST)
    TABLESPACE pg_default;
  CREATE INDEX IF NOT EXISTS idx_wlist_range_taxon_id
    ON public.wlist_range USING btree
    (taxon_id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
  CREATE INDEX IF NOT EXISTS idx_wlist_range_taxon_id_r
    ON public.wlist_range USING btree
    (taxon_id_r COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;

-- cannot fk until changes are resolved...
--   Black-bellied Storm-Petrel (sp_id 66) now polytypic but do not know range
alter table wlist_range
    add constraint wlist_range_wlist_taxon_id_fk
        foreign key (taxon_id) references wlist;

  copy wlist_range FROM '/Users/glennehmke/MEGAsync/Taxonomy/wlist_range_dump.csv' DELIMITER ',' CSV HEADER;

    CREATE SEQUENCE IF NOT EXISTS public.wlist_range_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1

  ALTER TABLE IF EXISTS wlist_range
      ADD COLUMN id integer NOT NULL DEFAULT nextval('wlist_range_seq'::regclass);
  ALTER TABLE IF EXISTS wlist_range
      ADD PRIMARY KEY (id);



-- check wlist_range has wlist and/or range taxon_ids
--   switch predicates... to get orphans from wlist against range
  SELECT
     wlist_range.taxon_id AS wlist_range_taxon_id,
     range.taxon_id_r AS range_taxon_id_r
  FROM range
  LEFT JOIN wlist_range ON range.taxon_id_r = wlist_range.taxon_id_r
  WHERE
    wlist_range.taxon_id is null
--     OR range.taxon_id_r is not null
  GROUP BY
    wlist_range.taxon_id,
    range.taxon_id_r


          -- sundries
                        -- do as automation from range layers - needs to somehow include row duplication so manual at this point
                    -- NOT CHECKED
                      copy wlist_range FROM '/Volumes/Data/wlist_range.csv' DELIMITER ',' CSV HEADER;

                      -- do correctly
                        table all taxon_id_r
                        add field table with taxon_id
                        populate taxon_id with unique combinations of taxon_id_r

                        CASE
                          WHEN
                            SELECT
                              Count(DISTINCT taxon_id_r) AS taxon_id_r
                            FROM range
                            = 1
                          THEN somehow take 2 off the right to get taxon_id a
                          THEN WHERE count = 2 THEN somehow take 2 off the right to get taxon_id a


                        SPLIT_PART(taxon_id_r, delimiter, position)??



                      ALTER TABLE wlist_range
                          ADD CONSTRAINT wlist_range_pkey PRIMARY KEY (id);
                      CREATE INDEX IF NOT EXISTS idx_wlist_range_sp_id
                      ON wlist_range (sp_id);
                      CREATE INDEX IF NOT EXISTS idx_wlist_range_taxon_id_r
                      ON wlist_range (taxon_id_r);
                      CREATE INDEX IF NOT EXISTS idx_wlist_range_taxon_id
                      ON wlist_range (taxon_id);


                -- inventory wlist_range with wlist
                DROP VIEW IF EXISTS wlist_range_inventory_species;
                CREATE VIEW wlist_range_inventory_species AS
                SELECT DISTINCT
                  wlist_sp.taxon_sort,
                  wlist_sp.sp_id AS wlist_sp_id,
                  wlist_sp.taxon_name,
                  wlist_sp.taxon_scientific_name,
                  wlist_range.sp_id  AS wlist_range_sp_id
                FROM wlist_sp
                LEFT JOIN wlist_range ON wlist_sp.sp_id = wlist_range.sp_id
                --  -- below to identify unmapped species
                -- WHERE
                --   wlist_range.sp_id IS NULL
                ORDER BY wlist_sp.taxon_sort ASC
                ;

                DROP VIEW IF EXISTS wlist_range_inventory_ultrataxa;
                CREATE VIEW wlist_range_inventory_ultrataxa AS
                SELECT DISTINCT
                  wlist.taxon_sort,
                  wlist.taxon_id AS wlist_taxon_id,
                  wlist.taxon_name,
                  wlist.taxon_scientific_name,
                  wlist_range.taxon_id  AS wlist_range_taxon_id
                FROM wlist
                LEFT JOIN wlist_range ON wlist.taxon_id = wlist_range.taxon_id
                --  below to identify unmapped ultrataxa
                -- WHERE
                --   wlist_range.taxon_id IS NULL
                --   AND wlist.is_ultrataxon = 1
                ORDER BY wlist.taxon_sort ASC
                ;

-- covariates table
  DROP TABLE IF EXISTS wlist_covariates;
  CREATE TABLE wlist_covariates (
    taxon_id_cov varchar(20) NOT NULL,
    taxonomic_notes text DEFAULT NULL,
    notes text DEFAULT NULL,
    waterbird_habitat_groups varchar DEFAULT NULL,
    kingford_guilds varchar DEFAULT NULL,
    coastal_range_ge smallint DEFAULT NULL,
    national_priority_taxa smallint DEFAULT NULL,
    national_priority_taxa_2022 smallint DEFAULT NULL,
    grouping_notes text DEFAULT NULL,
    tas_endemic smallint DEFAULT NULL,
    v2_change varchar DEFAULT NULL,
    v2_change_notes text DEFAULT NULL,
    v21_change varchar DEFAULT NULL,
    v21_change_notes text DEFAULT NULL,
    v3_change varchar DEFAULT NULL,
    v3_fields_changed varchar DEFAULT NULL,
    v3_species_splits varchar DEFAULT NULL,
    v32_change varchar DEFAULT NULL,
    v4_change_not_implimented smallint DEFAULT NULL,
    v4_change_required varchar DEFAULT NULL,
    range_layer_updated varchar DEFAULT NULL,
    range_change_type varchar DEFAULT NULL,
    range_notes text DEFAULT NULL,
    range_confidence text DEFAULT NULL,
    intracontinental_migrant smallint DEFAULT NULL,
    coastal_range_bb smallint DEFAULT NULL,
    coastal_range_bb_notes varchar DEFAULT NULL,
    coastal_range smallint DEFAULT NULL -- additive of GE and BB for now
  );

  copy wlist_covariates FROM '/Volumes/Data/wlist_covariates.csv' DELIMITER ',' CSV HEADER;

-- add Barry Baker coastal classifications
  DROP TABLE IF EXISTS wlist_coastal_bb;
  CREATE TABLE wlist_coastal_bb (
    sp_id smallint NOT NULL,
    taxon_id varchar NOT NULL,
    coastal_range_bb_notes varchar DEFAULT NULL,
    coastal_range_bb int DEFAULT NULL,
    taxon_name varchar DEFAULT NULL,
    taxon_scientific_name varchar DEFAULT NULL,
    avibase_id varchar DEFAULT NULL,
    PRIMARY KEY (taxon_id)
  );
  copy wlist_coastal_bb FROM '/Users/glennehmke/MEGAsync/energy/Coastal_BB.csv' DELIMITER ',' CSV HEADER;





  -- check 4.1 vs 4.2 matches
    SELECT
        wlist.sp_id,
        wlist.taxon_id,
        wlist.taxon_name,
        wlist.coastal_range,
        wlist_coastal_bb.*
    FROM wlist
    FULL OUTER JOIN wlist_coastal_bb ON wlist.taxon_id = wlist_coastal_bb.taxon_id
    WHERE wlist_coastal_bb.coastal_bb = 1
    ;
    -- no orphans
  -- GE vs BB classifications
    SELECT
        wlist.sp_id,
        wlist.taxon_id,
        wlist.taxon_name,
        wlist.coastal_range,
        wlist_coastal_bb.*
    FROM wlist
    JOIN wlist_coastal_bb ON wlist.taxon_id = wlist_coastal_bb.taxon_id
    WHERE
        wlist_coastal_bb.coastal_bb = 1
        AND wlist.coastal_range IS NULL
    ;

    alter table public.wlist_covariates
      add coastal_range_bb smallint default null;
    comment on column public.wlist_covariates.coastal_range_bb is 'Barry Baker picks for marine birds';

    alter table public.wlist_covariates
      add coastal_range_bb_notes varchar default null;
    comment on column public.wlist_covariates.coastal_range_bb_notes is 'bary baker notes on marine bird coastal ranges';

	UPDATE wlist_covariates
	SET
		coastal_range_bb = wlist_coastal_bb.coastal_range_bb,
		coastal_range_bb_notes = wlist_coastal_bb.coastal_range_bb_notes
	FROM wlist_coastal_bb
	WHERE
	  wlist_covariates.taxon_id = wlist_coastal_bb.taxon_id
	;

  -- integrate coastal range classifications - for now .... make trigger
    alter table wlist_covariates
      add coastal_range smallint default null;

    UPDATE wlist_covariates
    SET coastal_range = GREATEST(coastal_range_ge, coastal_range_bb)
    ;

-- make wlist + covariates view
  DROP VIEW IF EXISTS wlist_all;
  CREATE VIEW wlist_all AS
  SELECT
    wlist.*,
    wlist_covariates.*
  FROM wlist
  RIGHT JOIN wlist_covariates ON wlist_covariates.taxon_id_cov = wlist.taxon_id
  ;

  DROP VIEW IF EXISTS wlist_sp_all;
  CREATE VIEW wlist_sp_all AS
  SELECT
    wlist.*,
    wlist_covariates.*
  FROM wlist
  RIGHT JOIN wlist_covariates ON wlist_covariates.taxon_id_cov = wlist.taxon_id
  WHERE wlist.taxon_level = 'sp'
  ;

-- get new sp_id
SELECT
  MAX(sp_id) + 1 AS next_sp_id
FROM wlist
WHERE sp_id BETWEEN 5000 AND 6000;



-- checks
  SELECT taxon_id, Count(taxon_id) AS NumRows
  FROM wlist
  GROUP BY taxon_id
  ORDER BY NumRows DESC;


-- merge birdata taxa into single list
  DROP TABLE IF EXISTS species_subspecies;
  CREATE TABLE species_subspecies (
    sp_id int NOT NULL,
    taxon_id varchar(6) NOT NULL,
    common_name varchar(100) NOT NULL,
    scientific_name varchar(100) NULL,
    is_ultrataxon smallint DEFAULT NULL
  );

  INSERT INTO species_subspecies (sp_id, taxon_id, common_name, scientific_name, is_ultrataxon)
  SELECT
    id,
    taxon_id,
    common_name,
    scientific_name,
    is_ultrataxon
  FROM species;

  INSERT INTO species_subspecies (sp_id, taxon_id, common_name, scientific_name)
  SELECT
    species_id,
    taxon_id,
    common_name,
    scientific_name
  FROM subspecies;

-- interrogate birdata /wlist deltas
  -- all rows from wlist against birdata
  SELECT
    wlist.sp_id,
    wlist.taxon_id,
    wlist.taxon_name,
    wlist.taxon_scientific_name,
    species_subspecies.sp_id,
    species_subspecies.taxon_id,
    species_subspecies.common_name,
    species_subspecies.scientific_name
  FROM wlist LEFT JOIN species_subspecies ON wlist.taxon_id = species_subspecies.taxon_id;

-- find non-matching sp_ids based on name fields
  SELECT
    wlist_sp.sp_id,
    wlist_sp.taxon_name,
    wlist_sp.taxon_scientific_name,
    species.id,
    species.common_name,
    species.scientific_name
  FROM wlist_sp FULL OUTER JOIN species ON wlist_sp.sp_id = species.id
  GROUP BY
    wlist_sp.sp_id,
    wlist_sp.taxon_name,
    wlist_sp.taxon_scientific_name,
    species.id,
    species.common_name,
    species.scientific_name
  HAVING
    wlist_sp.taxon_name <> species.common_name
    OR wlist_sp.taxon_scientific_name <> species.scientific_name
  ;


  DROP TABLE IF EXISTS wlist_HabLit;
  CREATE TABLE "wlist_HabLit" (
    "SpNo" SMALLINT(4) NOT NULL,
    "InLit_AridWood" TINYINT(1) DEFAULT NULL,
    "InLit_AridGrass" TINYINT(1) DEFAULT NULL,
    "InLit_Chenopod" TINYINT(1) DEFAULT NULL,
    "InLit_DryScero" TINYINT(1) DEFAULT NULL,
    "InLit_WetScero" TINYINT(1) DEFAULT NULL,
    "InLit_Rainforest" TINYINT(1) DEFAULT NULL,
    "InLit_Mallee" TINYINT(1) DEFAULT NULL,
    "InLit_Savanna" TINYINT(1) DEFAULT NULL
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
  ALTER TABLE "wlist_HabLit" ADD PRIMARY KEY("SpNo");
  -- import file through dialogue without headers


-- import BLI
  make as per bli_current.xlsx

  DROP TABLE IF EXISTS bli_hbw;
  CREATE TABLE bli_hbw (
    id int NOT NULL,
    seq int NOT NULL,
    ssp_seq int DEFAULT NULL,
    taxon_name varchar(255) DEFAULT NULL,
    taxon_scientific_name varchar(255) DEFAULT NULL,
    recognised varchar(2) DEFAULT NULL,
    red_list_cat varchar(10) DEFAULT NULL,
    sis_rec_sp int DEFAULT NULL,
    subspp_id varchar(20) DEFAULT NULL,
    sis_rec int NOT NULL
  );

  copy bli_hbw FROM '/Users/glennehmke/MEGAsync/Taxonomy/bli_hbw.csv' DELIMITER ',' CSV HEADER;

  DELETE FROM bli_hbw
  WHERE
  recognised = 'NR';

  ALTER TABLE bli_hbw
      ADD CONSTRAINT bli_hbw_pkey PRIMARY KEY (id);

  -- xxxx
  SELECT
    wlist.taxon_sort,
    wlist.sp_id,
    wlist.taxon_id,
    wlist.taxon_name,
    wlist.taxon_scientific_name,
    bli_hbw.id,
    bli_hbw.seq AS BLI_HBW_seq,
    bli_hbw.ssp_seq AS BLI_HBW_ssp_seq,
    bli_hbw.sis_rec_sp AS BLI_HBW_SISRecID,
    bli_hbw.subspp_id AS BLI_HBW_subspp_id,
    bli_hbw.taxon_name AS BLI_HBW_CommonName,
    bli_hbw.taxon_scientific_name AS BLI_HBW_ScientificName,
    bli_hbw.red_list_cat AS BLI_HBW_red_list_cat
  FROM wlist LEFT JOIN bli_hbw ON wlist.taxon_scientific_name = bli_hbw.taxon_scientific_name
  ORDER BY wlist.taxon_sort ASC;


-- RLI categories
  DROP TABLE IF EXISTS lut_rli;
  CREATE TABLE lut_rli (
    id int NOT NULL,
    code varchar(255) DEFAULT NULL,
    status varchar(255) DEFAULT NULL
  );

-- wlist va birdata species common names
SELECT
  wlist_sp.sp_id,
  wlist_sp.taxon_name,
  wlist_sp.population,
  species.common_name AS birdata_common_name
FROM wlist_sp
LEFT JOIN species ON wlist_sp.sp_id = species.id
;

-- wlist va birdata species scientific names
SELECT
  wlist_sp.sp_id,
  wlist_sp.taxon_scientific_name,
  wlist_sp.population,
  species.scientific_name AS birdata_scientific_name
FROM wlist_sp
LEFT JOIN species ON wlist_sp.sp_id = species.id
;

-- find name change updates only
SELECT
  wlist_sp.taxon_name,
  species.common_name
FROM wlist_sp FULL OUTER JOIN species ON species.id = wlist_sp.sp_id
WHERE
  wlist_sp.taxon_name <> species.common_name
;

SELECT
  wlist_all.taxon_id,
  wlist_all.taxon_name
FROM wlist_all
JOIN wlist_range ON wlist_all.taxon_id = wlist_range.taxon_id
WHERE
  wlist_all.v4_change_required IS NOT NULL
  AND wlist_range.taxon_id_r NOT LIKE '%.%'
GROUP BY
  wlist_all.taxon_id,
  wlist_all.taxon_name
;

-- # species vs subspecies ultrataxa
  -- toggle is_ultrataxon for all taxa
  SELECT
    taxon_level,
    COUNT(taxon_id)
  FROM wlist
  WHERE
    wlist.is_ultrataxon = 1
    AND
    (population = 'Non-breeding'
    OR population = 'Extinct, endemic'
    OR population = 'Extinct, Endemic'
    OR population = 'Extinct (Australia only)'
    OR population = 'Endemic (breeding only)'
    OR population = 'Endemic'
    OR population = 'Australian')
  GROUP BY
    taxon_level
  ;

-- # species vs subspecies ultrataxa by status X-TAB it
  SELECT
    sub.taxon_level,
    lut_rli.category,
    COUNT(sub.taxon_id)
  FROM
      (SELECT
        taxon_level,
        rli_2020,
        taxon_id
      FROM wlist
      WHERE
        wlist.is_ultrataxon = 1
        AND
        (population = 'Non-breeding'
        OR population = 'Extinct, endemic'
        OR population = 'Extinct, Endemic'
        OR population = 'Extinct (Australia only)'
        OR population = 'Endemic (breeding only)'
        OR population = 'Endemic'
        OR population = 'Australian')
      )sub
  LEFT JOIN lut_rli ON sub.rli_2020 = lut_rli.id
  GROUP BY
    sub.taxon_level,
    lut_rli.category
  ;

UPDATE wlist
SET coastal = NULL;

UPDATE wlist
SET coastal = wlist_covariates.coastal_range_ge
FROM wlist_covariates
WHERE wlist.taxon_id = wlist_covariates.taxon_id_cov;


DROP VIEW IF EXISTS wlist_core;
CREATE VIEW wlist_core AS
SELECT
  wlist.taxon_sort,
  wlist.is_ultrataxon,
  wlist.taxon_level,
  wlist.sp_id,
  wlist.taxon_id,
  wlist.taxon_name,
  wlist.taxon_scientific_name,
  wlist.family_name,
  wlist.family_scientific_name,
  wlist."order",
  wlist.population,
  wlist.rli_1990,
  wlist.rli_2000,
  wlist.rli_2010,
  wlist.rli_2020,
  wlist.bird_group,
  wlist.bird_sub_group,
  wlist.supplementary,
  wlist.avibase_id,
  wlist.coastal
FROM wlist
ORDER BY wlist.taxon_sort ASC
;


-- make wlist big
CREATE TABLE wlist_full AS
SELECT
  wlist.*,
  wlist_covariates.*
FROM wlist
LEFT JOIN wlist_covariates ON wlist.taxon_id = wlist_covariates.taxon_id_cov
;

-- then delete wlist + covariates and run with this





-- with JD 2023
SELECT
  CASE
    WHEN wlist.alist_change = 1 THEN 'Implementable'
    WHEN wlist.alist_change = 0 THEN 'Not implementable'
    WHEN wlist.alist_change = 0.5 THEN 'Partially implementable'
    ELSE NULL END AS alist_change,
  wlist.alist_change_note,
  -- expand list.
  wlist.change_class AS wlist_v2_v4_change_class,
  wlist.change_class_notes AS wlist_v2_v4_change_notes,
  wlist.taxon_sort,
  wlist.is_ultrataxon,
  wlist.taxon_level,
  wlist.sp_id,
  wlist.taxon_id,
  wlist.taxon_name,
  wlist.taxon_scientific_name,
  wlist.family_name,
  wlist.family_scientific_name,
  wlist.t_order AS order,
  wlist.population,
  wlist.rli_1990,
  wlist.rli_2000,
  wlist.rli_2010,
  wlist.rli_2020,
  rl.category AS "Australian status 2020",
  wlist.bird_group,
  wlist.avibase_id,
  wlist_jd.changeneeded_v2_v4 wlist_jd_changeneeded_v2_v4,
  wlist_jd.changetype wlist_jd_changetype,
  wlist_jd.spatialchangetype wlist_jd_spatialchangetype,
  wlist_jd.responsibility wlist_jd_responsibility,
  wlist_jd.implemented wlist_jd_implemented,
  wlist_jd.implementedwhere wlist_jd_implementedwhere
FROM wlist
JOIN lut_rli rl ON wlist.rli_2020 = rl.id
LEFT JOIN wlist_jd ON wlist.taxon_id = wlist_jd.taxon_id
ORDER BY wlist.taxon_sort
;

-------------
-- is core

-- ... existing code ...
-- is core

-- 1. Add the is_core field to wlist table
ALTER TABLE wlist
ADD COLUMN is_core SMALLINT DEFAULT NULL;

COMMENT ON COLUMN wlist.is_core IS 'Core taxa flag: 1 = core taxa (not extinct/failed introduction), NULL = non-core';

-- 2. Update is_core based on population values
UPDATE wlist
SET is_core = CASE
    WHEN population IS NULL THEN 1
    WHEN population NOT LIKE '%Extinct%'
         AND population <> 'Failed introduction' THEN 1
    ELSE NULL
END;

-- 3. Create the trigger function to maintain is_core on population changes
CREATE OR REPLACE FUNCTION update_is_core()
RETURNS TRIGGER AS $$
BEGIN
    -- Set is_core based on population value
    IF NEW.population IS NULL
       OR (NEW.population NOT LIKE '%Extinct%'
           AND NEW.population <> 'Failed introduction') THEN
        NEW.is_core := 1;
    ELSE
        NEW.is_core := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create the trigger on wlist table
DROP TRIGGER IF EXISTS trg_update_is_core ON wlist;

CREATE TRIGGER trg_update_is_core
BEFORE INSERT OR UPDATE OF population ON wlist
FOR EACH ROW
EXECUTE FUNCTION update_is_core();

### Summary of Changes:
1. **Added `is_core` column** - A field that stores `1` for core taxa or for non-core taxa (matching your existing pattern of using `1` or rather than `1` or `0`). `SMALLINT``NULL``NULL`
2. **Updated existing records** - Sets `is_core = 1` for all taxa where:
    - Population does NOT contain 'Extinct' (catches all extinct variants like 'Extinct', 'Extinct, endemic', 'Extinct (Australia only)', etc.)
    - Population is NOT 'Failed introduction'
    - Population is NULL (assumed to be core)

3. **Created trigger function** - `update_is_core()` automatically evaluates the population field and sets `is_core` appropriately.
4. **Created trigger** - `trg_update_is_core` fires:
    - `BEFORE INSERT` - Sets `is_core` when new records are added
    - `BEFORE UPDATE OF population` - Recalculates `is_core` when the population field changes

The trigger uses `BEFORE` timing so it can modify the `NEW` record directly before it's written to the table.
--


-- make table wlist_supp - comment "supplementary listings - eg non-taxonomic units, hybrid taxa, group listings etc"

INSERT INTO wlist_supp (
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
    bird_group,
    bird_sub_group,
    supplementary
)
SELECT
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
    bird_group,
    bird_sub_group,
    supplementary
FROM wlist
WHERE taxon_scientific_name IS NULL;


DELETE FROM wlist_supp
WHERE EXISTS (
    SELECT 1
    FROM wlist
    WHERE wlist.taxon_id = wlist_supp.taxon_id
);


insert into wlist_supp



-- records not in wlist from pre avilist
SELECT *
FROM wlist_pre_avilist
WHERE taxon_id NOT IN (SELECT taxon_id FROM wlist WHERE taxon_id IS NOT NULL);



WITH not_in_wlist AS (
    SELECT *
    FROM wlist_pre_avilist
    WHERE taxon_id NOT IN (SELECT taxon_id FROM wlist WHERE taxon_id IS NOT NULL)
)
INSERT INTO wlist_supp (
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
    bird_group,
    bird_sub_group,
    supplementary
)
SELECT
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
    bird_group,
    bird_sub_group,
    supplementary
FROM not_in_wlist
;

SELECT
    taxon_id,
    COUNT(*) AS duplicate_count
FROM wlist_supp
GROUP BY taxon_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

DELETE FROM wlist_supp
WHERE ctid NOT IN (
    SELECT MIN(ctid)
    FROM wlist_supp
    GROUP BY taxon_id
);


wlist_ssp_ultrataxon_taxonid_check

add a check for taxon_id not begins with 'u' and is_ultrataxon = 1.
check for entries with no aust_rli status.
SELECT *
FROM wlist
WHERE is_core = 1
  AND aust_rli IS NULL
  AND is_ultrataxon = 1
  AND population NOT IN ('Introduced')
ORDER BY taxon_sort;


