


-- identify differences based on one of x fields differing using a concat predicate
-- identify wlist_v4 entries that differ from v2
alter table wlist
  drop column v2_taxon_id_diff_sci;
alter table wlist
  drop column v2_taxon_id_diff_common;
alter table wlist
  drop column v2_taxon_name_diff_id;
alter table wlist
  drop column v2_taxon_name_diff_sci;
alter table wlist
  drop column v2_taxon_sci_name_diff_id;
alter table wlist
  drop column v2_taxon_sci_name_diff_name;
alter table wlist
  add v2_taxon_id_diff_sci integer,
  add v2_taxon_id_diff_common integer,
  add v2_taxon_name_diff_id integer,
  add v2_taxon_name_diff_sci integer,
  add v2_taxon_sci_name_diff_id integer,
  add v2_taxon_sci_name_diff_name integer
;

comment on column wlist.v2_taxon_id_diff_sci is 'taxon_id differs based on taxon_scientific_name';
comment on column wlist.v2_taxon_id_diff_common is 'taxon_id differs based on taxon_name';
comment on column wlist.v2_taxon_name_diff_id is 'taxon_name differs based on taxon_id';
comment on column wlist.v2_taxon_name_diff_sci is 'taxon_name differs based on taxon_scientific_name';
comment on column wlist.v2_taxon_sci_name_diff_id is 'taxon_scientific_name differs based on taxon_id';
comment on column wlist.v2_taxon_sci_name_diff_name is 'taxon_scientific_name differs based on taxon_name';

UPDATE wlist
SET v2_taxon_id_diff_sci = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist
    FULL OUTER JOIN wlist_v2 ON wlist.taxon_id = wlist_v2.taxon_id
    WHERE
      wlist.taxon_id IS NULL
    )sub
WHERE
  wlist.taxon_scientific_name = sub.v2_taxon_scientific_name
;

UPDATE wlist
SET v2_taxon_id_diff_common = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist
    FULL OUTER JOIN wlist_v2 ON wlist.taxon_id = wlist_v2.taxon_id
    WHERE
      wlist.taxon_id IS NULL
    )sub
WHERE
  wlist.taxon_name = sub.v2_taxon_name
;

UPDATE wlist
SET v2_taxon_name_diff_id = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist
    FULL OUTER JOIN wlist_v2 ON wlist.taxon_name = wlist_v2.taxon_name
    WHERE
      wlist.taxon_name IS NULL
    )sub
WHERE
  wlist.taxon_id = sub.v2_taxon_id
;

UPDATE wlist
SET v2_taxon_name_diff_sci = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist
    FULL OUTER JOIN wlist_v2 ON wlist.taxon_name = wlist_v2.taxon_name
    WHERE
      wlist.taxon_name IS NULL
    )sub
WHERE
  wlist.taxon_scientific_name = sub.v2_taxon_scientific_name
;

UPDATE wlist
SET v2_taxon_sci_name_diff_id = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist
    FULL OUTER JOIN wlist_v2 ON wlist.taxon_scientific_name = wlist_v2.taxon_scientific_name
    WHERE
      wlist.taxon_scientific_name IS NULL
    )sub
WHERE
  wlist.taxon_id = sub.v2_taxon_id
;

UPDATE wlist
SET v2_taxon_sci_name_diff_name = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist
    FULL OUTER JOIN wlist_v2 ON wlist.taxon_scientific_name = wlist_v2.taxon_scientific_name
    WHERE
      wlist.taxon_scientific_name IS NULL
    )sub
WHERE
  wlist.taxon_name = sub.v2_taxon_name
;

