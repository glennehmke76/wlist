# A working list (wlist) integrated reconciliation of v2-v4 and AviList changes

*Glenn Ehmke - March 2026*

> This is an update of the September 2024 v2-v4 reconciliation - see wlab reconciliation.pdf.


- Total rows in core wlist: 1742
- change_class populated: 361
- change_class_avilist populated: 128
- Total # changes: 444

_Table generation code_
```sql
SELECT
      COUNT(*) AS total_rows,
      COUNT(w.change_class) AS change_class_non_null,
      COUNT(w.change_class_avilist) AS change_class_avilist_non_null,
      COUNT(*) FILTER (WHERE w.change_class IS NOT NULL OR w.change_class_avilist IS NOT NULL) AS num_changes
    FROM wlist w
    ;
```

*Note: Exported integrated table to integrated_changes.csv*

## # changes by type
![Grouped bar chart](/Users/glennehmke/MEGA/py_proj/wabd/wlist/reconciliation/wlist_change_class_grouped_bar.png)

## Overall frequency – change_class
| change_class_id | change_class_desc | count |
| --- | --- | --- |
| 1a | Species split - allopatric | 51 |
| 1b | Species split - parapatric | 6 |
| 1c | Species split - indeterminate/unknown | 2 |
| 2a | Species lump - allopatric | 1 |
| 3a | Subspecies split - allopatric | 32 |
| 3b | Subspecies split - parapatric | 4 |
| 3c | Subspecies split - indeterminate/unknown | 9 |
| 4a | Subspecies lump - allopatric | 12 |
| 4b | Subspecies lump - parapatric | 7 |
| 4c | Subspecies lump - indeterminate/unknown | 3 |
| 5a | Non-taxonomic change - scientific name  | 109 |
| 5a/b | Non-taxonomic change - scientific and common names | 9 |
| 5a/c | Non-taxonomic change - scientific name  and taxon_id | 2 |
| 5b | Non-taxonomic change - common name  | 78 |
| 5c | Non-taxonomic change - taxon_id | 34 |
| 6a | New listing - species | 1 |
| 6b | New listing - subspecies | 1 |

_Table generation code_
```sql
SELECT
      w.taxon_level,
      w.taxon_id,
      w.taxon_name,
      w.change_class,
      w.change_class_avilist,
      c1.id AS change_class_id,
      c1.description AS change_class_desc,
      c2.id AS change_class_avilist_id,
      c2.description AS change_class_avilist_desc
    FROM wlist w
    LEFT JOIN wlist_change_class c1 ON w.change_class = c1.id
    LEFT JOIN wlist_change_class c2 ON w.change_class_avilist = c2.id
    ORDER BY w.taxon_sort
    ;
```

## Overall frequency – change_class_avilist
| change_class_avilist_id | change_class_avilist_desc | count |
| --- | --- | --- |
| 1a | Species split - allopatric | 44 |
| 1b | Species split - parapatric | 5 |
| 2a | Species lump - allopatric | 16 |
| 2b | Species lump - parapatric | 11 |
| 3a | Subspecies split - allopatric | 3 |
| 3b | Subspecies split - parapatric | 7 |
| 3c | Subspecies split - indeterminate/unknown | 4 |
| 4a | Subspecies lump - allopatric | 16 |
| 4b | Subspecies lump - parapatric | 10 |
| 4c | Subspecies lump - indeterminate/unknown | 1 |
| 5a | Non-taxonomic change - scientific name  | 4 |
| 5a/b | Non-taxonomic change - scientific and common names | 2 |
| 5b | Non-taxonomic change - common name  | 3 |
| 6a | New listing - species | 1 |
| 6b | New listing - subspecies | 1 |

_Table generation code_
```sql
SELECT
      w.taxon_level,
      w.taxon_id,
      w.taxon_name,
      w.change_class,
      w.change_class_avilist,
      c1.id AS change_class_id,
      c1.description AS change_class_desc,
      c2.id AS change_class_avilist_id,
      c2.description AS change_class_avilist_desc
    FROM wlist w
    LEFT JOIN wlist_change_class c1 ON w.change_class = c1.id
    LEFT JOIN wlist_change_class c2 ON w.change_class_avilist = c2.id
    ORDER BY w.taxon_sort
    ;
```

## Highlight: rows with values in BOTH fields
Total rows with both fields populated: 45

