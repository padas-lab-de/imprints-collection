# poi_v3: English POI schema linked to Foursquare (E49)

Date 2026-11-10. Input: `topics/poi_v2.jsonl` (779 German nodes, unchanged). Output: `topics/poi_v3.jsonl` (753 English nodes).
Build: `python3 -I scripts/E49/poi_v3_build.py <fsq.csv> <align.tsv> topics/poi_v2.jsonl results/E49/refs/poi.jsonl`
(the draft alignment comes from `scripts/E49/poi_v3_align.py`). Check: `python3 -I scripts/E49/check_poi_schema.py topics/poi_v3.jsonl` reports OK.

Format of `topics/poi_v3.jsonl`, one line per node:
`{"id": kebab-case slug of the name, "name": English name, "parent": parent id (root: own id), "fsq_ids": [FSQ category ids], "de": v2 German name, or a list if v2 nodes were merged (null for an added node)}`.
The lines are in tree order (root, then each child followed by its own children).

## 1. Source and licence

- Taxonomy: Foursquare OS Places categories, 1279 categories, levels 1 to 6 (1: 11, 2: 457, 3: 474, 4: 241, 5: 82, 6: 14).
- Page: https://docs.foursquare.com/data-products/docs/categories (page `updatedAt` 2026-09-16T23:01:10Z). The page embeds the Observable notebook
  https://observablehq.com/embed/da51c7e6d46cd01e ("Places OS, Pro & Premium Categories"). Its file attachment `fsq-places-os-categories.csv`
  (columns category_id, category_name, category_label) was used. It was downloaded on 2026-11-10, and its sha256 is
  `1e805f6164ba7d70f8f1f22773e0a5a5edf492bf91245283aa2953add2cbcffa`. The local copy is at `datasets/E49/fsq_raw/` (not in git).
- Licence: FSQ OS Places is released under Apache-2.0 (Hugging Face dataset `foursquare/fsq-os-places`; latest release there dt=2026-10-15).
  The HF dataset is gated, so it was not downloaded. The category list is the one that the docs page publishes.
- The only duplicate FSQ name is "Restaurant". All lookups use the full label path.

## 2. Link v2 -> FSQ (`results/E49/poi_v2_to_fsq.csv`)

The German original `topics/categories.jsonl` (796 rows) is a translated subset of FSQ, in FSQ order. A monotone alignment (trigram similarity
plus a depth bonus, `poi_v3_align.py`) gave a draft. All 779 pairs were reviewed by hand, and 41 lines were corrected (the `OVERRIDE_LINE` table
in the build script; most are places where the German order differs from the FSQ order). The cleanup renames and the 3 duplicate lines of the
first pass are resolved through the original names.

- exact: 762, approx: 17, none: 0. Every v2 node comes from an FSQ category, so no node is project-specific.
- 7 nodes are relinked to a better FSQ category. The note column gives the original link:
  - Fußballverein: Football (American football) -> Soccer Club. This was a translation error.
  - Volkshochschule: Community College -> Adult Education. This was a translation error.
  - Kneipe: Dive Bar -> Pub.
  - Baseballverein, Basketballverein, Golfclub: sport -> Club.
  - Eishockeystadion: Hockey -> Hockey Rink.
- approx (with reason in the CSV):
  - Translation errors: Südländisches Food-Restaurant (US Southern food), Herausgeber (should be Verlag) and Apfelwein (the drink vs. a cidery).
  - Meaning differs: Agentur für Arbeit (federal agency vs. any job agency), Entsorgung (Dump), Marktplatz (place vs. event), Brettladen, Hütte,
    Kindergarten, Handelsschule, Notfallzentrum, Eisstockschießen, Leichtathletikverein, Eishockeystadion and Attraktion.
  - The two v2 roots that hold extra FSQ top levels: Kunst und Unterhaltung and Sport und Freizeit.
- Hand check: the draft alignment was reviewed, and the full v3 tree (name, `de`, FSQ path) was read after the overrides. No wrong link was
  found, but a second reader should spot-check the 41 override lines. Checks of renamed and duplicate nodes: Holzeinschlagsunternehmen -> Logging Service; Koffergeschäft -> Luggage Store; Karaoke-Bar -> Bar >
  Karaoke Bar; Rettungsdienst -> Emergency Service > Ambulance Service; Rathaus -> Government Building > City Hall.

