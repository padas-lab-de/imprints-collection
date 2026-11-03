"""E23: German hosts (all TLDs) from Common Crawl URL indexes that we have never crawled.

Per crawl: stream the cc-index Parquet files with DuckDB (columns url_host_name, fetch_status,
content_languages only), group 200 pages by lowercased host, keep hosts with >= 1 page whose
content_languages contains 'deu'. pages200 is counted per file chunk and only for chunks where the
host has a German page (undercount of non-German pages elsewhere). Then diff against the known
hosts (www-collapsed), apply classify() filters from scripts/E22/frontier.py, write outputs.

German host = at least one 200 page whose content_languages starts with 'deu' (primary German).
The loose rule (any 'deu') is reported only as a count.

Usage: PYTHONPATH=src python scripts/E23/cc_candidates.py --out-dir OUT --seeds seed_hosts.txt.gz \
  --known LIST... [--frontier scripts/E22/frontier.py] [--crawls CC-MAIN-2026-43 ...] [--max-crawls 8]
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import time
import urllib.request
from pathlib import Path

import duckdb

BASE = "https://data.commoncrawl.org/"
DACH = ("de", "at", "ch")
CHUNK = 10


def collapse(h):
    """www-collapsed key of a host."""
    h = h.strip().lower()
    return h[4:] if h.startswith("www.") else h


def german_rule(primary, anyd, loose=False):
    return (anyd if loose else primary) > 0


def not_known(keys, known):
    """Keys (already collapsed) not in the known set (already collapsed)."""
    return {k for k in keys if k not in known}


def pick_form(forms):
    """forms: {host_form: pages200}; the most-seen form, ties -> shortest then alphabetical."""
    return sorted(forms, key=lambda f: (-forms[f], len(f), f))[0]


def tld_of(h):
    return h.rsplit(".", 1)[-1]


def crawl_files(crawl):
    u = f"{BASE}crawl-data/{crawl}/cc-index-table.paths.gz"
    txt = gzip.decompress(urllib.request.urlopen(u).read()).decode()
    return [BASE + l.strip() for l in txt.splitlines() if "subset=warc/" in l]


def connect(tmp):
    c = duckdb.connect()
    c.execute("INSTALL httpfs; LOAD httpfs;")
    c.execute(f"SET memory_limit='1.5GB'; SET threads=4; SET temp_directory='{tmp}'")
    return c


def extract(c, crawl, out):
    """Write parquet (h, pages200, pages_deu, pages_anydeu); return (files, compressed bytes of the 3 columns)."""
    files = crawl_files(crawl)
    meta = 0
    c.execute("CREATE OR REPLACE TABLE part (h VARCHAR, p200 BIGINT, pd BIGINT, pa BIGINT)")
    for i in range(0, len(files), CHUNK):
        L = str(files[i : i + CHUNK])
        mq = (
            f"SELECT sum(total_compressed_size) FROM parquet_metadata({L}) WHERE path_in_schema IN "
            "('url_host_name','fetch_status','content_languages')"
        )
        q = f"""INSERT INTO part SELECT lower(url_host_name) h, count(*) p200,
 sum((content_languages LIKE 'deu%')::int) pd, sum((content_languages LIKE '%deu%')::int) pa
 FROM read_parquet({L}) WHERE fetch_status=200 GROUP BY 1 HAVING pa>0"""
        for attempt in range(8):  # CC answers 403/503 under load: back off and retry the chunk
            try:
                m = c.sql(mq).fetchone()[0]
                c.execute(q)
                meta += m
                break
            except duckdb.HTTPException as e:
                print("retry", i, attempt, str(e)[:80], flush=True)
                time.sleep(20 * (attempt + 1))
        else:
            raise RuntimeError(f"chunk {i} failed")
    c.execute(
        f"COPY (SELECT h, sum(p200) pages200, sum(pd) pages_deu, sum(pa) pages_anydeu FROM part GROUP BY 1) "
        f"TO '{out}' (FORMAT parquet)"
    )
    return len(files), meta


def load_known(c, seeds, lists):
    c.execute("CREATE OR REPLACE TABLE known (k VARCHAR)")
    for p in [seeds] + list(lists):
        c.execute(
            f"INSERT INTO known SELECT DISTINCT regexp_replace(lower(trim(column0)),'^www\\.','') FROM "
            f"read_csv('{p}',header=false,columns={{'column0':'VARCHAR'}},delim='\\x01',quote='',escape='')"
        )
    c.execute("CREATE OR REPLACE TABLE known2 AS SELECT DISTINCT k FROM known")
    return c.sql("SELECT count(*) FROM known2").fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--known", nargs="*", default=[])
    ap.add_argument("--frontier", default=str(Path(__file__).resolve().parent.parent / "E22/frontier.py"))
    ap.add_argument("--crawls", nargs="*")
    ap.add_argument("--max-crawls", type=int, default=8)
    ap.add_argument("--stop-frac", type=float, default=0.05)
    a = ap.parse_args()
    out = Path(a.out_dir)
    (out / "per_crawl").mkdir(parents=True, exist_ok=True)
    (out / "tmp").mkdir(exist_ok=True)
    crawls = a.crawls or [
        x["id"] for x in json.load(urllib.request.urlopen("https://index.commoncrawl.org/collinfo.json"))
    ]
    c = connect(out / "tmp")
    nk = load_known(c, a.seeds, a.known)
    print("known collapsed", nk, flush=True)
    used, log = [], []
    for crawl in crawls[: a.max_crawls]:
        pq = out / "per_crawl" / f"{crawl}.parquet"
        t = time.time()
        nf, by = (0, 0)
        if not pq.exists():
            nf, by = extract(c, crawl, pq)
        used.append(crawl)
        c.execute(
            "CREATE OR REPLACE TABLE allc AS "
            + " UNION ALL ".join(
                f"SELECT '{x}' crawl, h, pages200, pages_deu, pages_anydeu FROM '{out}/per_crawl/{x}.parquet'"
                for x in used
            )
        )
        row = {"crawl": crawl, "files": nf, "bytes_read_est": by, "secs": round(time.time() - t)}
        for rule, col in (("primary", "pages_deu"), ("any", "pages_anydeu")):
            row[f"cum_not_known_{rule}"] = c.sql(
                f"SELECT count(DISTINCT regexp_replace(h,'^www\\.','')) FROM allc WHERE {col}>0 AND "
                "regexp_replace(h,'^www\\.','') NOT IN (SELECT k FROM known2)"
            ).fetchone()[0]
        row["german_hosts_primary_this_crawl"] = c.sql(
            f"SELECT count(DISTINCT regexp_replace(h,'^www\\.','')) FROM '{pq}' WHERE pages_deu>0"
        ).fetchone()[0]
        prev = log[-1]["cum_not_known_primary"] if log else 0
        row["marginal_primary"] = row["cum_not_known_primary"] - prev
        log.append(row)
        print(json.dumps(row), flush=True)
        if prev and row["marginal_primary"] < a.stop_frac * row["cum_not_known_primary"]:
            print("stop: marginal below", a.stop_frac, flush=True)
            break
    (out / "crawl_log.json").write_text(json.dumps(log, indent=1))
    finish(c, out, a.frontier)


def finish(c, out, frontier):
    spec = importlib.util.spec_from_file_location("frontier", frontier)
    fr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fr)
    # union over crawls, www-collapsed; host form = the one with most 200 pages
    c.execute(
        """CREATE OR REPLACE TABLE forms AS SELECT regexp_replace(h,'^www\\.','') k, h, sum(pages200) p200,
        sum(pages_deu) pd, sum(pages_anydeu) pa FROM allc GROUP BY 1,2"""
    )
    c.execute(
        """CREATE OR REPLACE TABLE uni AS SELECT k, arg_max(h, p200) host, sum(p200) pages200,
        sum(pd) pages_deu, sum(pa) pages_anydeu FROM forms GROUP BY 1"""
    )
    c.execute(
        "CREATE OR REPLACE TABLE ncr AS SELECT regexp_replace(h,'^www\\.','') k, count(DISTINCT crawl) n_crawls "
        "FROM allc GROUP BY 1"
    )
    rows = c.sql(
        """SELECT u.host, u.pages200, u.pages_deu, u.pages_anydeu, n.n_crawls FROM uni u JOIN ncr n USING (k)
        WHERE u.k NOT IN (SELECT k FROM known2)"""
    ).fetchall()
    cache, keep = {}, []
    drops = {"bad": 0, "platform": 0, "bad_primary": 0, "platform_primary": 0}
    for host, p200, pd, pa, nc in rows:
        r = fr.classify(host, set(), cache)
        if r in ("bad", "platform"):
            drops[r] += 1
            drops[r + "_primary"] += pd > 0
        else:
            keep.append(host)
    kp = out / "tmp" / "kept_hosts.txt"
    kp.write_text("".join(h + "\n" for h in keep))
    c.execute(
        f"""CREATE OR REPLACE TABLE fin AS SELECT u.host, regexp_extract(u.host,'([^.]+)$') tld, n.n_crawls,
        u.pages200, u.pages_deu, u.pages_anydeu, regexp_extract(u.host,'([^.]+)$') IN ('de','at','ch') dach
        FROM uni u JOIN ncr n USING (k) JOIN read_csv('{kp}',header=false,columns={{'h':'VARCHAR'}},delim='\\x01',quote='',escape='') kk
        ON kk.h=u.host"""
    )
    c.execute(f"COPY (SELECT * FROM fin) TO '{out}/cc_german_union_notknown_filtered_anydeu.parquet' (FORMAT parquet)")
    c.execute(
        f"COPY (SELECT host,tld,n_crawls,pages200,pages_deu,dach FROM fin WHERE pages_deu>0 ORDER BY host) "
        f"TO '{out}/cc_german_candidates.parquet' (FORMAT parquet)"
    )
    chosts = [r[0] for r in c.sql("SELECT host FROM fin WHERE pages_deu>0 ORDER BY host").fetchall()]
    data = "".join(h + "\n" for h in chosts).encode()
    (out / "cc_german_candidates.txt").write_bytes(data)
    dg = hashlib.sha256(data).hexdigest()
    (out / "cc_german_candidates.txt.sha256").write_text(f"{dg}  cc_german_candidates.txt\n")
    st = {
        "not_known_any_deu_before_filter": len(rows),
        "not_known_primary_before_filter": sum(1 for r in rows if r[2] > 0),
        "drops": drops,
        "kept_any_deu": len(keep),
        "candidates_primary": len(chosts),
        "candidates_dach": c.sql("SELECT count(*) FROM fin WHERE pages_deu>0 AND dach").fetchone()[0],
        "sha256": dg,
    }
    (out / "final_stats.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
