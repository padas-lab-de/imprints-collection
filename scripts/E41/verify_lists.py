"""Check L1..L4: sizes, no www.-pairs, no DACH TLD, pairwise disjoint (www-collapsed), none crawled (L1-L3)."""
import duckdb

O = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E41/"
c = duckdb.connect(O + "e41.duckdb", read_only=True)
nw = lambda h: h[4:] if h.startswith("www.") else h
L = {n: [l.strip().lower() for l in open(O + n + ".txt") if l.strip()] for n in ["L4", "L3", "L1", "L2"]}
for n, v in L.items():
    col = {nw(h) for h in v}
    print(n, len(v), "distinct collapsed", len(col), "www-prefixed", sum(h.startswith("www.") for h in v),
          "DACH tld", sum(h.rsplit(".", 1)[-1] in ("li", "de", "at", "ch") for h in v))
ns = list(L)
for i in range(4):
    for j in range(i + 1, 4):
        print("overlap", ns[i], ns[j], len({nw(h) for h in L[ns[i]]} & {nw(h) for h in L[ns[j]]}))
for n in ["L3", "L1", "L2"]:
    open(O + "_z.txt", "w").write("".join(nw(h) + "\n" for h in L[n]))
    r = c.execute("select count(*) from read_csv(?,header=false,columns={'a':'varchar'},delim='\t',quote='',escape='') where a in (select h from crawled)", [O + "_z.txt"]).fetchone()
    print(n, "already crawled", r[0])
