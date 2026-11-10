"""E49 poi_v3, step 1: align the original German category list to the Foursquare taxonomy.

The German list (topics/categories.jsonl, 796 rows, same names and order as the user's upload) is a
translated subset of the FSQ category list, in FSQ order. This script does a monotone alignment
(dynamic programming) of the German sequence to the FSQ sequence. The score uses a character-trigram
similarity of German and English names (after a small word glossary) and a bonus when the depths agree.
The result is only a draft: every pair was reviewed by hand, and fixes go into the override table of
poi_v3_build.py.

Usage: python3 -I scripts/E49/poi_v3_align.py <fsq.csv> <categories.jsonl> <out.tsv>
"""

import csv
import json
import re
import sys

GLOSS = {
    "laden": "store", "geschäft": "store", "shop": "shop", "händler": "dealer", "dienst": "service",
    "service": "service", "zentrum": "center", "center": "center", "restaurant": "restaurant",
    "bar": "bar", "museum": "museum", "schule": "school", "club": "club", "klub": "club", "verein": "club",
    "park": "park", "platz": "field", "bahn": "track", "halle": "hall", "saal": "hall", "kirche": "church",
    "büro": "office", "amt": "office", "station": "station", "haltestelle": "stop", "markt": "market",
    "arzt": "doctor", "praxis": "office", "klinik": "clinic", "studio": "studio", "agentur": "agency",
    "berater": "consultant", "beratung": "consulting", "reparatur": "repair", "werkstatt": "shop",
    "unternehmen": "company", "firma": "company", "hersteller": "manufacturer", "bäckerei": "bakery",
    "tempel": "temple", "hotel": "hotel", "café": "cafe", "kaffee": "coffee", "tee": "tea", "wein": "wine",
    "bier": "beer", "brauerei": "brewery", "garten": "garden", "kunst": "art", "musik": "music",
    "sport": "sports", "auto": "car", "kfz": "automotive", "fahrrad": "bicycle", "boot": "boat",
    "schiff": "boat", "flughafen": "airport", "bahnhof": "station", "zug": "train", "bus": "bus",
    "hafen": "harbor", "strand": "beach", "see": "lake", "berg": "mountain", "wald": "forest",
    "brücke": "bridge", "tier": "pet", "haustier": "pet", "kinder": "kids", "kind": "child",
    "möbel": "furniture", "kleidung": "clothing", "schuh": "shoe", "schuhe": "shoe", "buch": "book",
    "spielzeug": "toy", "elektronik": "electronics", "computer": "computer", "handy": "mobile phone",
    "versicherung": "insurance", "bank": "bank", "immobilien": "real estate", "rechts": "law",
    "anwalt": "lawyer", "steuer": "tax", "bau": "construction", "dach": "roofing", "maler": "painting",
    "elektriker": "electrician", "klempner": "plumber", "reinigung": "cleaning", "umzug": "moving",
    "lager": "storage", "großhandel": "wholesale", "großhändler": "wholesaler", "fabrik": "factory",
    "druck": "print", "foto": "photo", "fotograf": "photographer", "veranstaltung": "event", "ereignis": "event",
    "fest": "festival", "festival": "festival", "konferenz": "conference", "messe": "convention",
    "gemeinschaft": "community", "regierung": "government", "polizei": "police", "feuerwache": "fire station",
    "gefängnis": "prison", "gericht": "courthouse", "rathaus": "city hall", "post": "post office",
    "bibliothek": "library", "universität": "university", "hochschule": "college", "kindergarten": "kindergarten",
    "gymnasium": "high school", "grundschule": "elementary school", "zahnarzt": "dentist", "apotheke": "pharmacy",
    "krankenhaus": "hospital", "notaufnahme": "emergency room", "optiker": "optometrist", "friseur": "hair",
    "salon": "salon", "spa": "spa", "massage": "massage", "tattoo": "tattoo", "schönheit": "beauty",
    "gesundheit": "health", "medizin": "medicine", "essen": "food", "lebensmittel": "grocery", "trinken": "drinking",
    "metzger": "butcher", "fisch": "fish", "fleisch": "meat", "obst": "fruit", "gemüse": "vegetable",
    "süßigkeiten": "candy", "schokolade": "chocolate", "eis": "ice cream", "pizza": "pizza", "burger": "burger",
    "küche": "kitchen", "speisen": "food", "imbiss": "snack", "reise": "travel", "reisen": "travel",
    "transport": "transportation", "verkehr": "transportation", "taxi": "taxi", "miet": "rental",
    "vermietung": "rental", "schwimmbad": "pool", "pool": "pool", "golf": "golf", "tennis": "tennis",
    "fußball": "soccer", "ski": "ski", "reit": "equestrian", "pferde": "horse", "fitness": "gym",
    "turnhalle": "gym", "stadion": "stadium", "theater": "theater", "kino": "movie theater", "zoo": "zoo",
    "denkmal": "monument", "schloss": "castle", "burg": "castle", "hütte": "hut", "insel": "island",
    "fluss": "river", "höhle": "cave", "wasserfall": "waterfall", "aussichtspunkt": "scenic lookout",
    "wohnung": "apartment", "wohn": "residential", "heim": "home", "senioren": "senior", "jugend": "youth",
    "sozial": "social", "organisation": "organization", "gemeinnützige": "non-profit", "religiös": "religious",
    "spiritu": "spiritual", "moschee": "mosque", "synagoge": "synagogue", "friedhof": "cemetery",
    "bestattung": "funeral", "hochzeit": "wedding", "blumen": "flower", "geschenk": "gift", "schmuck": "jewelry",
    "uhren": "watch", "brillen": "eyewear", "waffen": "gun", "jagd": "hunting", "angel": "fishing",
    "werkzeug": "tool", "baumarkt": "hardware store", "heimwerker": "home improvement", "garten-": "garden",
    "italienisches": "italian", "französisches": "french", "deutsches": "german", "spanisches": "spanish",
    "griechisches": "greek", "türkisches": "turkish", "chinesisches": "chinese", "japanisches": "japanese",
    "indisches": "indian", "thailändisches": "thai", "mexikanisches": "mexican", "amerikanisches": "american",
    "asiatisches": "asian", "vietnamesisches": "vietnamese", "koreanisches": "korean",
}


