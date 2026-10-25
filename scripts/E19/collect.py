#!/usr/bin/env python3
"""E19 recovery list: hosts of the E16 crawl worth retrying from a second IP (D22 A).

Selection rule (applied per host row of a COMPLETE E16 fetch_status_batch*.tsv):
  status == host_not_found  AND  the detail ("https:<reason>;http:<reason>") has a
  retryable reason on at least one scheme.
Retryable reasons: http403, http429, http503, timeout, conn, refused.
Not retryable on their own: dns, ssl, empty, redirects, binary, none, other and
all other http<code> (404, 500, 406, 202, ...). A host with a retryable reason on one
scheme and a non-retryable one on the other is selected (e.g. "https:ssl;http:timeout").
Primary cause (for the counts) by priority: throttle (429/503) > 403 > timeout >
conn/refused; the full set of causes is kept in the list file.
Optional --include-throttled adds hosts with throttled > 0 whose status is not
imprint_found (cause "throttled"); they are counted separately.
The 48 hosts of the Strato gold deferral are written to a separate list and are not
part of the cause counts; recovery_all.txt is the de-duplicated union for the run.

A batch counts only if complete: 25,000 data rows, or for the last batch of the seed
list (needs --seed-file or --total-hosts) the remainder. Files are only read.
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# datasets/ is untracked: use IC_DATA_ROOT, else the nearest parent of the checkout holding datasets/
ROOT = next(
    (p for p in [Path(os.environ.get("IC_DATA_ROOT", REPO)), *REPO.parents] if (p / "datasets" / "E16").is_dir()),
    REPO,
)
BATCH_SIZE = 25_000
COLUMNS = ["host", "status", "detail", "provider", "attempts", "requests", "throttled", "seconds", "end_time"]
RETRYABLE = {
    "http403": "403",
    "http429": "throttle",
    "http503": "throttle",
    "timeout": "timeout",
    "conn": "conn_refused",
    "refused": "conn_refused",
}
PRIORITY = ["throttle", "403", "timeout", "conn_refused"]
BATCH_RE = re.compile(r"fetch_status_batch(\d+)\.tsv$")


def read_rows(path):
    """Data rows of a status TSV as dicts; rows with a wrong column count (a line being written) are skipped."""
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader, None)
        if header != COLUMNS:
            return rows
        for r in reader:
            if len(r) == len(COLUMNS):
                rows.append(dict(zip(COLUMNS, r)))
    return rows


def expected_rows(batch_id, total_hosts=None, batch_size=BATCH_SIZE):
    """Rows a complete batch has: batch_size, or the remainder for the last batch."""
    if total_hosts is None:
        return batch_size
    return min(batch_size, max(total_hosts - batch_id * batch_size, 0))


def is_complete(rows, batch_id, total_hosts=None, batch_size=BATCH_SIZE):
    return len(rows) == expected_rows(batch_id, total_hosts, batch_size)


def causes_of(detail):
    """Set of retryable cause names in a detail string."""
    out = set()
    for part in detail.split(";"):
        reason = part.split(":", 1)[-1].strip()
        if reason in RETRYABLE:
            out.add(RETRYABLE[reason])
    return out


def primary_cause(causes):
    for c in PRIORITY:
        if c in causes:
            return c
    return None


def classify(row, include_throttled=False):
    """(primary_cause, all_causes) of a row, or None when it is not selected."""
    if row["status"] == "host_not_found":
        causes = causes_of(row["detail"])
        if causes:
            return primary_cause(causes), causes
    elif include_throttled and row["status"] != "imprint_found" and row["throttled"] not in ("", "0"):
        return "throttled", {"throttled"}
    return None


def complete_batches(seeds_dir, total_hosts=None, batch_size=BATCH_SIZE):
    """({batch_id: rows} of complete batches, [(batch_id, n_rows, expected)] of skipped ones)."""
    done, skipped = {}, []
    for p in sorted(Path(seeds_dir).glob("fetch_status_batch*.tsv")):
        m = BATCH_RE.search(p.name)
        if not m:
            continue
        bid = int(m.group(1))
        rows = read_rows(p)
        if is_complete(rows, bid, total_hosts, batch_size):
            done[bid] = rows
        else:
            skipped.append((bid, len(rows), expected_rows(bid, total_hosts, batch_size)))
    return done, skipped


def select(batches, include_throttled=False):
    """List of dicts host, cause, causes, provider, batch."""
    out = []
    for bid, rows in sorted(batches.items()):
        for r in rows:
            c = classify(r, include_throttled)
            if c:
                out.append(
                    {
                        "host": r["host"],
                        "cause": c[0],
                        "causes": ",".join(sorted(c[1])),
                        "provider": r["provider"] or "-",
                        "batch": bid,
                    }
                )
    return out


def write_counts(selected, path_cause, path_provider, top=30):
    by_cause = Counter(s["cause"] for s in selected)
    with open(path_cause, "w") as f:
        f.write("cause\thosts\n")
        for k, v in by_cause.most_common():
            f.write(f"{k}\t{v}\n")
        f.write(f"total\t{len(selected)}\n")
    by_prov = Counter((s["provider"], s["cause"]) for s in selected)
    prov_tot = Counter(s["provider"] for s in selected)
    causes = [c for c in PRIORITY + ["throttled"] if c in by_cause]
    with open(path_provider, "w") as f:
        f.write("provider\t" + "\t".join(causes) + "\ttotal\n")
        shown = prov_tot.most_common(top)
        for prov, tot in shown:
            f.write(f"{prov}\t" + "\t".join(str(by_prov[(prov, c)]) for c in causes) + f"\t{tot}\n")
        rest = sum(prov_tot.values()) - sum(t for _, t in shown)
        if rest:
            f.write(f"(other {len(prov_tot) - len(shown)} networks)\t" + "\t" * len(causes) + f"{rest}\n")
    return by_cause, prov_tot


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds-dir", default=str(ROOT / "datasets/E16/seeds"))
    ap.add_argument("--out-dir", default=str(ROOT / "datasets/E19"))
    ap.add_argument("--deferred", default=str(ROOT / "datasets/gold/deferred_strato.txt"))
    ap.add_argument(
        "--seed-file",
        default=str(ROOT / "datasets/E16/seed_hosts_shuffled.txt"),
        help="seed list; its line count fixes the size of the last batch",
    )
    ap.add_argument("--total-hosts", type=int, help="seed list size (instead of --seed-file)")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--include-throttled", action="store_true")
    a = ap.parse_args(argv)

    total = a.total_hosts
    if total is None and Path(a.seed_file).exists():
        with open(a.seed_file, "rb") as f:
            total = sum(1 for line in f if line.strip())
    batches, skipped = complete_batches(a.seeds_dir, total, a.batch_size)
    selected = select(batches, a.include_throttled)

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seen = {}
    for s in selected:
        seen.setdefault(s["host"], s)
    with open(out / "recovery_hosts.tsv", "w") as f:
        f.write("host\tcause\tcauses\tprovider\tbatch\n")
        for s in seen.values():
            f.write("\t".join(str(s[k]) for k in ("host", "cause", "causes", "provider", "batch")) + "\n")
    deferred = []
    if Path(a.deferred).exists():
        deferred = list(dict.fromkeys(l.strip() for l in open(a.deferred) if l.strip()))
    (out / "recovery_hosts.txt").write_text("".join(h + "\n" for h in seen))
    (out / "deferred_strato_hosts.txt").write_text("".join(h + "\n" for h in deferred))
    allh = list(dict.fromkeys(list(seen) + deferred))
    (out / "recovery_all.txt").write_text("".join(h + "\n" for h in allh))
    by_cause, prov_tot = write_counts(selected, out / "counts_by_cause.tsv", out / "counts_by_provider.tsv")
    n_rows = sum(len(r) for r in batches.values())
    (out / "collect_info.txt").write_text(
        f"complete_batches\t{len(batches)}\nhosts_in_complete_batches\t{n_rows}\n"
        f"skipped_incomplete\t{skipped}\ninclude_throttled\t{a.include_throttled}\n"
        f"recovery_hosts\t{len(seen)}\ndeferred_strato\t{len(deferred)}\nrecovery_all\t{len(allh)}\n"
    )

    print(f"complete batches: {len(batches)} ({n_rows} hosts); skipped incomplete: {skipped}")
    for k, v in by_cause.most_common():
        print(f"  {k:14} {v:7} ({v / max(n_rows, 1):.2%} of crawled hosts)")
    print(f"recovery hosts {len(seen)}, deferred Strato {len(deferred)}, union {len(allh)}")
    print(f"top networks: {prov_tot.most_common(5)}")
    print(f"written to {out}")


if __name__ == "__main__":
    sys.exit(main())