## 3. Counts

| | v2 | v3 |
|---|---|---|
| nodes | 779 | 753 (-27 merged, +1 added) |
| roots | 8 | 8 |
| inner non-root nodes | 5 | 45 |
| depth 0 / 1 / 2 | 8 / 689 / 82 | 8 / 357 / 388 |
| leaves | 766 | 700 |

Leaves per root in v3: Arts, Entertainment and Events 47; Business and Professional Services 160; Community and Government 86; Dining and Drinking 100;
Health and Medicine 51; Retail 132; Sports, Recreation and Outdoors 80; Travel and Transportation 44.

## 4. Changes

### 4.1 Roots (8 kept; 2 renamed)
- Kunst und Unterhaltung -> **Arts, Entertainment and Events** (fsq_ids: Arts and Entertainment + Event). The v2 move of the FSQ Event classes
  is kept, and the name now says it.
- Sport und Freizeit -> **Sports, Recreation and Outdoors** (fsq_ids: Sports and Recreation + Landmarks and Outdoors). The v2 move of the
  59 Landmarks and Outdoors classes is kept, and the name now says it. This answers the D50 item "natural features (Baum, Vulkan, Fluss, Brücke,
  Tunnel) under Sport und Freizeit". They stay, because a 9th root for a few hundred outdoor websites would not help.
- The other 6 roots take the FSQ top-level names. Nightlife Spot stays a single node under Arts, Entertainment and Events (as in v2).

### 4.2 General and specific classes: 45 groups (depth 2 restored)
After the flattening, v2 had general and specific classes as siblings (Restaurant / Italienisches Restaurant, Arzt / Kardiologe, Bar / Cocktailbar).
In v3, each such general class is a group (depth 1) again, and its FSQ descendants are its children (depth 2). Deeper FSQ levels are attached to
the group, so the maximum depth stays 2 (for example, Chinese Restaurant is under Restaurant, next to Asian Restaurant). A node goes under a
group only when the group is in the same root. The 5 v2 inner nodes stay groups.

Groups (children): Movie Theater (1); Museum (3); Performing Arts Venue (6); Entertainment Event (5); Market or Fair Event (4); Event Space (5);
Automotive Service (5); Financial Service (14); Food and Beverage Service (2); Health and Beauty Service (10); Home Improvement Service (26);
Legal Service (3); Manufacturer or Factory (1); Office (7); Pet Service (2); Photography Service (3); Real Estate Service (5); Technology Business (3);
Education (29); Government Building (7); Law Enforcement and Public Safety (3); Organization (9); Spiritual Center (14); Bar (19);
Cafe, Coffee and Tea House (3); Dessert Shop (7); Restaurant (54); Emergency Service (2); Hospital (2); Mental Health Service (2); Physician (22);
Automotive Retail (10); Bookstore (1); Computers and Electronics Retail (4); Fashion Retail (13); Food and Beverage Retail (22);
Furniture and Home Store (6); Sporting Goods Retail (14); Park (6); Gym and Fitness Studio (3); Sports Club (7); Lodging (8);
Tourist Information and Service (1); Transport Hub (10); Transportation Service (5).

Law Enforcement and Public Safety stays a group directly under the root, not under Government Building (that would be depth 3).
Attraction stays at root level; it is not put under Amusement Park (in German, Attraktion means any tourist attraction).

