import json, sys
sys.path.insert(0, '/home/dinzinger/.claude/jobs/4110e328/tmp/adjud')
from common import ROOT, load_schema, path, children, load_raw

poi, wz, wzt = load_schema()
PAR = {'poi': poi, 'wz': wz}
CONF = {'low': 0, 'medium': 1, 'high': 2}

# Disagreements: host -> (choice, main, extras, confidence, reason)
DIS = {'poi': {
 'arts.columbia.edu': ('A', 'Universität', ['Kunstschule', 'Hochschule und Universität'], 'high', 'University school of the arts; Universität as for WZ 85.40.1.'),
 'daruweb.org': ('B', 'Gemeinschaft und Regierung', ['Organisation', 'Kulturzentrum'], 'low', 'R4: online language/culture site, no leaf fits; topic root.'),
 'externals.io': ('B', 'Softwareunternehmen', ['IT-Service'], 'low', 'R4: online reader for the PHP mailing list; nearest leaf is software.'),
 'magicmonday.ch': ('A', 'Unterhaltungsveranstaltung', ['Wohltätigkeit'], 'medium', 'R2: the site presents a charity dinner event series.'),
 'sippd.conservatoriodimusica.it': ('B', 'Hochschule und Universität', ['Musikschule'], 'medium', 'Conservatorio is a higher arts school (Kunsthochschule).'),
 'wintergarten-ratgeber.net': ('B', 'Heimwerkerservice', ['Herausgeber', 'Deck- und Terrassenunternehmer'], 'low', 'R4: online advice portal; nearest topic leaf is home improvement.'),
 'www.besen-zum-kuahstall.de': ('B', 'Weinbar', ['Weingut', 'Deutsches Restaurant'], 'medium', 'R2: homepage leads with the Besen wine tavern; winery as extra.'),
 'www.bienenbleibe.com': ('A', 'Land- und Forstwirtschaftsdienst', ['Bauernhof'], 'medium', 'Renting out bee colonies with care is an agricultural service.'),
 'www.carpartbrand.de': ('B', 'Großhändler', ['Autoteile und Zubehör'], 'medium', 'B2B parts distribution; matches WZ wholesale 46.72.0.'),
 'www.eiposcert.de': ('B', 'Unternehmensdienst', [], 'medium', 'Certification body; a fitting leaf exists, so not the root.'),
 'www.florafelt.de': ('B', 'Gartencenter', ['Hersteller'], 'medium', 'R2: the site presents a garden-products shop; maker as extra.'),
 'www.haustueren-kinge.de': ('A', 'Auftragnehmer für Türen und Fenster', ['Baubedarfsgeschäft'], 'medium', 'Text names own fitters (Eigene Monteure); door contractor.'),
 'www.heckelbassoons.info': ('B', 'Musikladen', ['Herausgeber', 'Kunst und Unterhaltung'], 'low', 'R4: hobby bassoon database with instruments for sale; nearest leaf.'),
 'www.latein-online.net': ('B', 'Nachhilfeservice', ['Sprachschule', 'Ausbildung'], 'low', 'R3/R4: private Latin learning site; nearest leaf is tutoring.'),
 'www.luftbilder-von-deutschland.de': ('B', 'Fotograf', ['Fotoservice'], 'low', 'R4: online aerial-photo portal; topic leaf preferred over root.'),
 'www.mueller-thurgau-preis.de': ('A', 'Anderes Ereignis', ['Organisation'], 'medium', 'R2: the site presents the wine competition, not the association.'),
 'www.nachtwei.de': ('A', 'Gemeinschaft und Regierung', ['Organisation', 'Herausgeber'], 'low', 'R3/R4: personal politics publication site; no leaf fits, topic root.'),
 'www.purux-pool.de': ('A', 'Hersteller von Chemikalien und Gasen', ['Schwimmbadbedarfsgeschäft'], 'medium', 'Brand site of the manufacturer; matches WZ 20.59.9.'),
 'www.stephanh.de': ('B', 'Sport und Freizeit', ['Touristische Informationen und Service', 'Fotograf'], 'low', 'R3: private leisure homepage, mixed topic; topic root.'),
 'www.training-for-pets.com': ('A', 'Haustierservice', ['Tierbetreuung und Tierpension'], 'medium', 'Counselling, training and boarding; general pet-service leaf.'),
 'www.vom-allenbach.de': ('A', 'Kasino', [], 'low', 'R1: hijacked, but content (casino review) is coherent.'),
}, 'wz': {
 'blog.barcamps.eu': ('B', '58.29.0', ['63.10.9', '94.99.9'], 'low', 'Own hosted open-source tool; as for other SaaS lines (58.29.0).'),
 'cpg-hh.de': ('B', '85.31', ['85.31.2', '85.31.1'], 'high', 'R6: Gymnasium spans Sek I and II; stop at 85.31.'),
 'fulda.pneumatici100.it': ('B', '46.72.0', ['46.18.2'], 'medium', 'B2B tyre wholesale; matches POI Großhändler.'),
 'gothe-edelstahl.de': ('B', '24.20', ['24.20.1', '24.20.3'], 'medium', 'R6: tubes and fittings both lead; text does not decide.'),
 'gutschein.vdu-furtwangen.de': ('A', '82.99.9', ['94.11.0'], 'medium', 'R2: site presents a gift-voucher service; association as extra.'),
 'hellmuth-scheunemann.de': ('A', '98.20.0', ['90.12.0'], 'low', 'R3: private family memorial site for a deceased painter.'),
 'leipziger-muenzhandlung.de': ('A', '47.92.1', ['47.69.9'], 'medium', 'Site puts the coin auctions first; shop as extra.'),
 'live.nordbayern-wetter.info': ('A', '98.20.0', ['74.99.9', '63.10.9'], 'low', 'R3: private hobby weather station.'),
 'matthiasheil.de': ('B', '85.31', ['98.20.0'], 'low', 'R2 over R3: page presents his Gymnasium teaching; R6 stop at 85.31.'),
 'portal-ow.vsz.ch': ('B', '84.24.0', ['71.20.0'], 'medium', 'Vehicle registration office; keyword Kraftfahrzeugzulassungsstellen in 84.24.0.'),
 'sippd.conservatoriodimusica.it': ('B', '85.40.1', ['85.52.0'], 'medium', '85.40.1 includes Kunsthochschulen; conservatorio fits.'),
 'wiki.k10plus.de': ('B', '91.11.0', ['63.10.1'], 'low', 'Library network wiki; matches agreed POI Bibliothek.'),
 'www.besen-zum-kuahstall.de': ('B', '56.30.1', ['11.02.0', '01.21.0'], 'medium', 'R2: Besen tavern leads; R7: winery 11.02.0 + 01.21.0 as extras.'),
 'www.dkbav.de': ('A', '69.10.3', ['70.20.0', '66.29.0'], 'medium', 'Rentenberater named; keyword Rentenberatung in 69.10.3.'),
 'www.foerderverein-wendepunkt-arnsberg.de': ('A', '88.99.9', ['94.99.9'], 'medium', 'Projects for refugees and seniors; keywords in 88.99.9.'),
 'www.luftbilder-von-deutschland.de': ('A', '63.91.0', ['58.19.0'], 'low', 'Page is mostly link lists to aerial-photo sources.'),
 'www.mueller-thurgau-preis.de': ('A', '82.30.0', ['94.11.0'], 'medium', 'R2: site presents the competition (event); association as extra.'),
 'www.raiffeisendruckerei.de': ('A', '26.11.9', ['18.12.0'], 'medium', 'Makes debit/credit chip cards; keyword Multifunktionskreditkarten in 26.11.9.'),
 'www.technodrive.com': ('A', '27.11.2', ['27.11.1', '26.51.1'], 'medium', 'Core product is stepping-motor drivers (Stromrichter).'),
 'www.vom-allenbach.de': ('A', '58.19.0', ['92.00.3'], 'low', 'R1: hijacked, coherent casino-review content (publishing).'),
 'www.zeit-stiftung.de': ('B', '94.99', ['94.99.1', '94.99.2'], 'medium', 'R6: science/education and culture both; text does not decide.'),
}}

