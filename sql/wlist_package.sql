-- export core wlist
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
  wlist.t_order AS order,
  wlist.avibase_id,
  wlist.bird_group,
  wlist.population,
  CASE
    WHEN wlist.coastal_range = 1 THEN 'Obligate'
    WHEN wlist.coastal_range = 5 THEN 'Facultative'
  ELSE NULL END AS coastal_range,
  wlist.aust_rli_1990,
  wlist.aust_rli_2000,
  wlist.aust_rli_2010,
  wlist.aust_rli,
  rl.category AS aust_rli_status_desc
FROM wlist
LEFT JOIN lut_rli rl ON wlist.aust_rli = rl.id
ORDER BY wlist.taxon_sort
;

-- export extinction risk status look-up
SELECT
  lut_rli.id,
  lut_rli.code,
  lut_rli.category
FROM lut_rli;

-- export avilist changes sidecar
SELECT
  wlist.taxon_id,
  CASE
    WHEN wlist.alist_change = 1 THEN 'Implementable'
    WHEN wlist.alist_change = 0 THEN 'Not implementable'
    WHEN wlist.alist_change = 0.5 THEN 'Partially implementable'
    ELSE NULL END AS alist_change,
  wlist.alist_change_note
FROM wlist
WHERE
  wlist.alist_change IS NOT NULL
ORDER BY wlist.taxon_sort
;

-- DDL output
-- =============================================================================
-- TABLE: wlist (parent table)
-- =============================================================================
DROP TABLE IF EXISTS wlist CASCADE;
CREATE TABLE wlist (
    -- Primary identifiers
    taxon_id            VARCHAR(20) NOT NULL,
    sp_id               INTEGER,
    taxon_sort          INTEGER NOT NULL,
    is_ultrataxon       BOOLEAN DEFAULT FALSE,
    taxon_level         VARCHAR(50),
    taxon_name          VARCHAR(255) NOT NULL,
    taxon_scientific_name VARCHAR(255),
    family_name         VARCHAR(100),
    family_scientific_name VARCHAR(100),
    t_order             VARCHAR(100),
    avibase_id          VARCHAR(50),
    bird_group          VARCHAR(100),
    population          VARCHAR(255),
    coastal_range       SMALLINT,
    aust_rli_1990       SMALLINT,
    aust_rli_2000       SMALLINT,
    aust_rli_2010       SMALLINT,
    aust_rli            SMALLINT,
    alist_change        NUMERIC(3,1),
    alist_change_note   TEXT,

    -- Constraints
    CONSTRAINT wlist_pkey PRIMARY KEY (taxon_id),
    CONSTRAINT wlist_taxon_name_ukey UNIQUE (taxon_name),
    CONSTRAINT wlist_taxon_scientific_name_ukey UNIQUE (taxon_scientific_name),
    CONSTRAINT wlist_aust_rli_fkey FOREIGN KEY (aust_rli)
        REFERENCES lut_rli(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT wlist_coastal_range_check CHECK (coastal_range IN (1, 2)),
    CONSTRAINT wlist_alist_change_check CHECK (alist_change IN (0, 0.5, 1)),
    CONSTRAINT wlist_ssp_ultrataxon_check CHECK (
        NOT (taxon_level = 'ssp' AND (is_ultrataxon IS NULL OR is_ultrataxon = FALSE))
    )
);
-- Indexes for wlist
CREATE UNIQUE INDEX idx_wlist_taxon_id ON wlist (taxon_id);
CREATE INDEX idx_wlist_taxon_sort ON wlist (taxon_sort);
CREATE INDEX idx_wlist_sp_id ON wlist (sp_id);
CREATE INDEX idx_wlist_aust_rli ON wlist (aust_rli);
CREATE INDEX idx_wlist_bird_group ON wlist (bird_group);

-- Table comments
COMMENT ON TABLE wlist IS 'Core working list of bird taxa with taxonomic and conservation data';
COMMENT ON COLUMN wlist.taxon_id IS 'Primary taxon identifier';
COMMENT ON COLUMN wlist.taxon_sort IS 'Sorting order for taxonomic display';
COMMENT ON COLUMN wlist.aust_rli IS 'Current Australian Red List Index status (FK to lut_rli)';
COMMENT ON COLUMN wlist.coastal_range IS 'Coastal range: 1=Obligate, 5=Facultative';
COMMENT ON COLUMN wlist.alist_change IS 'Avilist implementability: 0=Not, 0.5=Partial, 1=Full';

-- =============================================================================
-- TABLE: lut_rli (lookup table - Red List Index categories)
-- =============================================================================
-- Reference table for extinction risk status categories

DROP TABLE IF EXISTS lut_rli CASCADE;
CREATE TABLE lut_rli (
    id          SMALLINT NOT NULL,
    code        VARCHAR(10) NOT NULL,
    category    VARCHAR(100) NOT NULL,

    -- Constraints
    CONSTRAINT lut_rli_pkey PRIMARY KEY (id),
    CONSTRAINT lut_rli_code_ukey UNIQUE (code)
);

-- Indexes for lut_rli
CREATE UNIQUE INDEX idx_lut_rli_id ON lut_rli (id);
CREATE INDEX idx_lut_rli_code ON lut_rli (code);

-- Table comments
COMMENT ON TABLE lut_rli IS 'Lookup table for Red List Index extinction risk categories';
COMMENT ON COLUMN lut_rli.id IS 'Primary key and foreign key target';
COMMENT ON COLUMN lut_rli.code IS 'Short code for status (e.g., LC, VU, EN)';
COMMENT ON COLUMN lut_rli.category IS 'Full category description';


-- =============================================================================
-- RELATIONSHIPS SUMMARY
-- =============================================================================
/*
    ┌─────────────────────┐         ┌─────────────────┐
    │       wlist         │         │     lut_rli     │
    ├─────────────────────┤         ├─────────────────┤
    │ taxon_id (PK)       │         │ id (PK)         │
    │ aust_rli (FK) ──────┼────────►│ code (UNIQUE)   │
    │ ...                 │         │ category        │
    └─────────────────────┘         └─────────────────┘

    Foreign Keys:
    • wlist.aust_rli → lut_rli.id

    Indexes:
    • wlist: taxon_id (PK), taxon_sort, sp_id, avibase_id, aust_rli,
             bird_group, family_name, alist_change (partial)
    • lut_rli: id (PK), code (unique)

    Check Constraints:
    • wlist.coastal_range: IN (1, 5)
    • wlist.alist_change: IN (0, 0.5, 1)
 */