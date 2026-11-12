# E53 phase-1 screen: schema coverage and phase-2 sizes (PARTIAL: screen still running)

Screened sites n = 1,011 of S1 (n1 = 20,000); N0 = 3,901,721; population estimate = count x N0 / n = count x 3,859.3.
Classes from the fixed E50 configs: POI v3 retrieve k30 (gemma r-short, qwen r-low), WZ retrieve k30 c1500, address mode main (f-schema). Union = either model (address cases: or the text detector). Prediction errors (counted as no class): none.

## 1. Classes per depth

| depth | classes | union >=1 | >=5 | >=10 | >=25 | gemma >=1 / >=10 / >=25 | qwen >=1 / >=10 / >=25 |
|---|---:|---:|---:|---:|---:|---:|---:|
| POI L1 | 8 | 8 | 8 | 8 | 8 | 8 / 8 / 8 | 8 / 8 / 8 |
| POI L2 | 357 | 165 | 59 | 29 | 6 | 149 / 24 / 5 | 153 / 23 / 5 |
| WZ section | 22 | 21 | 18 | 16 | 12 | 19 / 16 / 12 | 20 / 16 / 12 |
| WZ division | 87 | 73 | 42 | 31 | 15 | 69 / 29 / 13 | 68 / 28 / 12 |
| WZ group | 287 | 174 | 60 | 31 | 12 | 161 / 27 / 10 | 153 / 29 / 9 |
| address cases | 7 | 7 | 7 | 7 | 5 | 7 / 7 / 5 | 7 / 7 / 5 |

Per-class counts for all depths: `datasets/E53/screen/coverage_classes.tsv` (columns group, class, title, union, gemma, qwen, population estimate).

### POI L1

| class | title | union | gemma | qwen | population est. |
|---|---|---:|---:|---:|---:|
| poi1:business-and-professional-services | Business and Professional Services | 482 | 453 | 462 | 1,860,168 |
| poi1:community-and-government | Community and Government | 165 | 160 | 152 | 636,779 |
| poi1:retail | Retail | 114 | 106 | 95 | 439,957 |
| poi1:health-and-medicine | Health and Medicine | 90 | 85 | 83 | 347,334 |
| poi1:sports-recreation-and-outdoors | Sports, Recreation and Outdoors | 49 | 45 | 44 | 189,104 |
| poi1:arts-entertainment-and-events | Arts, Entertainment and Events | 48 | 39 | 40 | 185,245 |
| poi1:travel-and-transportation | Travel and Transportation | 45 | 45 | 42 | 173,667 |
| poi1:dining-and-drinking | Dining and Drinking | 40 | 38 | 40 | 154,371 |

### WZ section

| class | title | union | gemma | qwen | population est. |
|---|---|---:|---:|---:|---:|
| wz1:N | Erbringung von wissenschaftlichen und technischen Dienstleistungen | 122 | 116 | 116 | 470,831 |
| wz1:T | Erbringung von sonstigen Dienstleistungen | 118 | 102 | 110 | 455,394 |
| wz1:G | Handel | 111 | 100 | 103 | 428,379 |
| wz1:S | Kunst, Sport und Erholung | 107 | 98 | 94 | 412,942 |
| wz1:R | Gesundheits- und Sozialwesen | 101 | 99 | 93 | 389,786 |
| wz1:C | Verarbeitendes Gewerbe | 84 | 82 | 65 | 324,179 |
| wz1:K | Telekommunikation, Softwareentwicklung, IT-Beratung und Erbringung sonstiger Dienstleistungen der Informationstechnologie und der Computerinfrastruktur | 80 | 72 | 72 | 308,742 |
| wz1:I | Gastgewerbe | 63 | 59 | 62 | 243,134 |
| wz1:Q | Erziehung und Unterricht | 57 | 52 | 56 | 219,978 |
| wz1:F | Baugewerbe | 56 | 56 | 49 | 216,119 |
| wz1:J | Verlagswesen, Rundfunk sowie Erstellung und Verbreitung von Medieninhalten | 51 | 47 | 42 | 196,823 |
| wz1:O | Erbringung von sonstigen wirtschaftlichen Dienstleistungen | 38 | 37 | 34 | 146,652 |
| wz1:P | Öffentliche Verwaltung, Verteidigung; Sozialversicherung | 17 | 17 | 16 | 65,608 |
| wz1:M | Grundstücks- und Wohnungswesen | 16 | 16 | 13 | 61,748 |
| wz1:A | Land- und Forstwirtschaft, Fischerei | 15 | 13 | 14 | 57,889 |
| wz1:H | Verkehr und Lagerei | 14 | 12 | 13 | 54,030 |
| wz1:L | Erbringung von Finanz- und Versicherungsdienstleistungen | 9 | 8 | 8 | 34,733 |
| wz1:E | Abwasser- und Abfallentsorgung und Beseitigung von Umweltverschmutzungen | 6 | 5 | 5 | 23,156 |
| wz1:U | Private Haushalte mit Haushaltspersonal sowie Herstellung von Waren und Erbringung von Dienstleistungen durch private Haushalte für den Eigenbedarf ohne ausgeprägten Schwerpunkt | 2 | 2 | 0 | 7,719 |
| wz1:B | Bergbau und Gewinnung von Steinen und Erden | 1 | 0 | 1 | 3,859 |
| wz1:D | Energieversorgung | 1 | 0 | 1 | 3,859 |
| wz1:V | Exterritoriale Organisationen und Körperschaften | 0 | 0 | 0 | 0 |