# Rule changes on agreed lines: host -> dict of overrides + rule tag
RULE = {'poi': {
 'thunderalleyspeedpark.com': dict(confidence='low', note='hijacked; current content is online slot gambling', rule='R1'),
 'extravegant.de': dict(confidence='low', rule='R3'),
 'peisker-ranch.de': dict(confidence='low', rule='R3'),
}, 'wz': {
 'ddhaider.at': dict(main='11.02.0', extra=['01.21.0', '55.20.2'], rule='R7'),
 'thunderalleyspeedpark.com': dict(confidence='low', note='hijacked; current content is online slot gambling', rule='R1'),
 'peisker-ranch.de': dict(main='98.20.0', extra=['85.51.0'], confidence='low', rule='R3'),
}}

ONLINE_ONLY = set('''externals.io www.dealabs.com philippinenforum sex-in-frauenfeld sex-in-neuss gesundheit-ratgeber
mussgrillen.de extravegant.de religie.wiara.pl wintergarten-ratgeber.net www.luftbilder-von-deutschland.de
www.heckelbassoons.info www.latein-online.net www.nachtwei.de www.stephanh.de sffaudio contrax.app blog.barcamps.eu
bayern.moose-deutschland.de live.nordbayern-wetter.info hellmuth-scheunemann.de daruweb.org www.vom-allenbach.de
thunderalleyspeedpark.com www.martin-riedlingen.de yo.ceramic.school school.the-skill.io'''.split())

