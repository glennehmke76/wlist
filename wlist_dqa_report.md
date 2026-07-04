# wlist – Data Quality Assessment Report

**Generated:** 2026-04-13 06:27 UTC  
**Database:** dcoredb @ localhost:5432  
**Total taxa assessed:** 1,739

## 1. Summary

| Assessment | Result | Status |
|---|---|---|
| Referential integrity | 0 orphaned aust_rli value(s) | ✅ PASS |
| Constraint compliance – is_coastal | 0 invalid value(s) | ✅ PASS |
| Constraint compliance – alist_change | 0 invalid value(s) | ✅ PASS |
| Duplicate taxon names | 0 duplicate(s) | ✅ PASS |
| Duplicate scientific names | 0 duplicate(s) | ✅ PASS |
| Duplicate taxon_id values | 0 duplicate(s) | ✅ PASS |
| Duplicate taxon_sort values | 0 duplicate(s) | ✅ PASS |
| AviBase ID coverage | 98.2% populated | ⚠️ PARTIAL |
| RLI coverage (current) | 72.2% populated | ⚠️ PARTIAL |

## 2. Constraints

| Constraint | Table | Type | Applies to | Purpose |
|---|---|---|---|---|
| lut_rli_pk | lut_rli | PRIMARY KEY | id |  |
| wlist_alist_change_check | wlist | CHECK | (alist_change = ANY (ARRAY[0::numeric, 0.5, 1::numeric])) | Only accepts valid Avilist implementability values. |
| wlist_aust_rli_fkey | wlist | FOREIGN KEY | aust_rli | Ensures Red List values reference valid categories. Cascades on update; sets NULL on delete. |
| wlist_change_class_avilist_fkey | wlist | FOREIGN KEY | change_class_avilist |  |
| wlist_change_class_fkey | wlist | FOREIGN KEY | change_class |  |
| wlist_coastal_range_check | wlist | CHECK | (is_coastal = ANY (ARRAY[1, 2])) | Only accepts valid coastal range codes. |
| wlist_pk | wlist | PRIMARY KEY | taxon_id |  |
| wlist_sci_name_level_check | wlist | CHECK | (taxon_scientific_name IS NULL OR taxon_level::text = 'sp'::text AND array_length(regexp_split_to_array(TRIM(BOTH FRO... |  |
| wlist_ssp_ultrataxon_check | wlist | CHECK | (taxon_level::text <> 'ssp'::text OR is_ultrataxon = 1) | Ensures every subspecies (ssp) row is flagged as an ultrataxon; subspecies cannot have is_ultrataxon NULL or FALSE. |
| wlist_taxon_name_ukey | wlist | UNIQUE | taxon_name | Ensures no two taxa share the same common name. |
| wlist_taxon_scientific_name_ukey | wlist | UNIQUE | taxon_scientific_name | Ensures no two taxa share the same scientific name. |
| wlist_ultrataxon_taxonid_check | wlist | CHECK | ((taxon_id::text !~~ 'u%'::text OR is_ultrataxon = 1) AND (is_ultrataxon IS NULL OR taxon_id::text ~~ 'u%'::text)) |  |
| wlist_change_class_pk | wlist_change_class | PRIMARY KEY | id |  |
| wlist_covariates_pkey | wlist_covariates | PRIMARY KEY | taxon_id_cov |  |
| wlist_range_pkey | wlist_range | PRIMARY KEY | id |  |
| wlist_range_measures_pkey | wlist_range_measures | PRIMARY KEY | id |  |
| wlist_range_measures_taxon_id_key | wlist_range_measures | UNIQUE | taxon_id |  |

## 3. Indexes

| Index | Table | Type | Column | Purpose |
|---|---|---|---|---|
| lut_rli_pk | lut_rli | btree | id |  |
| idx_wlist_sp_id | wlist | btree | sp_id |  |
| wlist_pk | wlist | btree | taxon_id |  |
| wlist_taxon_name_ukey | wlist | btree | taxon_name |  |
| wlist_taxon_scientific_name_ukey | wlist | btree | taxon_scientific_name |  |
| wlist_taxon_sort_uindex | wlist | btree | taxon_sort |  |
| wlist_change_class_pk | wlist_change_class | btree | id |  |
| wlist_covariates_pkey | wlist_covariates | btree | taxon_id_cov |  |
| idx_wlist_range_sp_id | wlist_range | btree | sp_id |  |
| idx_wlist_range_taxon_id | wlist_range | btree | taxon_id |  |
| idx_wlist_range_taxon_id_r | wlist_range | btree | taxon_id_r |  |
| wlist_range_pkey | wlist_range | btree | id |  |
| wlist_range_measures_pkey | wlist_range_measures | btree | id |  |
| wlist_range_measures_taxon_id_key | wlist_range_measures | btree | taxon_id |  |

## 4. Referential Integrity

**lut_rli** contains 6 category entries.  
**wlist.aust_rli → lut_rli.id:** 0 orphaned value(s).  

> All `aust_rli` values resolve correctly to a `lut_rli` entry.

## 5. Constraint Compliance

| Constraint | Allowed values | Violations |
|---|---|---|
| is_coastal | 1, 2 | 0 |
| alist_change | 0, 0.5, 1 | 0 |

> All values satisfy their check constraints.

## 6. Functions and Procedures

| Name | Type | Arguments | Returns | Language | Purpose |
|---|---|---|---|---|---|
| update_is_core | FUNCTION |  | trigger | plpgsql | Trigger function to set is_core based on population value. |
| update_rli_required | FUNCTION |  | trigger | plpgsql |  |
| update_ssp_required | FUNCTION |  | trigger | plpgsql | Trigger function to maintain ssp_required across sibling rows. |
| wlist_add_row | PROCEDURE | IN p_taxon_sort_target integer, IN p_taxon_id character varying, IN p_is_ultrataxon smallint, IN p_taxon_level character varying, IN p_sp_id smallint, IN p_taxon_name character varying, IN p_taxon_scientific_name character varying, IN p_family_name character varying, IN p_family_scientific_name character varying, IN p_t_order character varying, IN p_population character varying, IN p_aust_rli_1990 smallint, IN p_aust_rli_2000 smallint, IN p_aust_rli_2010 smallint, IN p_aust_rli smallint, IN p_bird_sub_group character varying, IN p_supplementary smallint, IN p_avibase_id character varying |  | plpgsql | Procedure to insert a row into wlist and shift taxon_sort values below. |
| wlist_delete_row | PROCEDURE | IN p_taxon_id character varying |  | plpgsql | Procedure to delete a row from wlist and close the taxon_sort gap. |

## 7. Triggers

| Trigger | Table | Timing | Events | Level | Function | Enabled | Purpose |
|---|---|---|---|---|---|---|---|
| audit_wlist | wlist | After | INSERT OR DELETE OR UPDATE | Row | log.change_trigger | O |  |
| trg_update_is_core | wlist | Before | INSERT OR UPDATE OF population | Row | update_is_core | O | Maintains is_core flag when population changes or a row is inserted. |
| trg_update_rli_required | wlist | Before | INSERT OR UPDATE OF is_core, is_ultrataxon, population, aust_rli | Row | update_rli_required | O |  |
| trg_update_ssp_required | wlist | After | INSERT OR DELETE OR UPDATE OF is_ultrataxon, taxon_level, sp_id | Row | update_ssp_required | O | Keeps ssp_required in sync when is_ultrataxon/taxon_level/sp_id change or rows are added/removed. |

> Where triggers exist, the linked function/procedure column indicates the database routine invoked by the trigger.

## 8. Duplicate Detection

| Field | Duplicate groups |
|---|---|
| taxon_name | 0 |
| taxon_scientific_name | 0 |
| taxon_id | 0 |
| taxon_sort | 0 |

> No duplicate names or identifiers detected.

## 9. AviBase ID and RLI Coverage

### AviBase identifier

| Metric | Count | Coverage |
|---|---|---|
| AviBase ID populated | 1,708 | 98.2% |

#### Missing AviBase identifiers

| taxon_id | taxon_name | taxon_sci | population |
|---|---|---|---|
| u9939 | Helmeted Guineafowl (ssp) | Numida meleagris ssp | Introduced |
| u902 | Red Junglefowl (ssp) | Gallus gallus ssp | Introduced |
| u950 | Common Pheasant (ssp) | Phasianus colchicus ssp | Introduced |
| u756 | Lord Howe Metallic Pigeon | Columba vitiensis godmanae | Extinct, Endemic |
| u748 | Amsterdam Albatross | Diomedea amsterdamensis | Non-breeding |
| u845 | Tristan Albatross | Diomedea dabbenena | Non-breeding |
| u859 | Campbell Albatross | Thalassarche impavida | Non-breeding |
| u861 | White-capped Albatross | Thalassarche steadi | Non-breeding |
| u863 | Chatham Albatross | Thalassarche eremita | Non-breeding |
| u78a | New Caledonian Gould's Petrel | Pterodroma leucoptera caledonica | Non-breeding |
| u78b | Australian Gould's Petrel | Pterodroma leucoptera leucoptera | Endemic (breeding only) |
| u138a | Eastern Hooded Plover | Thinornis cucullatus cucullatus | Endemic |
| u138b | Western Hooded Plover | Thinornis cucullatus tregellasi | Endemic |
| u114a | Furneaux White-fronted Tern | Sterna striata incerta | Australian |
| u114b | New Zealand White-fronted Tern | Sterna striata striata | Non-breeding |
| u512c | Dirk Hartog Western Grasswren | Amytornis textilis carteri | Extinct, Endemic |
| u512d | Murchison Western Grasswren | Amytornis textilis giganturus | Extinct, Endemic |
| u490b | Southern Cape York Tropical Scrubwren | Sericornis beccarii dubius | Endemic |
| 437 | Copperback Quail-thrush | Cinclosoma clarum  | Endemic |
| u660a | Torresian Blue-faced Parrot-Finch | Erythrura trichroa sigillifer | Australian |
| u994 | Eurasian Tree Sparrow (ssp) | Passer montanus ssp | Introduced |
| u997 | Common Greenfinch (ssp) | Chloris chloris ssp | Introduced |
| u790 | Common Redpoll (ssp) | Acanthis flammea cabaret | Introduced |
| u996 | European Goldfinch (ssp) | Carduelis carduelis ssp | Introduced |
| u869 | Red Bishop | Euplectes orix | Failed introduction |
| u873 | Red-vented Bulbul | Pycnonotus cafer | Failed introduction |
| u951 | White-winged Widowbird | Euplectes albonotatus | Failed introduction |
| 987 | Weka | Gallirallus australis | Failed introduction |
| u987 | Stewart Island Weka | Gallirallus australis scotti | Failed introduction |
| u5000 | Chukar partridge | Alectoris chukar | Failed introduction |
| u5029 | Asian Golden Weaver | Ploceus hypoxanthus | Failed introduction |

> Orphans are due to global list differences and are expected

### Australian Red List Index – coverage by time period

| Period | Taxa assessed | Coverage |
|---|---|---|
| 1990 | 1,255 | 72.2% |
| 2000 | 1,255 | 72.2% |
| 2010 | 1,255 | 72.2% |
| Current | 1,255 | 72.2% |
| No assessment (any period) | 484 | 27.8% of all taxa |

> Taxa with no RLI assessment across any time period may include recently described taxa, data-deficient taxa, or ultrataxa outside the scope of formal assessment cycles.

#### Missing Australian RLI (required taxa)

| taxon_id | taxon_name | taxon_sci | population |
|---|---|---|---|
| u212 | Australasian Shoveler | Spatula rhynchotis | Australian |
| u793 | Collared Imperial-Pigeon | Ducula mullerii | Australian |
| u23 | Superb Fruit-Dove | Ptilinopus superbus | Australian |
| u316 | Papuan Frogmouth | Podargus papuensis | Australian |
| u340 | Chestnut-breasted Cuckoo | Cacomantis castaneiventris | Australian |
| u336 | Oriental Cuckoo | Cuculus optatus | Non-breeding |
| u5136 | New Caledonian Storm-Petrel | Fregetta lineata | Non-breeding/vagrant? |
| u66a | Black-bellied Storm-Petrel (ssp tropica) | Fregetta tropica tropica | Non-breeding |
| u66b | Black-bellied Storm-Petrel (ssp melanoleuca) | Fregetta tropica melanoleuca | Non-breeding |
| u941 | Salvin's Prion | Pachyptila salvini | Non-breeding |
| u83a | Northern Fairy Prion | Pachyptila turtur turtur | Australian |
| u83b | Southern Fairy Prion | Pachyptila turtur subantarctica | Australian |
| u69 | Wedge-tailed Shearwater | Ardenna pacifica | Australian |
| u184 | Great-billed Heron | Ardea sumatrana | Australian |
| u188 | White-faced Heron | Egretta novaehollandiae | Australian |
| u146 | Pied Stilt | Himantopus leucocephalus | Australian |
| u171 | Comb-crested Jacana | Irediparra gallinacea | Australian |
| u115 | Greater Crested Tern | Thalasseus bergii | Australian |
| u219 | Swamp Harrier | Circus approximans | Australian |
| u352a | Central Queensland Noisy Pitta | Pitta versicolor intermedia | Endemic |
| u352b | Cape York Noisy Pitta | Pitta versicolor simillima | Australian |
| u352c | Central East Coast Noisy Pitta | Pitta versicolor versicolor | Endemic |
| u5124 | Variegated Fairy-wren | Malurus lamberti | Endemic |
| u578 | White-naped Honeyeater | Melithreptus lunatus | Endemic |
| u617d | Eyre Peninsula White-eared Honeyeater | Nesoptilotis leucotis schoddei | Endemic |
| u617e | Inland White-eared Honeyeater | Nesoptilotis leucotis depauperata | Endemic |
| u586 | Scarlet Honeyeater | Myzomela sanguinolenta | Australian |
| u607 | White-lined Honeyeater | Meliphaga albilineata | Endemic |
| u634c | Cape York Noisy Miner | Manorina melanocephala titaniota | Endemic |
| u5157 | Chestnut Quail-thrush | Cinclosoma castanotum | Endemic |
| u438 | Chestnut-breasted Quail-thrush | Cinclosoma castaneothorax | Endemic |
| u728 | Restless Flycatcher | Myiagra inquieta | Australian |
| u371 | Frill-necked Monarch | Arses lorealis | Endemic |
| u442 | Northern Scrub-robin | Drymodes superciliaris | Australian |
| u564 | Australian Mistletoebird | Dicaeum hirundinaceum hirundinaceum | Endemic |
| u650a | South-eastern Beautiful Firetail | Stagonopleura bella bella | Endemic |
| u650b | Glenelg Beautiful Firetail | Stagonopleura bella interposita | Endemic |
| u650c | Western Beautiful Firetail | Stagonopleura bella samueli | Endemic |
| u664a | Black-bellied Crimson Finch | Neochmia phaeton phaeton | Australian |
| u663c | Western Star Finch | Emblema ruficauda subclarescens | Endemic |
| u653 | Zebra Finch | Taeniopygia guttata | Australian |

## 10. Notes

- This assessment focuses on structural and relational quality. It does not validate scientific names against external taxonomic authorities (e.g. AviList, AviBase).
- Duplicate name detection flags groups for review; some duplication between species and nominate subspecies records is by design.
- RLI coverage below 100% for historical periods (1990, 2000, 2010) is expected where taxa were not formally assessed in those cycles.