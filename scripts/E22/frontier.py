"""E22: round-1 link-expansion frontier from the E16 seed crawl's discovered_external_hosts.txt.

Same rules as scripts/E14/candidates.py (lower/strip, dedupe, clean-hosts check_url, drop seed hosts
exact and www.-variant, platform filter, www/non-www collapse); seeds = the full E16 seed list.
Streams the discovered files; fetched hosts are counted from the fetch_status_batch*.tsv files.

Usage: python frontier.py --seeds SEEDS.txt --input-dir DIR [DIR...] --out-dir OUT
       [--overlap LIST...] [--total-hosts 6560119]
Each input dir holds discovered_external_hosts.txt and fetch_status_batch*.tsv.
Writes OUT/round1_frontier_partial.txt (+ .sha256) and OUT/frontier_stats.json.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from ic.utils.filter_utils import check_url

_E10 = (Path(__file__).resolve().parent.parent / "E10/candidates.py").read_text()
exec(_E10[_E10.index("PLATFORMS = {") : _E10.index("def tld(h):")])  # PLATFORMS, platform()

TLD_GROUPS = ("de", "at", "ch", "com", "eu", "org", "net")


def variants(h):
    return {h[4:]} if h.startswith("www.") else {"www." + h}


def tld_group(h):
    t = h.rsplit(".", 1)[-1]
    return t if t in TLD_GROUPS else "other"


def read_hosts(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            h = line.strip().lower()
            if h:
                yield h


def count_fetched(dirs):
    """Unique hosts over all fetch_status_batch*.tsv (header and partial last line skipped)."""
    hosts, per_file = set(), {}
    for d in dirs:
        for p in sorted(Path(d).glob("fetch_status_batch*.tsv")):
            n = 0
            with open(p, encoding="utf-8") as f:
                next(f, None)
                for line in f:
                    if line.endswith("\n"):
                        hosts.add(line.split("\t", 1)[0].strip().lower())
                        n += 1
            per_file[p.name] = n
    return hosts, per_file


def classify(h, seeds, cache):
    """Return 'bad' (clean-hosts), 'seed', 'platform' or 'new'."""
    r = cache.get(h)
    if r is None:
        if not check_url(h, is_host=True):
            r = "bad"
        elif h in seeds or variants(h) & seeds:
            r = "seed"
        elif platform(h):
            r = "platform"
        else:
            r = "new"
        cache[h] = r
    return r


def heaps_fit(points):
    """Least squares on log U = log c + b log N; points = [(N, U)]."""
    xs = [math.log(n) for n, u in points]
    ys = [math.log(u) for n, u in points]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return math.exp(my - b * mx), b


def build(seeds, dirs, n_checkpoints=10):
    """Return (final candidate set, stats, curves); curves[i] = rarefaction of dirs[i]'s stream."""
    cache = {}
    lines = 0
    seen_new = set()
    curves = []
    for d in dirs:
        p = Path(d) / "discovered_external_hosts.txt"
        total = sum(1 for _ in open(p, "rb"))
        step = max(1, total // n_checkpoints)
        local, c = set(), []
        for i, h in enumerate(read_hosts(p), 1):
            lines += 1
            if classify(h, seeds, cache) == "new":
                local.add(h)
            if i % step == 0:
                c.append((i / total, len(local)))
        curves.append(c)
        seen_new |= local
    cnt = Counter(cache.values())
    final = {h for h in seen_new if not (h.startswith("www.") and h[4:] in seen_new)}
    stats = {
        "lines": lines,
        "unique": len(cache),
        "clean": len(cache) - cnt["bad"],
        "in_seed": cnt["seed"],
        "new_before_platform": cnt["new"] + cnt["platform"],
        "dropped_platforms": cnt["platform"],
        "new_before_www_collapse": len(seen_new),
        "www_collapsed": len(seen_new) - len(final),
        "candidates": len(final),
    }
    return final, stats, curves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--input-dir", nargs="+", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--overlap", nargs="*", default=[])
    ap.add_argument("--total-hosts", type=int, default=6_560_119)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seeds = set(read_hosts(a.seeds))
    fetched, per_file = count_fetched(a.input_dir)
    final, st, curves = build(seeds, a.input_dir)
    st["seed_list_hosts"] = len(seeds)
    st["fetched_hosts"] = len(fetched)
    st["fetched_per_file"] = per_file
    st["new_per_fetched_host"] = len(final) / max(1, len(fetched))
    st["tld_split"] = dict(Counter(tld_group(h) for h in final).most_common())
    # Heaps fit on the first input dir's stream; x = fraction of its lines * its fetched hosts
    f0, _ = count_fetched(a.input_dir[:1])
    pts = [(len(f0) * x, u) for x, u in curves[0] if u > 0]
    if len(pts) >= 3:
        c, b = heaps_fit(pts)
        st["heaps_fit_first_dir"] = {"dir": a.input_dir[0], "c": c, "b": b, "points": pts}
        n = len(fetched)
        st["projection_total_hosts"] = a.total_hosts
        st["projection_linear"] = round(len(final) / n * a.total_hosts)
        st["projection_heaps"] = round(len(final) * (a.total_hosts / n) ** b)
    path = out / "round1_frontier_partial.txt"
    data = "".join(h + "\n" for h in sorted(final)).encode()
    path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    (out / "round1_frontier_partial.txt.sha256").write_text(f"{digest}  {path.name}\n")
    st["sha256"] = digest
    for ov in a.overlap:
        ovs = set(read_hosts(ov))
        st.setdefault("overlap", {})[ov] = {
            "list": len(ovs),
            "in_frontier": len(ovs & final),
            "in_frontier_or_www_variant": sum(1 for h in ovs if h in final or variants(h) & final),
        }
    (out / "frontier_stats.json").write_text(json.dumps(st, indent=1))
    show = {k: v for k, v in st.items() if k not in ("fetched_per_file", "heaps_fit_first_dir")}
    print(json.dumps(show, indent=1))
    if "heaps_fit_first_dir" in st:
        print("heaps b", st["heaps_fit_first_dir"]["b"], "c", st["heaps_fit_first_dir"]["c"])


if __name__ == "__main__":
    main()
