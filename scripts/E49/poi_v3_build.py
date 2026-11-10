"""E49 poi_v3, step 2: link poi_v2 to Foursquare (FSQ) categories and build the English schema poi_v3.

Inputs (positional):
  fsq_csv     FSQ OS Places category list (category_id, category_name, category_label), downloaded from
              the attachment of https://docs.foursquare.com/data-products/docs/categories (see poi_v3_changes.md)
  align_tsv   draft alignment of topics/categories.jsonl to FSQ (output of poi_v3_align.py)
  poi_v2      topics/poi_v2.jsonl
  refs_v2     results/E49/refs/poi.jsonl
Outputs (fixed paths, relative to the repository root):
  topics/poi_v3.jsonl, results/E49/poi_v2_to_fsq.csv, results/E49/poi_v2_to_v3.json,
  results/E49/refs/poi_v3.jsonl, results/E49/refs/poi_v3_migration.tsv

Usage: python3 -I scripts/E49/poi_v3_build.py <fsq_csv> <align_tsv> topics/poi_v2.jsonl results/E49/refs/poi.jsonl
"""

import csv
import json
import re
import sys
import unicodedata
from collections import Counter

# ---------------------------------------------------------------------------------------------------------------
# 1. Link: German original line (topics/categories.jsonl) -> FSQ category. The draft alignment is right except
#    for these lines (checked by hand); the value is the FSQ category_name (unique for all these names).
OVERRIDE_LINE = {
    22: "Drive-in Theater", 25: "History Museum", 26: "Science Museum", 51: "Motorcycle Repair Shop",
    71: "Equipment Rental Service", 240: "College Administrative Building", 241: "College Lab",
    242: "College Library", 243: "College Residence Hall", 244: "College Theater", 245: "Community College",
    246: "Fraternity House", 338: "Hookah Bar", 382: "Noodle Restaurant", 388: "Dumpling Restaurant",
    405: "Brazilian Restaurant", 414: "Russian Restaurant", 419: "Seafood Restaurant", 521: "Dive Spot",
    522: "Farm", 523: "Field", 524: "Forest", 534: "Lighthouse", 539: "Nature Preserve", 540: "Nudist Beach",
    541: "Other Great Outdoors", 551: "Pedestrian Plaza", 561: "Tree", 563: "Volcano", 733: "Climbing Gym",
    734: "Dance Studio", 735: "Hockey", 736: "Race Track", 738: "Running and Track", 742: "Canoe and Kayak Rental",
    754: "Electric Vehicle Charging Station", 755: "Fuel Station", 760: "Hostel", 769: "Port", 772: "Toll Booth",
    774: "Tour Provider",
}
# names the first cleanup (results/E49/poi_v2_cleanup.md, part E) changed: v2 name -> original name
CLEANUP_RENAME = {
    "Buchhaltungsservice": "Buchhaltungs- und Buchhaltungsservice",
    "Holzeinschlagsunternehmen": "Protokollierungsdienst",
    "Text- und technischer Schreibservice": "Text-, Text- und technischer Schreibservice",
    "Entsorgung": "Entsorgen", "Öffentliche Toilette": "Öffentliches Badezimmer",
    "Gynäkologe und Geburtshelfer": "Geburtshelfer Gynäkologe (Ob-gyn)",
    "Wohnwagen- und Wohnmobilhändler": "Wohnmobil- und Wohnmobilhändler", "Koffergeschäft": "Gepäckaufbewahrung",
    "Nahrungsergänzungsmittelgeschäft": "Ergänzungsladen", "Autohof": "Truck Stop",
}
# names that occurred twice in the original: the kept line (cleanup part A)
KEPT_LINE = {"Karaoke-Bar": 341, "Rettungsdienst": 457, "Rathaus": 270}

