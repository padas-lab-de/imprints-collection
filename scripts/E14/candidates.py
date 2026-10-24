"""E14: build the round-k candidate list from a round's discovered_external_hosts.txt.

Same rules as scripts/E10/candidates.py (lower/strip, dedupe, clean-hosts check_url, drop seed hosts
exact and www.-variant, platform filter, www/non-www collapse) plus: drop hosts already fetched in
earlier rounds (exact and www.-variant). Platform table is taken from the E10 script source.
Usage: python candidates.py DISCOVERED OUT_DIR SAMPLE_N EARLIER_CANDIDATE_FILE...
Writes OUT_DIR/candidate_hosts.txt (all), OUT_DIR/fetch_hosts.txt (all if <= ~20k, else a
random.seed(20261023) sample of SAMPLE_N) and OUT_DIR/stats.json.
"""
import gzip
import json
import random
import sys
from pathlib import Path

from ic.utils.filter_utils import check_url

R = Path("/home/dinzinger/GitHub/imprints-collection")
src = (Path(__file__).resolve().parent.parent / "E10/candidates.py").read_text()
a = src.index("PLATFORMS = {")
b = src.index("def tld(h):")
exec(src[a:b])  # defines PLATFORMS, platform()


def variants(h):
    return {h[4:]} if h.startswith("www.") else {"www." + h}


disc, out, sample_n = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
earlier = set()
for p in sys.argv[4:]:
    earlier |= {l.strip().lower() for l in open(p) if l.strip()}
out.mkdir(parents=True, exist_ok=True)
with gzip.open(R / "seed_hosts.txt.gz", "rt", encoding="utf-8") as f:
    seeds = {l.strip().lower() for l in f if l.strip()}
lines = [l.strip().lower() for l in disc.read_text(encoding="utf-8").splitlines() if l.strip()]
st = {"lines": len(lines), "unique": len(set(lines))}
clean = {h for h in set(lines) if check_url(h, is_host=True)}
st["clean"] = len(clean)
in_seed = {h for h in clean if h in seeds or variants(h) & seeds}
in_earlier = {h for h in clean - in_seed if h in earlier or variants(h) & earlier}
new = clean - in_seed - in_earlier
st["in_seed"] = len(in_seed)
st["already_fetched_earlier_rounds"] = len(in_earlier)
st["new"] = len(new)
keep = {h for h in new if not platform(h)}
st["dropped_platforms"] = len(new) - len(keep)
final = {h for h in keep if not (h.startswith("www.") and h[4:] in keep)}
st["www_collapsed"] = len(keep) - len(final)
st["candidates"] = len(final)
fin = sorted(final)
if len(fin) <= 20500:
    fetch = fin
else:
    random.seed(20261023)
    fetch = sorted(random.sample(fin, sample_n))
st["to_fetch"] = len(fetch)
(out / "candidate_hosts.txt").write_text("\n".join(fin) + "\n")
(out / "fetch_hosts.txt").write_text("\n".join(fetch) + "\n")
(out / "stats.json").write_text(json.dumps(st, indent=1))
print(json.dumps(st, indent=1))
