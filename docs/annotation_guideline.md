# Annotation guideline v0.2: imprints, addresses, operator type and topic

Status: v0.2 (2026-10-24), for E18 (1,000-item gold set, three labellers L1, L2, L3). It replaces v0.1 (old gold set). Decisions behind it: D14 A (label the live site, from the frozen capture), D15 C (label from scratch; no model output), D12 (town as written; location scored by geocoding), D11 (topic from the homepage). Examples are public company or municipality imprints from the E8/E12 pilot captures (`datasets/E8/render/<host>/`, `datasets/E12/render/<host>/`).

## 1. What one item is

One host (for example `heroes-burgers.de`). You see its **frozen capture**: full-page screenshots (`landing`, `imprint`) and the rendered DOM text of the same pages. Label what a visitor sees on the **live site**; the capture is that site, frozen.

- Use the capture first. Open the live site (link in the tool header) only to settle something the capture lacks: no capture, empty capture, imprint not captured, an address behind a click. Then tick `used_live_site` and write why in `comment`.
- The capture may be wrong (consent banner covers the page, cut-off screenshot, wrong page). Tick `capture_problem`, say what, and label from the live site.
- You see no model output, no detector result and no stratum. Do not guess how an item was sampled.
- One pass per item, typically a few minutes. If it takes more than about ten, label your best reading, add a `comment`, and move on.

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

Select the text in the DOM text pane and press the arrow button next to a field (copy, do not type). Keep spelling, case and abbreviations as written. Do not correct or expand anything.

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

The first 50 items in your list are the same for all three labellers. Label them without talking. Then we compare, discuss every difference and change this guideline (v0.3) before the main round. Later, about 200 items are labelled twice independently; do not discuss them. The tool shows no other labeller's labels.