# The source link is a translation error or a sport-level category; the v3 node links to this FSQ category
# (full label). Note in the CSV.
RELINK = {
    "Fußballverein": ("Sports and Recreation > Soccer > Soccer Club",
                      "source link 'Football' (American football): translation error; German means soccer club"),
    "Baseballverein": ("Sports and Recreation > Baseball > Baseball Club", "source link 'Baseball' (sport level)"),
    "Basketballverein": ("Sports and Recreation > Basketball > Basketball Club",
                         "source link 'Basketball' (sport level)"),
    "Golfclub": ("Sports and Recreation > Golf > Golf Club", "source link 'Golf' (sport level)"),
    "Eishockeystadion": ("Sports and Recreation > Hockey > Hockey Rink", "source link 'Hockey' (sport level)"),
    "Kneipe": ("Dining and Drinking > Bar > Pub", "source link 'Dive Bar' (US term); a Kneipe is a pub"),
    "Volkshochschule": ("Community and Government > Education > Adult Education",
                        "source link 'Community College' (US two-year college): translation error; "
                        "a Volkshochschule is adult education"),
}
# match = approx: the German class and the closest FSQ category differ in meaning (reason given)
APPROX = {
    "Eishockeystadion": "ice hockey stadium; FSQ has Hockey Rink (closest)",
    "Leichtathletikverein": "athletics club; FSQ has only the sport 'Running and Track' (and Running Club)",
    "Handelsschule": "Handelsschule is a commercial school; FSQ Trade School = vocational school (wider)",
    "Apfelwein": "German names the drink (cider); FSQ Cidery is a cider maker or cider bar",
    "Brettladen": "literal 'board shop'; FSQ Board Store is a board-sports (skate, surf, snowboard) store",
    "Kindergarten": "FSQ Nursery School; in Germany Kindergarten and Kita overlap",
    "Hütte": "FSQ Lodge (lodging type); German Hütte is mostly a mountain or ski hut",
    "Südländisches Food-Restaurant": "translation error: FSQ means US Southern cuisine, German reads 'southern "
                                     "(Mediterranean) food'",
    "Agentur für Arbeit": "German name is the Federal Employment Agency; FSQ Employment Agency is any job agency",
    "Entsorgung": "FSQ Dump (landfill); German Entsorgung is any waste disposal",
    "Marktplatz": "German Marktplatz is a market square (place); FSQ Marketplace is an event category",
    "Eisstockschießen": "Eisstockschießen (Bavarian curling) is a sport; FSQ Curling Ice is the venue",
    "Notfallzentrum": "FSQ Urgent Care Center (US walk-in clinic); no German equivalent",
    "Herausgeber": "FSQ Publisher; the German word for a publishing company is Verlag",
    "Attraktion": "FSQ Attraction is under Amusement Park; German Attraktion is any tourist attraction",
    "Sport und Freizeit": "FSQ Sports and Recreation; v2 also holds all Landmarks and Outdoors classes",
    "Kunst und Unterhaltung": "FSQ Arts and Entertainment; v2 also holds the Event and Nightlife classes",
}

# ---------------------------------------------------------------------------------------------------------------
# 2. v3 second pass. Keys are v2 German names.
ROOT_NAME = {
    "Kunst und Unterhaltung": "Arts, Entertainment and Events",
    "Geschäfts- und professionelle Dienstleistungen": "Business and Professional Services",
    "Gemeinschaft und Regierung": "Community and Government",
    "Essen und Trinken": "Dining and Drinking",
    "Gesundheit und Medizin": "Health and Medicine",
    "Einzelhandel": "Retail",
    "Sport und Freizeit": "Sports, Recreation and Outdoors",
    "Reisen und Transport": "Travel and Transportation",
}
ROOT_EXTRA_FSQ = {"Kunst und Unterhaltung": ["Event"], "Sport und Freizeit": ["Landmarks and Outdoors"]}