Detailed rows (both values present):
| taxon_level | taxon_id | taxon_name | change_class_desc | change_class_avilist_desc |
| --- | --- | --- | --- | --- |
| ssp | u1c | King Island Emu | Non-taxonomic change - scientific name  | Species lump - allopatric |
| sp | u3 | Eastern Rockhopper Penguin | Non-taxonomic change - taxon_id | Species split - allopatric |
| sp | u69 | Wedge-tailed Shearwater | Non-taxonomic change - taxon_id | Subspecies lump - allopatric |
| sp | u910 | South Georgia Diving-Petrel | New listing - species | Species lump - allopatric |
| ssp | u193a | Eastern Little Heron | Subspecies split - allopatric | Subspecies lump - parapatric |
| ssp | u193b | Western Little Heron | Subspecies split - allopatric | Subspecies lump - parapatric |
| sp | u977 | Eastern Cattle Egret | Non-taxonomic change - scientific name  | Species split - allopatric |
| sp | 125 | Silver Gull | Non-taxonomic change - scientific name  | Subspecies split - parapatric |
| ssp | u981a | Southern Atlantic-Pacific Kelp Gull | Subspecies split - indeterminate/unknown | Subspecies lump - indeterminate/unknown |
| sp | 253 | Sooty Owl | Non-taxonomic change - taxon_id | Species lump - allopatric |
| ssp | u253a | Greater Sooty Owl | Subspecies split - allopatric | Species lump - allopatric |
| ssp | u239 | Australian Brown Falcon | Subspecies split - allopatric | Subspecies split - indeterminate/unknown |
| sp | u5153 | Naretha Bluebonnet | Non-taxonomic change - scientific name  | Species split - allopatric |
| ssp | u352b | Cape York Noisy Pitta | Subspecies lump - parapatric | Subspecies lump - allopatric |
| ssp | u352c | Central East Coast Noisy Pitta | Subspecies lump - parapatric | Subspecies lump - allopatric |
| ssp | u5150a | Pilbara Ranges Grasswren | Non-taxonomic change - common name  | Species split - allopatric |
| ssp | u5150b | Cape Range Grasswren | Subspecies split - allopatric | Species split - allopatric |
| ssp | u5149a | Sandhill Rufous Grasswren | Non-taxonomic change - common name  | Species split - allopatric |
| ssp | u5149b | Yellabinna Rufous Grasswren | Subspecies split - allopatric | Species split - allopatric |
| sp | u5148 | Opalton Grasswren | Non-taxonomic change - common name  | Species split - allopatric |
| sp | 641 | Blue-faced Honeyeater | Species split - parapatric | Species lump - parapatric |
| ssp | u641a | Eastern Blue-faced Honeyeater | Non-taxonomic change - taxon_id | Species lump - parapatric |
| ssp | u641b | Cape York Blue-faced Honeyeater | Species split - parapatric | Species lump - parapatric |
| ssp | u641c | Northern Blue-faced Honeyeater | Non-taxonomic change - taxon_id | Species lump - parapatric |
| sp | 580 | Black-chinned Honeyeater | Species split - allopatric | Species lump - parapatric |
| ssp | u580a | South-eastern Black-chinned Honeyeater | Species split - allopatric | Species lump - parapatric |
| ssp | u488f | Buff-breasted Scrubwren | Non-taxonomic change - common name  | Species split - allopatric |
| ssp | u5155a | Kangaroo Island Spotted Scrubwren | Non-taxonomic change - common name  | Species split - allopatric |
| ssp | u5155b | West Coast Spotted Scrubwren | Non-taxonomic change - common name  | Species split - allopatric |
| ssp | u5155g | South-western Spotted Scrubwren | Non-taxonomic change - common name  | Species split - allopatric |
| ssp | u5155h | Nullarbor Coast Spotted Scrubwren | Non-taxonomic change - common name  | Species split - allopatric |
| sp | u5157 | Chestnut Quail-thrush | Non-taxonomic change - scientific name  | Species split - parapatric |
| ssp | u437a | Eastern Copperback Quail-thrush | Non-taxonomic change - scientific name  | Species split - parapatric |
| ssp | u437b | Inland Copperback Quail-thrush | Non-taxonomic change - scientific name  | Species split - parapatric |
| ssp | u437c | South-western Copperback Quail-thrush | Non-taxonomic change - scientific name  | Species split - parapatric |
| sp | 8415 | Grey Whistler | Species split - allopatric | Species lump - allopatric |
| ssp | u8415a | Queensland Grey-headed Whistler | Species split - allopatric | Species lump - allopatric |
| ssp | u8415b | Brown Whistler | Species split - allopatric | Species lump - allopatric |
| ssp | u400c | Papuan Mangrove Golden Whistler | Non-taxonomic change - scientific name  | Subspecies split - parapatric |
| sp | 379 | Lemon-bellied Flycatcher | Species split - allopatric | Species lump - allopatric |
| ssp | u379d | Kimberley Lemon-bellied Flycatcher | Species split - allopatric | Species lump - allopatric |
| ssp | u524b | Western Australian Reed-Warbler | Subspecies split - parapatric | Subspecies lump - parapatric |
| ssp | u664a | Black-bellied Crimson Finch | Species split - allopatric | Subspecies lump - allopatric |
| ssp | u665b | White-bellied Crimson Finch | Species split - allopatric | Subspecies lump - allopatric |
| ssp | u660a | Torresian Blue-faced Parrot-Finch | Non-taxonomic change - common name  | Subspecies split - allopatric |

_Table generation code_
```sql
SELECT
      w.taxon_level,
      w.taxon_id,
      w.taxon_name,
      w.change_class,
      w.change_class_avilist,
      c1.id AS change_class_id,
      c1.description AS change_class_desc,
      c2.id AS change_class_avilist_id,
      c2.description AS change_class_avilist_desc
    FROM wlist w
    LEFT JOIN wlist_change_class c1 ON w.change_class = c1.id
    LEFT JOIN wlist_change_class c2 ON w.change_class_avilist = c2.id
    ORDER BY w.taxon_sort
    ;
```
