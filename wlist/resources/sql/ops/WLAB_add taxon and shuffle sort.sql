--
-- example add MacGillivray's Prion after Salvin's
  -- Salvin = 369

-- get new sp_id
SELECT
  MAX(sp_id) + 1 AS next_sp_id
FROM wlist
WHERE sp_id BETWEEN 5000 AND 6000;


UPDATE wlist
SET taxon_sort = taxon_sort + 1
WHERE taxon_sort >= 1109
AND sp_id NOT IN (513, 5148, 5149, 5150)
;

  -- add row (in this case clone then alter relevent fields using the missing taxon_sort)