### address cases

| class | title | union | gemma | qwen | population est. |
|---|---|---:|---:|---:|---:|
| addr:multi |  | 204 | 204 | 204 | 787,291 |
| addr:at |  | 88 | 88 | 87 | 339,616 |
| lang:non_de |  | 71 | 71 | 71 | 274,008 |
| addr:ch |  | 55 | 55 | 55 | 212,260 |
| addr:none |  | 55 | 55 | 55 | 212,260 |
| addr:non_dach |  | 19 | 18 | 17 | 73,326 |
| addr:po_box |  | 17 | 17 | 16 | 65,608 |

### POI L2: classes by union count in S1

| members in S1 | 0-0 | 1-4 | 5-9 | 10-24 | 25-99 | >=100 |
|---|---:|---:|---:|---:|---:|---:|
| classes | 192 | 106 | 30 | 23 | 6 | 0 |

### WZ division: classes by union count in S1

| members in S1 | 0-0 | 1-4 | 5-9 | 10-24 | 25-99 | >=100 |
|---|---:|---:|---:|---:|---:|---:|
| classes | 14 | 31 | 11 | 16 | 15 | 0 |

### WZ group: classes by union count in S1

| members in S1 | 0-0 | 1-4 | 5-9 | 10-24 | 25-99 | >=100 |
|---|---:|---:|---:|---:|---:|---:|
| classes | 113 | 114 | 29 | 19 | 12 | 0 |

## 2. Phase-2 size per target

Core 600 (first 600 of a seeded permutation of the screened sites, seed 20261113) + rarest-first oversample with union memberships (`src/ic/gold/sampling.py` `_fill`, no budget). A class is **short in S1** if it has fewer than T union members in the screen; then all its members are drawn. 'n1 to fill' = size of S1 at which the rarest short class with >= 1 member would have T members (T x n / count); classes with 0 members need more than T x n / 3 (rule of three, 95%).

| target | items (core + extra) | target classes | short in S1 (0 members) | still short in sample | n1 to fill all short classes with >= 1 member |
|---|---:|---:|---:|---:|---:|
| (a) top level T=25 (POI L1, WZ sections, address cases) | 649 (600 + 49) | 37 | 12 (1) | 12 | 25,275 |
| (b) (a) + WZ divisions T=10 | 694 (600 + 94) | 124 | 68 (15) | 68 | 25,275 |
| (c) (b) + POI L2 T=5 | 752 (600 + 152) | 481 | 366 (207) | 367 | 25,275 |
| (d) (b) + POI L2 T=10 | 822 (600 + 222) | 481 | 396 (207) | 396 | 25,275 |
| (e) (a) + WZ divisions T=5 + POI L2 T=5 | 738 (600 + 138) | 481 | 355 (207) | 355 | 25,275 |
| (f) (d) + WZ groups T=5 | 825 (600 + 225) | 768 | 623 (320) | 628 | 25,275 |
| (g) top level T=10 + WZ divisions T=10 + POI L2 T=10 | 811 (600 + 211) | 481 | 390 (207) | 390 | 10,110 |

