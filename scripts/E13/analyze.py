"""
E13 dry-run analysis: yield, error mix, provider groups, throughput, resources.

Usage: analyze.py <run dir> <fetch log> <resources.tsv> [<E9 output for comparison>]
Reads fetch_status_batch*.tsv (one line per finished host) and the batch outputs.
"""

import collections
import glob
import json
import os
import re
import statistics
import subprocess
import sys

run_dir, log_path, res_path = sys.argv[1:4]

STRATO = {"v4:81.169.145"}  # Strato shared hosting front ends (E5/E8)
IONOS = {"v4:217.160.0"}


def tld(host):
    return host.rsplit(".", 1)[-1].lower()


# --- status log ------------------------------------------------------------
rows = {}
dups = 0
for path in sorted(glob.glob(os.path.join(run_dir, "fetch_status_batch*.tsv"))):
    with open(path, encoding="UTF-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            if not line.endswith("\n"):
                continue
            r = dict(zip(header, line.rstrip("\n").split("\t")))
            if r["host"] in rows:
                dups += 1
            rows[r["host"]] = r
print(f"hosts with status: {len(rows)} (duplicate lines {dups})")

status = collections.Counter(r["status"] for r in rows.values())
print("status:", dict(status))
reach = [r for r in rows.values() if r["status"] in ("imprint_found", "imprint_not_found")]
found = [r for r in reach if r["status"] == "imprint_found"]
de_reach = [r for r in reach if tld(r["host"]) == "de"]
de_found = [r for r in de_reach if r["status"] == "imprint_found"]
print(f"found/reachable: {len(found)}/{len(reach)} = {len(found)/len(reach):.1%}")
print(f".de found/reachable: {len(de_found)}/{len(de_reach)} = {len(de_found)/len(de_reach):.1%}")
for t in ["de", "at", "ch", "com", "net", "org", "eu"]:
    rr = [r for r in reach if tld(r["host"]) == t]
    ff = [r for r in rr if r["status"] == "imprint_found"]
    if rr:
        print(f"  .{t}: {len(ff)}/{len(rr)} = {len(ff)/len(rr):.1%}")

# Cross-check with the output files
n_out = 0
for path in sorted(glob.glob(os.path.join(run_dir, "imprints_batch*.jsonl.gz"))):
    out = subprocess.run(["bash", "-c", f"zcat '{path}' | wc -l"], capture_output=True, text=True)
    n_out += int(out.stdout.strip() or 0)
print(f"records in outputs: {n_out} (reachable by status {len(reach)})")


# --- error mix of hosts without a landing page -------------------------------
def category(detail):
    parts = [p.split(":", 1)[1] for p in detail.split(";") if ":" in p]
    if not parts:
        return "none"
    codes = [p for p in parts if p.startswith("http")]
    for code in ("http429", "http503"):
        if code in codes:
            return code
    if codes:
        c = int(codes[-1][4:])
        return f"http{c // 100}xx" if c not in (403, 404) else f"http{c}"
    if "dns" in parts:
        return "dns"
    if "timeout" in parts:
        return "timeout"
    return parts[-1]


fail = [r for r in rows.values() if r["status"] == "host_not_found"]
mix = collections.Counter(category(r["detail"]) for r in fail)
print(f"\nhost_not_found {len(fail)} ({len(fail)/len(rows):.1%}) by cause:")
for k, v in mix.most_common():
    print(f"  {k}: {v} ({v/len(rows):.2%} of all)")

# --- provider groups ---------------------------------------------------------
groups = collections.defaultdict(list)
for r in rows.values():
    groups[r["provider"] or "-"].append(r)
print(f"\nprovider groups: {len(groups)}")
print("group\thosts\treach\tfound\tthrottled_hosts\tretried\tended_429_503\trequests")
top = sorted(groups.items(), key=lambda kv: -len(kv[1]))[:15]
for g, rs in top:
    rr = [r for r in rs if r["status"] in ("imprint_found", "imprint_not_found")]
    ff = [r for r in rr if r["status"] == "imprint_found"]
    thr = sum(1 for r in rs if int(r["throttled"]) > 0)
    retried = sum(1 for r in rs if int(r["attempts"]) > 1)
    ended = sum(1 for r in rs if r["status"] == "host_not_found" and category(r["detail"]) in ("http429", "http503"))
    reqs = sum(int(r["requests"]) for r in rs)
    print(f"{g}\t{len(rs)}\t{len(rr)}\t{len(ff)}\t{thr}\t{retried}\t{ended}\t{reqs}")

thr_all = [r for r in rows.values() if int(r["throttled"]) > 0]
retried = [r for r in rows.values() if int(r["attempts"]) > 1]
ended = [r for r in fail if category(r["detail"]) in ("http429", "http503")]
print(f"\nhosts with any 429/503: {len(thr_all)}; retried later: {len(retried)}; "
      f"retried and then reachable: {sum(1 for r in retried if r['status'] in ('imprint_found', 'imprint_not_found'))}; "
      f"ended as 429/503 landing failure: {len(ended)}")
print("429/503 landing failures by group:", collections.Counter(r["provider"] for r in ended).most_common(10))
strato = [r for g in STRATO for r in groups.get(g, [])]
s_reach = [r for r in strato if r["status"] in ("imprint_found", "imprint_not_found")]
print(f"Strato 81.169.145/24: {len(strato)} hosts, reachable {len(s_reach)}, "
      f"found {sum(1 for r in s_reach if r['status']=='imprint_found')}, "
      f"hosts with 429/503 {sum(1 for r in strato if int(r['throttled'])>0)}, "
      f"ended 503 {sum(1 for r in strato if r['status']=='host_not_found' and category(r['detail'])=='http503')}")

# --- requests and time per host ------------------------------------------------
reqs = [int(r["requests"]) for r in rows.values()]
print(f"\nrequests per host: mean {statistics.mean(reqs):.2f}; reachable hosts mean "
      f"{statistics.mean(int(r['requests']) for r in reach):.2f}")
secs = [float(r["seconds"]) for r in rows.values()]
print(f"seconds per host: mean {statistics.mean(secs):.1f}, median {statistics.median(secs):.1f}, "
      f"p99 {sorted(secs)[int(len(secs)*0.99)]:.1f}")

# --- throughput over time (end_time of each host) ------------------------------
ends = sorted(int(r["end_time"]) for r in rows.values())
t0 = ends[0]
buckets = collections.Counter((t - t0) // 600 for t in ends)
print("\nhosts finished per 10 min (hosts/min):")
print(" ".join(f"{k*10}:{v/10:.0f}" for k, v in sorted(buckets.items())))

# Progress lines: run segments, limiter wait
prog = []
for line in open(log_path, encoding="UTF-8", errors="replace"):
    m = re.search(r"progress batch (\d+): (\d+)/(\d+) hosts in ([\d.]+) min .* wait ([\d.]+) worker-min", line)
    if m:
        prog.append(tuple(float(x) for x in m.groups()))
stats_lines = re.findall(r"Batch (\d+) statistics \(([\d.]+) min\)", open(log_path, errors="replace").read())
print("batch durations (min):", stats_lines)

# --- resources -----------------------------------------------------------------
cpu, rss, thr, load = [], [], [], []
with open(res_path) as f:
    next(f)
    for line in f:
        t, pid, c, r, n, l, a = line.rstrip("\n").split("\t")
        if pid != "-" and c:
            cpu.append(float(c)); rss.append(int(r)); thr.append(int(n)); load.append(float(l))
if cpu:
    print(f"\nCPU% median {statistics.median(cpu):.0f} p95 {sorted(cpu)[int(len(cpu)*0.95)]:.0f} max {max(cpu):.0f}; "
          f"RSS max {max(rss)} MB; threads max {max(thr)}; load1 median {statistics.median(load):.1f}")

# --- disk ------------------------------------------------------------------------
sizes = collections.Counter()
for path in glob.glob(os.path.join(run_dir, "*")):
    kind = re.sub(r"\d+", "N", os.path.basename(path))
    sizes[kind] += os.path.getsize(path)
print("\ndisk:", {k: f"{v/1e6:.1f} MB" for k, v in sizes.items()})
