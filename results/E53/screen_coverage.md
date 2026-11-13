# E53 phase-1 screen: schema coverage and phase-2 sizes

Screened sites n = 19,998 of S1 (n1 = 20,000); N0 = 3,901,721; population estimate = count x N0 / n = count x 195.1.
Classes from the fixed E50 configs: POI v3 retrieve k30 (gemma r-short, qwen r-low), WZ retrieve k30 c1500, address mode main (f-schema). Union = either model (address cases: or the text detector). Prediction errors (counted as no class): none.

## 1. Classes per depth

| depth | classes | union >=1 | >=5 | >=10 | >=25 | gemma >=1 / >=10 / >=25 | qwen >=1 / >=10 / >=25 |
|---|---:|---:|---:|---:|---:|---:|---:|
| POI L1 | 8 | 8 | 8 | 8 | 8 | 8 / 8 / 8 | 8 / 8 / 8 |
| POI L2 | 357 | 300 | 225 | 184 | 125 | 294 / 165 / 111 | 286 / 164 / 115 |
| WZ section | 22 | 22 | 21 | 20 | 20 | 22 / 20 / 20 | 22 / 20 / 20 |
| WZ division | 87 | 84 | 78 | 75 | 64 | 83 / 73 / 63 | 84 / 72 / 60 |
| WZ group | 287 | 264 | 217 | 188 | 133 | 262 / 178 / 123 | 259 / 173 / 118 |
| address cases | 7 | 7 | 7 | 7 | 7 | 7 / 7 / 7 | 7 / 7 / 7 |

Per-class counts for all depths: `datasets/E53/screen/coverage_classes.tsv` (columns group, class, title, union, gemma, qwen, population estimate).

### POI L1

| class | title | union | gemma | qwen | population est. |
|---|---|---:|---:|---:|---:|
| poi1:business-and-professional-services | Business and Professional Services | 9387 | 8813 | 8941 | 1,831,456 |
| poi1:community-and-government | Community and Government | 3454 | 3286 | 3112 | 673,895 |
| poi1:retail | Retail | 2140 | 2039 | 1856 | 417,526 |
| poi1:health-and-medicine | Health and Medicine | 1683 | 1620 | 1556 | 328,363 |
| poi1:arts-entertainment-and-events | Arts, Entertainment and Events | 1169 | 949 | 1025 | 228,078 |
| poi1:sports-recreation-and-outdoors | Sports, Recreation and Outdoors | 1102 | 983 | 1016 | 215,006 |
| poi1:travel-and-transportation | Travel and Transportation | 1068 | 1024 | 1009 | 208,373 |
| poi1:dining-and-drinking | Dining and Drinking | 561 | 540 | 553 | 109,454 |

### WZ section

| class | title | union | gemma | qwen | population est. |
|---|---|---:|---:|---:|---:|
| wz1:N | Erbringung von wissenschaftlichen und technischen Dienstleistungen | 2445 | 2305 | 2289 | 477,033 |
| wz1:T | Erbringung von sonstigen Dienstleistungen | 2277 | 1975 | 2098 | 444,255 |
| wz1:S | Kunst, Sport und Erholung | 2200 | 2033 | 1995 | 429,232 |
| wz1:G | Handel | 2061 | 1879 | 1914 | 402,113 |
| wz1:R | Gesundheits- und Sozialwesen | 1927 | 1861 | 1747 | 375,968 |
| wz1:K | Telekommunikation, Softwareentwicklung, IT-Beratung und Erbringung sonstiger Dienstleistungen der Informationstechnologie und der Computerinfrastruktur | 1548 | 1325 | 1342 | 302,023 |
| wz1:C | Verarbeitendes Gewerbe | 1415 | 1325 | 1182 | 276,074 |
| wz1:Q | Erziehung und Unterricht | 1388 | 1207 | 1308 | 270,807 |
| wz1:I | Gastgewerbe | 1255 | 1214 | 1233 | 244,857 |
| wz1:J | Verlagswesen, Rundfunk sowie Erstellung und Verbreitung von Medieninhalten | 1232 | 1135 | 943 | 240,370 |
| wz1:F | Baugewerbe | 1013 | 978 | 916 | 197,642 |
| wz1:O | Erbringung von sonstigen wirtschaftlichen Dienstleistungen | 984 | 913 | 841 | 191,984 |
| wz1:M | Grundstücks- und Wohnungswesen | 362 | 349 | 334 | 70,628 |
| wz1:A | Land- und Forstwirtschaft, Fischerei | 322 | 285 | 293 | 62,824 |
| wz1:L | Erbringung von Finanz- und Versicherungsdienstleistungen | 317 | 304 | 284 | 61,848 |
| wz1:P | Öffentliche Verwaltung, Verteidigung; Sozialversicherung | 316 | 303 | 289 | 61,653 |
| wz1:H | Verkehr und Lagerei | 258 | 246 | 236 | 50,337 |
| wz1:E | Abwasser- und Abfallentsorgung und Beseitigung von Umweltverschmutzungen | 92 | 86 | 73 | 17,950 |
| wz1:D | Energieversorgung | 66 | 59 | 58 | 12,877 |
| wz1:U | Private Haushalte mit Haushaltspersonal sowie Herstellung von Waren und Erbringung von Dienstleistungen durch private Haushalte für den Eigenbedarf ohne ausgeprägten Schwerpunkt | 38 | 27 | 26 | 7,414 |
| wz1:B | Bergbau und Gewinnung von Steinen und Erden | 6 | 5 | 6 | 1,171 |
| wz1:V | Exterritoriale Organisationen und Körperschaften | 2 | 1 | 1 | 390 |