# merged node -> kept node (the kept node's v3 name covers both)
MERGE = {
    "Kindertagesstätte": "Kindergarten", "Vorschule": "Kindergarten",
    "Volkshochschule": "Erwachsenenbildung",
    "Schwesternschaftshaus": "Verbindungshaus",
    "Militärbasis": "Militär",
    "Wohnung oder Eigentumswohnung": "Wohnhaus",
    "Clubhaus": "Sozial-Club",
    "Firmenannehmlichkeit": "Firmenkantine", "Firmencafé": "Firmenkantine",
    "Fabrik": "Hersteller",
    "Lager": "Lagereinrichtung",
    "Forschungslabor": "Labor",
    "Mobilfunkunternehmen": "Telekommunikationsdienst",
    "Immobilienentwicklungs- und Titelunternehmen": "Gewerbeimmobilienentwickler",
    "Café": "Café, Kaffee- und Teehaus",
    "Notfallzentrum": "Notaufnahme",
    "Fleisch- und Meeresfrüchteladen": "Metzger", "Wurstladen": "Metzger",
    "Baubedarfsgeschäft": "Baumarkt",
    "Zeitungsstand": "Zeitungshändler",
    "Staats- oder Provinzpark": "Naturpark",
    "Übernachtung mit Frühstück": "Pension",
    "Marineterminal": "Hafen",
    "Wohnwagenpark": "Wohnmobilpark",
    "Hütte": "Berghütte",
    "Lager oder Großhandel": "Großhändler",
    "Entsorgung": "Abfallentsorgungsdienst",
}
MERGE_REASON = {
    "Kindertagesstätte": "Kita, Kindergarten and Vorschule are one institution type in Germany (Kita)",
    "Vorschule": "Kita, Kindergarten and Vorschule are one institution type in Germany (Kita)",
    "Volkshochschule": "VHS is adult education; its FSQ link (Community College) was a translation error",
    "Schwesternschaftshaus": "sorority houses do not exist in Germany; one node for student association houses",
    "Militärbasis": "Military and Military Base: same websites (Bundeswehr sites)",
    "Wohnung oder Eigentumswohnung": "apartment building vs residential building: not separable from a website",
    "Clubhaus": "a club house is the club's building; one node for clubs and associations (Vereine)",
    "Firmenannehmlichkeit": "US office amenity classes; one node for company canteens and amenities",
    "Firmencafé": "US office amenity classes; one node for company canteens and amenities",
    "Fabrik": "synonym of Hersteller (factory = manufacturer site)",
    "Lager": "synonym of Lagereinrichtung (warehouse / storage facility)",
    "Forschungslabor": "synonym of Labor",
    "Mobilfunkunternehmen": "mobile operators are telecommunication services",
    "Immobilienentwicklungs- und Titelunternehmen": "title companies are US-specific; same as real estate developer",
    "Café": "same meaning as its parent Café, Kaffee- und Teehaus",
    "Notfallzentrum": "US urgent care center; in Germany emergency room / Notfallpraxis",
    "Fleisch- und Meeresfrüchteladen": "butcher, meat store and sausage store are one shop type (Metzgerei)",
    "Wurstladen": "butcher, meat store and sausage store are one shop type (Metzgerei)",
    "Baubedarfsgeschäft": "Baumarkt and Baustoffhandel overlap for website classification",
    "Zeitungsstand": "newsagent and newsstand: same shop type",
    "Staats- oder Provinzpark": "US/Canadian park type; nearest German type is Naturpark",
    "Übernachtung mit Frühstück": "Bed and breakfast and Pension: same lodging type in Germany",
    "Marineterminal": "US term; ferry and cargo terminals are ports",
    "Wohnwagenpark": "US trailer park (mobile homes) does not exist in Germany; caravan park = RV park",
    "Hütte": "Hütte (Lodge) and Berghütte (Mountain Hut) overlap across roots; one lodging node",
    "Lager oder Großhandel": "duplicate of Großhändler across roots (Retail vs Business)",
    "Entsorgung": "duplicate of Abfallentsorgungsdienst across roots (Community vs Business)",
}