-- do sci names differ
alter table wlist drop column if exists v2_taxon_sci_name_diff;
alter table wlist add v2_taxon_sci_name_diff integer;
UPDATE wlist
SET v2_taxon_sci_name_diff = 1
FROM
  (SELECT
    wlist.is_ultrataxon AS v4_is_ultrataxon,
    wlist.taxon_level AS v4_taxon_level,
    wlist.sp_id AS v4_sp_id,
    wlist.taxon_id AS v4_taxon_id,
    wlist.taxon_name AS v4_taxon_name,
    wlist.taxon_scientific_name AS v4_taxon_scientific_name,
    wlist_v2.is_ultrataxon AS v2_is_ultrataxon,
    wlist_v2.taxon_level AS v2_taxon_level,
    wlist_v2.sp_id AS v2_sp_id,
    wlist_v2.taxon_id AS v2_taxon_id,
    wlist_v2.taxon_name AS v2_taxon_name,
    wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
  FROM wlist
  FULL OUTER JOIN wlist_v2 ON wlist.taxon_scientific_name = wlist_v2.taxon_scientific_name
  WHERE
    wlist.taxon_scientific_name IS NULL
  )sub
WHERE wlist.taxon_id = sub.v4_taxon_id
;





------------------------
------------------------
-- identify wlist_v2 entries that differ from v4
-- populate wlist_v4 with changes from wlist_v2
alter table wlist_v2
  drop column v4_taxon_id_diff_sci;
alter table wlist_v2
  drop column v4_taxon_id_diff_common;
alter table wlist_v2
  drop column v4_taxon_name_diff_id;
alter table wlist_v2
  drop column v4_taxon_name_diff_sci;
alter table wlist_v2
  drop column v4_taxon_sci_name_diff_id;
alter table wlist_v2
  drop column v4_taxon_sci_name_diff_name;

alter table wlist_v2
  add v4_taxon_id_diff_sci integer,
  add v4_taxon_id_diff_common integer,
  add v4_taxon_name_diff_id integer,
  add v4_taxon_name_diff_sci integer,
  add v4_taxon_sci_name_diff_id integer,
  add v4_taxon_sci_name_diff_name integer
;

comment on column wlist_v2.v4_taxon_id_diff_sci is 'taxon_id differs based on taxon_scientific_name';
comment on column wlist_v2.v4_taxon_id_diff_common is 'taxon_id differs based on taxon_name';
comment on column wlist_v2.v4_taxon_name_diff_id is 'taxon_name differs based on taxon_id';
comment on column wlist_v2.v4_taxon_name_diff_sci is 'taxon_name differs based on taxon_scientific_name';
comment on column wlist_v2.v4_taxon_sci_name_diff_id is 'taxon_scientific_name differs based on taxon_id';
comment on column wlist_v2.v4_taxon_sci_name_diff_name is 'taxon_scientific_name differs based on taxon_name';

UPDATE wlist_v2
SET v4_taxon_id_diff_sci = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist_v2
    FULL OUTER JOIN wlist ON wlist_v2.taxon_id = wlist.taxon_id
    WHERE
      wlist.taxon_id IS NULL
    )sub
WHERE
  wlist_v2.taxon_scientific_name = sub.v2_taxon_scientific_name
;

UPDATE wlist_v2
SET v4_taxon_id_diff_common = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist_v2
    FULL OUTER JOIN wlist ON wlist_v2.taxon_id = wlist.taxon_id
    WHERE
      wlist.taxon_id IS NULL
    )sub
WHERE
  wlist_v2.taxon_name = sub.v2_taxon_name
;

UPDATE wlist_v2
SET v4_taxon_name_diff_id = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist_v2
    FULL OUTER JOIN wlist ON wlist_v2.taxon_name = wlist.taxon_name
    WHERE
      wlist.taxon_name IS NULL
    )sub
WHERE
  wlist_v2.taxon_id = sub.v2_taxon_id
;

UPDATE wlist_v2
SET v4_taxon_name_diff_sci = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist_v2
    FULL OUTER JOIN wlist ON wlist_v2.taxon_name = wlist.taxon_name
    WHERE
      wlist.taxon_name IS NULL
    )sub
WHERE
  wlist_v2.taxon_scientific_name = sub.v2_taxon_scientific_name
;

UPDATE wlist_v2
SET v4_taxon_sci_name_diff_id = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist_v2
    FULL OUTER JOIN wlist ON wlist_v2.taxon_scientific_name = wlist.taxon_scientific_name
    WHERE
      wlist.taxon_scientific_name IS NULL
    )sub
WHERE
  wlist_v2.taxon_id = sub.v2_taxon_id
;

