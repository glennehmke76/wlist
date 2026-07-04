```python
# Import required libraries
import sys
import os
import pandas as pd
from IPython.display import display, HTML

# Add the base_plots directory to the path to import db_connection
sys.path.append(os.path.join('../..', 'base_plots'))
from db_connection import connect_to_database, execute_query

# Connect to the database
conn = connect_to_database(user="glennehmke", dbname="birdata_plus")

# SQL query to execute
sql_query = """
SELECT
  CASE
    WHEN w.alist_change = 1 THEN 'Implementable'
    WHEN w.alist_change = 0 THEN 'Not implementable'
    WHEN w.alist_change = 0.5 THEN 'Partially implementable'
    ELSE NULL END "AviList change",
  w.alist_change_note "Change note",
  w.taxon_id,
  w.taxon_name "Taxon name",
  w.taxon_scientific_name "Taxon scientific name",
  w.population "Population",
  rl.category AS "Australian status 2020",
  w.taxon_sort "Taxon sort"
FROM wlist w
JOIN lut_rli rl ON w.rli_2020 = rl.id
WHERE alist_change IS NOT NULL
ORDER BY w.taxon_sort
"""

# Execute the query
results = execute_query(conn, sql_query)

# Get column names from the query
column_names = [
    "AviList change",
    "Change note",
    "taxon_id",
    "Taxon name",
    "Taxon scientific name",
    "Population",
    "Australian status 2020",
    "Taxon sort"
]

# Create a DataFrame from the results
df = pd.DataFrame(results, columns=column_names)


# Function to format multi-line text for HTML display
def format_multiline_text(text):
    if pd.isna(text):
        return ""
    return text.replace('\n', '<br>')


# Apply the formatting to the Change note column
df['Change note formatted'] = df['Change note'].apply(format_multiline_text)

# Create a copy of the DataFrame for display
display_df = df.copy()
display_df['Change note'] = display_df['Change note formatted']
display_df = display_df.drop(columns=['Change note formatted', 'Taxon sort'])

# Define CSS style for wrapping text in the Change note column
css_style = """
<style>
table {
    border-collapse: collapse;
    width: 100%;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #f2f2f2;
}
td:nth-child(2) {  /* Change note is the 2nd column */
    word-wrap: break-word;
    max-width: 900px;  /* Increased by 300% from 300px */
    white-space: normal;
    text-align: left;
}
td:nth-child(3) {  /* taxon_id is the 3rd column */
    max-width: 30%;  /* Reduced by 70% */
    width: 30%;
    text-align: left;
}
/* Ensure all cells are left-justified */
td {
    text-align: left !important;
}
</style>
"""

# Display the results as HTML with CSS styling to preserve formatting and wrap text
html_table = display_df.to_html(escape=False, index=False)
display(HTML(css_style + html_table))

# Close the database connection
conn.close()

```

    OK 0.02s 100 row(s)