# English names that differ from the FSQ name (US-centric or misleading for German websites)
NAME = {
    "Fußballverein": "Football (Soccer) Club",
    "Leichtathletikverein": "Athletics Club",
    "Eishockeystadion": "Ice Hockey Rink",
    "Fitnessstudio": "Gym and Fitness Studio",
    "Handelsschule": "Vocational School",
    "Kindergarten": "Kindergarten and Daycare",
    "Verbindungshaus": "Student Fraternity or Sorority House",
    "Kapitolgebäude": "Parliament Building",
    "Militär": "Military Facility",
    "Sozial-Club": "Club or Association",
    "Firmenkantine": "Company Canteen or Amenity",
    "Hersteller": "Manufacturer or Factory",
    "Lagereinrichtung": "Warehouse or Storage Facility",
    "Gewerbeimmobilienentwickler": "Real Estate Developer",
    "Café, Kaffee- und Teehaus": "Cafe, Coffee and Tea House",
    "Notaufnahme": "Emergency Room or Urgent Care",
    "Metzger": "Butcher or Meat Store",
    "Baumarkt": "Hardware Store and Building Supplies",
    "Zeitungshändler": "Newsagent or Newsstand",
    "Naturpark": "Nature Park",
    "Pension": "Guesthouse or Bed and Breakfast",
    "Hafen": "Port or Marine Terminal",
    "Wohnmobilpark": "Motorhome and Caravan Park",
    "Berghütte": "Mountain Hut or Lodge",
    "Marktplatz": "Market or Fair Event",
    "Plaza": "Town Square",
    "Fußgängerzone": "Pedestrian Zone",
    "Andere tolle Naturerlebnisse": "Other Outdoor Place",
    "Großer Laden": "Large-Format Store",
    "Brettladen": "Board Sports Store",
    "Kuruyemişçi-Shop": "Nut and Dried Fruit Store",
    "Turşucu-Shop": "Pickle Store",
    "Südländisches Food-Restaurant": "Southern US Restaurant",
    "AIDS-Ressource": "HIV/AIDS Support Service",
    "Standort des Mietwagens": "Car Rental",
    "Öffentliche Toilette": "Public Toilet",
    "Druckshop": "Print Shop",
    "Eisstockschießen": "Curling Rink",
    "Kreditagentur": "Loan Agency",
}
NAME_REASON = {
    "Fußballverein": "FSQ 'Soccer Club' is US usage; 'Football' alone is ambiguous",
    "Leichtathletikverein": "German class is a club; FSQ 'Running and Track' is the sport",
    "Eishockeystadion": "FSQ 'Hockey Rink' is ambiguous (field hockey vs ice hockey)",
    "Fitnessstudio": "FSQ 'Gym and Studio' is vague",
    "Handelsschule": "FSQ 'Trade School' is US usage; German Berufsschule = vocational school",
    "Kapitolgebäude": "US term; German Landtag / Bundestag buildings",
    "Plaza": "US/Spanish term; German Platz = town square",
    "Fußgängerzone": "FSQ 'Pedestrian Plaza'; German Fußgängerzone = pedestrian zone",
    "Andere tolle Naturerlebnisse": "FSQ 'Other Great Outdoors' is marketing language",
    "Großer Laden": "FSQ 'Big Box Store' is US usage",
    "Brettladen": "FSQ 'Board Store' is unclear",
    "Kuruyemişçi-Shop": "Turkish shop type, named by what it sells",
    "Turşucu-Shop": "Turkish shop type, named by what it sells",
    "Südländisches Food-Restaurant": "FSQ 'Southern Food Restaurant' reads as Mediterranean in German",
    "AIDS-Ressource": "FSQ 'AIDS Resource' is unclear",
    "Standort des Mietwagens": "FSQ 'Rental Car Location'; the websites are car rental companies",
    "Öffentliche Toilette": "FSQ 'Public Bathroom' is US usage",
    "Druckshop": "FSQ 'Print Store'; covers print shops and printing companies",
    "Eisstockschießen": "FSQ 'Curling Ice' is unclear",
    "Kreditagentur": "FSQ 'Loans Agency' is not idiomatic",
    "Marktplatz": "FSQ 'Marketplace' (event) clashes with Market (Retail)",
}