### 4.3 Merges (27 v2 nodes into 23 kept nodes)
| Merged (v2) | Into (v3 id) | Reason |
|---|---|---|
| Kindertagesstätte, Vorschule | kindergarten-and-daycare (Kindergarten) | Kita, Kindergarten and Vorschule are one institution type in Germany. Kinderbetreuungsdienst (child-care service: childminders) stays separate. |
| Volkshochschule | adult-education | A VHS is adult education. The FSQ link (Community College) was a translation error. |
| Schwesternschaftshaus | student-fraternity-or-sorority-house | There are no sorority houses in Germany. One node for houses of student associations. |
| Militärbasis | military-facility | Military and Military Base have the same websites. |
| Wohnung oder Eigentumswohnung | residential-building | These cannot be told apart from a website. |
| Clubhaus | club-or-association | A club house is the club's building. One node for clubs and Vereine. |
| Firmenannehmlichkeit, Firmencafé | company-canteen-or-amenity | US office amenity classes. |
| Fabrik | manufacturer-or-factory | Synonym of Hersteller (D50). |
| Lager | warehouse-or-storage-facility | Synonym of Lagereinrichtung (D50). |
| Forschungslabor | laboratory | Synonym of Labor (D50). Medical Lab and College Lab stay separate. |
| Mobilfunkunternehmen | telecommunication-service | Mobile operators are telecommunication services. |
| Immobilienentwicklungs- und Titelunternehmen | real-estate-developer | Title companies are US-specific. Same as Gewerbeimmobilienentwickler. |
| Café | cafe-coffee-and-tea-house | Same meaning as its parent. |
| Notfallzentrum | emergency-room-or-urgent-care | A US urgent care center; in Germany this is a Notaufnahme or Notfallpraxis (D50). Notdienst stays as the group, and Rettungsdienst stays under it. |
| Fleisch- und Meeresfrüchteladen, Wurstladen | butcher-or-meat-store | One shop type, Metzgerei (D50). Fish Market stays. |
| Baubedarfsgeschäft | hardware-store-and-building-supplies | Baumarkt and Baustoffhandel overlap (D50). |
| Zeitungsstand | newsagent-or-newsstand | Same shop type (D50). |
| Staats- oder Provinzpark | nature-park | A US or Canadian park type. The nearest German type is Naturpark. |
| Übernachtung mit Frühstück | guesthouse-or-bed-and-breakfast | Same lodging type as Pension (D50). |
| Marineterminal | port-or-marine-terminal | A US term. Ferry and cargo terminals are ports. |
| Wohnwagenpark | motorhome-and-caravan-park | Cross-root overlap with Wohnmobilpark (D50). US trailer parks do not exist in Germany. |
| Hütte | mountain-hut-or-lodge | Cross-root overlap with Berghütte (D50). |
| Lager oder Großhandel | wholesaler | Cross-root overlap with Großhändler (D50). |
| Entsorgung | waste-management-service | Cross-root overlap with Abfallentsorgungsdienst (D50). |

D50 overlaps kept as separate nodes:
- Hafen oder Marina (leisure harbour, Outdoors) vs Port or Marine Terminal (commercial port, Travel).
- Markt (permanent market, Retail) vs Market or Fair Event (Christmas market, street fair, trade fair). The event node is renamed so that the two no longer look alike.

### 4.4 Moves (parent changed beyond the group rule)
| Node (v2) | v2 parent | v3 parent | Reason |
|---|---|---|---|
| Versicherungsagentur | Geschäfts- und prof. Dienstl. | Financial Service | Insurance is a financial service. |
| Nachhilfeservice | Geschäfts- und prof. Dienstl. | Education (root Community and Government) | Tutoring is education. FSQ places it under Business Services. |
| Lotteriehändler | Geschäfts- und prof. Dienstl. | Retail (root) | Next to Betting Shop. A lottery outlet is a shop. FSQ places it under Business Services. |
| Auditorium, Ballsaal, Hochzeitssaal, Veranstaltungsraum im Freien, Kongresszentrum | Geschäfts- und prof. Dienstl. | Event Space (new) | Venues for hire, under their FSQ general class. |
| Hersteller von Chemikalien und Gasen | Geschäfts- und prof. Dienstl. | Manufacturer or Factory | A specific manufacturer. |
| Sozial-Club | Gemeinschaft und Regierung | Organization | Clubs and associations are organisations. |
| Baseball-, Basketball-, Fußball-, Leichtathletik-, Segel-, Schwimmverein, Golfclub | Sport und Freizeit | Sports Club | Specific sports clubs under the general one. |
| Berghütte (+ Hütte) | Sport und Freizeit | Lodging (root Travel) | A mountain hut is lodging. |
| Brettladen | Einzelhandel | Sporting Goods Retail | A board-sports store. |
| Standort des Mietwagens | (Transport Hub in FSQ) | Travel (root) | Car rental companies, next to Bike Rental and Boat Rental. |
| Kindergarten (+ Kita, Vorschule) | Ausbildung | Education | Stays in Education. In FSQ, Daycare is under Child Care Service. |
| Trockenreiniger | Geschäfts- und prof. Dienstl. | same (root) | The v2 fix is kept, although FSQ places it under Health and Beauty Service. |

