# poi_v2.jsonl cleanup (E49)

Date 2026-11-09. Input: `topics/poi_v2.jsonl` as committed in 4e94ccd (796 lines, the user's V2). Output: the same file, overwritten (779 lines). The format is the same: one JSON object per line, `{"name", "parent"}`, root has `parent == name`, UTF-8 not escaped. The remaining lines keep their order. `topics/categories.jsonl` is not changed.

Scope: only obvious errors. The user's moves are kept: events stay in "Kunst und Unterhaltung", outdoor places stay in "Sport und Freizeit", "Nachtleben-Spot" stays in "Kunst und Unterhaltung", and the flattening to depth 2 stays. No new classes and no style renames.

Check: `python scripts/E49/check_poi_schema.py topics/poi_v2.jsonl`. Before: 5 errors (3 duplicate names, 2 roots without children). After: OK.

## Changes

Line numbers refer to the input file (796 lines).

### A. Exact duplicate names (3, one node removed per name)
| Line | Name | Before | After | Reason |
|---|---|---|---|---|
| 18 | Karaoke-Bar | parent Kunst und Unterhaltung | removed (line 341 kept, parent Essen und Trinken) | A karaoke bar is a bar. All other bar types are in Essen und Trinken, also the similar Pianobar (343) and Sportbar (346). |
| 278 | Rettungsdienst | parent Strafverfolgung und öffentliche Sicherheit | removed (line 457 kept, parent Gesundheit und Medizin) | In Germany, Rettungsdienst is the ambulance and emergency medical service. Its websites are about emergency medicine. It is next to Notdienst, Notaufnahme and Notfallzentrum. Fire brigades have their own class, Feuerwache. |
| 324 | Rathaus | parent Gemeinschaft und Regierung | removed (line 270 kept, same parent) | Same name and same parent. |

### B. Roots without children (2 removed)
| Line | Name | Before | After | Reason |
|---|---|---|---|---|
| 433 | Ereignis | root, 0 children | removed | The user moved all 14 former children to Kunst und Unterhaltung. "Anderes Ereignis" (447) stays the catch-all for events. If the empty root stays, the model can choose "Ereignis" as a class next to those events, and that makes the user's move unclear. |
| 507 | Sehenswürdigkeiten und im Freien | root, 0 children | removed | The user moved all 59 former children to Sport und Freizeit. Tourist sites are still covered: Attraktion (3), Historische und geschützte Stätte, Schloss, Monument, Malerischer Aussichtspunkt. |

### C. Near-duplicates (12 nodes merged into the kept class)
| Line | Name | Before (parent) | After | Reason |
|---|---|---|---|---|
| 95 | Friseurladen | Gesundheits- und Schönheitsservice | removed, use Friseursalon (100) | Synonyms in German (barber shop / hair salon both translated to Friseur). Same parent. |
| 158 | Büro für Unternehmens- und Strategieberatung | Geschäfts- und professionelle Dienstleistungen | removed, use Unternehmensberater (151) | After the flattening, both are siblings, and both mean management consulting. |
| 247 | Allgemeine Hochschule und Universität | Ausbildung | removed, use Hochschule und Universität (239) | This was the "general" child of 239. After the flattening it is a sibling with the same meaning. |
| 452 | Service für betreutes Wohnen | Gesundheit und Medizin | removed, use Betreutes Wohnen (228, Gemeinschaft und Regierung) | Same class in two roots. 228 is next to Altersheim and Seniorenservice. |
| 481 | Arztpraxis | Gesundheit und Medizin | removed, use Arzt (477) | A doctor's website is a practice website. After the flattening, both are siblings with the same meaning. The specialist classes (Kardiologe etc.) stay. |
| 568 | Anderes Nachtleben | Kunst und Unterhaltung | removed, use Nachtleben-Spot (567) | This was the catch-all child of Nachtleben-Spot. Now both are siblings with the same meaning. |
| 574 | Autowerkstatt | Einzelhandel | removed, use Kfz-Reparaturwerkstatt (49) | Synonyms. Also, a repair workshop does not belong under Einzelhandel. |
| 586 | Automobilgeschäft | Einzelhandel | removed, use Automobileinzelhandel (575) | Synonyms. Same parent. |
| 610 | Augenpflegegeschäft | Einzelhandel | removed, use Optiker (474) | "Eye care store" is an Optiker in German. "Augenpflegegeschäft" is not a German term. |
| 625 | Finanz- oder Rechtsdienstleistung | Einzelhandel | removed, use Finanzdienstleistung (75) or Juristischer Dienst (143) | This is the union of two existing classes, and it is under the wrong root (retail). |
| 670 | Marihuana-Apotheke | Einzelhandel | removed, use Cannabisladen (594) | Same class. The name also clashes with Apotheke (687). |
| 693 | Raucherladen | Einzelhandel | removed, use Tabakladen (713) | "Smoke shop". "Raucherladen" is not a German term. The German equivalent is Tabakladen. |

### D. Wrong parent (1)
| Line | Name | Before | After | Reason |
|---|---|---|---|---|
| 98 | Trockenreiniger | Gesundheits- und Schönheitsservice | Geschäfts- und professionelle Dienstleistungen | A dry cleaner is not a health or beauty service. Now with Waschsalon and Wäscheservice. |

### E. Name errors: typos, mistranslations, English leftovers (10 renames, parent unchanged)
| Line | Before | After | Reason |
|---|---|---|---|
| 76 | Buchhaltungs- und Buchhaltungsservice | Buchhaltungsservice | Repeated word ("accounting and bookkeeping" translated twice as Buchhaltung). |
| 148 | Protokollierungsdienst | Holzeinschlagsunternehmen | Mistranslation of "Logging Service" (forestry), not log files. The alphabetical neighbours in the source list (Locksmith, Lottery) confirm this. |
| 224 | Text-, Text- und technischer Schreibservice | Text- und technischer Schreibservice | Repeated word. |
| 234 | Entsorgen | Entsorgung | A verb used as a class name. Changed to the noun. |
| 300 | Öffentliches Badezimmer | Öffentliche Toilette | Mistranslation of "public bathroom". |
| 489 | Geburtshelfer Gynäkologe (Ob-gyn) | Gynäkologe und Geburtshelfer | English abbreviation "Ob-gyn", and the words were run together. |
| 579 | Wohnmobil- und Wohnmobilhändler | Wohnwagen- und Wohnmobilhändler | Repeated word ("RV and motorhome"). |
| 669 | Gepäckaufbewahrung | Koffergeschäft | Mistranslation of "Luggage Store" (it is under Einzelhandel). As "luggage storage", it was also a near-duplicate of Gepäckschließfach (747). |
| 710 | Ergänzungsladen | Nahrungsergänzungsmittelgeschäft | Mistranslation of "Supplement Store". |
| 796 | Truck Stop | Autohof | English leftover. Autohof is the German term. |

Total: 28 changes = 3 duplicates + 2 empty roots + 12 near-duplicate merges + 1 reparent + 10 renames (17 lines removed).

## Final counts (after)
- Nodes 779. Roots 8. Inner (non-root) nodes 5. Leaves 766. Max depth 2 (depth histogram: 0: 8, 1: 689, 2: 82).
- Inner nodes (children): Finanzdienstleistung (13), Gesundheits- und Schönheitsservice (10), Ausbildung (32), Strafverfolgung und öffentliche Sicherheit (3), Lebensmittel- und Getränkeeinzelhandel (24).
- Leaves per root (including leaves under its inner nodes):

| Root | Leaves |
|---|---|
| Kunst und Unterhaltung | 52 |
| Geschäfts- und professionelle Dienstleistungen | 179 |
| Gemeinschaft und Regierung | 97 |
| Essen und Trinken | 105 |
| Gesundheit und Medizin | 56 |
| Einzelhandel | 142 |
| Sport und Freizeit | 85 |
| Reisen und Transport | 50 |

Note: after the 2 removals above, "Strafverfolgung und öffentliche Sicherheit" has only 3 children (Feuerwache, Polizeistation, Bewährungshilfe).

## Not obvious, left as is (user may want to look)
- Flattening overlaps: former parents are now siblings of their former children, for example Restaurant and Italienisches Restaurant, Bar and Cocktailbar, Arzt and Kardiologe, Café and "Café, Kaffee- und Teehaus", Universität and Hochschule und Universität, Museum and Kunstmuseum. These are general and specific classes, not synonyms. They were kept. The prompt or scoring must handle "general vs. specific".
- Overlaps across roots: Hafen oder Marina (Sport und Freizeit) vs Hafen (Reisen und Transport). Berghütte vs Hütte. Wohnwagenpark (Gemeinschaft) vs Wohnmobilpark (Reisen). Markt (Einzelhandel) vs Marktplatz (Kunst und Unterhaltung). Kinderbetreuungsdienst (Geschäftsdienste) vs Kindertagesstätte, Kindergarten, Vorschule (Ausbildung). Lager oder Großhandel (Einzelhandel) vs Großhändler, Lager (Geschäftsdienste).
- Possible near-synonyms: Fabrik vs Hersteller. Lager vs Lagereinrichtung. Labor vs Forschungslabor. Zeitungshändler vs Zeitungsstand. Metzger vs Fleisch- und Meeresfrüchteladen vs Wurstladen. Übernachtung mit Frühstück vs Pension. Baubedarfsgeschäft vs Baumarkt. Notdienst vs Notfallzentrum vs Notaufnahme. Entsorgung vs Abfallentsorgungsdienst.
- Questionable parents: Apotheke under Einzelhandel (not Gesundheit). Versicherungsagentur and Nachhilfeservice under Geschäftsdienste (not Finanzdienstleistung or Ausbildung). Auditorium and Ballsaal under Geschäftsdienste. Lotteriehändler (Geschäftsdienste) vs Wettbüro (Einzelhandel). Badehaus under Gesundheits- und Schönheitsservice vs Sauna under Sport und Freizeit. Places that are not organisations (Baum, Vulkan, Hügel, Fluss, Brücke, Tunnel) under Sport und Freizeit.
- Awkward or US-centric translations whose meaning is still clear enough: Großer Laden (big-box store), Brettladen (board shop), Herausgeber (Verlag), Schwesternschaftshaus (sorority house; in German "Schwesternschaft" means a nursing association), Marineterminal, Kapitolgebäude, Staats- oder Provinzpark, Südländisches Food-Restaurant (US Southern food), Immobilienentwicklungs- und Titelunternehmen ("title company" does not exist in Germany), Apfelwein (a drink, not a place; probably "Cidery"), Firmenannehmlichkeit, AIDS-Ressource, Plaza, Standort des Mietwagens, Kuruyemişçi-Shop and Turşucu-Shop.
- Rettungsdienst and Karaoke-Bar: the parent that is kept is a judgement call (see A). The other parent is also possible.