# Group nodes: depth 1 in v3. A node goes under the nearest FSQ ancestor that is a group of the same root
# (the "general" node), otherwise under its root. Max depth stays 2.
GROUPS = [
    "Kino", "Museum", "Veranstaltungsort für darstellende Künste", "Unterhaltungsveranstaltung", "Marktplatz",
    "Automobilservice", "Finanzdienstleistung", "Lebensmittel- und Getränkeservice",
    "Gesundheits- und Schönheitsservice", "Heimwerkerservice", "Juristischer Dienst", "Büro", "Haustierservice",
    "Fotoservice", "Immobilienservice", "Technologiegeschäft", "Hersteller", "@event-space",
    "Ausbildung", "Regierungsgebäude", "Strafverfolgung und öffentliche Sicherheit", "Organisation",
    "Spirituelles Zentrum",
    "Bar", "Café, Kaffee- und Teehaus", "Dessertladen", "Restaurant",
    "Notdienst", "Krankenhaus", "Psychiatrischer Dienst", "Arzt",
    "Automobileinzelhandel", "Buchhandlung", "Computer- und Elektronikeinzelhandel", "Modeeinzelhandel",
    "Lebensmittel- und Getränkeeinzelhandel", "Möbel- und Einrichtungsgeschäft", "Sportartikeleinzelhandel",
    "Fitnessstudio", "Park", "Sportverein",
    "Unterkunft", "Verkehrsknotenpunkt", "Transportdienst", "Touristische Informationen und Service",
]
# explicit parent (v2 name of the new parent, a root, or "@new-id"); overrides the FSQ rule
PARENT = {
    "Trockenreiniger": "Geschäfts- und professionelle Dienstleistungen",
    "Versicherungsagentur": "Finanzdienstleistung",
    "Nachhilfeservice": "Ausbildung",
    "Lotteriehändler": "Einzelhandel",
    "Auditorium": "@event-space", "Ballsaal": "@event-space", "Hochzeitssaal": "@event-space",
    "Veranstaltungsraum im Freien": "@event-space", "Kongresszentrum": "@event-space",
    "Hersteller von Chemikalien und Gasen": "Hersteller",
    "Sozial-Club": "Organisation",
    "Baseballverein": "Sportverein", "Basketballverein": "Sportverein", "Fußballverein": "Sportverein",
    "Golfclub": "Sportverein", "Leichtathletikverein": "Sportverein", "Segelverein": "Sportverein",
    "Schwimmverein": "Sportverein",
    "Berghütte": "Unterkunft",
    "Brettladen": "Sportartikeleinzelhandel",
    "Standort des Mietwagens": "Reisen und Transport",
    "Kindergarten": "Ausbildung",
    "Großhändler": "Geschäfts- und professionelle Dienstleistungen",
}
PARENT_REASON = {
    "Trockenreiniger": "keeps the v2 fix (not a beauty service), although FSQ has it there",
    "Versicherungsagentur": "insurance is a financial service (was a sibling of Finanzdienstleistung)",
    "Nachhilfeservice": "tutoring is education (FSQ: Business and Professional Services)",
    "Lotteriehändler": "next to Wettbüro (betting shop); a lottery outlet is a shop (FSQ: Business Services)",
    "Auditorium": "venue for hire; grouped under the new Event Space",
    "Ballsaal": "venue for hire; grouped under the new Event Space",
    "Hochzeitssaal": "venue for hire; grouped under the new Event Space",
    "Veranstaltungsraum im Freien": "venue for hire; grouped under the new Event Space",
    "Kongresszentrum": "venue for hire; grouped under the new Event Space",
    "Hersteller von Chemikalien und Gasen": "a specific manufacturer",
    "Sozial-Club": "clubs and associations are organisations",
    "Baseballverein": "a specific sports club", "Basketballverein": "a specific sports club",
    "Fußballverein": "a specific sports club", "Golfclub": "a specific sports club",
    "Leichtathletikverein": "a specific sports club", "Segelverein": "a specific sports club",
    "Schwimmverein": "a specific sports club",
    "Berghütte": "a mountain hut is lodging (was under Sport und Freizeit; merged with Hütte)",
    "Brettladen": "a board-sports store is a sporting goods store",
    "Standort des Mietwagens": "car rental is a rental business, next to bike and boat rental, not a hub",
    "Kindergarten": "stays in Education (Kita); FSQ Daycare is under Child Care Service",
}
# new nodes (not in v2): id -> (name, FSQ label, v2 parent name, reason)
ADD = {
    "@event-space": ("Event Space", "Business and Professional Services > Event Space",
                     "Geschäfts- und professionelle Dienstleistungen",
                     "FSQ general class for venues for hire; parent of Auditorium, Ballroom, Wedding Hall, "
                     "Outdoor Event Space, Convention Center"),
}


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s.replace("&", " and ")).strip("-")