Nodes whose root changed: Lotteriehändler, Nachhilfeservice, Berghütte, and the merged Entsorgung, Wohnwagenpark and Lager oder Großhandel.

Other D50 parent questions, decided without a move:
- Apotheke stays in Retail. FSQ places Pharmacy in Retail, and a pharmacy website is a shop website. Drugstore and Medical Supply Store are next to it.
- Badehaus (Bath House, Health and Beauty Service) and Sauna (Sports) both stay. This follows FSQ; see the open doubts.

### 4.5 Names that differ from the FSQ name (US-centric or misleading for German websites)
Football (Soccer) Club (Soccer Club); Athletics Club (Running and Track); Ice Hockey Rink (Hockey Rink); Gym and Fitness Studio (Gym and Studio);
Vocational School (Trade School; the German "Handelsschule" was also too narrow); Kindergarten and Daycare; Student Fraternity or Sorority House;
Parliament Building (Capitol Building); Military Facility; Club or Association (Social Club); Company Canteen or Amenity; Manufacturer or Factory;
Warehouse or Storage Facility; Real Estate Developer; Cafe, Coffee and Tea House; Emergency Room or Urgent Care; Butcher or Meat Store;
Hardware Store and Building Supplies; Newsagent or Newsstand; Nature Park (Natural Park); Guesthouse or Bed and Breakfast; Port or Marine Terminal;
Motorhome and Caravan Park (RV Park); Mountain Hut or Lodge; Market or Fair Event (Marketplace); Town Square (Plaza); Pedestrian Zone (Pedestrian Plaza);
Other Outdoor Place (Other Great Outdoors); Large-Format Store (Big Box Store); Board Sports Store (Board Store);
Nut and Dried Fruit Store (Kuruyemişçi Shop); Pickle Store (Turşucu Shop); Southern US Restaurant (Southern Food Restaurant);
HIV/AIDS Support Service (AIDS Resource); Car Rental (Rental Car Location); Public Toilet (Public Bathroom); Print Shop (Print Store);
Curling Rink (Curling Ice); Loan Agency (Loans Agency). All other nodes use the FSQ name. Kneipe is "Pub", which is the FSQ name of its new link.

### 4.6 Translation errors found through the link
Fußballverein (American football), Volkshochschule (Community College), Südländisches Food-Restaurant (US Southern food), Herausgeber (Publisher = Verlag),
Apfelwein (Cidery), Brettladen (Board Store), Agentur für Arbeit (Employment Agency), Handelsschule (Trade School), Kneipe (Dive Bar), Entsorgung (Dump),
Hütte (Lodge). In v3, each is fixed by a relink, a name or a merge. The German `de` field keeps the v2 name for traceability.

### 4.7 Additions and deletions
- Added: **Event Space** (FSQ Business and Professional Services > Event Space). It is the general class for venues for hire (5 children).
- Deleted: none. Every v2 node maps to a v3 node (`results/E49/poi_v2_to_v3.json`, 779 keys).

### 4.8 Missing classes reported by the labellers
| Class | Result | Reason |
|---|---|---|
| association / club (Verein) | covered, not added | Social Club is renamed "Club or Association" (with Club House) and placed under Organization. Sports clubs are under Sports Club. |
| fan club | not added | Use Club or Association. FSQ has no fan-club category. |
| vocational school | covered, not added | FSQ Trade School exists in v2 (Handelsschule); renamed "Vocational School". |
| printing company | covered, not added | FSQ Print Store exists in v2 (Druckshop); renamed "Print Shop". FSQ has no separate printing-company category. |
| political party | not added | FSQ has no such category. Use Campaign Office (Office) or Organization. |
| certification body | not added | No FSQ category. Use Business Service. |
| breeder | not added | No FSQ category. Use Farm or Pet Service. |
| writer / author | not added | No FSQ category. Writing, Copywriting and Technical Writing Service covers commercial writers. |
| coach / mediator | not added | No FSQ category. Career Counselor, Management Consultant or Mental Health Service are the nearest. |
| weather station | not added | No FSQ category. Research Station is the nearest. |
| coin / collectibles dealer | not added | No FSQ category. Use Antique Store or Hobby Store. |
| online forum / web service | not added | Not a place (no POI); FSQ has none. Labelling rule R4 (nearest leaf, online_only) applies. |
| blog / online magazine | not added | Not a place; FSQ has none. Use Publisher or Media Agency with online_only (R4). |