- (a) top level T=25 (POI L1, WZ sections, address cases): short in S1 by depth: WZ section 10, address cases 2. Short top-level/address classes: wz1:A (15), wz1:B (1), wz1:D (1), wz1:E (6), wz1:H (14), wz1:L (9), wz1:M (16), wz1:P (17), wz1:U (2), wz1:V (0), addr:po_box (17), addr:non_dach (19).
- (b) (a) + WZ divisions T=10: short in S1 by depth: WZ section 10, address cases 2, WZ division 56. Short top-level/address classes: wz1:A (15), wz1:B (1), wz1:D (1), wz1:E (6), wz1:H (14), wz1:L (9), wz1:M (16), wz1:P (17), wz1:U (2), wz1:V (0), addr:po_box (17), addr:non_dach (19).
- (c) (b) + POI L2 T=5: short in S1 by depth: WZ section 10, address cases 2, WZ division 56, POI L2 298. Short top-level/address classes: wz1:A (15), wz1:B (1), wz1:D (1), wz1:E (6), wz1:H (14), wz1:L (9), wz1:M (16), wz1:P (17), wz1:U (2), wz1:V (0), addr:po_box (17), addr:non_dach (19).
- (d) (b) + POI L2 T=10: short in S1 by depth: WZ section 10, address cases 2, WZ division 56, POI L2 328. Short top-level/address classes: wz1:A (15), wz1:B (1), wz1:D (1), wz1:E (6), wz1:H (14), wz1:L (9), wz1:M (16), wz1:P (17), wz1:U (2), wz1:V (0), addr:po_box (17), addr:non_dach (19).
- (e) (a) + WZ divisions T=5 + POI L2 T=5: short in S1 by depth: WZ section 10, address cases 2, WZ division 45, POI L2 298. Short top-level/address classes: wz1:A (15), wz1:B (1), wz1:D (1), wz1:E (6), wz1:H (14), wz1:L (9), wz1:M (16), wz1:P (17), wz1:U (2), wz1:V (0), addr:po_box (17), addr:non_dach (19).
- (f) (d) + WZ groups T=5: short in S1 by depth: WZ section 10, address cases 2, WZ division 56, POI L2 328, WZ group 227. Short top-level/address classes: wz1:A (15), wz1:B (1), wz1:D (1), wz1:E (6), wz1:H (14), wz1:L (9), wz1:M (16), wz1:P (17), wz1:U (2), wz1:V (0), addr:po_box (17), addr:non_dach (19).
- (g) top level T=10 + WZ divisions T=10 + POI L2 T=10: short in S1 by depth: WZ section 6, WZ division 56, POI L2 328. Short top-level/address classes: wz1:B (1), wz1:D (1), wz1:E (6), wz1:L (9), wz1:U (2), wz1:V (0).

### Projection to the full S1 (n1 = 20,000)

Bootstrap: 20,000 draws with replacement from the 1,011 screened sites, same procedure. Classes with 0 members in the screen stay at 0, and rare classes are noisy; a rough guide until the screen ends.

| target | projected items (core + extra) | projected short in S1 | projected still short in sample |
|---|---:|---:|---:|
| (a) top level T=25 (POI L1, WZ sections, address cases) | 783 (600 + 183) | 3 | 3 |
| (b) (a) + WZ divisions T=10 | 1,002 (600 + 402) | 17 | 18 |
| (c) (b) + POI L2 T=5 | 1,281 (600 + 681) | 209 | 216 |
| (d) (b) + POI L2 T=10 | 1,823 (600 + 1,223) | 209 | 209 |
| (e) (a) + WZ divisions T=5 + POI L2 T=5 | 1,189 (600 + 589) | 209 | 211 |
| (f) (d) + WZ groups T=5 | 1,929 (600 + 1,329) | 322 | 326 |
| (g) top level T=10 + WZ divisions T=10 + POI L2 T=10 | 1,771 (600 + 1,171) | 207 | 207 |

## 3. S1 size needed per depth (union counts)

Smallest n1 at which every class with >= 1 member in the screen reaches T (T x n / min count), and number of classes with 0 members in the screen.

| depth | 0 members | T=5 | T=10 | T=25 |
|---|---:|---:|---:|---:|
| POI L1 | 0 | 127 | 253 | 632 |
| POI L2 | 192 | 5,055 | 10,110 | 25,275 |
| WZ section | 1 | 5,055 | 10,110 | 25,275 |
| WZ division | 14 | 5,055 | 10,110 | 25,275 |
| WZ group | 113 | 5,055 | 10,110 | 25,275 |
| address cases | 0 | 298 | 595 | 1,487 |