def main(fsq_path, align_path, v2_path, refs_path):
    fsq = list(csv.DictReader(open(fsq_path, encoding="utf-8")))
    by_label = {r["category_label"]: r for r in fsq}
    by_name = {}
    for r in fsq:
        by_name.setdefault(r["category_name"], []).append(r)
    assert len(by_label) == len(fsq)

    # --- link every v2 node to the FSQ category of its original line
    lines = {}
    for l in open(align_path, encoding="utf-8"):
        f = l.rstrip("\n").split("\t")
        i = int(f[0])
        lab = by_name[OVERRIDE_LINE[i]][0]["category_label"] if i in OVERRIDE_LINE else f[4]
        assert len(by_name.get(OVERRIDE_LINE.get(i, ""), [0])) == 1
        lines.setdefault(f[1], []).append((i, lab))
    v2 = [json.loads(l) for l in open(v2_path, encoding="utf-8") if l.strip()]
    v2par = {r["name"]: (None if r["parent"] == r["name"] else r["parent"]) for r in v2}
    assert len(v2par) == len(v2)
    link = {}
    for r in v2:
        c = lines[CLEANUP_RENAME.get(r["name"], r["name"])]
        if len(c) > 1:
            c = [x for x in c if x[0] == KEPT_LINE[r["name"]]]
        link[r["name"]] = c[0][1]
    best = {n: RELINK[n][0] if n in RELINK else lab for n, lab in link.items()}

    def v2root(n):
        while v2par[n] is not None:
            n = v2par[n]
        return n

    # --- CSV v2 -> FSQ
    with open("results/E49/poi_v2_to_fsq.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["german_name", "german_parent", "fsq_id", "fsq_name", "fsq_path", "match", "note"])
        for r in v2:
            n = r["name"]
            row = by_label[best[n]]
            notes = []
            if n in RELINK:
                notes.append(RELINK[n][1])
            if n in APPROX:
                notes.append(APPROX[n])
            w.writerow([n, v2par[n] or "", row["category_id"], row["category_name"], row["category_label"],
                        "approx" if n in APPROX else "exact", "; ".join(notes)])

    # --- v3 nodes: one per kept v2 node plus additions
    keep = [r["name"] for r in v2 if r["name"] not in MERGE]
    for a, b in MERGE.items():
        assert b in v2par and b not in MERGE and a in v2par, (a, b)
    members = {n: [n] for n in keep}
    for a, b in MERGE.items():
        members[b].append(a)
    name_en, vid = {}, {}
    for n in keep:
        if v2par[n] is None:
            name_en[n] = ROOT_NAME[n]
        else:
            name_en[n] = NAME.get(n, by_label[best[n]]["category_name"])
    for k, (nm, _lab, _p, _r) in ADD.items():
        name_en[k] = nm
    for k, nm in name_en.items():
        vid[k] = slug(nm)
    assert len(set(vid.values())) == len(vid), Counter(vid.values()).most_common(3)
    group_by_label = {}
    for g in GROUPS:
        lab = ADD[g][1] if g in ADD else best[g]
        group_by_label[lab] = g

    def root_of(k):
        if k in ADD:
            return ADD[k][2]
        if k in PARENT:
            p = PARENT[k]
            return root_of(p) if v2par.get(p, "x") is not None else p
        return v2root(k)

    parent = {}
    for k in list(keep) + list(ADD):
        if k in ADD:
            parent[k] = ADD[k][2]
        elif v2par[k] is None:
            parent[k] = None
        elif k in PARENT:
            parent[k] = PARENT[k]
        elif k in GROUPS:
            parent[k] = root_of(k)
        else:
            parent[k] = root_of(k)
            lab = best[k]
            anc = lab.split(" > ")
            for d in range(len(anc) - 1, 0, -1):
                g = group_by_label.get(" > ".join(anc[:d]))
                if g is not None and g in name_en and root_of(g) == root_of(k):
                    parent[k] = g
                    break
    # depth check
    def depth(k):
        d = 0
        while parent[k] is not None:
            k, d = parent[k], d + 1
        return d
    assert max(depth(k) for k in parent) <= 2

    # order: preorder, children in v2 file order (added nodes at the position of their first child)
    pos = {r["name"]: i for i, r in enumerate(v2)}
    for k in ADD:
        pos[k] = min(pos[c] for c in parent if parent[c] == k) - 0.5
    kids = {}
    for k in sorted(parent, key=lambda x: pos[x]):
        kids.setdefault(parent[k], []).append(k)
    order = []

    def walk(k):
        order.append(k)
        for c in kids.get(k, []):
            walk(c)
    for r in kids[None]:
        walk(r)
    assert len(order) == len(parent)

    with open("topics/poi_v3.jsonl", "w", encoding="utf-8") as f:
        for k in order:
            if k in ADD:
                ids, de = [by_label[ADD[k][1]]["category_id"]], None
            else:
                labs = [best[m] for m in members[k]] + [lab for lab in ROOT_EXTRA_FSQ.get(k, [])]
                ids = []
                for lab in labs:
                    i = by_label[lab]["category_id"]
                    if i not in ids:
                        ids.append(i)
                de = members[k] if len(members[k]) > 1 else k
            rec = {"id": vid[k], "name": name_en[k], "parent": vid[parent[k]] if parent[k] else vid[k],
                   "fsq_ids": ids, "de": de}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    v2tov3 = {r["name"]: vid[MERGE.get(r["name"], r["name"])] for r in v2}
    with open("results/E49/poi_v2_to_v3.json", "w", encoding="utf-8") as f:
        json.dump(v2tov3, f, ensure_ascii=False, indent=1)
        f.write("\n")

    # --- migrate the references
    path3 = {}
    for k in parent:
        p, cur = [], k
        while cur is not None:
            p.append(vid[cur])
            cur = parent[cur]
        path3[vid[k]] = p[::-1]
    out, log = [], []
    for l in open(refs_path, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        main_ = v2tov3[r["main"]] if r["main"] is not None else None
        anc = set(path3.get(main_, []))
        extra, dropped = [], []
        for e in r["extra"]:
            x = v2tov3[e]
            if x in anc or x in extra:
                dropped.append(f"{e}->{x}")
            else:
                extra.append(x)
        flags = []
        if r["main"] is not None and MERGE.get(r["main"]):
            flags.append(f"main merged: {r['main']} -> {main_}")
        if r["main"] is not None and r["main"] in members and len(members[r["main"]]) > 1:
            flags.append(f"main widened: {main_} also covers {', '.join(members[r['main']][1:])}")
        for d in dropped:
            e, x = d.split("->")
            if x == main_:
                flags.append(f"extra merged into main: {e}")
            else:
                flags.append(f"extra now ancestor or duplicate: {e} -> {x}")
        if r["main"] is not None and r["path"] and path3[main_][0] != vid[r["path"][0]]:
            flags.append(f"root changed: {r['path'][0]} -> {path3[main_][0]}")
        new = dict(r)
        new.update({"schema": "poi3", "main": main_, "extra": extra, "path": path3.get(main_, [])})
        out.append(new)
        log.append((r["host"], r["main"] or "", main_ or "", "; ".join(flags)))
    with open("results/E49/refs/poi_v3.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open("results/E49/refs/poi_v3_migration.tsv", "w", encoding="utf-8") as f:
        f.write("host\tmain_v2\tmain_v3\tflags\n")
        for t in log:
            f.write("\t".join(t) + "\n")

    # --- summary
    mt = Counter("approx" if n in APPROX else "exact" for n in v2par)
    print(f"v2 nodes {len(v2)}  v3 nodes {len(order)}  merged {len(MERGE)}  added {len(ADD)}")
    print(f"matches {dict(mt)}  relinked {len(RELINK)}")
    print(f"depth histogram {dict(sorted(Counter(depth(k) for k in parent).items()))}")
    print(f"groups {sum(1 for k in parent if depth(k) == 1 and k in kids)}")
    print(f"refs {len(out)}  flagged {sum(1 for t in log if t[3])}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