UPDATE wlist_v2
SET v4_taxon_sci_name_diff_name = 1
FROM
    (SELECT
      wlist.taxon_id AS v4_taxon_id,
      wlist.taxon_name AS v4_taxon_name,
      wlist.taxon_scientific_name AS taxon_scientific_name,
      wlist_v2.taxon_id AS v2_taxon_id,
      wlist_v2.taxon_name AS v2_taxon_name,
      wlist_v2.taxon_scientific_name AS v2_taxon_scientific_name
    FROM wlist_v2
    FULL OUTER JOIN wlist ON wlist_v2.taxon_scientific_name = wlist.taxon_scientific_name
    WHERE
      wlist.taxon_scientific_name IS NULL
    )sub
WHERE
  wlist_v2.taxon_name = sub.v2_taxon_name
;

-- v2 entries which have changed based on any of an id or name difference in v4
DROP VIEW IF EXISTS wlist_v4_rows_differing_from_v2;
CREATE VIEW wlist_v4_rows_differing_from_v2 AS
SELECT
  wlist.taxon_sort,
  wlist.is_ultrataxon,
  wlist.taxon_level,
  wlist.sp_id,
  wlist.taxon_id,
  wlist.taxon_name,
  wlist.taxon_scientific_name,
  wlist.population,
  v2_taxon_id_diff_sci,
  v2_taxon_id_diff_common,
  v2_taxon_name_diff_id,
  v2_taxon_name_diff_sci,
  v2_taxon_sci_name_diff_id,
  v2_taxon_sci_name_diff_name,
  v2_taxon_sci_name_diff
FROM wlist
FULL OUTER JOIN wlist_v2
ON CONCAT(wlist.sp_id, wlist.taxon_id, wlist.taxon_name, wlist.taxon_scientific_name) = CONCAT(wlist_v2.sp_id, wlist_v2.taxon_id, wlist_v2.taxon_name, wlist_v2.taxon_scientific_name)
WHERE
  CONCAT(wlist_v2.sp_id, wlist_v2.taxon_id, wlist_v2.taxon_name, wlist_v2.taxon_scientific_name) = ''
;
comment on view wlist_v4_rows_differing_from_v2 is 'v2 entries which have changed based on any of an id or name difference in v4';

-- v4 entries which were different in v2 based on any of an id or name difference in v2
DROP VIEW IF EXISTS wlist_v2_rows_differing_from_v4;
CREATE VIEW wlist_v2_rows_differing_from_v4 AS
SELECT
  wlist_v2.taxon_sort,
  wlist_v2.is_ultrataxon,
  wlist_v2.taxon_level,
  wlist_v2.sp_id,
  wlist_v2.taxon_id,
  wlist_v2.taxon_name,
  wlist_v2.taxon_scientific_name,
  v4_taxon_id_diff_sci,
  v4_taxon_id_diff_common,
  v4_taxon_name_diff_id,
  v4_taxon_name_diff_sci,
  v4_taxon_sci_name_diff_id,
  v4_taxon_sci_name_diff_name
FROM wlist
FULL OUTER JOIN wlist_v2
ON CONCAT(wlist.sp_id, wlist.taxon_id, wlist.taxon_name, wlist.taxon_scientific_name) = CONCAT(wlist_v2.sp_id, wlist_v2.taxon_id, wlist_v2.taxon_name, wlist_v2.taxon_scientific_name)
WHERE
  CONCAT(wlist.sp_id, wlist.taxon_id, wlist.taxon_name, wlist.taxon_scientific_name) = ''
;
comment on view wlist_v4_rows_differing_from_v2 is 'v4 entries which were different in v2 based on any of an id or name difference in v2';

SELECT
  SUM(v2_taxon_id_diff_sci) AS num_v2_taxon_id_diff_sci,
  SUM(v2_taxon_id_diff_common) AS num_v2_taxon_id_diff_common,
  SUM(v2_taxon_name_diff_id) AS num_v2_taxon_name_diff_id,
  SUM(v2_taxon_name_diff_sci) AS num_v2_taxon_name_diff_sci,
  SUM(v2_taxon_sci_name_diff_id) AS num_v2_taxon_sci_name_diff_id,
  SUM(v2_taxon_sci_name_diff_name) AS num_v2_taxon_sci_name_diff_name
