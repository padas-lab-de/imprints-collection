#!/usr/bin/env python3
"""E49: build topics/wz2025.jsonl (WZ 2025) from BA structure + Klassifikationsserver keywords.

Sources (see results/E49/wz2025_schema.md):
  BA   Systematik-WZ-2025-Excel.xlsx  -> codes, titles, levels, parents (BA page named by the user)
  KS   Klassifikationsserver wz2025 complete.csv (zip) -> Stichwoerter, Einschluesse/Ausschluesse (BA offers
       the WZ 2025 keyword index and explanations nowhere; only for WZ 2008)

Usage (from repo root):  python3 -I scripts/E49/wz2025_build.py [RAW_DIR] [OUT_JSONL]
Only the standard library is used. Downloaded files are untrusted data: parsed, never executed.
"""
import csv
import datetime
import io
import json
import re
import statistics
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_RAW = "/home/dinzinger/GitLab/fim/imprints-collection/datasets/E49/wz2025_raw"
BA_URL = (
    "https://statistik.arbeitsagentur.de/DE/Statischer-Content/Grundlagen/Klassifikationen/"
    "Klassifikation-der-Wirtschaftszweige/Generische-Publikationen/Systematik-WZ-2025-Excel.xlsx"
    "?__blob=publicationFile&v=1"
)
KS_URL = "https://www.klassifikationsserver.de/klassService/thyme/variant/download/wz2025?file=complete&type=csv"
BA_FILE, KS_FILE = "Systematik-WZ-2025-Excel.xlsx", "ks_complete.csv"
LEVELS = {1: "abschnitt", 2: "abteilung", 3: "gruppe", 4: "klasse", 5: "unterklasse"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def download(url, path):
    if path.exists():
        return
    req = urllib.request.Request(url, headers={"User-Agent": "imprints-collection-E49/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        path.write_bytes(r.read())


def read_xlsx(path):
    """Return {sheet_name: [row(list of str|None)]} using the stdlib only."""
    z = zipfile.ZipFile(path)
    ss = [
        "".join(t.text or "" for t in si.iter("{%s}t" % NS["m"]))
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)
    ]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    rid = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    for s in wb.find("m:sheets", NS):
        rows = []
        root = ET.fromstring(z.read("xl/" + target[s.get(rid)].lstrip("/").replace("xl/", "")))
        for r in root.findall(".//m:row", NS):
            row = []
            for c in r:
                v = c.find("m:v", NS)
                row.append(None if v is None else (ss[int(v.text)] if c.get("t") == "s" else v.text))
            rows.append(row)
        out[s.get("name")] = rows
    return out


def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def read_ba(path):
    sheets = read_xlsx(path)
    names = list(sheets)
    created = None
    for row in sheets[names[0]]:
        if row and row[0] == "Erstellungsdatum:" and row[1]:
            created = (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(row[1]))).isoformat()
    nodes = {}  # code -> (level, title)
    by_title = {"Abschnitte": 1, "Abteilungen": 2, "Gruppen": 3, "Klassen": 4, "Unterklassen": 5}
    sect_range = {}
    for name in names[1:]:
        rows = sheets[name]
        lvl = by_title.get(norm(rows[2][0] if len(rows[2]) else "")) if len(rows) > 2 else None
        if lvl is None:
            if norm(rows[2][0]) == "Abteilungen zu Abschnitt":  # mapping sheet: letter, range, title
                for r in rows[6:]:
                    if r and len(r) >= 3 and r[0] and r[1]:
                        sect_range[r[0]] = r[1]
            continue
        for r in rows[6:]:
            if r and len(r) >= 2 and r[0] and r[1] and re.fullmatch(r"[A-V]|\d\d(\.\d{1,2}){0,2}", norm(r[0])):
                nodes[norm(r[0])] = (lvl, norm(r[1]))
    return nodes, sect_range, created


def parent_of(code, level, sect_range):
    if level == 1:
        return None
    if level == 2:
        n = int(code)
        for letter, rng in sect_range.items():
            lo, _, hi = rng.partition("-")
            if int(lo) <= n <= int(hi or lo):
                return letter
        raise ValueError(code)
    return {3: code[:2], 4: code[:4], 5: code[:5]}[level]


def read_ks(path):
    z = zipfile.ZipFile(path)

    def rd(marker):
        n = [x for x in z.namelist() if marker in x][0]
        return n, list(csv.reader(io.StringIO(z.read(n).decode("utf-8-sig")), delimiter=";"))

    name, rows = rd("mit_Erl")
    h = next(i for i, r in enumerate(rows) if r and r[0] == "Schlüssel WZ 2025")
    hdr = rows[h]
    expl = {}
    for r in rows[h + 1 :]:
        d = dict(zip(hdr, r))
        expl[r[0]] = (int(r[1]), norm(r[2]), norm(d["Einschlüsse"]), norm(d["Umfasst ferner"]), norm(d["Ausschlüsse"]))
    _, rows = rd("Stichw")
    h = next(i for i, r in enumerate(rows) if r and r[0] == "Stichwort")
    kw = defaultdict(list)
    for r in rows[h + 1 :]:
        k, c = norm(r[0]), norm(r[1])
        if k and k not in kw[c]:
            kw[c].append(k)
    return expl, kw, name


def main():
    raw = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RAW)
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "topics/wz2025.jsonl")
    raw.mkdir(parents=True, exist_ok=True)
    download(BA_URL, raw / BA_FILE)
    download(KS_URL, raw / KS_FILE)
    ba, sect_range, created = read_ba(raw / BA_FILE)
    expl, kw, ksname = read_ks(raw / KS_FILE)
    print(f"BA xlsx Erstellungsdatum: {created}; KS file: {ksname}")

    # cross-check BA vs KS
    print("only in BA:", sorted(set(ba) - set(expl))[:10], "only in KS:", sorted(set(expl) - set(ba))[:10])
    diff = [c for c in ba if c in expl and (ba[c][0] != expl[c][0] or norm(ba[c][1]).lower() != expl[c][1].lower())]
    print("level/title (case-insens.) mismatches BA vs KS:", len(diff), diff[:10])
    print("keyword codes not in structure:", sorted(set(kw) - set(ba)))

    kids = defaultdict(list)
    par = {c: parent_of(c, ba[c][0], sect_range) for c in ba}
    for c in sorted(ba):
        kids[par[c]].append(c)
    ordered = []

    def walk(c):
        ordered.append(c)
        for k in kids[c]:
            walk(k)

    for c in sorted(kids[None]):
        walk(c)
    assert len(ordered) == len(ba)
    for c in ba:
        assert par[c] is None or par[c] in ba, c

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for c in ordered:
            lvl, title = ba[c]
            e = expl.get(c, (lvl, title, "", "", ""))  # 01.12.0 is missing in the KS export
            inc = " ".join(x for x in (e[2], e[3]) if x)
            rec = {"code": c, "level": LEVELS[lvl], "title": title, "parent": par[c], "keywords": kw.get(c, [])}
            if inc:
                rec["includes"] = inc
            if e[4]:
                rec["excludes"] = e[4]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # statistics for the report
    per = defaultdict(list)
    cnt = Counter()
    for c in ba:
        L = LEVELS[ba[c][0]]
        cnt[L] += 1
        per[L].append(len(kw.get(c, [])))
    for L in LEVELS.values():
        v = per[L]
        print(f"{L:12s} n={cnt[L]:4d} kw_total={sum(v):6d} min={min(v)} median={statistics.median(v)} max={max(v)} no_kw={v.count(0)}")
    print("total nodes", len(ba), "total keyword links", sum(len(v) for v in kw.values()))
    print("nodes with includes:", sum(1 for c in ba if c in expl and (expl[c][2] or expl[c][3])), "excludes:", sum(1 for c in ba if c in expl and expl[c][4]))
    print("wrote", out)


if __name__ == "__main__":
    main()
