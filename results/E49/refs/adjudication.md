# E49 reference labels: adjudication

Inputs: two independent label passes (datasets/E49/refs_raw/A, B), 200 dev hosts per schema.
Outputs: results/E49/refs/poi.jsonl, results/E49/refs/wz.jsonl (raw fields + `agree_ab`; POI also `online_only`).
Rules: section "Adjudication rules (E49)" in results/E49/labelling_spec.md.
Build: `python3 -I /home/dinzinger/.claude/jobs/4110e328/tmp/adjud/build.py`; check: `python3 -I /home/dinzinger/.claude/jobs/4110e328/tmp/adjud/validate.py` (0 errors).

## Counts

| Schema | A and B agree | A chosen | B chosen | New label | Rule changes on agreed lines |
|---|---|---|---|---|---|
| POI | 179 | 9 | 12 | 0 | 4 (R1 thunderalleyspeedpark.com: conf low + "hijacked"; R3 extravegant.de, peisker-ranch.de: conf low; R5 korat-katzen.de: root extra removed) |
| WZ | 179 | 11 | 10 | 0 | 4 (R7 ddhaider.at: 01.21.0 -> 11.02.0; R3 peisker-ranch.de: 85.51.0 -> 98.20.0; R1 thunderalleyspeedpark.com: conf low + "hijacked"; R5 opel-amz.de: extra 47.81 removed) |
| Total | 358 | 20 | 22 | 0 | 8 |

POI `online_only` = true on 27 lines. main = null on 1 line per schema (www.thecitypress.com, R1: spam only, A and B agree).
In some disagreements the final extras differ from the chosen pass (counted as A or B by the main).

## The 42 disagreements