FROM wlist;

SELECT
  SUM(v4_taxon_id_diff_sci) AS num_v4_taxon_id_diff_sci,
  SUM(v4_taxon_id_diff_common) AS num_v4_taxon_id_diff_common,
  SUM(v4_taxon_name_diff_id) AS num_v4_taxon_name_diff_id,
  SUM(v4_taxon_name_diff_sci) AS num_v4_taxon_name_diff_sci,
  SUM(v4_taxon_sci_name_diff_id) AS num_v4_taxon_sci_name_diff_id,
  SUM(v4_taxon_sci_name_diff_name) AS num_v4_taxon_sci_name_diff_name
FROM wlist_v2;

-- bring in JD data and join - note I am using working wlist and he has wlist
SELECT
  wlist.*,
  wlist_jd.*
FROM wlist
FULL OUTER JOIN wlist_jd ON wlist.taxon_id = wlist_jd.taxon_id
;


-- do reconciliation
-- import
drop table if exists wlist_reco;
create table wlist_reco
(
    taxon_id  varchar DEFAULT NULL,
    change_class  varchar DEFAULT NULL,
    change_class_notes text DEFAULT NULL,
    sum_ref_diff_queries text DEFAULT NULL
);
copy wlist_reco FROM '/Users/glennehmke/Downloads/wlist_reco.csv' DELIMITER ';' CSV;


-- import via ingester
UPDATE wlist_reco
SET change_class = NULL
WHERE change_class = '0';
UPDATE wlist_reco
SET change_class_notes = NULL
WHERE change_class_notes = '0';
UPDATE wlist_reco
SET sum_ref_diff_queries = NULL
WHERE sum_ref_diff_queries = '0';

SELECT
  COUNT(change_class) AS num
FROM wlist_reco
WHERE change_class IS NOT NULL;

-- append to wlist
alter table public.wlist
  drop column if exists change_class;
alter table public.wlist
  drop column if exists change_class_notes;
alter table public.wlist
  drop column if exists sum_ref_diff_queries;

alter table public.wlist
    add change_class varchar;
alter table public.wlist
    add change_class_notes text;
alter table public.wlist
    add sum_ref_diff_queries integer;

UPDATE wlist
SET change_class = wlist_reco.change_class
FROM wlist_reco
WHERE wlist.taxon_id = wlist_reco.taxon_id;

UPDATE wlist
SET change_class_notes = wlist_reco.change_class_notes
FROM wlist_reco
WHERE wlist.taxon_id = wlist_reco.taxon_id;

UPDATE wlist
SET sum_ref_diff_queries = wlist_reco.sum_ref_diff_queries
FROM wlist_reco
WHERE wlist.taxon_id = wlist_reco.taxon_id;

-- make change type lut
DROP TABLE IF EXISTS lut_wlist_change_class CASCADE;
CREATE TABLE lut_wlist_change_class (
  id int NOT NULL,
  class int DEFAULT NULL,
  description text DEFAULT NULL,
  PRIMARY KEY (id)
);

-- summarise
SELECT
  wlist.change_class,
  lut_wlist_change_class.description,
  COUNT(wlist.taxon_id) AS num_changes
FROM wlist
LEFT JOIN lut_wlist_change_class ON wlist.change_class = lut_wlist_change_class.id
WHERE wlist.change_class IS NOT NULL
GROUP BY
  wlist.change_class,
  lut_wlist_change_class.description
ORDER BY
  wlist.change_class
;

-- compare
-- wlist_v4_DONOT EDIT missed
SELECT
  wlist.change_class,
  lut_wlist_change_class.description,
  COUNT(wlist.taxon_id) AS num_changes
FROM wlist
LEFT JOIN lut_wlist_change_class ON wlist.change_class = lut_wlist_change_class.id
JOIN wlist_jd ON wlist.taxon_id = wlist_jd.taxon_id
WHERE
  wlist.change_class IS NOT NULL
  AND wlist_jd.changeneeded_v2_v4 = '0'
GROUP BY
  wlist.change_class,
  lut_wlist_change_class.description
ORDER BY
  wlist.change_class
;