<style>
table {
    border-collapse: collapse;
    width: 100%;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #f2f2f2;
}
td:nth-child(2) {  /* Change note is the 2nd column */
    word-wrap: break-word;
    max-width: 900px;  /* Increased by 300% from 300px */
    white-space: normal;
    text-align: left;
}
td:nth-child(3) {  /* taxon_id is the 3rd column */
    max-width: 30%;  /* Reduced by 70% */
    width: 30%;
    text-align: left;
}
/* Ensure all cells are left-justified */
td {
    text-align: left !important;
}
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>AviList change</th>
      <th>Change note</th>
      <th>taxon_id</th>
      <th>Taxon name</th>
      <th>Taxon scientific name</th>
      <th>Population</th>
      <th>Australian status 2020</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Implementable</td>
      <td>The extinct King and Kangaroo Island Emus, formerly classified as species, are now considered subspecies of Emu, despite substantial morphological differences.</td>
      <td>u1c</td>
      <td>King Island Emu</td>
      <td>Dromaius novaehollandiae minor</td>
      <td>Extinct, Endemic</td>
      <td>Extinct</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The extinct King and Kangaroo Island Emus, formerly classified as species, are now considered subspecies of Emu, despite substantial morphological differences.</td>
      <td>u1d</td>
      <td>Kangaroo Island Emu</td>
      <td>Dromaius novaehollandiae baudinianus</td>
      <td>Extinct, Endemic</td>
      <td>Extinct</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Addition of a specific Australian subspecies.</td>
      <td>u208</td>
      <td>Western Pacific Black Duck</td>
      <td>Anas superciliosa superciliosa</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Now listed as having two subspecies but ranges unknown hence retained as monotypic for a working list</td>
      <td>u210</td>
      <td>Chestnut Teal</td>
      <td>Anas castanea</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Papuan and Eastern subspecies lumped</td>
      <td>u30c</td>
      <td>Eastern Peaceful Dove</td>
      <td>Geopelia placida placida</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Global split sees the core Australian taxa (endemic to Christmas Island) classified as a monotypic species (formerly Christmas Island Glossy Swiftlet). AviList have named 'Christmas Swiftlet', but it doesn't come with Santa, hence Christmas Island Switflet is applied.</td>
      <td>u9925</td>
      <td>Christmas Island Swiftlet</td>
      <td>Collocalia natalis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Trivial global subspecies lump – now monotypic – single Australian ultrataxon remains.</td>
      <td>u51</td>
      <td>Spotless Crake</td>
      <td>Zapornia tabuensis</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly a subspecies of Southern Rockhopper Penguin (Eudyptes chrysocome), Eastern Rockhopper Penguin is now considered a species (Eudyptes filholi). Subspecies name has precedence Ehmke et al. (2017).</td>
      <td>u3</td>
      <td>Eastern Rockhopper Penguin</td>
      <td>Eudyptes filholi</td>
      <td>Australian</td>
      <td>Endangered</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Consultation of seabird experts required given this change would result in loss of ultrataxa and these are allopatric breeding species (though spatial ranges in Australian waters are similar). Birds are readily identifiable.</td>
      <td>u88</td>
      <td>Black-browed Albatross</td>
      <td>Thalassarche melanophris</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Consultation of seabird experts required given this change would result in loss of ultrataxa and these are allopatric breeding species (though spatial ranges in Australian waters are similar). Birds are readily identifiable.</td>
      <td>u859</td>
      <td>Campbell Albatross</td>
      <td>Thalassarche impavida</td>
      <td>Non-breeding</td>
      <td>Vulnerable</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Consultation of seabird experts required given Shy and White-capped Albatrosses are allopatric in breeding, possess distinct ecological traits (e.g., annual versus biennial breeding) and have distinctions in pelagic foraging ranges in Australian waters. White-capped are true pelagic (found mainly outside the continental shelf), while Shy are the opposite. Since no subspecies are listed in AviList, grouping these species would result in the loss of ultrataxa. This has potential conservation implications and would also lead to the loss of spatial information.</td>
      <td>u91</td>
      <td>Shy Albatross</td>
      <td>Thalassarche cauta</td>
      <td>Endemic (breeding only)</td>
      <td>Near Threatened</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Consultation of seabird experts required given Shy and White-capped Albatrosses are allopatric in breeding, possess distinct ecological traits (e.g., annual versus biennial breeding) and have distinctions in pelagic foraging ranges in Australian waters. White-capped are true pelagic (found mainly outside the continental shelf), while Shy are the opposite. Since no subspecies are listed in AviList, grouping these species would result in the loss of ultrataxa. This has potential conservation implications and would also lead to the loss of spatial information.</td>
      <td>u861</td>
      <td>White-capped Albatross</td>
      <td>Thalassarche steadi</td>
      <td>Non-breeding</td>
      <td>Near Threatened</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Avilist lumps Australian and New Caledonian, but the Australian taxon has a very active recovery program and its extinction risk is greater than the global species (endangered vs vulnerable). Given the substantial conservation implications involved in lumping the subspecies, the change is not yet implemented pending review.</td>
      <td>u78a</td>
      <td>New Caledonian Gould's Petrel</td>
      <td>Pterodroma leucoptera caledonica</td>
      <td>Non-breeding</td>
      <td>Vulnerable</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Avilist lumps Australian and New Caledonian, but the Australian taxon has a very active recovery program and its extinction risk is greater than the global species (endangered vs vulnerable). Given the substantial conservation implications involved in lumping the subspecies, the change is not yet implemented pending review.</td>
      <td>u78b</td>
      <td>Australian Gould's Petrel</td>
      <td>Pterodroma leucoptera leucoptera</td>
      <td>Endemic (breeding only)</td>
      <td>Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The New Zealand breeding endemic Whenua Hou Diving-Petrel (Pelecanoides whenuahouensis) lumped into South Georgian Diving-Petrel (Pelecanoides georgicus), now polytypic.<br><br>South Georgian Diving-Petrel retained for P. g. georgicus (although it also breeds on Indian and other Southern ocean islands, including Macquarie) and Whenua Hou Diving-Petrel for P. g. Pelecanoides georgicus whenuahouensis. South Georgia Diving-Petrel is used for the species, though nonsensical given it’s vastly wider distribution than the single island of South Georgia.</td>
      <td>u910</td>
      <td>South Georgia Diving-Petrel</td>
      <td>Pelecanoides georgicus</td>
      <td>Australian</td>
      <td>Critically Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The New Zealand breeding endemic Whenua Hou Diving-Petrel (Pelecanoides whenuahouensis)lumped with South Georgian Diving-Petrel (Pelecanoides georgicus georgicus) as Pelecanoides georgicus whenuahouensis.</td>
      <td>u910a</td>
      <td>South Georgian Diving-Petrel</td>
      <td>Pelecanoides georgicus georgicus</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The New Zealand breeding endemic Whenua Hou Diving-Petrel (Pelecanoides whenuahouensis)lumped with South Georgian Diving-Petrel (Pelecanoides georgicus georgicus) as Pelecanoides georgicus whenuahouensis.</td>
      <td>u910b</td>
      <td>Whenua Hou Diving-Petrel</td>
      <td>Pelecanoides georgicus whenuahouensis</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Australian subspecies reverted to a previous treatment with two core subspecies (macrorhynch and stagnatilis). Common names Eastern and Western, with precedent from Ehmke et al. (2017).</td>
      <td>u193a</td>
      <td>Eastern Little Heron</td>
      <td>Butorides atricapilla macrorhyncha</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Australian subspecies reverted to a previous treatment with two core subspecies (macrorhynch and stagnatilis). Common names Eastern and Western, with precedent from Ehmke et al. (2017).</td>
      <td>u193b</td>
      <td>Western Little Heron</td>
      <td>Butorides atricapilla stagnatilis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Trivial global split – single Australian ultrataxa remains.</td>
      <td>u977</td>
      <td>Eastern Cattle Egret</td>
      <td>Ardea coromanda</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Incorrectly lumped by AviList, who were not aware of pertinent research. AviList has been made aware of the relevant research (Weston et al. 2020) and will restore the subspecies in their next edition. Necessary to retain as polytypic given conservation dependencies of both taxa.<br><br>Weston et al. (2020) Conservation Genetics - https://doi.org/10.1007/s10592-020-01286-2</td>
      <td>u138a</td>
      <td>Eastern Hooded Plover</td>
      <td>Thinornis cucullatus cucullatus</td>
      <td>Endemic</td>
      <td>Vulnerable</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Incorrectly lumped by AviList, who were not aware of pertinent research. AviList has been made aware of the relevant research (Weston et al. 2020) and will restore the subspecies in their next edition. Necessary to retain as polytypic given conservation dependencies of both taxa.<br><br>Weston et al. (2020) Conservation Genetics - https://doi.org/10.1007/s10592-020-01286-2</td>
      <td>u138b</td>
      <td>Western Hooded Plover</td>
      <td>Thinornis cucullatus tregellasi</td>
      <td>Endemic</td>
      <td>Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Core Australian subspecies variegatus remains and the existing subspecies common name is retained with precedent from Ehmke et al. (2017).</td>
      <td>u150</td>
      <td>Eastern Siberian Whimbrel</td>
      <td>Numenius phaeopus variegatus</td>
      <td>Non-breeding</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Global taxonomic shuffle sees the Australian subspecies of White Tern Gygis alba candida split as a species Gygis candida (Common White Tern). <br><br>The Australian subspecies is now the nominotypical (Gygis candida candida). The former subspecies name Indo-Pacific White Tern (Ehmke et al. 2017) is now appropriate for the Australian subspecies, reflecting its distribution as distinct from Gygis candida leucopes, which is endemic to the South Pacific.</td>
      <td>972</td>
      <td>Common White Tern</td>
      <td>Gygis candida</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Global taxonomic shuffle sees the Australian subspecies of White Tern Gygis alba candida split as a species Gygis candida (Common White Tern). <br><br>The Australian subspecies is now the nominotypical (Gygis candida candida). The former subspecies name Indo-Pacific White Tern (Ehmke et al. 2017) is now appropriate for the Australian subspecies, reflecting its distribution as distinct from Gygis candida leucopes, which is endemic to the South Pacific.</td>
      <td>u972</td>
      <td>Indo-Pacific White Tern</td>
      <td>Gygis candida candida</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Partially implementable</td>
      <td>Common name change required as taxon now defined as having a wider distribution (Australasia + South America, Falklands, South Georgia), hence Australasian is not appropriate. Southern Atlantic-Pacific Kelp Gull, although long, reflects subspecies distribution.</td>
      <td>u981a</td>
      <td>Southern Atlantic-Pacific Kelp Gull</td>
      <td>Larus dominicanus dominicanus</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment, lumping the recently split species.<br>Subspecies names retained from the former species.</td>
      <td>u253a</td>
      <td>Greater Sooty Owl</td>
      <td>Tyto tenebricosa tenebricosa</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment, lumping the recently split species.<br>Subspecies names retained from the former species.</td>
      <td>u253b</td>
      <td>Lesser Sooty Owl</td>
      <td>Tyto tenebricosa multipunctata</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Trivial global split - ssp name required, monikered .ssp for now</td>
      <td>u249</td>
      <td>Barn Owl ssp.</td>
      <td>Tyto javanica delicatula</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species name change arising from global split.</td>
      <td>u327a</td>
      <td>South-eastern Torresian Kingfisher</td>
      <td>Todiramphus sordidus colcloughi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species name change arising from global split.</td>
      <td>u327b</td>
      <td>Pilbara Torresian Kingfisher</td>
      <td>Todiramphus sordidus pilbara</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species name change arising from global split.</td>
      <td>u327c</td>
      <td>Northern Torresian Kingfisher</td>
      <td>Todiramphus sordidus sordidus</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Changed to polytypic in AviList (two subspecies), but ranges unknown so retained as monotypic for a working list</td>
      <td>u239</td>
      <td>Australian Brown Falcon</td>
      <td>Falco berigora berigora</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Speculative split of Naretha Bluebonnet Northiella haematogaster narethae to Naretha Bluebonnet (Northiella narethae).</td>
      <td>u5153</td>
      <td>Naretha Bluebonnet</td>
      <td>Northiella narethae</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Subspecies sceintific name change.</td>
      <td>u282d</td>
      <td>Fleurieu Adelaide Rosella</td>
      <td>Platycercus elegans adelaidae</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Long history of uncertainty in complex. Formerly Red-fronted Parakeet with three core Australian subspecies - Norfolk Island Green Parrot (Cyanoramphus novaezelandiae cookie), (extinct) Macquarie Island Red-fronted Parakeet (Cyanoramphus novaezelandiae erythrotis) and (extinct) Lord Howe Red-fronted Parakeet (Cyanoramphus novaezelandiae subflavescens), Australian taxa now split into Red-crowned Parakeet which has four subspecies, three endemic to New Zealand and Macquarie Island Red-fronted Parakeet (Cyanoramphus novaezelandiae erythrotis. <br><br>The extinct Macquarie Island Red-fronted Parakeet is now the only Australian taxon of Red-fronted Parakeet, the Tasman subspecies now forming a distinct species.</td>
      <td>u808</td>
      <td>Macquarie Island Red-fronted Parakeet</td>
      <td>Cyanoramphus novaezelandiae erythrotis</td>
      <td>Extinct, Endemic</td>
      <td>Extinct</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species scientific name change arising from global split. Well established common name retained.</td>
      <td>u5156a</td>
      <td>Norfolk Island Green Parrot</td>
      <td>Cyanoramphus cookii cookii</td>
      <td>Endemic</td>
      <td>Vulnerable</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species scientific name change arising from global split. Red-fronted removed from subspecies name given the split of that taxon. Being the only parakeet to occur on the island, Lord Howe Parakeet is appropriate.</td>
      <td>u5156b</td>
      <td>Lord Howe Parakeet</td>
      <td>Cyanoramphus cookii subflavescens</td>
      <td>Extinct, Endemic</td>
      <td>Extinct</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>307</td>
      <td>Elegant Parrot</td>
      <td>Neophema elegans</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u307a</td>
      <td>Western Elegant Parrot</td>
      <td>Neophema elegans carteri</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u307b</td>
      <td>Eastern Elegant Parrot</td>
      <td>Neophema elegans elegans</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>308</td>
      <td>Rock Parrot</td>
      <td>Neophema petrophila</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u308a</td>
      <td>Western Rock Parrot</td>
      <td>Neophema petrophila petrophila</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u308b</td>
      <td>Eastern Rock Parrot</td>
      <td>Neophema petrophila zietzi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Scientific name change.<br><br>Change of subspecies classification for the small population occurring in Australia on the northern Torres Straight Islands (Boigu and Saibai). <br><br>Named Arafura Coconut Lorikeet (Ehmke et al. 2017), the Australian taxon used to be classified as Trichoglossus haematodus nigrogularis (following Collar et al. 2019), but AviList now lists the Australian taxon as Trichoglossus haematodus caeruleiceps.<br><br>Collar, N.; Christie, D.; Kirwan, G. M. (2019). del Hoyo, Josep; Elliott, Andrew; Sargatal, Jordi; Christie, David A; de Juana, Eduardo (eds.). "Coconut Lorikeet (Trichoglossus haematodus)". Handbook of the Birds of the World Alive. Barcelona: Lynx Edicions. Retrieved 21 February 2019<br><br>There appears to be a history of uncertatintly around the classification of these subspecies, but the sceintific name is altered here in line with the distributional information in AviList. The common name is retained reflecting the geographic distribution of the taxon.</td>
      <td>u9947</td>
      <td>Arafura Coconut Lorikeet</td>
      <td>Trichoglossus haematodus caeruleiceps</td>
      <td>Non-breeding</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Lumped back into Double-eyed Fig-Parrot</td>
      <td>u261c</td>
      <td>Coxen's Fig-Parrot</td>
      <td>Cyclopsitta diophthalma coxeni</td>
      <td>Endemic</td>
      <td>Critically Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formally Cape York Spotted Catbird (Ailuroedus melanotis joanae), now split as Black-eared Catbird (Ailuroedus melanotis).</td>
      <td>u677</td>
      <td>Black-eared Catbird</td>
      <td>Ailuroedus melanotis</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formally Wet Tropics Spotted Catbird (Ailuroedus melanotis maculosus), now a monotypic species Spotted Catbird (Ailuroedus maculosus).</td>
      <td>u5151</td>
      <td>Spotted Catbird</td>
      <td>Ailuroedus maculosus</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly named Pilbara Rufous Grasswren. Given Rufous is synonymous with the ‘Sandhill Grasswren’, and Pilbara Grasswren is now a species name for two subspecies, ‘Pilbara Ranges’ Grasswren is allocated for Amytornis whitei whitei, in recognition of its distribution across the inland ranges of the Pilbara.</td>
      <td>u5150a</td>
      <td>Pilbara Ranges Grasswren</td>
      <td>Amytornis whitei whitei</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly a subspecies of Striated Grasswren, now of Pilbara Grasswren. Existing subspecies name retained.</td>
      <td>u5150b</td>
      <td>Cape Range Grasswren</td>
      <td>Amytornis whitei parvus</td>
      <td>Endemic</td>
      <td>Critically Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly a subspecies of Striated Grasswren, now of Pilbara Grasswren. Existing subspecies name retained.</td>
      <td>5149a</td>
      <td>Sandhill Rufous Grasswren</td>
      <td>Amytornis oweni oweni</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly a subspecies of Striated Grasswren, now of Pilbara Grasswren. Existing subspecies name retained.</td>
      <td>5149b</td>
      <td>Yellabinna Rufous Grasswren</td>
      <td>Amytornis oweni aenigma</td>
      <td>Endemic</td>
      <td>Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly a subspecies of Striated Grasswren, 'Rusty Striated Grasswren', now a monotypic species. Name reflects distribution.</td>
      <td>u5148</td>
      <td>Opalton Grasswren</td>
      <td>Amytornis rowleyi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u641a</td>
      <td>Eastern Blue-faced Honeyeater</td>
      <td>Entomyzon cyanotis cyanotis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u641b</td>
      <td>Cape York Blue-faced Honeyeater</td>
      <td>Entomyzon cyanotis griseigularis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u641c</td>
      <td>Northern Blue-faced Honeyeater</td>
      <td>Entomyzon cyanotis albipennis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>580</td>
      <td>Black-chinned Honeyeater</td>
      <td>Melithreptus gularis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u580a</td>
      <td>South-eastern Black-chinned Honeyeater</td>
      <td>Melithreptus gularis gularis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Subspecies names from Ehmke et al. (2017).</td>
      <td>u580b</td>
      <td>Golden-backed Honeyeater</td>
      <td>Melithreptus gularis laetior</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u488c</td>
      <td>Flinders Island White-browed Scrubwren</td>
      <td>Sericornis frontalis flindersi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u488d</td>
      <td>South-eastern White-browed Scrubwren</td>
      <td>Sericornis frontalis frontalis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u488e</td>
      <td>Southern Mainland White-browed Scrubwren</td>
      <td>Sericornis frontalis harterti</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u488f</td>
      <td>Buff-breasted Scrubwren</td>
      <td>Sericornis frontalis laevigaster</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u488i</td>
      <td>Mount Lofty Ranges White-browed Scrubwren</td>
      <td>Sericornis frontalis rosinae</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u488j</td>
      <td>Central east Coast White-browed Scrubwren</td>
      <td>Sericornis frontalis tweedi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u5155a</td>
      <td>Kangaroo Island Spotted Scrubwren</td>
      <td>Sericornis maculatus ashbyi</td>
      <td>Endemic</td>
      <td>Endangered</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u5155b</td>
      <td>West Coast Spotted Scrubwren</td>
      <td>Sericornis maculatus balstoni</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u5155g</td>
      <td>South-western Spotted Scrubwren</td>
      <td>Sericornis maculatus maculatus</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Species split, subspecies epithets retained from Ehmke et al. (2017)</td>
      <td>u5155h</td>
      <td>Nullarbor Coast Spotted Scrubwren</td>
      <td>Sericornis maculatus mellori</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Only 1 ssp identified in Australia in AviList but there is no note as to why S. b. minimus and dubius have been lumped. In line with policy of not lumping ultrataxa without cause, and S. b. minimus and dubius having discrete ranges in Australia (with a hybrid zone), both Australian subspecies are retained in line with Schodde and Mason (1999) and Gregory (2024).<br><br>Gregory, P. (2024). Tropical Scrubwren (Sericornis beccarii), version 1.2. In Birds of the World (N. D. Sly and M. G. Smith, Editors). Cornell Lab of Ornithology, Ithaca, NY, USA. https://doi.org/10.2173/bow.becscr1.01.2</td>
      <td>u490a</td>
      <td>Northern Cape York Tropical Scrubwren</td>
      <td>Sericornis beccarii minimus</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>Only 1 ssp identified in Australia in AviList but there is no note as to why S. b. minimus and dubius have been lumped. In line with policy of not lumping ultrataxa without cause, and S. b. minimus and dubius having discrete ranges in Australia (with a hybrid zone), both Australian subspecies are retained in line with Schodde and Mason (1999) and Gregory (2024).<br><br>Gregory, P. (2024). Tropical Scrubwren (Sericornis beccarii), version 1.2. In Birds of the World (N. D. Sly and M. G. Smith, Editors). Cornell Lab of Ornithology, Ithaca, NY, USA. https://doi.org/10.2173/bow.becscr1.01.2</td>
      <td>u490b</td>
      <td>Southern Cape York Tropical Scrubwren</td>
      <td>Sericornis beccarii dubius</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Partially implementable</td>
      <td>Though it is prototypical of the Eyre Peninsula, Cinclosoma clarum morgani forms a hybrid swarm with C.c clarum and C. c fordianum to its west, in the case of fordianum all the way to Shark Bay). Thus, Eyre Peninsula is not an appropriate epithet. <br><br>This subspecies is however the easternmost of the ‘Copperback Quail-thrushes’. Epithet allocated for Cinclosoma clarum morgani is henceforth Eastern.<br><br>Range limits not yet resolved.</td>
      <td>u437a</td>
      <td>Eastern Copperback Quail-thrush</td>
      <td>Cinclosoma clarum morgani</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Partially implementable</td>
      <td>Prototypical of the Great Victoria Desert and potentially north (though seemingly only with historical records), Cinclosoma clarum clarum hybridises with C. c. morgani and with C. c.  fordianum to its south. <br><br>With precedent in Ehmke et al. (2017), and reflecting the primarily inland distribution, ‘Inland’ is retained as a subspecies epithet.<br><br>Range limits not yet resolved.</td>
      <td>u437b</td>
      <td>Inland Copperback Quail-thrush</td>
      <td>Cinclosoma clarum clarum</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Partially implementable</td>
      <td>Prototypical of southwestern Australia and the Nullabour Plain, Cinclosoma clarum fordianum forms a hybrid swarm with C. c. clarum to its north and east and C. c morgani to its extreme east (Eyre Peninsula).  <br><br>Neither the westernmost nor clearly the southernmost of the Copperback Quail-thrushes, and with With precedent in Ehmke et al. (2017), the epithet ‘South-western’ is retained for Cinclosoma clarum fordianum.<br><br>Range limits not yet resolved.</td>
      <td>u437c</td>
      <td>South-western Copperback Quail-thrush</td>
      <td>Cinclosoma clarum fordianum</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion of recent split of Brown Whistler (Pachycephala simplex) from Grey-headed Whistler (Pachycephala griseiceps) to previous treatment.</td>
      <td>u8415a</td>
      <td>Queensland Grey-headed Whistler</td>
      <td>Pachycephala simplex peninsulae</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion of recent split of Brown Whistler (Pachycephala simplex) from Grey-headed Whistler (Pachycephala griseiceps) to previous treatment.</td>
      <td>u8415b</td>
      <td>Brown Whistler</td>
      <td>Pachycephala simplex simplex</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>AviList proposes the addition of a subspecies, Pachycephala melanura violetae (around the Kimberley region), but this would also involve a complex revision of other subspecies limits, including hybrid zones for which there appears no specific information. <br><br>AviList (and other authorities) note extreme uncertainty in classification and that the treatment of this species is ‘incomplete and further research on species limits in this complex is warranted’. <br><br>Given the uncertainty in classification and distribution, the existing treatment is retained.</td>
      <td>u400a</td>
      <td>Western Mangrove Golden Whistler</td>
      <td>Pachycephala melanura melanura</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>AviList proposes the addition of a subspecies, Pachycephala melanura violetae (around the Kimberley region), but this would also involve a complex revision of other subspecies limits, including hybrid zones for which there appears no specific information. <br><br>AviList (and other authorities) note extreme uncertainty in classification and that the treatment of this species is ‘incomplete and further research on species limits in this complex is warranted’. <br><br>Given the uncertainty in classification and distribution, the existing treatment is retained.</td>
      <td>u400b</td>
      <td>Eastern Mangrove Golden Whistler</td>
      <td>Pachycephala melanura robusta</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Not implementable</td>
      <td>AviList proposes the addition of a subspecies, Pachycephala melanura violetae (around the Kimberley region), but this would also involve a complex revision of other subspecies limits, including hybrid zones for which there appears no specific information. <br><br>AviList (and other authorities) note extreme uncertainty in classification and that the treatment of this species is ‘incomplete and further research on species limits in this complex is warranted’. <br><br>Given the uncertainty in classification and distribution, the existing treatment is retained.</td>
      <td>u400c</td>
      <td>Papuan Mangrove Golden Whistler</td>
      <td>Pachycephala melanura spinicaudus</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The three southernmost eastern Australia taxa - Capricorn (gouldii), Southern (rufogaster) and Bowen Coast (synaptica) – are lumped and named Southern Little Shrike-thrush(rufogaster).<br><br>Limmen Bight (aelptes) is lumped with North-western (parvula), becoming Western Little Shrike-thrush.<br><br>Hybrid zone ids changed to suit.</td>
      <td>u413b</td>
      <td>Wet Tropics Little Shrike-thrush</td>
      <td>Colluricincla megarhyncha griseata</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The three southernmost eastern Australia taxa - Capricorn (gouldii), Southern (rufogaster) and Bowen Coast (synaptica) – are lumped and named Southern Little Shrike-thrush(rufogaster).<br><br>Limmen Bight (aelptes) is lumped with North-western (parvula), becoming Western Little Shrike-thrush.<br><br>Hybrid zone ids changed to suit.</td>
      <td>u413d</td>
      <td>Cape York Little Shrike-thrush</td>
      <td>Colluricincla megarhyncha normani</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The three southernmost eastern Australia taxa - Capricorn (gouldii), Southern (rufogaster) and Bowen Coast (synaptica) – are lumped and named Southern Little Shrike-thrush(rufogaster).<br><br>Limmen Bight (aelptes) is lumped with North-western (parvula), becoming Western Little Shrike-thrush.<br><br>Hybrid zone ids changed to suit.</td>
      <td>u413e</td>
      <td>Western Little Shrike-thrush</td>
      <td>Colluricincla megarhyncha parvula</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>The three southernmost eastern Australia taxa - Capricorn (gouldii), Southern (rufogaster) and Bowen Coast (synaptica) – are lumped and named Southern Little Shrike-thrush(rufogaster).<br><br>Limmen Bight (aelptes) is lumped with North-western (parvula), becoming Western Little Shrike-thrush.<br><br>Hybrid zone ids changed to suit.</td>
      <td>u413g</td>
      <td>Southern Little Shrike-thrush</td>
      <td>Colluricincla megarhyncha rufogaster</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Coastal New South Wales Australian Magpie (Gymnorhina tibicen tibicen) and Eastern Australian Magpie (Gymnorhina tibicen terraereginae) now lumped as Eastern Australian Magpie (Gymnorhina tibicen tibicen).</td>
      <td>u705f</td>
      <td>Eastern Australian Magpie</td>
      <td>Gymnorhina tibicen tibicen</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Avilist has lumped this but it is trivial in Aust - just a sp sci name change</td>
      <td>u363a</td>
      <td>Papuan Northern Fantail</td>
      <td>Rhipidura rufiventris gularis</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Avilist has lumped this but it is trivial in Aust - just a sp sci name change</td>
      <td>u363b</td>
      <td>Australian Northern Fantail</td>
      <td>Rhipidura rufiventris isura</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Wet Tropics subspecies (melanorrhous) lumped with Southern (gouldii). Abrupt range boundary with Cape York subspecies (albiventris) now with the combined Southern subspecies.</td>
      <td>u375a</td>
      <td>Cape York Spectacled Monarch</td>
      <td>Symposiachrus trivirgatus albiventris</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Wet Tropics subspecies (melanorrhous) lumped with Southern (gouldii). Abrupt range boundary with Cape York subspecies (albiventris) now with the combined Southern subspecies.</td>
      <td>u375b</td>
      <td>Southern Spectacled Monarch</td>
      <td>Symposiachrus trivirgatus gouldii</td>
      <td>Endemic (breeding only)</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Previously split from as a distinct species from Western Lemon-bellied Flycatcher (Microeca flavigaster tormenti) to Kimberely Flycatcher (Microeca tormenti), now reverted to previous treatment. Common name Kimberely Flycatcher retained for brevity.</td>
      <td>u379d</td>
      <td>Kimberley Lemon-bellied Flycatcher</td>
      <td>Microeca flavigaster tormenti</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion of a recently proposed subspecies split of Kimberley population as a distinct subspecies (Acrocephalus australis carterae) to previous treatment.</td>
      <td>u524a</td>
      <td>Eastern Australian Reed-Warbler</td>
      <td>Acrocephalus australis australis</td>
      <td>Endemic (breeding only)</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion of a recently proposed subspecies split of Kimberley population as a distinct subspecies (Acrocephalus australis carterae) to previous treatment.</td>
      <td>u524b</td>
      <td>Western Australian Reed-Warbler</td>
      <td>Acrocephalus australis gouldi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Formerly a subspecies of Island Thrush, along with the extinct Lord Howe Thrush (Turdus poliocephalus poliocephalus) and Norfolk Island Thrush (Turdus poliocephalus vinitinctus), now a monotypic species. Subspecies name from Ehmke et al. (2017).</td>
      <td>u5154</td>
      <td>Christmas Island Thrush</td>
      <td>Turdus erythropleurus</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>AviList call this 'Sahul Sunbird' based on a global split. I have changed the sci name but retained the common name in like with local nomenclature</td>
      <td>u572</td>
      <td>Australian Olive-backed Sunbird</td>
      <td>Cinnyris frenatus frenatus</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Reversion to previous treatment. Species lumped after being split previously.</td>
      <td>u665b</td>
      <td>White-bellied Crimson Finch</td>
      <td>Neochmia phaeton evangelinae</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Subspecies macgillivrayi is limited to the Australian Wet Tropics, whereas it was formerly thought to extend through to New Guinea. Subspecies sigillifer now the New Guinea subspecies with a range noted as extending through to NE Queensland. Only two historical records on northeastern Cape York from which to assume occurrence. Subspecies may not constitute a core Australian taxon and range is not mapped, given the paucity of data, but is listed as Torresian Blue-faced Parrot-Finch with precedent from Ehmke et al. (2017). <br><br>Payne, R. B. (2020). Blue-faced Parrotfinch (Erythrura trichroa), version 1.0. In Birds of the World (J. del Hoyo, A. Elliott, J. Sargatal, D. A. Christie, and E. de Juana, Editors). Cornell Lab of Ornithology, Ithaca, NY, USA. https://doi.org/10.2173/bow.blfpar3.01</td>
      <td>u660a</td>
      <td>Torresian Blue-faced Parrot-Finch</td>
      <td>Erythrura trichroa sigillifer</td>
      <td>Australian</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>Revised subspecies distribution of the core Australian subspecies. Now monikered Wet Tropics, reflecting its endemism to that region.</td>
      <td>u660b</td>
      <td>Wet Tropics Blue-faced Parrot-Finch</td>
      <td>Erythrura trichroa macgillivrayi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>AviList have split the Australian and New Zealand taxa as species, but this is a long-debated classification and they note confirmation is required. There are no practical implications arising from the change other than a change of the common name from Australasian to Australian which is implemented here (noting a revision is not unlikely).</td>
      <td>u647a</td>
      <td>Central Australian Pipit</td>
      <td>Anthus australis australis</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>AviList have split the Australian and New Zealand taxa as species, but this is a long-debated classification and they note confirmation is required. There are no practical implications arising from the change other than a change of the common name from Australasian to Australian which is implemented here (noting a revision is not unlikely).</td>
      <td>u647b</td>
      <td>South-western Australian Pipit</td>
      <td>Anthus australis bilbali</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>AviList have split the Australian and New Zealand taxa as species, but this is a long-debated classification and they note confirmation is required. There are no practical implications arising from the change other than a change of the common name from Australasian to Australian which is implemented here (noting a revision is not unlikely).</td>
      <td>u647c</td>
      <td>Tasmanian Australian Pipit</td>
      <td>Anthus australis bistriatus</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
    <tr>
      <td>Implementable</td>
      <td>AviList have split the Australian and New Zealand taxa as species, but this is a long-debated classification and they note confirmation is required. There are no practical implications arising from the change other than a change of the common name from Australasian to Australian which is implemented here (noting a revision is not unlikely).</td>
      <td>u647d</td>
      <td>Northern Australian Pipit</td>
      <td>Anthus australis rogersi</td>
      <td>Endemic</td>
      <td>Least Concern</td>
    </tr>
  </tbody>
</table>



```python

```