### address cases

| class | title | union | gemma | qwen | population est. |
|---|---|---:|---:|---:|---:|
| addr:multi |  | 4392 | 4392 | 4392 | 856,904 |
| lang:non_de |  | 1685 | 1685 | 1685 | 328,753 |
| addr:at |  | 1613 | 1612 | 1604 | 314,705 |
| addr:ch |  | 1228 | 1226 | 1225 | 239,590 |
| addr:none |  | 1193 | 1193 | 1193 | 232,761 |
| addr:non_dach |  | 448 | 434 | 413 | 87,407 |
| addr:po_box |  | 391 | 391 | 382 | 76,286 |

### POI L2: classes by union count in S1

| members in S1 | 0-0 | 1-4 | 5-9 | 10-24 | 25-99 | >=100 |
|---|---:|---:|---:|---:|---:|---:|
| classes | 57 | 75 | 41 | 59 | 76 | 49 |

### WZ division: classes by union count in S1

| members in S1 | 0-0 | 1-4 | 5-9 | 10-24 | 25-99 | >=100 |
|---|---:|---:|---:|---:|---:|---:|
| classes | 3 | 6 | 3 | 11 | 24 | 40 |

### WZ group: classes by union count in S1

| members in S1 | 0-0 | 1-4 | 5-9 | 10-24 | 25-99 | >=100 |
|---|---:|---:|---:|---:|---:|---:|
| classes | 23 | 47 | 29 | 55 | 81 | 52 |

## 2. Phase-2 size per target

Core 600 (first 600 of a seeded permutation of the screened sites, seed 20261113) + rarest-first oversample with union memberships (`src/ic/gold/sampling.py` `_fill`, no budget). A class is **short in S1** if it has fewer than T union members in the screen; then all its members are drawn. 'n1 to fill' = size of S1 at which the rarest short class with >= 1 member would have T members (T x n / count); classes with 0 members need more than T x n / 3 (rule of three, 95%).

| target | items (core + extra) | target classes | short in S1 (0 members) | still short in sample | n1 to fill all short classes with >= 1 member |
|---|---:|---:|---:|---:|---:|
| (a) top level T=25 (POI L1, WZ sections, address cases) | 769 (600 + 169) | 37 | 2 (0) | 2 | 249,975 |
| (b) (a) + WZ divisions T=10 | 1,036 (600 + 436) | 124 | 14 (3) | 15 | 249,975 |
| (c) (b) + POI L2 T=5 | 1,585 (600 + 985) | 481 | 146 (60) | 148 | 249,975 |
| (d) (b) + POI L2 T=10 | 2,233 (600 + 1,633) | 481 | 187 (60) | 188 | 249,975 |
| (e) (a) + WZ divisions T=5 + POI L2 T=5 | 1,468 (600 + 868) | 481 | 143 (60) | 147 | 249,975 |
| (f) (d) + WZ groups T=5 | 2,433 (600 + 1,833) | 768 | 257 (83) | 267 | 249,975 |
| (h) (a) + POI L2 T=5 + WZ groups T=5 (evaluation depths) | 1,795 (600 + 1,195) | 681 | 204 (80) | 206 | 249,975 |
| (i) (a) + POI L2 T=3 + WZ groups T=3 (evaluation depths, light) | 1,327 (600 + 727) | 681 | 155 (80) | 158 | 249,975 |
| (g) top level T=10 + WZ divisions T=10 + POI L2 T=10 | 2,231 (600 + 1,631) | 481 | 187 (60) | 187 | 199,980 |