-- wlist_v4_DONOT EDIT identified but not necessary
SELECT
  COUNT(wlist.taxon_id) AS num_changes
FROM wlist
LEFT JOIN lut_wlist_change_class ON wlist.change_class = lut_wlist_change_class.id
JOIN wlist_jd ON wlist.taxon_id = wlist_jd.taxon_id
WHERE
  wlist.change_class IS NULL
  AND wlist_jd.changeneeded_v2_v4 = '1'
;

-- Relative difference queries
SELECT
  wlist.change_class,
  lut_wlist_change_class.description,
  COUNT(wlist.taxon_id) AS num_changes
FROM wlist
LEFT JOIN lut_wlist_change_class ON wlist.change_class = lut_wlist_change_class.id
WHERE
  wlist.change_class IS NOT NULL
  AND wlist.sum_ref_diff_queries IS NULL
GROUP BY
  wlist.change_class,
  lut_wlist_change_class.description
ORDER BY
  wlist.change_class
;

SELECT
  COUNT(wlist.taxon_id) AS num_changes
FROM wlist
LEFT JOIN lut_wlist_change_class ON wlist.change_class = lut_wlist_change_class.id
WHERE
  wlist.change_class IS NULL
  AND wlist.sum_ref_diff_queries IS NOT NULL
;

-- export for review
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
  wlist.t_order,
  wlist.population,
  wlist.supplementary,
  wlist.avibase_id,
  wlist.v2_taxon_id_diff_sci,
  wlist.v2_taxon_id_diff_common,
  wlist.v2_taxon_name_diff_id,
  wlist.v2_taxon_name_diff_sci,
  wlist.v2_taxon_sci_name_diff_id,
  wlist.v2_taxon_sci_name_diff_name,
  wlist.v2_taxon_sci_name_diff,
  wlist.change_class,
  wlist.change_class_notes,
  wlist.sum_ref_diff_queries,
  wlist_jd.changeneeded_v2_v4 wlist_jd_changeneeded_v2_v4,
  wlist_jd.changetype wlist_jd_changetype,
  wlist_jd.spatialchangetype wlist_jd_spatialchangetype,
  wlist_jd.responsibility wlist_jd_responsibility,
  wlist_jd.implemented wlist_jd_implemented,
  wlist_jd.implementedwhere wlist_jd_implementedwhere
FROM wlist
LEFT JOIN wlist_jd ON wlist.taxon_id = wlist_jd.taxon_id
;

--------------------
-- avilist
--------------------
-- export summary of all changes
SELECT
  w.taxon_level,
  w.taxon_id,
  w.taxon_name,
  w.change_class,
  w.change_class_avilist,
  c1.description AS change_class_desc,
  c2.description AS change_class_avilist_desc
FROM wlist w
LEFT JOIN wlist_change_class c1 ON w.change_class = c1.id
LEFT JOIN wlist_change_class c2 ON w.change_class_avilist = c2.id
WHERE w.change_class IS NOT NULL OR w.change_class_avilist IS NOT NULL
ORDER BY w.taxon_sort
;

-- totals
SELECT
  COUNT(*) FILTER (WHERE w.change_class IS NOT NULL OR w.change_class_avilist IS NOT NULL) AS num_changes
FROM wlist w;

-- change summary by tranche
SELECT
  c.id,
  c.description,
  COALESCE(cc.frequency, 0) AS change_class_freq,
  COALESCE(cc.pct_of_total, 0) AS change_class_pct,
  COALESCE(ca.frequency, 0) AS change_class_avilist_freq,
  COALESCE(ca.pct_of_total, 0) AS change_class_avilist_pct
FROM wlist_change_class c
LEFT JOIN (
  SELECT
    w.change_class,
    COUNT(*) AS frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
  FROM wlist w
  WHERE w.change_class IS NOT NULL
  GROUP BY w.change_class
) cc ON c.id = cc.change_class
LEFT JOIN (
  SELECT
    w.change_class_avilist,
    COUNT(*) AS frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
  FROM wlist w
  WHERE w.change_class_avilist IS NOT NULL
  GROUP BY w.change_class_avilist
) ca ON c.id = ca.change_class_avilist
ORDER BY c.id;

