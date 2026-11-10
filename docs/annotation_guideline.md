# Annotation guideline: imprints, addresses, operator type and topic

Status: 2026-10-24, for E18 (1,000-item gold set, three labellers L1, L2, L3). Decisions behind it: D14 A (label the live site, from the frozen capture), D24 B (a model suggestion is shown on every item), D12 (town as written; location scored by geocoding), D11 (topic from the homepage). Examples are public company or municipality imprints from the E8/E12 pilot captures (`datasets/E8/render/<host>/`, `datasets/E12/render/<host>/`).

## 1. What one item is

One host (for example `heroes-burgers.de`). You see its **frozen capture**: full-page screenshots (`landing`, `imprint`) and the rendered DOM text of the same pages. Label what a visitor sees on the **live site**; the capture is that site, frozen.

- Use the capture first. Open the live site (link in the tool header) only to settle something the capture lacks: no capture, empty capture, imprint not captured, an address behind a click. Then tick `used_live_site` and write why in `comment`.
- The capture may be wrong (consent banner covers the page, cut-off screenshot, wrong page). Tick `capture_problem`, say what, and label from the live site.
- You see a model suggestion (section 1.1), but no detector result and no stratum. Do not guess how an item was sampled.
- One pass per item, typically a few minutes. If it takes more than about ten, label your best reading, add a `comment`, and move on.

### 1.1 Working with suggestions

Every item opens with a model suggestion. A banner and the pill "pre-filled" mark it. Suggested values are violet. Orange fields are "not found verbatim in the captured text: check it".

- The suggestion is a draft. Check every field against the capture and accept, correct or delete it.
- Delete spurious address rows: duplicates; banks, BaFin, chambers, ombudsman, Google; town-only rows taken from a "Sitz" or register-court line (3.1).
- Known weak spots: a town-only main address, template placeholder text, a house number left in the street field, an extra country.
- An empty suggestion does not mean there is no address. Look at the imprint yourself.
- Never accept a value you have not seen in the capture.
- The detailed topic labels (5.1) are never pre-filled. Decide them yourself.

## 2. Site status and imprint

### 2.1 Site status (always fill)

