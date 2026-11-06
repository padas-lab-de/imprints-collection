"""E41 non-DACH parity lists L1..L4. Usage: build_e41.py STAGE  (excl | l4 | l3 | l1 | l2). Disjoint order L4, L3, L1, L2.
W = repo checkout with scripts/E22/frontier.py (symlink E41/R)."""
import glob, gzip, hashlib, json, os, sys
from collections import Counter
from pathlib import Path
import duckdb

T = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp"
O = T + "/E41"
W = O + "/R"
sys.path.insert(0, W + "/src")
sys.path.insert(0, W + "/scripts/E22")
import frontier as F  # classify(): clean-hosts check_url + E10 platform filter

DACH = ("de", "at", "ch", "li")
ORDER = ["L4", "L3", "L1", "L2"]
stage = sys.argv[1]
con = duckdb.connect(O + "/e41.duckdb")
con.execute("set memory_limit='4GB'; set threads=4; set temp_directory='" + O + "/tmpdb'")
CSV3 = "columns={'a':'varchar','b':'varchar','c':'varchar'},quote='',escape='',null_padding=true,ignore_errors=true"


def nw(h):
    return h[4:] if h.startswith("www.") else h


def tld(h):
    return h.rsplit(".", 1)[-1]


def rd(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f:
        for l in f:
            l = l.strip().lower()
            if l:
                yield l


def write(name, hosts):
    data = "".join(h + "\n" for h in sorted(hosts)).encode()
    Path(f"{O}/{name}.txt").write_bytes(data)
    d = hashlib.sha256(data).hexdigest()
    Path(f"{O}/{name}.txt.sha256").write_text(f"{d}  {name}.txt\n")
    return d


def prev_lists(upto):
    s = set()
    for n in ORDER[: ORDER.index(upto)]:
        s |= {nw(h) for h in rd(f"{O}/{n}.txt")}
    return s


def filt(cands, name):
    """classify (clean-hosts + platform) + blog drop + www dedup + disjoint from earlier lists."""
    info, cache, c, keep = {}, {}, Counter(), set()
    for h in cands:
        r = F.classify(h, set(), cache)
        c[r] += 1
        if r == "new":
            keep.add(h)
    info["classify"] = dict(c)
    keep = {h for h in keep if not (h.endswith(".blogspot.de") or h.endswith(".blog.de"))}
    info["after_blog_drop"] = len(keep)
    keep = {h for h in keep if not (h.startswith("www.") and h[4:] in keep)}
    info["after_www_dedup"] = len(keep)
    prev = prev_lists(name)
    n0 = len(keep)
    keep = {h for h in keep if nw(h) not in prev}
    info["removed_overlap_earlier_lists"] = n0 - len(keep)
    return keep, info


def finish(name, keep, info):
    info["size"] = len(keep)
    info["sha256"] = write(name, keep)
    info["tld_mix"] = dict(Counter(tld(h) for h in keep).most_common(15))
    info["n_tlds"] = len({tld(h) for h in keep})
    json.dump(info, open(f"{O}/counts_{name}.json", "w"), indent=1)
    print(name, json.dumps(info, indent=1))


def inputs():
    return [p for p in sorted(glob.glob(T + "/E31/r3/in/*.tsv")) if not p.endswith("manifest.tsv")]


if stage == "excl":
    files = inputs()
    con.execute("create or replace table crawled(h varchar)")
    for p in files:
        con.execute(
            "insert into crawled select distinct regexp_replace(lower(trim(a)),'^www\\.','') from read_csv(?,delim='\t',header=false,"
            + CSV3 + ") where a<>'host' and trim(a)<>''", [p])
    pil = sorted(glob.glob(T + "/E33/q*_pilot.txt"))
    for p in pil:
        con.execute("insert into crawled select distinct regexp_replace(lower(trim(column0)),'^www\\.','') from read_csv(?,header=false,columns={'column0':'varchar'},quote='',escape='')", [p])
    con.execute("create or replace table crawled2 as select distinct h from crawled")
    con.execute("drop table crawled")
    con.execute("alter table crawled2 rename to crawled")
    n = con.execute("select count(*) from crawled").fetchone()[0]
    json.dump({"files": len(files), "pilots": pil, "crawled_www_collapsed": n}, open(O + "/counts_excl.json", "w"), indent=1)
    print("files", len(files), "crawled", n)

elif stage == "l4":
    # E16 non-DACH imprint_not_found, never imprint_found in any source (www-collapsed).
    # Parity with E37 (T/E37/mk.py): no classify filter, the hosts were fetched in E16 already.
    con.execute("create or replace table st(h varchar, s varchar, e16 boolean)")
    for p in inputs():
        is16 = "_E16_E16_seeds.tsv" in p
        con.execute(
            "insert into st select lower(trim(a)), b, ? from read_csv(?,delim='\t',header=false," + CSV3
            + ") where a<>'host' and (b='imprint_found'" + (" or b='imprint_not_found'" if is16 else "") + ")", [is16, p])
    con.execute("create or replace table found as select distinct regexp_replace(h,'^www\\.','') h from st where s='imprint_found'")
    con.execute("create or replace table c16 as select distinct h from st where e16 and s='imprint_not_found'")
    info = {"e16_not_found_hosts_total": con.execute("select count(*) from c16").fetchone()[0]}
    rows = [r[0] for r in con.execute("select h from c16 where regexp_replace(h,'^www\\.','') not in (select h from found)").fetchall()]
    info["not_found_never_found_all_tlds"] = len(rows)
    seen = {}
    for h in sorted(rows):
        if tld(h) not in DACH:
            seen.setdefault(nw(h), h)
    info["non_dach_never_found"] = len(seen)
    finish("L4", set(seen.values()), info)

elif stage == "l3":
    # method of T/E34/round3/build_r3.py, keeping the non-DACH hosts; plus outlinks of the finished round 3 crawl itself
    snaps = sorted(glob.glob(T + "/E34/round3/snap/*.txt"))
    e35 = "/home/dinzinger/GitHub/imprints-collection-e35/datasets/E34r3/"
    extra = [e35 + "pilot/discovered_external_hosts.txt", e35 + "full/discovered_external_hosts.txt"]
    uniq, lines = set(), 0
    for p in snaps + extra:
        for h in rd(p):
            lines += 1
            uniq.add(h)
    info = {"snap_files": len(snaps), "extra_files": len(extra), "lines": lines, "unique": len(uniq)}
    kf = [W + "/seed_hosts.txt.gz", T + "/e22_hosts.txt", T + "/d29/round2_frontier_rest.txt",
          T + "/round1_frontier_A.txt", T + "/E23/cc_german_candidates.txt", T + "/E25/cc43_dach_new.txt",
          T + "/E26/cc43_dach_rest.txt", T + "/E29/e29_rest.txt", T + "/E30/e30_rest.txt"]
    kf += sorted(glob.glob(T + "/E24/new_hosts_*.txt")) + sorted(glob.glob(T + "/E27/pool_p*.txt"))
    kf += sorted(glob.glob(T + "/E28/p*.txt"))
    kf += [T + f"/E33/pool_q{i}.txt" for i in (1, 3, 4)]  # pool_q2 = L1 itself: L3 comes first in the order
    kf += [T + "/E33/e33_rest.txt", T + "/E37/e37_rest.txt"]
    kf += sorted(glob.glob(T + "/E33/q*_pilot.txt")) + [T + "/E36/pilot/pilot.txt"]
    kf += [T + "/E34/frontier_new_seeds.txt", T + "/E34/e34_rest.txt", T + "/E34/round2/frontier_r2.txt",
           T + "/E34/round2/pilot_r2.txt", T + "/E34/round2/e34r2_rest.txt",
           T + "/E34/round3/frontier_r3.txt", T + "/E34/round3/e34r3_rest.txt", T + "/E34/round3/pilot_r3.txt"]
    con.execute("create or replace table known(h varchar)")
    for p in kf:
        comp = "gzip" if p.endswith(".gz") else "none"
        con.execute("insert into known select distinct regexp_replace(lower(trim(column0)),'^www\\.','') from read_csv(?,delim='\t',header=false,columns={'column0':'varchar'},quote='',escape='',compression=?) where trim(column0)<>''", [p, comp])
    con.execute("create or replace table knownd as select distinct h from known")
    con.execute("drop table known")
    info["known_files"] = [os.path.basename(p) for p in kf]
    info["known_hosts"] = con.execute("select count(*) from knownd").fetchone()[0]
    open(O + "/l3_uniq.txt", "w").write("".join(h + "\n" for h in sorted(uniq)))
    con.execute("create or replace table u as select column0 h from read_csv(?,delim='\t',header=false,columns={'column0':'varchar'},quote='',escape='')", [O + "/l3_uniq.txt"])
    st = {}
    st["crawled"] = con.execute("select count(*) from u where regexp_replace(h,'^www\\.','') in (select h from crawled)").fetchone()[0]
    st["known_list_not_crawled"] = con.execute("select count(*) from u where regexp_replace(h,'^www\\.','') not in (select h from crawled) and regexp_replace(h,'^www\\.','') in (select h from knownd)").fetchone()[0]
    rows = [r[0] for r in con.execute("select h from u where regexp_replace(h,'^www\\.','') not in (select h from crawled) and regexp_replace(h,'^www\\.','') not in (select h from knownd)").fetchall()]
    st["dach_tld_dropped"] = sum(1 for h in rows if tld(h) in DACH)
    rows = [h for h in rows if tld(h) not in DACH]
    info["pre_filter"] = st
    keep, i2 = filt(rows, "L3")
    info.update(i2)
    finish("L3", keep, info)

elif stage == "l1":
    # FineWeb-2 non-DACH = Q2 pool (T/E33/pool_q2.txt) minus crawled; li dropped (non-DACH here excludes li)
    q2 = list(rd(T + "/E33/pool_q2.txt"))
    info = {"q2_pool": len(q2)}
    n = len(q2)
    q2 = [h for h in q2 if tld(h) not in DACH]
    info["dropped_dach_tld_in_q2"] = n - len(q2)
    open(O + "/l1_q2.txt", "w").write("".join(nw(h) + "\n" for h in q2))
    con.execute("create or replace table u as select column0 h from read_csv(?,delim='\t',header=false,columns={'column0':'varchar'},quote='',escape='')", [O + "/l1_q2.txt"])
    cr = {r[0] for r in con.execute("select h from u where h in (select h from crawled)").fetchall()}
    info["removed_crawled"] = len(cr)
    q2 = [h for h in q2 if nw(h) not in cr]
    keep, i2 = filt(q2, "L1")
    info.update(i2)
    finish("L1", keep, info)

elif stage == "l2":
    # HPLT v2 deu_Latn, Internet-Archive-only (collections wide*/survey* only), non-DACH: 1,070 shards (951 E33 + 119 E24) + E24 sample table
    sh = O + "/shards/hplt_*"
    con.execute(f"""create or replace table hp as select h, bool_or(not ia) anyoth from (
        select regexp_replace(host,'^www\\.','') h, (dump='ia') ia from read_parquet('{sh}')
        where host<>'' and regexp_matches(host,'^[a-z0-9._-]+$')) group by 1""")
    info = {"hplt_shards": len(glob.glob(O + "/shards/hplt_*")), "hosts_all_tlds": con.execute("select count(*) from hp").fetchone()[0]}
    info["ia_only_all_tlds"] = con.execute("select count(*) from hp where not anyoth").fetchone()[0]
    rows = [r[0] for r in con.execute("select h from hp where not anyoth and h not in (select h from crawled)").fetchall()]
    info["ia_only_not_crawled"] = len(rows)
    rows = [h for h in rows if tld(h) not in DACH]
    info["ia_only_not_crawled_non_dach"] = len(rows)
    keep, i2 = filt(rows, "L2")
    info.update(i2)
    finish("L2", keep, info)
