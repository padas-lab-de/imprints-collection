# E21 prefill spot-check (qwen-agentworld-35b-a3b, prompt e21-v1)

## Overall counts (all lines of datasets/gold/prefill.jsonl)
- The file has **982 lines** (982 distinct hosts), not 1000. `error` is null on all 982.
- site_status: live 819, http_error 62, unreachable 49, redirect_other_domain 42, **missing 10** (label is `{}` despite error null, e.g. jennyhughes-design.de, koenigssalz.de).
- Any address: **661** (321 with none). Address-count distribution: 0:321, 1:328, 2:194, 3:92, 4:27, 5+:20 (max 11).
- main_address_index set: **637**.
- Non-empty `check` on at least one address: **69** hosts. Flags: country 78, evidence 26, street 6, postcode 1, town 1.
- imprint_present: true 731, false 121, absent 130. imprint_location: separate_page 565, landing_page 101, other_domain 64, pdf 1, none 121, absent 130.
- operator_type: corporate 245, sole_trader 222, unclear 172, association 139, public_body 49, private_person 14, absent 141.
- topic: Business and Professional Services 179, Community and Government 133, Arts and Entertainment 110, Retail 90, Sports and Recreation 69, Health and Medicine 64, Travel and Transportation 55, Dining and Drinking 55, Event 49, Landmarks and Outdoors 28, Nightlife Spot 6, absent 144.
- Roles over 1,140 address rows: operator 695, other 132, representative 114, editor 88, operator_other_site 83, agency 77, host 36.

## Spot-check: 40 live hosts, random.seed(21) over the 819 live labels
Judged against imprint.txt (landing.txt when no imprint). "Main address correct" counts a correctly empty main (14 hosts with no address) as correct.

| Aspect | Result |
|---|---|
| (a) main address (or correct absence) exactly right | **34/40** (85%). Of the 26 hosts with a main address: 20 right, 6 wrong. |
| (b) address list clean (nothing spurious, nothing missing) | **23/40** (58%). 17 hosts have spurious rows, 0 have a missing address. |
| (c) operator_type plausible | **38/40** clear (36/40 if two debatable `unclear` are counted wrong) |
| (d) topic plausible | **36/40** clear (32/40 if four borderline are counted wrong) |
| site_status | 39/40 (yccuk.com is parked, labelled live) |

The 17 hosts with spurious rows split into: 8 pure duplicates (same address repeated as representative/editor/operator, which the guideline says to list once), and 9 third-party or non-imprint addresses (bank, ombudsman, regulator, hoster, Google, trademark owner, template text).

## Errors found
| Host | What was wrong |
|---|---|
| x-markets.com | Main = only "Frankfurt am Main" (Sitz line), no postal address in imprint; should be imprint_without_address. Duplicate representative row. |
| www.honeymoontip.com | Main street = "Hedwigstrasse 3", number empty (not split). Duplicate editor row; Genève office (Place Cornavin) typed `editor` instead of `other`. |
| www.its-t-time.com | Address is Wix template placeholder text ("FRAUEN PWR, Lindenstraße 507", "Diese Vorlage enthält Beispieltexte"); should be no address. |
| www.martinamuth.de | imprint.txt is the homepage; main = "Hamburg" taken from a FAQ sentence. No address exists in the capture. |
| www.donnaisabella.de | Main = "Pasewalk" only; landing text has no address. |
| www.diaph16.com | Main street "161 rue du général de Gaulle" with number not split; town "Mons-en-Barœul." and "Sarreguemines." carry a trailing full stop (not verbatim). |
| www.schoergenhummer.de | Main right, but 4 spurious rows: IHK Trier (agency), two ombudsman P.O. boxes, BaFin (all legal-information parties). |
| www.franzundspaeth.de | Berufsgenossenschaft address listed as `agency` (spurious). operator_type association for a GbR design office (should be corporate). |
| www.vhs-igb.de | 4 spurious rows: editor duplicate, two `operator_other_site` rows (music school, privacy-section office; one town field is "St. Ingbert (nachfolgend „VHS“ oder „wir“ genannt)"), Saarbrücken `other`. |
| lainaschwarz.de | Only address listed is Google Inc. (Mountain View) from the Analytics privacy text; imprint has no address. |
| www.heckelbassoons.info | Trademark owner Wilhelm Heckel GmbH listed as `operator_other_site` (number not split); site operator has no address. |
| saunah-ein-fass-aufmachen.de | Duplicate `operator_other_site` row of the operator. |
| kanzlei-spiess, zelte-eickhoff, abtei-sayn, allsun.de, www.trirock.de, www.kessel.in | Same operator address repeated as representative/editor/operator (1 to 2 spurious rows each). |
| www.selfmania-beratung.de | operator_type association for an eGbR (should be corporate). |
| yccuk.com | Parked domain ("may be for sale") labelled live, with operator_type/topic (Travel) filled. |
| www.csconstruction.com.au | Topic "Landmarks and Outdoors" for a construction firm. |
| p-buna.jp | Topic "Dining and Drinking" for a pension (lodging). |
| www.nageldesign-by-lina.de | Topic "Arts and Entertainment" for a nail studio. |
| Borderline (not counted in headline) | pasadenacsc.org and argus-fotokunst.de operator_type `unclear` (volunteer org / person); topics for saunah-ein-fass-aufmachen.de, hof-unter-den-milanen.de, thyssenkrupp-materials.ch, pesticides.cvuas.de; pesticides.cvuas.de and p-buna.jp have imprint_present true from a footer address only. |

## Verdict
Accept-or-correct pre-filling should save time: for clean single-address imprints (about 20 of 26 here) the main address, type and topic are right, so a labeller only confirms.
The recurring work is deleting rows (duplicates and bank/regulator/hoster/template addresses in 17 of 40) and checking town-only or imprint-less cases, so the tool should make row deletion one click and highlight rows whose evidence is not in the imprint text. Also fix the 10 empty labels and the 982 vs 1000 count.