- (a) top level T=25 (POI L1, WZ sections, address cases): short in S1 by depth: WZ section 2. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (b) (a) + WZ divisions T=10: short in S1 by depth: WZ section 2, WZ division 12. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (c) (b) + POI L2 T=5: short in S1 by depth: WZ section 2, WZ division 12, POI L2 132. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (d) (b) + POI L2 T=10: short in S1 by depth: WZ section 2, WZ division 12, POI L2 173. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (e) (a) + WZ divisions T=5 + POI L2 T=5: short in S1 by depth: WZ section 2, WZ division 9, POI L2 132. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (f) (d) + WZ groups T=5: short in S1 by depth: WZ section 2, WZ division 12, POI L2 173, WZ group 70. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (h) (a) + POI L2 T=5 + WZ groups T=5 (evaluation depths): short in S1 by depth: WZ section 2, POI L2 132, WZ group 70. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (i) (a) + POI L2 T=3 + WZ groups T=3 (evaluation depths, light): short in S1 by depth: WZ section 2, POI L2 102, WZ group 51. Short top-level/address classes: wz1:B (6), wz1:V (2).
- (g) top level T=10 + WZ divisions T=10 + POI L2 T=10: short in S1 by depth: WZ section 2, WZ division 12, POI L2 173. Short top-level/address classes: wz1:B (6), wz1:V (2).

### Projection to the full S1 (n1 = 20,000)

Bootstrap: 20,000 draws with replacement from the 19,998 screened sites, same procedure. Classes with 0 members in the screen stay at 0, and rare classes are noisy; a rough guide until the screen ends.

| target | projected items (core + extra) | projected short in S1 | projected still short in sample |
|---|---:|---:|---:|
| (a) top level T=25 (POI L1, WZ sections, address cases) | 791 (600 + 191) | 2 | 2 |
| (b) (a) + WZ divisions T=10 | 1,055 (600 + 455) | 16 | 17 |
| (c) (b) + POI L2 T=5 | 1,579 (600 + 979) | 149 | 152 |
| (d) (b) + POI L2 T=10 | 2,195 (600 + 1,595) | 186 | 187 |
| (e) (a) + WZ divisions T=5 + POI L2 T=5 | 1,449 (600 + 849) | 143 | 146 |
| (f) (d) + WZ groups T=5 | 2,392 (600 + 1,792) | 259 | 265 |
| (h) (a) + POI L2 T=5 + WZ groups T=5 (evaluation depths) | 1,756 (600 + 1,156) | 208 | 210 |
| (i) (a) + POI L2 T=3 + WZ groups T=3 (evaluation depths, light) | 1,300 (600 + 700) | 170 | 175 |
| (g) top level T=10 + WZ divisions T=10 + POI L2 T=10 | 2,178 (600 + 1,578) | 186 | 186 |

## 3. S1 size needed per depth (union counts)

Smallest n1 at which every class with >= 1 member in the screen reaches T (T x n / min count), and number of classes with 0 members in the screen.

| depth | 0 members | T=5 | T=10 | T=25 |
|---|---:|---:|---:|---:|
| POI L1 | 0 | 179 | 357 | 892 |
| POI L2 | 57 | 99,990 | 199,980 | 499,950 |
| WZ section | 0 | 49,995 | 99,990 | 249,975 |
| WZ division | 3 | 99,990 | 199,980 | 499,950 |
| WZ group | 23 | 99,990 | 199,980 | 499,950 |
| address cases | 0 | 256 | 512 | 1,279 |
