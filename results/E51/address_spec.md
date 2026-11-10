# E51 address labelling spec: reference addresses for the prompt study

Scope: the 500 E51 hosts (`results/E51/dev2_hosts.txt`, `results/E51/heldout2_hosts.txt`) and the 300 E49 hosts (`results/E49/dev_hosts.txt`, `results/E49/heldout/hosts.txt`).
Source: `docs/annotation_guideline.md`, sections 3.1 to 3.4 and 6. This spec changes only what is necessary because the labeller sees the model input and not the live site.
Use: reference labels for E50 (address prompt tuning). These are not gold labels.

## 1. What you label

- Input: `imprint_text` of the host in the input file (`datasets/E51/{dev2,heldout2}_inputs.jsonl`, `datasets/E49/{dev,heldout}_inputs.jsonl`). This is the text that the model sees. Show it with `python3 -I scripts/E51/show.py <inputs> <host>`.
- Label only from `imprint_text`. Do not use `homepage_text` for addresses. Do not open the web. Do not use your memory of the company.
- If an address is cut off by the 6,000-character budget, label the part that is in the text and write "truncated" in the note.

## 2. Which addresses

List every **postal address of a party named in the imprint** as one row, with a role (guideline 3.1).

- Do not list e-mail, phone, fax, URL or map links.
- Do not list addresses of third parties named only for legal information: banks, courts, register courts, supervisory authorities, chambers, arbitration boards (for example the EU ODR platform, Universalschlichtungsstelle), insurers, tax offices, data protection authorities.
- Do not list a town that appears only in a "Sitz", "Registergericht" or "Amtsgericht" line, when the same imprint gives no other address part for it.
- If the same address appears several times (provider block and "responsible for content"), list it once.
- A data protection officer or a "Datenschutzbeauftragter" with an own address: role `other`.

Roles (guideline 3.1): `operator`, `operator_other_site`, `representative`, `editor`, `agency`, `host`, `other`.
- `operator_other_site`: not used in E51 (the input has no other-domain imprint). Use `operator`.
- `representative` and `editor`: a person who represents the operator ("Vertreten durch") or who is responsible for the content ("V.i.S.d.P.", "§ 18 MStV", "§ 55 RStV") with an own postal address. If the address is the same as the operator's, list it once as `operator`. If it is different, list it with this role; it is main only when the operator has no address (section 3). (The guideline lists these roles only when the operator has no address; E51 lists them always, so that the scorer can ignore or count them.)
- `other`: branch, sister company, local office, second location of the operator that is not the seat, data protection officer.

## 3. The main address

`main_address_index` is the 0-based index of the address of the party that is responsible for the site (guideline 3.2):
1. the address in the block headed by § 5 DDG / § 5 TMG / "Angaben gemäß" / "Anbieter" / "Medieninhaber" / "Herausgeber";
2. if the operator has several addresses: the one marked Sitz, Hauptsitz, registered office, Gesellschaftssitz; else the street address (not a P.O. box) that comes first;
3. if the operator has no address: `representative`, then `editor`.

`agency`, `host` and `other` are never main. If only such roles are listed, set `main_address_index` to null and `no_address_reason` to `imprint_without_address`.

Order of rows: write the main address first (index 0) when possible, then the others in text order.

## 4. Fields

Each row has these fields (same as the gold schema, `src/ic/gold/annotate/schema.py`):

| Field | Rule |
|---|---|
| role | One of the roles above. |
| street | Street name only, as written (`Hauptstraße`, `Leibnizstr.`). No house number, no `c/o`, no company line. P.O. box: `Postfach` (or the word as written, for example `Postfach`, `Case postale`, `P.O. Box`). |
| number | House number as written, with suffix or range (`12a`, `3-5`). P.O. box: the box number. Empty if none. |
| postcode | As written, without the country prefix (`D-`, `A-`, `CH-`). Empty if none. |
| town | As written, with districts and additions (`Frankfurt am Main`, `Grimma /OT Kaditzsch`). Do not shorten, correct or expand. |
| country | As written. Empty if the text does not name it. Do not infer it from the postcode or TLD. |
| po_box | true for a P.O. box row, else false. |
| modality | Always `text` (the input is text only). |
| evidence | The verbatim span of `imprint_text` that contains the address. It can span several lines; copy the line breaks as they are, or join lines with one space. |

Every non-empty field must occur verbatim in `imprint_text` (the validator compares after it collapses white space). Exception: a value that you had to rebuild (for example a street and number written together without a space are still verbatim; a street spread over an image is not possible here). If you must break the rule, add the flag `not_verbatim` and say why in the note.

Address cases (guideline 3.3):
- Street and number in one token without a space (`Hauptstr.12`): split them; both parts are still verbatim.
- Partial address (postcode and town only, or town only with a street): list what is there. A row needs a street, a postcode or a town.
- P.O. box and street address of the operator: list both rows, the street address is main, flag `po_box`.
- Only a P.O. box: it is the main address, flag `po_box`.
- Address outside DE, AT, CH: list it normally and flag `non_dach`.
- Obfuscated postal address (split into pieces, letters replaced): flag `obfuscated`.

## 5. No address

If you list no address with a main role, set `no_address_reason`:
- `no_imprint`: `imprint_text` is empty, or it is not an imprint (wrong page: a shop page, a news page, a login, a cookie text, a privacy policy without a provider block, an error page, a parked page).
- `imprint_without_address`: the text is an imprint (provider name or legal block), but it gives no postal address of the operator (only e-mail, phone, a contact form, or only agency, host or other addresses).

A privacy policy that names the controller ("Verantwortlicher") with an address counts as an imprint for this spec: list the controller as `operator` and write "privacy policy" in the note. (The guideline counts it as no imprint on the live site; here the crawler selected the page as the imprint, and the model must read it.)

## 6. Flags

`multi_address` (at least two distinct operator-side locations: operator plus `other` branch, not only a P.O. box next to a street), `po_box`, `obfuscated`, `non_dach`, `not_verbatim` (E51 only).

## 7. Output format

One JSON line per host in the part file:

```json
{"host": "example.de", "addresses": [{"role": "operator", "street": "Hauptstraße", "number": "12a",
  "postcode": "12345", "town": "Musterstadt", "country": "", "po_box": false, "modality": "text",
  "evidence": "Muster GmbH\nHauptstraße 12a\n12345 Musterstadt"}],
 "main_address_index": 0, "no_address_reason": null, "flags": [], "confidence": "high", "note": ""}
```

- `addresses`: list, can be empty.
- `main_address_index`: integer index into `addresses`, or null.
- `no_address_reason`: null when a main address exists; else `no_imprint` or `imprint_without_address`.
- `confidence`: `high`, `medium` or `low`.
- `note`: one short sentence for hard cases; empty otherwise.

Final reference files (`results/E51/refs/addr_*.jsonl`) add `agree_ab` (bool) and, on lines where the passes disagree, a note that starts with "adjudicated: A|B|new;".

## 8. Agreement and scoring

Two passes A and B label each host independently. Agreement measures (scripts/E51/addr_agree.py):
- main: the (street, number, postcode, town) tuple of the main address is equal after white-space and case normalisation, or both have no main address with the same `no_address_reason`;
- operator set: the sets of tuples of rows with role `operator` are equal;
- all rows: the sets of (role, tuple) of all rows are equal.

## 9. Checks before you hand in

Run `python3 -I scripts/E51/check_part.py addr <inputs> <part file>`. Fix every error. Exactly one line per host.
