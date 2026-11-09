"""E43 (HPLT rest, IA-only) and E44 (FineWeb-2 dialects) pools + 5,000-host pilots, all TLDs.
Usage: build_e43e44.py e44 | e43.  Order: E44 first, E43 is disjoint from E44.
Exclusion: crawled hosts (T/E31/r3/in/*.tsv col 1 + E33 pilots, www-collapsed; table `crawled` of T/E41/e41.duckdb)
plus the E41 lists L1..L4. Filters as build_e41.py: frontier.classify (clean-hosts + platform), blogspot.de/blog.de drop, www dedup."""
import glob, hashlib, json, random, sys
from collections import Counter
from pathlib import Path
import duckdb

T = "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp"
O = T + "/E43"
O44 = T + "/E44"
W = T + "/E41/R"
sys.path.insert(0, W + "/src")
sys.path.insert(0, W + "/scripts/E22")
import frontier as F

DACH = ("de", "at", "ch", "li")
stage = sys.argv[1]


def nw(h):
    return h[4:] if h.startswith("www.") else h


def tld(h):
    return h.rsplit(".", 1)[-1]


def rd(p):
    with open(p, encoding="utf-8") as f:
        for l in f:
            l = l.strip().lower()
            if l:
                yield l


def write(path, hosts):
    data = "".join(h + "\n" for h in sorted(hosts)).encode()
    Path(path).write_bytes(data)
    d = hashlib.sha256(data).hexdigest()
    Path(path + ".sha256").write_text(f"{d}  {Path(path).name}\n")
    return d


def excluded(extra_lists):
    con = duckdb.connect(T + "/E41/e41.duckdb", read_only=True)
    ex = {r[0] for r in con.execute("select h from crawled").fetchall()}
    n_crawled = len(ex)
    l = set()
    for i in (1, 2, 3, 4):
        l |= {nw(h) for h in rd(f"{T}/E41/L{i}.txt")}
    e = set(ex) | l
    x = set()
    for p in extra_lists:
        x |= {nw(h) for h in rd(p)}
    return e | x, {"crawled_www_collapsed": n_crawled, "e41_lists_L1_L4": len(l), "excl_total": len(e | x)}


def filt(cands, excl, info):
    """cands: iterable of hosts (www-collapsed or not)."""
    cands = set(cands)
    info["candidates"] = len(cands)
    cands = {h for h in cands if nw(h) not in excl}
    info["after_excl_crawled_E41"] = len(cands)
    c, cache, keep = Counter(), {}, set()
    for h in sorted(cands):
        r = F.classify(h, set(), cache)
        c[r] += 1
        if r == "new":
            keep.add(h)
    info["classify"] = dict(c)
    info["after_classify"] = len(keep)
    keep = {h for h in keep if not (h.endswith(".blogspot.de") or h.endswith(".blog.de"))}
    info["after_blog_drop"] = len(keep)
    keep = {h for h in keep if not (h.startswith("www.") and h[4:] in keep)}
    info["after_www_dedup"] = len(keep)
    return keep


def finish(name, outdir, keep, info):
    info["size"] = len(keep)
    info["sha256"] = write(f"{outdir}/pool_{name}.txt", keep)
    info["tld_mix_top15"] = dict(Counter(tld(h) for h in keep).most_common(15))
    info["n_tlds"] = len({tld(h) for h in keep})
    info["dach_tld_share"] = round(sum(1 for h in keep if tld(h) in DACH) / max(1, len(keep)), 4)
    pil = sorted(random.Random(42).sample(sorted(keep), min(5000, len(keep))))
    info["pilot_size"] = len(pil)
    info["pilot_sha256"] = write(f"{outdir}/pilot_{name}.txt", pil)
    info["pilot_dach_tld_share"] = round(sum(1 for h in pil if tld(h) in DACH) / max(1, len(pil)), 4)
    json.dump(info, open(f"{outdir}/counts_{name}.json", "w"), indent=1)
    print(name, json.dumps(info, indent=1))


if stage == "e44":
    excl, info = excluded([])
    keep = filt(rd(T + "/E24/new_hosts_fw2_dialects.txt"), excl, info)
    finish("E44", O44, keep, info)
elif stage == "e43":
    excl, info = excluded([O44 + "/pool_E44.txt"])
    info["e44_pool_excluded"] = True
    con = duckdb.connect(O + "/e43.duckdb")
    con.execute("set memory_limit='3GB'; set threads=3; set temp_directory='" + O + "/tmpdb'")
    sh = O + "/shards/hplt_*"
    n_sh = len(glob.glob(sh))
    con.execute(f"""create or replace table hp as select h, bool_or(not ia) anyoth from (
        select regexp_replace(host,'^www\\.','') h, (dump='ia') ia from read_parquet('{sh}')
        where host<>'' and regexp_matches(host,'^[a-z0-9._-]+$')) group by 1""")
    info["hplt_shards"] = n_sh
    info["hosts_all"] = con.execute("select count(*) from hp").fetchone()[0]
    rows = [r[0] for r in con.execute("select h from hp where not anyoth").fetchall()]
    info["ia_only"] = len(rows)
    keep = filt(rows, excl, info)
    finish("E43", O, keep, info)
