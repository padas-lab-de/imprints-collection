import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from collect import read_rows
from merge_report import load_dir
W = Path(sys.argv[2])
e16 = {}
for r in load_dir(W / "e16_0_49"):
    e16[r["host"]] = r["status"]
rec = {}
for d in ["round1", "round1_s0", "round1_s1", "round1_s2", "round1_s3"]:
    for r in load_dir(W / "r1" / d):
        rec[r["host"]] = r["status"]
found = [h for h, s in rec.items() if s == "imprint_found"]
from collections import Counter
c = Counter(e16.get(h, "not_in_E16_0_49") for h in found)
print("recovery hosts", len(rec), "imprint_found", len(found))
print("E16 status of those:", dict(c))
print("E16 imprint_found in batches 0-49:", sum(1 for s in e16.values() if s == "imprint_found"))
new = [h for h in found if e16.get(h) != "imprint_found"]
print("net new", len(new))
out = W / "round1_net_new_imprint_hosts.txt"
out.write_text("".join(h + "\n" for h in sorted(new)))
