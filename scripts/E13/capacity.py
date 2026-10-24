"""E13: per-group capacity under the limiter, tail cost per batch, RSS over time."""

import collections
import glob
import statistics
import sys

run_dir, res_path = sys.argv[1:3]
CAP = 4
rows = []
for path in sorted(glob.glob(f"{run_dir}/fetch_status_batch*.tsv")):
    with open(path) as f:
        header = f.readline().rstrip("\n").split("\t")
        b = int(path[-10:-4])
        for line in f:
            r = dict(zip(header, line.rstrip("\n").split("\t")))
            r["batch"] = b
            rows.append(r)
n = len(rows)
for g, name in [("v4:217.160.0", "IONOS"), ("v4:81.169.145", "Strato")]:
    rs = [r for r in rows if r["provider"] == g]
    s = statistics.mean(float(r["seconds"]) for r in rs)
    req = statistics.mean(int(r["requests"]) for r in rs)
    cap = CAP / s * 60
    print(f"{name} {g}: {len(rs)} hosts ({len(rs)/n:.1%}), {s:.2f} s/host, {req:.2f} req/host, "
          f"capacity at {CAP} in flight {cap:.0f} hosts/min ({cap*req/60:.1f} req/s)")

# Per batch: time to 95% of hosts vs. full batch, and what the tail consists of
for b in sorted({r["batch"] for r in rows}):
    rs = sorted((int(r["end_time"]), r["provider"]) for r in rows if r["batch"] == b)
    t0 = min(t for t, _ in rs)
    t95 = rs[int(len(rs) * 0.95)][0]
    tail = collections.Counter(p for t, p in rs if t > t95)
    print(f"batch {b}: 95% done after {(t95-t0)/60:.1f} min, all after {(rs[-1][0]-t0)/60:.1f} min; "
          f"last 5% by group {tail.most_common(3)}")

rss = collections.defaultdict(int)
with open(res_path) as f:
    next(f)
    t0 = None
    for line in f:
        t, pid, c, r, *_ = line.split("\t")
        if pid == "-":
            continue
        t0 = t0 or int(t)
        k = (int(t) - t0) // 1800 * 30
        rss[k] = max(rss[k], int(r))
print("max RSS MB per 30 min:", dict(sorted(rss.items())))
