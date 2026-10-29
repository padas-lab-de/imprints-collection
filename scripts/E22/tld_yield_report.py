# Sum the tld_yield.py JSON files in DIR (E16 baseline file named e16*.json). usage: python3 scripts/E22/tld_yield_report.py DIR
import glob, json, sys
from collections import defaultdict

D = sys.argv[1]


def agg(fs):
    c = defaultdict(lambda: [0] * 5)
    for f in fs:
        for k, v in json.load(open(f)).items():
            for i in range(5):
                c[k][i] += v[i]
    return c


def show(c, name, n=14):
    T = [sum(v[i] for v in c.values()) for i in range(5)]
    print(f"\n{name}: hosts {T[0]:,} imprint {T[1]:,} ({T[1]/T[0]:.1%}) nxdomain {T[2]/T[0]:.1%} "
          f"deu-imprint {T[3]:,} ({T[3]/T[0]:.2%} of hosts) plz {T[4]:,}")
    print(f"{'tld':8}{'hosts':>9}{'share':>7}{'impr%':>7}{'deu%':>7}{'plz%':>7}{'deu n':>8}{'deu share':>10}")
    for k, v in sorted(c.items(), key=lambda x: -x[1][3])[:n]:
        print(f"{k:8}{v[0]:>9,}{v[0]/T[0]:>7.1%}{v[1]/v[0]:>7.1%}{v[3]/v[0]:>7.2%}{v[4]/v[0]:>7.2%}"
              f"{v[3]:>8,}{v[3]/max(T[3],1):>10.1%}")
    nd = {k: v for k, v in c.items() if k not in ("de", "at", "ch")}
    N = [sum(v[i] for v in nd.values()) for i in range(5)]
    print(f"non-DACH TLDs: {N[0]/T[0]:.1%} of hosts, {N[1]/max(T[1],1):.1%} of imprints, "
          f"{N[3]/max(T[3],1):.1%} of deu imprints, {N[4]/max(T[4],1):.1%} of plz imprints")


show(agg([f for f in glob.glob(f"{D}/*.json") if "e16" not in f]), "E22 depth-1 (5 VMs)")
show(agg([f"{D}/e16base.json"]), "E16 seeds baseline (aspe batches 0-2)", 8)