## 5. Reference labels (`results/E49/refs/poi_v3.jsonl`)

All 200 lines are migrated. `main`, `extra` and `path` are converted to v3 ids, `schema` is set to `"poi3"`, and the other fields are kept.
An extra that is now an ancestor of main, or the same node as main, is dropped. This is the rule of `refs_build.clean_extras`.
The flags for each line are in `results/E49/refs/poi_v3_migration.tsv`.

- 157 lines unchanged in meaning (only the ids are new).
- 43 lines flagged:
  - 21: an extra is now an ancestor of main (for example, Restaurant for Griechisches Restaurant) and is dropped. No information is lost; the path holds it.
  - 21: main is a node that absorbed a synonym (Hersteller + Fabrik, Erwachsenenbildung + Volkshochschule, ...). The class is the same or slightly wider.
  - 7 (overlapping the above): an extra was a synonym that is now merged into main (Fabrik, Wurstladen, Forschungslabor, Lager oder Großhandel) and is dropped.
  - 2 lines where main itself was merged: Forschungslabor -> laboratory, and Immobilienentwicklungs- und Titelunternehmen -> real-estate-developer.
    The class is wider; the meaning is not lost.
  - 1 line where the root changed: www.latein-online.net (Nachhilfeservice moves from Business to Education). Its extra, Ausbildung, is now its parent.
- Lines with lost meaning: 0. Lines with changed meaning: 3 (the 2 merged mains and the 1 root change).

## 6. Code
- `scripts/E49/tree.py` reads the v3 format: rows with "id" -> node id = id, title = name, keywords = German name(s). `SCHEMAS["poi3"] = "topics/poi_v3.jsonl"`.
  `label()` returns the id (kebab-case English), and `resolve()` accepts the id or the English name. The v2 and WZ formats are unchanged.
- `scripts/E49/check_poi_schema.py` reads v2 and v3. In v3 the key is "id", and both ids and names must be unique.
- `tests/test_e49_topic_study.py`: `test_poi3_loader`; `test_poi3_real_schema_and_migration_map` (every v2 name is mapped to an existing v3 node, every `de` maps back,
  and every ref path matches the v3 tree); `test_real_schemas_load` now includes poi3.

## 7. Open doubts
1. The 45 restored groups make general classes such as Restaurant, Physician and Bar inner nodes. Scoring at depth 1 versus depth 2 now behaves
   differently from v2 (388 nodes at depth 2 instead of 82). Prompts and few-shot examples built for v2 need the new paths.
2. Depth cap: some FSQ levels collapse into siblings under one group, for example Asian Restaurant next to Chinese Restaurant, Car Dealership next to
   New Car Dealership, Banking and Finance next to Bank, College and University next to University, and Primary and Secondary School next to Elementary School.
3. Nightlife Spot is a vague single node under Arts, Entertainment and Events. It could be merged into Night Club or Bar.
4. Bath House (Health and Beauty) and Sauna (Sports) still overlap for German Therme or Sauna websites.
5. Retirement Home (Community) and Nursing Home (Health) overlap in German (Altersheim vs Pflegeheim). They are not merged, because D50 did not list them.
6. Pharmacy stays in Retail, following FSQ. If the user wants all health providers in Health, it is a one-line move.
7. The merge of Lager oder Großhandel into Wholesaler moves cash-and-carry stores (Metro) out of Retail.
8. Several US-only classes are kept with their FSQ name, because they are harmless and unlikely to be chosen: Check Cashing Service, Kingdom Hall, Terreiro, Cemevi, Tiki Bar,
   Floating Market, Baseball Store, Southern US Restaurant, Hawaiian Restaurant, Bagel Shop. They could be deleted later, with E49 confusion evidence.
9. Leichtathletikverein links to the sport-level FSQ category (Running and Track). FSQ has no athletics-club category.
10. The schema is English, while the websites and v2 prompts are German. Each node carries `de`, and the loader puts it into `keywords`. That means `text(mode="kw")` shows the German names.
