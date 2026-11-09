import os  # D47: path constants below can be overridden by env
T = os.environ.get("T", "/home/dinzinger/.claude/jobs/cfd8c2d0/tmp/E34")
pilot = {l.strip() for l in open(f"{T}/pilot.txt") if l.strip()}
rest = [l.strip() for l in open(f"{T}/frontier_new_seeds.txt") if l.strip() and l.strip() not in pilot]
open(f"{T}/e34_rest.txt", "w").write("\n".join(rest) + "\n")
print("pilot", len(pilot), "rest", len(rest))
