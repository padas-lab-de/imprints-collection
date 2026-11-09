# WZ 2025 schema (E49 business schema)

Built 2026-11-09 by `scripts/E49/wz2025_build.py` into `topics/wz2025.jsonl` (2030 lines). Raw downloads: `datasets/E49/wz2025_raw/` (untracked).

## Sources by field
| Field | Source | URL |
|---|---|---|
| code, level, title, parent | BA "Systematik WZ 2025" xlsx (BA file created 2026-03-04) | https://statistik.arbeitsagentur.de/DE/Statischer-Content/Grundlagen/Klassifikationen/Klassifikation-der-Wirtschaftszweige/Generische-Publikationen/Systematik-WZ-2025-Excel.xlsx?__blob=publicationFile&v=1 (linked from the BA page named in D49) |
| keywords | Klassifikationsserver "Stichwörter" (inside the `complete.csv` zip), release 2026-11-05 | https://www.klassifikationsserver.de/klassService/thyme/variant/download/wz2025?file=complete&type=csv |
| includes, excludes | same Klassifikationsserver zip, file "Gliederung mit Erläuterung" | same |

BA offers the WZ 2025 structure only. Its keyword index and the explanations PDF exist only for WZ 2008 (the same BA page links the Klassifikationsserver for WZ 2025). Destatis (klassifikation-wz-2025.html) only links the Klassifikationsserver plus a correspondence xlsx WZ 2025 vs 2008 and a structure xlsx; those were not downloaded. The Klassifikationsserver is run by the Bayerisches Landesamt für Statistik for the statistical offices.

`parent` is derived from the code (Abteilung -> Abschnitt via the BA range sheet, e.g. 36-39 -> E; deeper levels via code prefix). `includes` = "Einschlüsse" + "Umfasst ferner" text; `excludes` = "Ausschlüsse". Whitespace is normalised and bullet lists are flattened to one line. These texts are the full explanation, not short (median 166 chars, max 7157; 25 nodes above 1500 chars); truncate downstream if needed.

## Counts
Levels (Ebene 1-5): abschnitt 22 (A-V), abteilung 87, gruppe 287, klasse 651, unterklasse 983; total 2030. BA and KS agree on all nodes except 01.12.0 (only in BA).

Keywords: 35 688 keyword-to-code links (35 690 rows, 2 exact duplicates dropped). All attach to unterklasse; none at higher levels, nothing copied up.

| level | nodes | keywords total | min / median / max per node | nodes without keywords |
|---|---|---|---|---|
| abschnitt | 22 | 0 | 0 / 0 / 0 | 22 |
| abteilung | 87 | 0 | 0 / 0 / 0 | 87 |
| gruppe | 287 | 0 | 0 / 0 / 0 | 287 |
| klasse | 651 | 0 | 0 / 0 / 0 | 651 |
| unterklasse | 983 | 35 688 | 0 / 16 / 1144 | 1 (01.12.0) |

Largest: 46.14.9 (1144), 47.52.0 (641), 46.17.2 (566), mostly "X, Großhandel / Herstellung / Handelsvermittlung" variants. includes is present on 1222 nodes, excludes on 994.

## Examples
- 96.21.0 "Frisör- und Barbiersalons": 10 keywords, e.g. "Damenfriseurgewerbe", "Coiffeure (Damen- und Herrenfriseurgewerbe)".
- 62.10.1 "Entwicklung und Programmierung von Internetpräsentationen": 19 keywords, e.g. "Homepagedesign", "Erstellen von Internetseiten (Webdesign)".
- Keywords carry qualifiers, e.g. "Abbauhämmer (handgeführte Druckluftwerkzeuge), Großhandel" -> 46.62.0. The same product maps to different codes by activity (Herstellung, Großhandel, Handelsvermittlung, Einzelhandel).

## Oddities
- Class 01.12 "Anbau von Reis" has no Unterklasse 01.12.0 in the KS export, but BA lists it. Kept (BA), with no keywords and no explanation text.
- Titles differ BA vs KS for two sections: E (BA "Abwasser- und Abfallentsorgung und Beseitigung von Umweltverschmutzungen"; KS "Wasserversorgung; Abwasser- ...") and U ("Haushaltspersonal" vs "Hauspersonal"). BA wording is used. KS Abschnitt titles are UPPERCASE; all other titles match case-insensitively.
- KS explanation texts are marked "Vorläufige Fassung der Erläuterungstexte (Stand vom 02.11.2026)" (preliminary; KS data stand 2026-11-05). Later BA/KS releases may differ.
- Source typo kept: "Programierung von Datenbanken" (62.10.9 keyword).
- Abschnitt, Abteilung, Gruppe and Klasse nodes have no keywords by design; a keyword-based method must aggregate from descendants.

## Terms of use
BA xlsx (sheet Impressum): (c) Statistik der Bundesagentur für Arbeit. Storing, redistribution and reproduction (also in part) are allowed with source attribution; content must not be altered or falsified; own calculations are allowed if marked; online use should link to the BA statistics homepage; commercial use (except press, broadcasting, scientific publications) needs BA permission. Our jsonl restructures and merges data: cite the sources and mark it as derived. KS files carry empty "Copyright" fields; Destatis states for related classifications "Verbreitung, auch auszugsweise, mit Quellenangabe gestattet". Check before redistributing the jsonl publicly.

## Rebuild
`python3 -I scripts/E49/wz2025_build.py datasets/E49/wz2025_raw topics/wz2025.jsonl` from the repo root (stdlib only; downloads if files are missing).
