# Annotation guideline: imprint addresses and topics

Status: draft v0.1 (2026-10-23), for D8-gold-set-extension. Applies to the ~300 new hard items and to the second annotation of 200 existing items.

## What one item is

One website (host). You see the extracted plain text of its imprint page (*Impressum*), plus URL and title. If the text is empty or not an imprint, still annotate (see "No address").

## Task 1: main postal address

Annotate **one** address: the postal address of the party responsible for the website (the *Diensteanbieter* named under § 5 DDG / formerly § 5 TMG, or "Verantwortlich"/"Herausgeber").

Fields, copied as written on the page (do not correct spelling, do not expand abbreviations):

| Field | Gold key | Notes |
|---|---|---|
| Country | `Country` | Write as on the page; if absent, infer from postcode/town and write `Deutschland`, `Österreich` or `Schweiz`. |
| Town | `Town` | Without district suffix unless it is part of the postal town (e.g. `Frankfurt am Main`). |
| Postcode | `PLZ` | Without country prefix (`D-`, `A-`, `CH-`). |
| Street | `Street` | Street name only, e.g. `Hauptstr.` |
| House number | `Streetnumber` | Including suffixes and ranges, e.g. `12a`, `3-5`. Empty if the page has none. |

Rules for hard cases:

1. **Several addresses** (headquarters + branches, operator + agency, editor + host): take the responsible operator's address. If the operator has several, take the one marked as *Sitz*/headquarters; otherwise the first one listed. Tick `multi_address`.
2. **Web agency or hosting provider** listed in addition to the operator: never annotate the agency.
3. **P.O. box only** (*Postfach*): Street = `Postfach`, House number = the box number. Tick `po_box`.
4. **Address split across lines or mixed with phone numbers**: reassemble; annotate only the address parts.
5. **Address only in an image or behind JavaScript** (text does not contain it): leave all fields empty and tick `not_in_text`. We evaluate on what the text contains.
6. **No address**: leave all fields empty and tick `no_address`. This is a valid, wanted outcome.
7. **Non-DACH address** (e.g. a German-language site run from Spain): annotate it normally; Country as written.

## Task 2: topic

Pick **one** of the 11 top-level classes for the **website as a whole** (use the homepage text if shown, not the imprint's legal boilerplate):

Arts and Entertainment · Business and Professional Services · Community and Government · Dining and Drinking · Event · Health and Medicine · Landmarks and Outdoors · Nightlife Spot · Retail · Sports and Recreation · Travel and Transportation

Tie-breakers:
- A shop that sells online → Retail; a service provider (lawyer, tradesperson, agency) → Business and Professional Services.
- Associations (*Verein*): by their purpose (sports club → Sports and Recreation, fire brigade or municipality → Community and Government).
- Hotels and holiday flats → Travel and Transportation; restaurants → Dining and Drinking.
- If two classes fit equally, tick `topic_ambiguous` and pick the first in the list above.

## Flags per item

`no_address`, `multi_address`, `po_box`, `not_in_text`, `topic_ambiguous`, free-text `comment`.

## Agreement

Two annotators label the same 200 items independently, without discussion. We report per-field agreement for addresses and Cohen's κ for topics, then adjudicate disagreements and refine this guideline (v0.2) before the remaining items.

## Open points

- Sampling of the ~300 hard items (strata: no address, multiple addresses, AT/CH, P.O. box, JS-only) needs a fresh fetch run (E4-fetch-yield-baseline) to draw from.
- Annotation tool (spreadsheet vs. a small web form) is not decided yet.
