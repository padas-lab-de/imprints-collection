import hashlib
import os  # D47: path constants below can be overridden by env
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp")
def col(h):
    h = h.strip().lower()
    return h[4:] if h.startswith("www.") else h
excl = set()
for q in ("q1", "q2", "q3", "q4"):
    excl |= {col(l) for l in open(f"{T}/E33/{q}_pilot.txt") if l.strip()}
e34 = {col(l) for l in open(f"{T}/E34/frontier_new_seeds.txt") if l.strip()}
out, seen, stats = [], set(), {}
for q in ("q4", "q3", "q1"):
    n = d_p = d_e = 0
    for l in open(f"{T}/E33/pool_{q}.txt"):
        h = col(l)
        if not h or h in seen:
            continue
        n += 1
        if h in excl:
            d_p += 1; continue
        if h in e34:
            d_e += 1; continue
        seen.add(h); out.append(h)
    stats[q] = (n, d_p, d_e)
data = "\n".join(out) + "\n"
open(f"{T}/E33/e33_rest.txt", "w").write(data)
print(stats, "rest", len(out), hashlib.sha256(data.encode()).hexdigest(), "batches", -(-len(out) // 25000))
