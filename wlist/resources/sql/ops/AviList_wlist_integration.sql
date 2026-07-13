DROP VIEW IF EXISTS wlist_avilist_integration;
CREATE VIEW wlist_avilist_integration AS
SELECT
  wlist.taxon_sort,
  wlist.is_ultrataxon,
  wlist.taxon_level,
  wlist.sp_id,
  wlist.taxon_id,
  wlist.taxon_name,
  wlist.taxon_scientific_name,
  wlist.population,
  -- joris D inventory of changes wlist v2 - v4.? changes from 2023
  wlist_jd.changeneeded_v2_v4 wlist_jd_changeneeded_v2_v4,
  wlist_jd.changetype wlist_jd_changetype,
  wlist_jd.spatialchangetype wlist_jd_spatialchangetype,
  wlist_jd.responsibility wlist_jd_responsibility,
  wlist_jd.implemented wlist_jd_implemented,
  wlist_jd.implementedwhere wlist_jd_implementedwhere,
  -- my inventory of changes wlist v2 - 4.6 changes
  wlist.v2_taxon_id_diff_sci,
  wlist.v2_taxon_id_diff_common,
  wlist.v2_taxon_name_diff_id,
  wlist.v2_taxon_name_diff_sci,
  wlist.v2_taxon_sci_name_diff_id,
  wlist.v2_taxon_sci_name_diff_name,
  wlist.v2_taxon_sci_name_diff,
  wlist.change_class,
  wlist.change_class_notes,
  -- SGs Avilist against wlist 4.3
  avilist.scientific_name,
  avilist.common_name_avilist,
  avilist.in_afd_not_wlab,
  avilist.abd_avibase_id,
  avilist.polytypic_but_ssp_in_australia_not_known,
  avilist.wlab_differs_from_avilist,
  avilist.subspecies_in_wlab_not_recognised_in_avilist,
  avilist.subspecies_recognised_by_avilist_not_in_wlab,
  avilist.differences_scientific_name,
  avilist.species_in_avilist_not_wlab,
  avilist.change_genus_spelling,
  avilist.change_species_spelling,
  avilist.change_subspecies_spelling,
  avilist.australian_population_listed_as_full_species_by_avilist,
  avilist.listed_as_subspecies_not_species_by_avilist,
  avilist.subspecies_lumped_by_avilist,
  avilist.subspecies_ignored_by_avilist,
  avilist.listed_in_error_as_occurring_in_australia,
  avilist.wlab_several_closely_related_species,
  avilist.wlab_hybrids,
  avilist.wlab_fictitious_species,
  avilist.additions_now_regular_visitors_or_with_established_population,
  avilist.subspecies_wrong_on_not_recognised_as_being_known_in_wlab,
  avilist.afd_list,
  avilist.in_afd_list_but_no_record_for_australia,
  avilist.afd_taxonomy_differs_from_avilist,
  avilist.subspecies,
  -- KH AviList against wlist4.3
  avilist_kh.avibase_avilist,
  avilist_kh.taxon_rank,
  avilist_kh.common_name_avilist as common_name_avilist_kh,
  avilist_kh.common_name_birdlife as common_name_birdlife_kh,
  avilist_kh.change_kh
FROM wlist
LEFT JOIN avilist ON wlist.taxon_id = avilist.taxon_id -- i.e. Sephen's April AviList version
LEFT JOIN avilist_kh ON wlist.taxon_id = avilist_kh.taxon_id -- Kerryn's AviList version
LEFT JOIN wlist_jd ON wlist.taxon_id = wlist_jd.taxon_id -- from 2013 changes in Birdata
;


SELECT
*
FROM wlist_avilist_integration
WHERE
  -- filter to get any changes on my or Kerryn or stephens fields
  (change_class is not null or change_kh is not null or wlab_differs_from_avilist is not null)
  -- add to filter to species (as classified in wlist 4.6)
  AND taxon_level = 'sp'
  -- add filer to exclude vagrants
  AND population != 'Vagrant'
;



SELECT
*
FROM wlist_avilist_integration
WHERE
   change_kh is not null and wlab_differs_from_avilist is null
  AND population != 'Vagrant'