| # | Schema | Host | A main | B main | Final main | Pick | Reason |
|---|---|---|---|---|---|---|---|
| 1 | POI | arts.columbia.edu | Universität | Kunstschule | Universität | A | University school of the arts; Universität as for WZ 85.40.1. |
| 2 | POI | daruweb.org | Kulturzentrum | Gemeinschaft und Regierung | Gemeinschaft und Regierung | B | R4: online language/culture site, no leaf fits; topic root. |
| 3 | POI | externals.io | Geschäfts- und professionelle Dienstleistungen | Softwareunternehmen | Softwareunternehmen | B | R4: online reader for the PHP mailing list; nearest leaf is software. |
| 4 | POI | magicmonday.ch | Unterhaltungsveranstaltung | Wohltätigkeit | Unterhaltungsveranstaltung | A | R2: the site presents a charity dinner event series. |
| 5 | POI | sippd.conservatoriodimusica.it | Musikschule | Hochschule und Universität | Hochschule und Universität | B | Conservatorio is a higher arts school (Kunsthochschule). |
| 6 | POI | wintergarten-ratgeber.net | Herausgeber | Heimwerkerservice | Heimwerkerservice | B | R4: online advice portal; nearest topic leaf is home improvement. |
| 7 | POI | www.besen-zum-kuahstall.de | Weingut | Weinbar | Weinbar | B | R2: homepage leads with the Besen wine tavern; winery as extra. |
| 8 | POI | www.bienenbleibe.com | Land- und Forstwirtschaftsdienst | Bauernhof | Land- und Forstwirtschaftsdienst | A | Renting out bee colonies with care is an agricultural service. |
| 9 | POI | www.carpartbrand.de | Autoteile und Zubehör | Großhändler | Großhändler | B | B2B parts distribution; matches WZ wholesale 46.72.0. |
| 10 | POI | www.eiposcert.de | Geschäfts- und professionelle Dienstleistungen | Unternehmensdienst | Unternehmensdienst | B | Certification body; a fitting leaf exists, so not the root. |
| 11 | POI | www.florafelt.de | Hersteller | Gartencenter | Gartencenter | B | R2: the site presents a garden-products shop; maker as extra. |
| 12 | POI | www.haustueren-kinge.de | Auftragnehmer für Türen und Fenster | Baubedarfsgeschäft | Auftragnehmer für Türen und Fenster | A | Text names own fitters (Eigene Monteure); door contractor. |
| 13 | POI | www.heckelbassoons.info | Kunst und Unterhaltung | Musikladen | Musikladen | B | R4: hobby bassoon database with instruments for sale; nearest leaf. |
| 14 | POI | www.latein-online.net | Ausbildung | Nachhilfeservice | Nachhilfeservice | B | R3/R4: private Latin learning site; nearest leaf is tutoring. |
| 15 | POI | www.luftbilder-von-deutschland.de | Geschäfts- und professionelle Dienstleistungen | Fotograf | Fotograf | B | R4: online aerial-photo portal; topic leaf preferred over root. |
| 16 | POI | www.mueller-thurgau-preis.de | Anderes Ereignis | Organisation | Anderes Ereignis | A | R2: the site presents the wine competition, not the association. |
| 17 | POI | www.nachtwei.de | Gemeinschaft und Regierung | Organisation | Gemeinschaft und Regierung | A | R3/R4: personal politics publication site; no leaf fits, topic root. |
| 18 | POI | www.purux-pool.de | Hersteller von Chemikalien und Gasen | Schwimmbadbedarfsgeschäft | Hersteller von Chemikalien und Gasen | A | Brand site of the manufacturer; matches WZ 20.59.9. |
| 19 | POI | www.stephanh.de | Touristische Informationen und Service | Sport und Freizeit | Sport und Freizeit | B | R3: private leisure homepage, mixed topic; topic root. |
| 20 | POI | www.training-for-pets.com | Haustierservice | Tierbetreuung und Tierpension | Haustierservice | A | Counselling, training and boarding; general pet-service leaf. |
| 21 | POI | www.vom-allenbach.de | Kasino | None | Kasino | A | R1: hijacked, but content (casino review) is coherent. |
| 22 | WZ | blog.barcamps.eu | 63.10.9 | 58.29.0 | 58.29.0 | B | Own hosted open-source tool; as for other SaaS lines (58.29.0). |
| 23 | WZ | cpg-hh.de | 85.31.2 | 85.31 | 85.31 | B | R6: Gymnasium spans Sek I and II; stop at 85.31. |
| 24 | WZ | fulda.pneumatici100.it | 46.18.2 | 46.72.0 | 46.72.0 | B | B2B tyre wholesale; matches POI Großhändler. |
| 25 | WZ | gothe-edelstahl.de | 24.20.1 | 24.20 | 24.20 | B | R6: tubes and fittings both lead; text does not decide. |
| 26 | WZ | gutschein.vdu-furtwangen.de | 82.99.9 | 94.11.0 | 82.99.9 | A | R2: site presents a gift-voucher service; association as extra. |
| 27 | WZ | hellmuth-scheunemann.de | 98.20.0 | 90.12.0 | 98.20.0 | A | R3: private family memorial site for a deceased painter. |
| 28 | WZ | leipziger-muenzhandlung.de | 47.92.1 | 47.69.9 | 47.92.1 | A | Site puts the coin auctions first; shop as extra. |
| 29 | WZ | live.nordbayern-wetter.info | 98.20.0 | 74.99.9 | 98.20.0 | A | R3: private hobby weather station. |
| 30 | WZ | matthiasheil.de | 98.20.0 | 85.31 | 85.31 | B | R2 over R3: page presents his Gymnasium teaching; R6 stop at 85.31. |
| 31 | WZ | portal-ow.vsz.ch | 84.13.0 | 84.24.0 | 84.24.0 | B | Vehicle registration office; keyword Kraftfahrzeugzulassungsstellen in 84.24.0. |
| 32 | WZ | sippd.conservatoriodimusica.it | 85.40.9 | 85.40.1 | 85.40.1 | B | 85.40.1 includes Kunsthochschulen; conservatorio fits. |
| 33 | WZ | wiki.k10plus.de | 63.10.1 | 91.11.0 | 91.11.0 | B | Library network wiki; matches agreed POI Bibliothek. |
| 34 | WZ | www.besen-zum-kuahstall.de | 01.21.0 | 56.30.1 | 56.30.1 | B | R2: Besen tavern leads; R7: winery 11.02.0 + 01.21.0 as extras. |
| 35 | WZ | www.dkbav.de | 69.10.3 | 70.20.0 | 69.10.3 | A | Rentenberater named; keyword Rentenberatung in 69.10.3. |
| 36 | WZ | www.foerderverein-wendepunkt-arnsberg.de | 88.99.9 | 94.99.9 | 88.99.9 | A | Projects for refugees and seniors; keywords in 88.99.9. |
| 37 | WZ | www.luftbilder-von-deutschland.de | 63.91.0 | 58.19.0 | 63.91.0 | A | Page is mostly link lists to aerial-photo sources. |
| 38 | WZ | www.mueller-thurgau-preis.de | 82.30.0 | 94.11.0 | 82.30.0 | A | R2: site presents the competition (event); association as extra. |
| 39 | WZ | www.raiffeisendruckerei.de | 26.11.9 | 18.12.0 | 26.11.9 | A | Makes debit/credit chip cards; keyword Multifunktionskreditkarten in 26.11.9. |
| 40 | WZ | www.technodrive.com | 27.11.2 | 27.11.1 | 27.11.2 | A | Core product is stepping-motor drivers (Stromrichter). |
| 41 | WZ | www.vom-allenbach.de | 58.19.0 | None | 58.19.0 | A | R1: hijacked, coherent casino-review content (publishing). |
| 42 | WZ | www.zeit-stiftung.de | 94.99.9 | 94.99 | 94.99 | B | R6: science/education and culture both; text does not decide. |

## Open questions

1. R4 "topic root" is not defined for mixed-topic private sites (www.stephanh.de: leisure photos, travel and Linux tips -> Sport und Freizeit chosen).
2. R4 `online_only` for (a) private homepages about a physical place or activity (peisker-ranch.de set false, martin-riedlingen.de set true), (b) SaaS companies (contrax.app, school.the-skill.io set true; kos.webuntis set false as a software firm), (c) main = null (www.thecitypress.com set false). The lead should confirm.
3. R2 versus the WZ convention that a maker who sells its own products is manufacturing: www.florafelt.de is POI Gartencenter (shop presented) but WZ stays with the agreed manufacturing label; www.purux-pool.de is POI manufacturer. The two schemas can therefore differ in viewpoint for the same host.
4. R2 versus R3 for personal pages about the owner's job (matthiasheil.de: WZ 85.31 with 98.20.0 as extra, POI Gymnasium). An alternative is 98.20.0 as main.
5. Close calls that a third rater could reasonably flip: www.training-for-pets.com (Haustierservice vs Tierbetreuung und Tierpension), www.foerderverein-wendepunkt-arnsberg.de (88.99.9 vs 94.99.9), www.technodrive.com (27.11.2 vs 27.11.1), wiki.k10plus.de (91.11.0 vs 63.10.1).
6. www.vom-allenbach.de: WZ 58.19.0 (review publishing) with 92.00.3 as extra; R1 does not say whether "coherent content" means the publisher activity or the promoted activity.