| Value | Use when |
|---|---|
| `live` | A real website with its own content loads. |
| `unreachable` | No website: DNS failure, timeout, connection refused, empty capture and the live site does not load either. |
| `http_error` | The server answers with an error page (403, 404, 429, 500, 503, "access denied"). If the live site works for you, it is `live` (crawl blocks are not the site's fault). |
| `parked` | Domain parking, "domain for sale", registrar placeholder, web-server default page ("It works", "Welcome to nginx"), "under construction" with no content, hosting placeholder. |
| `redirect_other_domain` | The host redirects to a different registrable domain that shows a real website. Label that site in full (steps 2.2 to 6), as for `live`. |
| `not_a_website` | Something loads but is not a website: a bare API/JSON, a file download, an intranet login only. |

Tie-breakers: a login page that shows a company name and an imprint link is `live`. A "coming soon" page with an imprint link is `live`. If only `unreachable` vs `http_error` is unclear, take `http_error` when you see any server answer.

If the status is not `live` or `redirect_other_domain`, the form hides the rest: operator type and topic stay empty, `no_address_reason` is `site_dead`. Add a comment only if something is odd.

### 2.2 Imprint (live sites)

Decision tree:

1. Is there a link or section labelled *Impressum*, *Legal notice*, *Imprint*, *Anbieterkennzeichnung*, *Offenlegung* (AT), *Mentions légales* (CH/FR), *Rechtliche Hinweise*, or a page that evidently serves as one (provider name, legal form, address, representative)? Look in the footer, header menu, burger menu and on the landing page itself. **Yes**: `imprint_present = yes`, go on. **No**: `imprint_present = no`, `imprint_location = none`. Stop here for the imprint.
2. Where is it? (`imprint_location`; take the first that fits)
   - `other_domain`: the imprint link leads to a different registrable domain (parent company, agency, imprint generator that is the real operator's page). Registrar placeholders or generic "get your imprint here" ads are not imprints.
   - `pdf`: the imprint is a PDF file.
   - `modal`: the imprint opens as an overlay, accordion or in-page fragment without a new page.
   - `landing_page`: the imprint text is part of the landing page itself (one-pager).
   - `separate_page`: its own page on the same domain.
3. `imprint_url`: the address of the imprint page (select it from the DOM text or type it; for `modal` and `landing_page` the landing page URL).

Tie-breakers:
- Only a *Kontakt* page exists, and it names the provider with legal form or address and no better page exists: count it as the imprint (`separate_page` or `landing_page`) and comment "kontakt as imprint".
- A privacy policy that contains the provider's name and address, with no imprint: not an imprint; `imprint_present = no`, comment "address in privacy policy".
- Imprint link exists but the page is empty, 404, or "coming soon": `imprint_present = yes`, and if there is no address, `imprint_without_address`.
- Several imprint links (site and shop): the one reachable from the landing page footer or menu first; if equal, the one named *Impressum*.

## 3. Addresses

### 3.1 What to list

List every **postal address of a party named in the imprint** as one row, with a role. Only addresses on the imprint (page, section, PDF), not footer addresses elsewhere on the site. Do not list e-mail, phone, URL or map links.

Do **not** list addresses of third parties named only for legal information: banks, courts, supervisory authorities, chambers, arbitration boards, insurers, tax offices. Example: the imprint of `meetingorganizer.copernicus.org` (Copernicus GmbH) lists the company at *Bahnhofsallee 1e, 37081 Göttingen*. It also gives a bank with "P.O. Box 1409, 37144 Northeim". The bank's P.O. box is not listed and not `po_box` for the operator.

If the same address appears several times (provider block and "responsible for content"), list it once.

Roles:

| Role | Meaning |
|---|---|
| `operator` | The provider under § 5 DDG / § 5 TMG ("Angaben gemäß § 5 DDG", Diensteanbieter, Anbieter, Betreiber, Herausgeber, Medieninhaber, Inhaber), on the site's own domain. |
| `operator_other_site` | The operator's address taken from an imprint on another domain that the site points to (`imprint_location = other_domain`). |
| `representative` | A person authorised to represent the operator ("Vertreten durch") with an own address, when the operator has none. |
| `editor` | "Verantwortlich für den Inhalt nach § 18 MStV / V.i.S.d.P." with an own address, when no operator address exists. |
| `agency` | Web agency, designer, photographer credit. |
| `host` | Hosting provider. |
| `other` | A further party whose address is given as a contact (branch, sister company, local office) that is not the operator's seat. |

### 3.2 The main address

`main_address_index` marks the address of the party responsible for the site:
1. the address in the block headed by § 5 DDG / "Angaben gemäß" / "Anbieter";
2. if the operator has several addresses: the one marked *Sitz*, *Hauptsitz*, *registered office*, *Gesellschaftssitz*; else the postal (not P.O. box) address listed first;
3. if the operator has no address: `representative`, then `editor`, then none (`imprint_without_address`).

`agency`, `host` and `other` are never main. When the only addresses listed are such roles, check "none of these is the operator's" in the form (`imprint_without_address`).

Example (multi-address, CH). `blogs.letemps.ch`: the imprint of Le Temps lists a seat, *Avenue du Bouchet 2, 1209 Genève*, plus editorial offices in Bern (*Bundesgasse 8-12, 3003 Berne*), Sion and Neuchâtel. List the seat as `operator` (main), the editorial offices as `other`. Flag `multi_address`.

### 3.3 Copying the fields

The suggestion pre-fills the fields; your job is to correct them. Compare each field with the DOM text. To fix one, select the text in the DOM text pane and press the arrow button next to the field (copy, do not type). Address cards have buttons for main, show evidence (it is highlighted in the DOM text) and remove. Keep spelling, case and abbreviations as written. Do not correct or expand anything.

| Field | Rule |
|---|---|
| street | Street name only (`Hauptstraße`, `Leibnizstr.`). No house number, no `c/o`, `z. Hd.` or company lines. |
| number | As written, with suffix or range (`12a`, `3-5`). Empty if none. |
| postcode | Digits only, without `D-`, `A-`, `CH-`. |
| town | **As written**, including districts and additions (`Grimma /OT Kaditzsch`, `Frankfurt am Main`) (D12). Do not shorten. |
| country | As written. Empty if the page does not name it. Do not infer it. |
| evidence | The verbatim span from the DOM text that contains the address; may span several lines. |

The tool's "split selection into fields" helper cuts a selected address at the postcode. Always check its result.

Address cases:
- **Split over lines or mixed with phone numbers:** copy the address parts only; evidence is the lines you used.
- **Partial address** (postcode and town, no street): list what is there. Example: `cardinalsbern.ch`, "Bern Cardinals / Baseball & Softball Club / 3000 Bern": postcode 3000, town Bern, street empty, role `operator`.
- **P.O. box** (*Postfach*, *Case postale*, *P.O. Box*): tick `po_box`; street = `Postfach`, number = box number. If the operator gives both a street address and a P.O. box, list both rows (same role), make the street address main, flag `po_box` only. If only a P.O. box exists, it is the main address.
- **Outside DACH** (e.g. a German-language site run from Thailand): list it normally and flag `non_dach`. Example: `clickthai-online.de`: *112/34 Moo 11 Soi Khao Talo, Nongprue Banglamung, Chonburi 20150, Thailand*.
- **Address in an image** (`modality = image`): read it from the screenshot and type it. Leave evidence empty (the tool stores `image`). Example: `aristoteles.media` shows the publisher's address only as a picture in the imprint; the DOM text has only the e-mail address.
- **Address in a PDF** (`modality = pdf`): type it from the PDF, evidence `pdf`.
- **Behind an interaction** (accordion, click-to-reveal, modal; `modality = js_only`): it counts. If the DOM text lacks it, open the live site, type the fields, put the visible text in evidence, tick `used_live_site`.
- **Address on another site:** follow the imprint link (the capture holds that page when the tool shows it as the imprint); role `operator_other_site`. Example: `cloud.bzm-ev.de` points to the imprint of its operator CSP24 on `csp24.com` (*Zwehrenbühlstr. 63, 72070 Tübingen*).
- **Obfuscated e-mail** (`info(at)...`) is irrelevant for the address; flag `obfuscated` only when the postal address itself is obfuscated (entities, split into pieces by script).
- **Company name without street** in the imprint but the footer or contact page shows the operator's address: still `imprint_without_address` (the imprint is what we evaluate); write "address in footer" in the comment.

### 3.4 No address

When the address list is empty the tool sets `no_address_reason`:
- `site_dead`: the site is not live.
- `no_imprint`: live, no imprint (2.2).
- `imprint_without_address`: an imprint exists but gives no postal address for the operator (only e-mail, phone, form, "address on request", or only agency/host addresses).

Examples of the three negatives: `0208.cloud` (DNS failure, `unreachable`, `site_dead`); a hobby site with a contact form and no legal page (`no_imprint`); `cardinalsbern.ch`-like club pages with only "3000 Bern" are **not** negatives (partial address).

## 4. Operator type

Legal form decides first; if none is named, look at who runs the site.

| Value | Includes | Typical tokens |
|---|---|---|
| `corporate` | Companies and legal entities with a business purpose, partnerships with a company name, co-operatives, charitable companies | GmbH, UG, AG, KG, GmbH & Co. KG, OHG, GbR with a trading name, SE, Ltd., S.A., Sàrl, eG, gGmbH |
| `association` | Clubs, associations, foundations, parties, unions, church parishes, initiatives | e.V., Verein, Verband, Stiftung, Partei, Kirchengemeinde, Förderverein |
| `public_body` | Authorities and bodies under public law | Gemeinde, Stadt, Landkreis, Land, Schule/Hochschule (public), Behörde, Kammer, Anstalt öffentlichen Rechts |
| `sole_trader` | A natural person acting in business or profession | Inhaber, e.K., Einzelunternehmen, freelancer, Freiberufler, single practice (doctor, lawyer), craftsperson |
| `private_person` | A person with no business or organisational purpose | personal blog, family or hobby page |
| `unclear` | Cannot be decided (no imprint and no hint) | |

Tie-breakers:
- GmbH & Co. KG is `corporate`. A private school run by a GmbH is `corporate`; a municipal school is `public_body`.
- A hobby site of a person who also runs a business is `sole_trader` only if the site advertises that business.
- The named operator counts, not the agency or the hoster.
- A volunteer fire brigade is `public_body` when the imprint names the municipality, else `association`.
- A partnership of professionals (GbR, PartG) without a trading name: `sole_trader`. Doubtful? Choose `unclear` and comment.

Examples: *Gemeinde Kollig, Pilliger Weg 33, 56751 Kollig* is `public_body`. *Copernicus GmbH* and *Gesundheitsforen Leipzig GmbH* are `corporate`. *Bern Cardinals, Baseball & Softball Club* is `association`.

## 5. Topic

One of 11 classes, for the **website as a whole**, judged on the homepage (D11) and not on the imprint's boilerplate. Pick what the site is about or offers.

| Class | Typical sites |
|---|---|
| Arts and Entertainment | museum, gallery, cinema, theatre, zoo, amusement, music school |
| Business and Professional Services | lawyer, tax adviser, craftsperson, agency, IT, consultancy, bank, insurance, hairdresser, trade, manufacturer without web shop |
| Community and Government | municipality, school, university, library, church, association with public purpose, fire brigade, cemetery |
| Dining and Drinking | restaurant, café, bakery with seating, caterer, hotel restaurant |
| Event | a single event or a series: festival, conference, concert, fair |
| Health and Medicine | doctor, clinic, therapy, vet, care service |
| Landmarks and Outdoors | sights, parks, trails, campsite, playground, viewpoint |
| Nightlife Spot | bar, club, disco, shisha lounge |
| Retail | web shop or shop, pharmacy |
| Sports and Recreation | sports club, gym, leisure facility |
| Travel and Transportation | hotel, holiday flat, travel agency, taxi, airline, rail |

Tie-breakers:
- Sells goods online: `Retail`. Sells a service or its know-how: `Business and Professional Services`.
- Clubs by purpose: sports club is `Sports and Recreation`, a choir `Arts and Entertainment`, fire brigade or municipality `Community and Government`.
- Hotel and holiday flat: `Travel and Transportation`; restaurant: `Dining and Drinking`; a hotel site that is mostly about its restaurant is still Travel unless the homepage leads with the restaurant.
- Conference website for one conference: `Event`; the organiser's own company site: by its business.
- A site of a person or company with no recognisable offer (parked, empty): pick the closest and tick `topic_ambiguous`.
- Two classes fit equally: tick `topic_ambiguous` and take the one that matches the first screen of the landing page.

Example: `heroes-burgers.de` (Heroes Burgers, *Leibnizstr. 13, 60316 Frankfurt am Main*) is `Dining and Drinking`. `herxheimamberg.de` is the municipality site of Herxheim am Berg: `Community and Government`.

### 5.1 Topic labels: POI v3 and WZ 2025

Status: 2026-11-10 (D51 B). Rules R1 to R7 come from the E49 topic study (`results/E49/labelling_spec.md`). The 11-class topic above stays. In addition, give each live site two detailed topic labels: one from the POI v3 tree (what the site offers, 753 nodes) and one from the WZ 2025 tree (economic activity, German WZ codes). The tool shows these in sections 5a and 5b. They are **not pre-filled**. Decide them yourself, from the capture only.

Each schema has these fields:

| Field | Rule |
|---|---|
| main label | One node. The finest level that you can decide. |
| extra labels | 0, 1 or 2 more nodes that are also correct (5.4). |
| confidence | `high`: the text makes it clear. `medium`: probably right, some doubt. `low`: a guess. |
| note | One short sentence. Write it when you stop above a leaf, when you leave the main label empty, or when the case is hard. |
| online only | POI only. Tick it for an online-only operator (5.6). |

How to search: type a word in the search field. For POI, the search finds English and German names (`Zahnarzt`, `dentist`). For WZ, it finds codes and German titles (`56.11`, `Gaststätten`). Each result shows its full path from the root. Check the path before you pick. The results show inner nodes and leaves. Use the path to see which level you pick.

### 5.2 Decide the activity that the site presents

1. Ask: what does the operator offer on this site? The purpose of the site decides.
2. Use the homepage first. Use the imprint only to understand who runs the site.
3. Do not label a topic that the site mentions only in passing. Do not label the web designer, the hoster or the legal text of the imprint.
4. A company site: the main business of the company. A shop: what it sells. An association: its purpose. A public body: the public body.
5. Several activities: take the one that the homepage shows first or shows most.
6. If the operator in the imprint has a different main business, add that business as an extra label (R2). Example: a car dealer's site that presents a workshop service. Main: the workshop. Extra: the car dealer.

### 5.3 When to stop at a higher level

Go down the tree. Take the deepest node that clearly fits (R6).

- Stop at an inner node when the text does not decide between its children. Write the reason in the note. Example: the site of a Gymnasium. WZ: stop at `85.31` (general secondary schools) if the text does not decide the unterklasse.
- Do not guess a leaf. A correct inner node is better than a wrong leaf.
- If you can decide the child, take the child. Example: the menu shows Italian food: take Italian Restaurant, not Restaurant.
- WZ: if a node has exactly one child, the two are the same decision. Write the child (the leaf, R6).
- Use the root of a tree only when nothing below it fits and the root is true.
- If no node fits, or the site has no usable content, leave the main label empty and write why in the note (5.7).

### 5.4 Extra labels

- You can add up to 2 extra labels per schema. Add one only if a careful labeller would also accept it. Do not add loosely related nodes.
- Good reasons: the site has a second main activity; a general node and a specific node are both right (for example Restaurant and Italian Restaurant, as siblings); the activity sits on the border of two WZ classes; the operator's own business differs from the activity the site presents (R2).
- An extra can be a leaf or an inner node.
- **R5:** an extra must not be the main label, and must not be an ancestor of the main label. The tool refuses to save such an extra. A descendant of the main label is allowed.

### 5.5 Private homepages and blogs

- A private, non-commercial homepage: WZ `98.20.0` (R3).
- The editorial blog of one person: WZ `58.19.0` (R3).
- POI for both: the leaf of the topic when it is clear. Otherwise the root of the topic. Set confidence to `low`.
- Do not decide the topic from the person's job when the site does not present that job.

### 5.6 Online-only operators (POI)

An online-only operator has no place that a visitor can visit: a blog, a forum, a portal, a dating site, a web service, an online magazine (R4).

- Pick the nearest leaf if one fits. If none fits, pick the root of the topic.
- Tick **online only**. Leave it off for all other sites, also for web shops of a real business.
- WZ: label the activity as usual.

### 5.7 Hijacked, parked and empty domains

- **Parked domain, error page, empty shop template** (no content): leave the main label empty for both schemas. Write "parked" or the reason in the note. Site status `parked` is already enough for the tool to hide the topic section.
- **Hijacked or spam domain** (R1): if the site has no operator and no topic that make sense together, leave the main label empty and write "hijacked" in the note. If the content now on the site is coherent (for example casino reviews), label that content, set confidence to `low`, and write "hijacked" in the note.

### 5.8 Two special cases (R7)

- A hotel whose site mentions only breakfast: WZ `55.10.2`.
- A winery that makes wine: WZ `11.02.0` as main, and `01.21.0` as an extra.

### 5.9 Checks before you save

- Both schemas have confidence. POI has the online only setting.
- Every extra is not the main and not an ancestor of the main.
- You did not copy a label from a model, from another labeller or from your memory of the E49 study. Use the capture only.

## 6. Flags and comment

Flags (the form pre-ticks some; untick if wrong): `multi_address` (at least two distinct operator-side locations, not just a P.O. box next to a street), `po_box` (an operator address is a P.O. box), `obfuscated`, `non_dach` (an operator address outside DE/AT/CH), `capture_problem`, `used_live_site`.

`comment`: short and in English or German. Required for: `used_live_site`, `capture_problem`, any rule you had to bend, `kontakt as imprint`, "address in footer". Never paste personal data into comments.

Personal data: copy addresses exactly as the imprint gives them, including the home address of a sole trader or club chair when it is the provider's address. Do not label e-mails, phone numbers or private persons' names.

## 7. Broken or odd captures

| Situation | What to do |
|---|---|
| No `<host>` directory, or empty | Open the live site; `capture_problem`, `used_live_site`, comment. |
| Screenshot missing, text present | Label from the text; if the layout matters, open the live site. |
| Text missing, screenshot present | Label from the screenshot; addresses as `modality = image`. |
| Consent banner covers the page | Label from the text if it is complete, else the live site. |
| Imprint not captured but exists | `used_live_site`; copy the address from the live site and put it in evidence (a warning may appear that evidence is not in the DOM text; that is fine here). |
| Capture says error, live site works | The live site wins: `live`, comment. |

## 8. Worked examples, one per stratum

| Stratum (hard case) | Host | What to label |
|---|---|---|
| site not live | `0208.cloud` | `unreachable`; nothing else. |
| no imprint | any hobby site with only a contact form | `live`, imprint no, `no_imprint`, operator type from content or `unclear`, topic from homepage. |
| imprint without address | club page with imprint listing e-mail and a name only | `live`, imprint yes, no address, `imprint_without_address`. |
| plain text address, corporate | `meetingorganizer.copernicus.org` | operator *Bahnhofsallee 1e, 37081 Göttingen*; bank P.O. box ignored; `corporate`. |
| public body | `kollig.orts.app` (JS-rendered imprint) | *Gemeinde Kollig, Pilliger Weg 33, 56751 Kollig*; representative address is identical and listed once; `public_body`; `Community and Government`. |
| JS-required imprint | `export.transplantations-register.de` | imprint appears only in the rendered text; operator *Gesundheitsforen Leipzig GmbH, Hainstraße 16, 04109 Leipzig*; `corporate`. |
| multi-address, CH | `blogs.letemps.ch` | seat main, editorial offices `other`, flag `multi_address`. |
| agency/hoster next to operator | any imprint with "Webdesign by ..." | list the agency as `agency`; main is the operator. |
| P.O. box | operator with Postfach only | street `Postfach`, number the box, `po_box`. |
| image-only address | `aristoteles.media` | address typed from the screenshot, `modality = image`. |
| partial address | `cardinalsbern.ch` | postcode 3000, town Bern, street empty. |
| non-DACH | `clickthai-online.de` | Thai address, `non_dach`. |
| imprint on another domain | `cloud.bzm-ev.de` | `other_domain`; address with role `operator_other_site`. |
| AT / CH | `.at`/`.ch` hosts | imprint terms differ (Medieninhaber, Offenlegung); four-digit postcode; same rules. |

## 9. Calibration and agreement

The first 50 items in your list are the same for all three labellers. Label them without talking. Then we compare, discuss every difference and update this guideline after calibration, before the main round. Later, about 200 items are labelled twice independently; do not discuss them. The tool shows no other labeller's labels. Both labellers see the same model suggestion, so the two labels are independent of each other but not of the suggestion.
