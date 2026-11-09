import sys
sale = "ts.domainname.de domainmarkt.de fruits.co aftermarket.eu domainmarktplatz.ch aftermarket.pl domainname.de domain-akquise.de namex.de domainkontor24.de domainkompetenz.de domaincatcher.com domain-rebellen.de domainhandel.biz webmax.ch".split()
registry = "denic.de nic.co.de".split()
hosting = "notavailable.goneo.de my.webagentur.at".split()
basis = {
    "ts.domainname.de": "crawled only; redirecting hosts show 'Der Domainname X steht zum Verkauf'",
    "domainmarkt.de": "own page: domain marketplace ('Finden Sie Ihre Premium Domain')",
    "fruits.co": "own page: 'domain sales platform'; redirecting hosts show 'Die Premium-Domain X ist auf fruits.co verfuegbar'",
    "aftermarket.eu": "own page: domain marketplace; hosts show 'Domain-Verkaufsangebot: X'",
    "domainmarktplatz.ch": "own page: Schweizer Domainmarktplatz",
    "aftermarket.pl": "own page: domain marketplace; hosts show 'Domain-Verkaufsangebot: X'",
    "domainname.de": "own page: Domains kaufen und verkaufen; hosts show 'X steht zum Verkauf'",
    "domain-akquise.de": "hosts show 'X - die Domain steht zum Verkauf'",
    "namex.de": "hosts show 'Der Domainname X steht zum Verkauf'",
    "domainkontor24.de": "own page: domain broker; 254 of its hosts flagged",
    "domainkompetenz.de": "own page: domain broker ('Kaufen Sie diese Domain')",
    "domaincatcher.com": "own page: Domainhandel (Domex, Redomain); hosts show 'wurde bei DomainCatcher eingetragen'",
    "domain-rebellen.de": "own page: 'Wir finden die Domain'; 267 hosts flagged",
    "domainhandel.biz": "own page: portfolio of 900 domains for sale",
    "webmax.ch": "own page: 'Sie wurden ueber Ihre Wunschdomain weitergeleitet? Dann koennte diese Domain zum Verkauf stehen'",
    "denic.de": "registry of .de (DENIC eG)",
    "nic.co.de": "registrar/registry of .co.de ('Domain Registrierungsstelle - freie Domains')",
    "notavailable.goneo.de": "hosting/registrar placeholder 'Fuer diese Domain wurden keine Inhalte hinterlegt'",
    "my.webagentur.at": "agency customer-centre login page (135 chars), landing page of unconfigured customer domains",
}
out = ["target\thosts\tcrawled\tclass\tbasis"]
cnt = {}
for l in open("/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E40/targets_raw.tsv").read().splitlines()[1:]:
    t, n, c = l.split("\t")
    cl = "domain_sale" if t in sale else "registry" if t in registry else "hosting_placeholder" if t in hosting else "real"
    cnt[cl] = cnt.get(cl, 0) + 1
    out.append(f"{t}\t{n}\t{c}\t{cl}\t{basis.get(t, 'real organisation or service (own page text and name)')}")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
print(cnt)