def single_child_leaf(schema, code):
    if schema != 'wz' or code is None: return code
    ch = children(wz)
    while code in ch and len(ch[code]) == 1:
        code = ch[code][0]
    return code

def clean_extras(schema, main, extras):
    anc = set(path(schema, PAR[schema], main))  # includes main
    out = []
    for e in extras:
        e = single_child_leaf(schema, e)
        if e in anc or e in out or e not in PAR[schema]: continue
        out.append(e)
    return out[:2]

def build(schema):
    A, B = load_raw('A', schema), load_raw('B', schema)
    hosts = [l.strip() for l in open(f'{ROOT}/results/E49/dev_hosts.txt') if l.strip()]
    oo_hosts = {h for h in hosts for k in ONLINE_ONLY if h == k or k in h}
    stats = {'A': 0, 'B': 0, 'new': 0, 'rule': 0, 'agree': 0}
    rows, table = [], []
    for h in hosts:
        a, b = A[h], B[h]
        agree = a['main'] == b['main']
        if not agree:
            ch, main, ex, conf, reason = DIS[schema][h]
            note = f'adjudicated: {ch}; {reason}'
            if ch == 'A' and main != a['main'] or ch == 'B' and main != b['main']:
                raise SystemExit(f'{h}: choice {ch} does not match main {main}')
            stats[ch] += 1
            table.append((h, a['main'], b['main'], main, ch, reason))
        else:
            stats['agree'] += 1
            main = a['main']
            ex = [e for e in a['extra'] if e in b['extra']] + a['extra'] + b['extra']
            conf = min(a['confidence'], b['confidence'], key=lambda c: CONF[c])
            note = a['note'] or b['note']
            r = RULE[schema].get(h)
            if r:
                main = r.get('main', main); ex = r.get('extra', ex); conf = r.get('confidence', conf)
                note = f"adjudicated: new; {r['rule']}" + (f"; {r['note']}" if 'note' in r else '') + f"; was: {a['main']}"
        main2 = single_child_leaf(schema, main)
        ex2 = clean_extras(schema, main2, ex)
        if agree and not RULE[schema].get(h):
            raw_ex = list(dict.fromkeys(ex))[:2]
            if ex2 != raw_ex and (len(set(ex) - set(ex2)) > 0 and any(e in set(path(schema, PAR[schema], main2)) for e in ex)):
                note = f'adjudicated: new; R5 extra removed; ' + (note or '')
                RULE[schema][h] = {'rule': 'R5'}
        if agree and RULE[schema].get(h): stats['rule'] += 1
        if main is None: ex2 = []
        row = dict(host=h, schema=schema, main=main2, extra=ex2, path=path(schema, PAR[schema], main2),
                   confidence=conf, note=note, agree_ab=agree)
        if schema == 'poi': row['online_only'] = h in oo_hosts
        rows.append(row)
    with open(f'{ROOT}/results/E49/refs/{schema}.jsonl', 'w') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return stats, table, rows

if __name__ == '__main__':
    for s in ('poi', 'wz'):
        st, tab, rows = build(s)
        print(s, st, 'rule-changed:', sorted(RULE[s]))
        print(s, 'online_only true:', sorted(r['host'] for r in rows if r.get('online_only')))
        json.dump(tab, open(f'/home/dinzinger/.claude/jobs/4110e328/tmp/adjud/table_{s}.json', 'w'), ensure_ascii=False)
