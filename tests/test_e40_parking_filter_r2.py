"""E40 round 2 patterns: positive and negative examples per r2 label, and round-1 reproducibility."""

import importlib.util
from pathlib import Path

import pytest

_root = Path(__file__).resolve().parents[1] / "scripts/E40"
spec = importlib.util.spec_from_file_location("parking_filter_r2", _root / "parking_filter.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

LONG = " Wir sind ein Handwerksbetrieb aus Passau und bieten Service rund um Haus und Garten." * 25  # > WEAK_MAX


def hit(title, content, desc="", patterns=None):
    return pf.detect(title, desc, content, None, patterns)


# (expected category, expected r2 label, title, description, content)
POSITIVE = [
    # sale
    ("sale", "r2_sale_template", "", "", "Domain abc.de kaufen? Wir ziehen mit dem Projekt um. Sind Sie am Kauf der Domain abc.de interessiert? domain@kv-gmbh.de"),
    ("sale", "r2_sale_template", "", "Sie können die Domain abc.de aktuell kaufen und sofort übernehmen.", ""),
    ("sale", "r2_sale_template", "", "", "abc.de wird zum Kauf angeboten! Provisionsfrei."),
    ("sale", "r2_sale_template", "", "", "Diese Domain können Sie käuflich erwerben. Kontakt: info@x.de"),
    ("sale", "r2_sale_template", "Our domain names for sale", "", "Browse our list."),
    ("sale", "r2_sale_template", "", "", "Listed on NamePros. Contact the owner."),
    ("sale", "r2_sale_template", "301Domains", "", "Inquiry form"),
    ("sale", "r2_sale_template", "", "", "Are you interested in this domain? Contact us."),
    ("sale", "r2_sale_template", "", "", "Interesse an einer unserer TOP-Domains? nonstop-domains"),
    ("sale", "r2_sale_template", "", "", "abc.de ist eine Domain der FIRSTMEDIA. Kooperation zum Ausbau der Domain gesucht."),
    ("sale", "r2_sale_template", "domain 'abc.de' zu verkaufen | lemmynet", "", ""),
    ("sale", "r2_sale_template", "", "", "abc.de zu verkaufen weitere Domains anzeigen"),
    ("sale", "r2_sale_template", "", "", "Domain info. Weitere Domains, die zum Verkauf stehen."),
    ("sale", "r2_name_for_sale", "", "", "abc.de steht zum Verkauf. Unterbreiten Sie uns ein Angebot."),
    ("sale", "r2_name_for_sale", "", "", "Die Domain „abc-xyz.de“ steht ab sofort zum Verkauf. Falls Sie Interesse haben"),
    ("sale", "r2_name_for_sale", "", "", "Diese Domain, , ist zum Verkauf."),
    ("sale", "r2_name_for_sale", "abc.de zu verkaufen", "", "Kontakt"),
    ("sale", "r2_name_for_sale", "", "", "Diese Domain ist frei, schreiben Sie uns, um sie zu erwerben."),
    # park
    ("park", "r2_park_template", "Domain im Kundenauftrag registriert", "", "Diese neue Domain wurde im Kundenauftrag registriert."),
    ("park", "r2_park_template", "", "", "Diese Domain ist bereits registriert Diese Domain ist bereits bei IONOS registriert." + LONG),
    ("park", "r2_park_template", "DENIC eG: TRANSIT-Informationsseite", "", "Die aufgerufene Domain ist derzeit nicht erreichbar Der Domaininhaber ist bereits informiert."),
    ("park", "r2_park_template", "Registered - BrandShelter", "", "This domain has been registered on behalf of a client."),
    ("park", "r2_park_template", "", "", "Diese Domain ist als Mail Domain registriert. freenet"),
    ("park", "r2_park_template", "", "", "This domain is used for email purposes only."),
    ("park", "r2_park_template", "", "", "Als Kunde von Muster Hosting GmbH können Sie diese Domain in Ihrem Kundenmenü selbst konfigurieren."),
    ("park", "r2_park_template", "Kundendomain", "", "Für diese Domain ist noch kein Inhalt hinterlegt."),
    ("park", "r2_park_template", "", "", "Die Domain abc.co.de kann noch registriert werden."),
    ("park", "r2_park_phrase", "", "", "Diese Domain wurde für einen unserer Kunden registriert."),
    ("park", "r2_park_phrase", "", "", "Die Domain wurde erfolgreich registriert. Sharkness"),
    ("park", "r2_park_phrase", "", "", "Diese Domain ist registriert, derzeit steht jedoch noch keine Website bereit."),
    ("park", "r2_park_phrase", "", "", "Diese Domain ist reserviert."),
    ("park", "r2_park_phrase", "", "", "Reserviert für Familie Maier"),
    ("park", "r2_park_phrase", "", "", "Diese Domain ist inaktiv."),
    ("park", "r2_park_phrase", "", "", "Diese Domain wird derzeit nicht für eine Website genutzt."),
    ("park", "r2_park_phrase", "", "", "Domain aktiv - technische Bereitstellung durch flosing"),
    # host
    ("host", "r2_host_template", "EUserv", "", "Domain, Homepage, Webspace oder Server nicht gefunden. Es wird deshalb dieser Platzhalter von EUserv angezeigt." + LONG),
    ("host", "r2_host_template", "", "", "Diese Domain ist keiner aktiven Website zugeordnet."),
    ("host", "r2_host_template", "", "", "DIESER WEBHOST WURDE NEU EINGERICHTET"),
    ("host", "r2_host_template", "", "", "Dieser Hinweis erscheint, weil auf diesem Account noch keine Daten hinterlegt sind."),
    ("host", "r2_host_template", "", "", "Für die Adresse wurde auf unserem Server (noch) kein Inhalt hinterlegt."),
    ("host", "r2_host_template", "", "", "Derzeit wurde noch kein Webseiteninhalt hinterlegt oder sie wurde gesperrt."),
    ("host", "r2_host_template", "tralios", "", "Für diese Domain ist keine Webseite verfügbar."),
    ("host", "r2_host_template", "", "", "Diese Domain zeigt erfolgreich auf den Server von Muster."),
    ("host", "r2_host_template", "", "", "Die Domain ist auf diesem Knotenpunkt nicht konfiguriert."),
    ("host", "r2_host_template", "", "", "Your custom domain abc.de is now connected."),
    ("host", "r2_host_phrase", "", "", "Sie haben den Webserver von Advantic erreicht."),
    ("host", "r2_host_phrase", "page4", "", "Die angegebene Homepage kann leider nicht aufgerufen werden."),
    ("host", "r2_host_phrase", "", "", "Webseite aktuell nicht erreichbar"),
    ("host", "r2_host_phrase", "", "", "Diese Seite ist lediglich ein Platzhalter."),
    ("host", "r2_host_phrase", "", "", "Domains & Hosting von helloly. In 3 Minuten zur eigenen Domain."),
    ("host", "r2_host_phrase", "", "", "Diese Domain wird bei Muster Hosting gehostet."),
    # constr
    ("constr", "r2_under_construction", "", "", "Hier entsteht in Kürze eine neue Webseite."),
    ("constr", "r2_under_construction", "", "", "Unsere Seite befindet sich zur Zeit im Umbau."),
    ("constr", "r2_under_construction", "", "", "Mehr Informationen folgt in Kürze."),
    ("constr", "r2_under_construction", "", "", "Die Website ist in Erstellung."),
    ("constr", "r2_under_construction", "Website folgt", "", ""),
    ("constr", "r2_under_construction", "", "", "Strona w przygotowaniu"),
    ("constr", "r2_under_construction", "", "", "This site is currently being migrated."),
]

# texts that must stay unflagged (no r1 and no r2 match)
NEGATIVE = [
    ("Autohaus", "", "Gebrauchtwagen: Der Golf steht zum Verkauf. Rufen Sie uns an."),
    ("Kauf", "", "Wir beraten Sie beim Kauf der richtigen Heizung."),
    ("Shop", "", "Die Artikel sind sofort lieferbar und zum Kauf in unserem Laden."),
    ("Hosting", "", "Unsere Kunden werden bei uns persönlich betreut. Domain und Webspace inklusive."),
    ("Praxis", "", "Termine nur nach Vereinbarung. Für unsere Kunden reservieren wir Parkplätze."),
    ("Hotel", "", "Zimmer können für Sie reserviert werden. Rufen Sie uns an."),
    ("Verein", "", "Unser Vereinsheim befindet sich in der Hauptstraße 3."),
    ("Blog", "", "Fortsetzung folgt. Bilder vom Sommerfest sind online."),
    ("Agentur", "", "Wir erstellen Websites und betreuen Ihre Domain, Ihren Webserver und Ihr E-Mail-Postfach."),
    ("Immobilien", "", "Das Haus in Passau ist zu verkaufen. Interesse? Schreiben Sie uns."),
    ("Kanzlei", "", "Für Mandanten ist ein Login-Bereich eingerichtet."),
    ("Bäckerei", "", "Brot, Brezen und Kuchen. Mail: info@baeckerei.de"),
]


@pytest.mark.parametrize("cat,label,title,desc,content", POSITIVE)
def test_r2_positive(cat, label, title, desc, content):
    r = hit(title, content, desc)
    assert r is not None and r[0] == cat, (r, content)
    # the r2 label decides when no round-1 pattern of the same or a more severe category matches
    r1 = hit(title, content, desc, pf.PATTERNS_R1)
    if r1 is None or pf.CAT_ORDER[r1[0]] > pf.CAT_ORDER[cat]:
        assert r[1] == label, (r, content)


@pytest.mark.parametrize("title,desc,content", NEGATIVE)
def test_r2_negative(title, desc, content):
    assert hit(title, content, desc) is None


@pytest.mark.parametrize("title,desc,content", NEGATIVE)
def test_r2_negative_long_page(title, desc, content):
    assert hit(title, content + LONG, desc) is None


def test_weak_r2_patterns_need_short_pages():
    assert hit("", "Diese Domain ist reserviert." + LONG) is None
    assert hit("", "abc.de steht zum Verkauf." + LONG) is None
    assert hit("", "Webseite aktuell nicht erreichbar." + LONG) is None


def test_strong_r2_patterns_on_long_pages():
    assert hit("", "Sind Sie am Kauf der Domain abc.de interessiert?" + LONG)[0] == "sale"
    assert hit("", "Diese neue Domain wurde im Kundenauftrag registriert." + LONG)[0] == "park"


def test_round1_reproducible():
    # round-1 misses: flagged with r1+r2, not with PATTERNS_R1
    for t in ("Our domain names for sale", "Strona w przygotowaniu", "Website folgt"):
        assert hit(t, "") is not None
        assert hit(t, "", patterns=pf.PATTERNS_R1) is None
    # r1 results stay the same where r1 matches with the most severe category
    assert hit("", "Diese Domain steht zum Verkauf.", patterns=pf.PATTERNS_R1)[1] == "domain_zum_verkauf"
    assert hit("", "Diese Domain steht zum Verkauf.")[1] == "domain_zum_verkauf"
    assert all(not lab.startswith("r2_") for _, lab, *_ in pf.PATTERNS_R1)
    assert all(lab.startswith("r2_") for _, lab, *_ in pf.PATTERNS_R2)
    assert pf.PATTERNS == pf.PATTERNS_R1 + pf.PATTERNS_R2


def test_scan_r2_rows_carry_r1_result_and_text(tmp_path):
    import gzip
    import io
    import json
    from collections import Counter

    def rec(h, title, content):
        return json.dumps({"host": h, "main": {"url": f"https://{h}", "title": title, "main_content": content}}) + "\n"

    with gzip.open(tmp_path / "imprints_batch000000.jsonl.gz", "wt") as f:
        f.write(rec("a.de", "", "Diese Domain steht zum Verkauf."))  # decided by r1
        f.write(rec("b.de", "Domain im Kundenauftrag registriert", "Hier entsteht eine neue Website."))  # r2 park over r1 constr
    buf = io.StringIO()
    pf.scan_dir(str(tmp_path), set(), buf, Counter())
    rows = {r[0]: r for r in (l.split("\t") for l in buf.getvalue().splitlines()) if r[1] == "F"}
    assert len(rows["a.de"]) == 7 and rows["a.de"][3] == "domain_zum_verkauf"
    b = rows["b.de"]
    assert b[2:4] == ["park", "r2_park_template"] and b[7:9] == ["constr", "under_construction"]
    assert b[10] == str(len("Hier entsteht eine neue Website.")) and b[11].startswith("Hier entsteht")
    p = tmp_path / "scan.tsv"
    p.write_text(buf.getvalue())
    fl, _, _ = pf.load_scan([p])
    assert fl["b.de"][:2] == ("park", "r2_park_template")


def _apply_inputs(tmp_path):
    """x.de: only found host flagged by r2_name_for_sale; y.de: flagged park; z.de: not flagged."""
    ind = tmp_path / "in"
    ind.mkdir()
    (ind / "a.tsv").write_text("x.de\timprint_found\t\ny.de\timprint_found\t\nz.de\timprint_found\t\n")
    (ind / "manifest.tsv").write_text("source\tvm\tdir\tfile\trows\tsha256\tstats\nS1\tv\td\ta.tsv\t0\t0\t\n")
    scan = tmp_path / "scan.tsv"
    scan.write_text(
        "x.de\tF\tsale\tr2_name_for_sale\thttps://x.de/\tt\tx.de steht zum Verkauf\n"
        "y.de\tF\tpark\tr2_park_phrase\thttps://y.de/\tt\tDiese Domain ist reserviert.\n"
    )
    targets = tmp_path / "targets.tsv"
    targets.write_text("target\tclass\n")
    return ind, scan, targets


def _finalize(tmp_path, r2):
    import subprocess
    import sys

    sites = tmp_path / "canonical_sites.txt"
    sites.write_text("x.de\ny.de\nz.de\n")
    cmd = [sys.executable, str(_root / "finalize_r2.py"), "--sites", str(sites), "--r1", str(r2), "--r2", str(r2)]
    subprocess.run(cmd, check=True, capture_output=True)
    return (r2 / "canonical_sites_after_filter.txt").read_text().split()


@pytest.mark.parametrize("flag_only", [False, True])
def test_name_for_sale_flag_only(tmp_path, flag_only):
    ind, scan, targets = _apply_inputs(tmp_path)
    out = tmp_path / "out"
    args = ["apply", "--in", str(ind), "--scan", str(scan), "--targets", str(targets), "--out", str(out)]
    pf.main(args + (["--name-for-sale-flag-only"] if flag_only else []))
    rows = [l.split("\t")[:2] for l in (out / "flagged_sites.tsv").read_text().splitlines()[1:]]
    # x.de is listed in both modes; only its category changes
    assert dict(rows) == {"x.de": "sale_flag" if flag_only else "sale", "y.de": "park"}
    # finalize_r2.py needs no option: sale_flag is kept, sale is dropped
    assert _finalize(tmp_path, out) == (["x.de", "z.de"] if flag_only else ["z.de"])
    rc = (out / "release_count_after_filter.tsv").read_text()
    assert ("flagged_sale_flag_kept\t1" in rc) == flag_only
