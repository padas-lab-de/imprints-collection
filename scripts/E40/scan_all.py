#!/usr/bin/env python3
"""E40: run `parking_filter.py scan DIR TARGETS...` for every dir of the E31 manifest and store the rows.

Usage: scan_all.py --manifest E31_IN/manifest.tsv --targets TARGETS.tsv --out OUTDIR [--local-workers 3]
Writes OUTDIR/<manifest file stem>.scan.tsv per dir and OUTDIR/coverage.tsv (dir, rows, #stats). Resumable
(finished outputs are kept). Remote side is read-only: script from stdin, nothing written on the VM
(`ssh -o BatchMode=yes VM nice -n 19 ionice -c3 python3 - scan DIR T... < parking_filter.py`).
One job per remote VM at a time, VMs in parallel; lorbeer (local) runs --local-workers jobs. ssh options:
BatchMode only.
"""

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL_VM = "lorbeer"


def scan(vm, d, fn, targets):
    script = (HERE / "parking_filter.py").read_bytes()
    base = ["nice", "-n", "19", "ionice", "-c3", "python3", "-", "scan", d, *targets]
    cmd = base if vm == LOCAL_VM else ["ssh", "-o", "BatchMode=yes", vm, *base]
    tmp = fn.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        r = subprocess.run(cmd, input=script, stdout=f, stderr=subprocess.PIPE)
    err = r.stderr.decode(errors="replace").strip().splitlines()
    stats = next((l[7:] for l in err if l.startswith("#stats ")), "")
    if r.returncode != 0 or not stats:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{vm}:{d} rc={r.returncode}: {' | '.join(err[-3:])}")
    tmp.rename(fn)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--local-workers", type=int, default=3)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    targets = [l.split("\t")[0] for l in open(a.targets).read().splitlines()[1:]]
    rows = [l.rstrip("\n").split("\t") for l in open(a.manifest)]
    head, rows = rows[0], [dict(zip(rows[0], r)) for r in rows[1:]]
    jobs = {}
    for r in rows:
        jobs.setdefault(r["vm"], []).append(r)

    def run(r):
        fn = out / (Path(r["file"]).stem + ".scan.tsv")
        if fn.exists():
            return r, "reused", None
        try:
            return r, scan(r["vm"], r["dir"], fn, targets), None
        except Exception as e:
            return r, "", e

    results = []
    with ThreadPoolExecutor(max_workers=sum(a.local_workers if v == LOCAL_VM else 1 for v in jobs)) as ex:
        # local jobs share a pool; remote VMs get one sequential chain each
        def chain(vm):
            return [run(r) for r in jobs[vm]]

        futs = [ex.submit(chain, vm) for vm in jobs if vm != LOCAL_VM]
        futs += [ex.submit(run, r) for r in jobs.get(LOCAL_VM, [])]
        for f in futs:
            x = f.result()
            for r, st, e in x if isinstance(x, list) else [x]:
                print("FAIL" if e else "ok", r["vm"], r["dir"], e or st, file=sys.stderr, flush=True)
                results.append((r, st, e))
    failed = [r["dir"] for r, _, e in results if e]
    with open(out / "coverage.tsv", "w") as f:
        f.write("source\tvm\tdir\tfile\tstatus\tstats\n")
        for r, st, e in results:
            f.write("\t".join([r["source"], r["vm"], r["dir"], r["file"], "FAILED" if e else "ok", str(e or st)]) + "\n")
    print(f"{len(results)} dirs, {len(failed)} failed", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