def norm(s: str) -> str:
    s = s.lower()
    s = s.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss").replace("é", "e")
    return re.sub(r"[^a-z ]+", " ", s)


def gloss(de: str) -> str:
    out = []
    low = de.lower()
    for k, v in GLOSS.items():
        if k in low:
            out.append(v)
    return de + " " + " ".join(out)


def tri(s: str) -> set:
    s = " " + norm(s) + " "
    return {s[i:i + 3] for i in range(len(s) - 2)}


def sim(de: str, en: str) -> float:
    a, b = tri(gloss(de)), tri(en)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def main(fsq_path: str, de_path: str, out_path: str) -> None:
    fsq = list(csv.DictReader(open(fsq_path, encoding="utf-8")))
    de = [json.loads(l) for l in open(de_path, encoding="utf-8") if l.strip()]
    par = {r["name"]: r["parent"] for r in de}

    def ddepth(n):
        k = 0
        while par.get(n):
            n, k = par[n], k + 1
        return k

    dd = [ddepth(r["name"]) for r in de]
    fd = [r["category_label"].count(" > ") for r in fsq]
    n, m = len(de), len(fsq)
    NEG = -1e9
    # score[i][j]: best score aligning de[:i] with fsq[:j], de[i-1] matched to fsq[j-1] or skipped fsq
    score = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1):
        score[0][j] = 0.0
    for i in range(1, n + 1):
        row, prev = score[i], score[i - 1]
        best_prev, best_j = NEG, -1
        for j in range(1, m + 1):
            # running max of prev[0..j-1]
            if prev[j - 1] > best_prev:
                best_prev, best_j = prev[j - 1], j - 1
            s = sim(de[i - 1]["name"], fsq[j - 1]["category_name"]) + (0.3 if dd[i - 1] == fd[j - 1] else 0.0)
            row[j] = best_prev + s
            back[i][j] = best_j
    j = max(range(m + 1), key=lambda k: score[n][k])
    pairs = []
    for i in range(n, 0, -1):
        pairs.append((i - 1, j - 1))
        j = back[i][j]
    pairs.reverse()
    with open(out_path, "w", encoding="utf-8") as f:
        for i, j in pairs:
            f.write("\t".join([str(i + 1), de[i]["name"], str(dd[i]), fsq[j]["category_id"], fsq[j]["category_label"],
                               f"{sim(de[i]['name'], fsq[j]['category_name']):.2f}"]) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
