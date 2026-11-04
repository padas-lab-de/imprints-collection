#!/usr/bin/env python3
"""E31: run scripts/E31/extract.py on every VM for every dir in sources.tsv and store compact TSVs.

Usage: pull.py --out OUTDIR [--sources sources.tsv] [--only-source E29,E30] [--only-vm abelie]
Writes OUTDIR/<vm>_<source>_<sub>.tsv (host, status, redirect target host) per dir and
OUTDIR/manifest.tsv (source, vm, dir, file, rows, sha256, stats), in sources.tsv order (that order is the
last-row order inside a source). Remote side is read-only: `ssh VM nice -n 19 python3 - DIR < extract.py`
(script from stdin, nothing written on the VM). lorbeer (this machine) runs locally. One job per VM at a
time, VMs in parallel. ssh options: BatchMode only; host-key options are never touched.
"""

import argparse
import hashlib
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL_VM = "lorbeer"


def stats_from_tsv(fn):
    """Stats recomputed from a finished TSV (used for reused files; jsonl diagnostics are not available)."""
    rows = found = with_url = 0
    with open(fn, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            rows += 1
            if c[1] == "imprint_found":
                found += 1
                with_url += bool(c[2])
    return f"files=? rows={rows} found={found} with_url={with_url} no_record={found - with_url} reused=1"


def extract(vm, d, fn):
    """Run extract.py on dir d of vm (stdin = script), write fn. Returns the #stats text."""
    script = (HERE / "extract.py").read_bytes()
    if vm == LOCAL_VM:
        cmd = ["nice", "-n", "19", "python3", "-", d]
    else:
        cmd = ["ssh", "-o", "BatchMode=yes", vm, "nice", "-n", "19", "python3", "-", d]
    tmp = fn.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        r = subprocess.run(cmd, input=script, stdout=f, stderr=subprocess.PIPE)
    err = r.stderr.decode(errors="replace").strip().splitlines()
    stats = next((l[7:] for l in err if l.startswith("#stats ")), "")
    if r.returncode != 0 or not stats:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{vm}:{d} failed rc={r.returncode}: {' | '.join(err[-3:])}")
    tmp.rename(fn)
    return stats


def run_one(vm, src, tree, sub, out, reuse=()):
    d = f"/home/dinzinger/{tree}/datasets/{sub}"
    fn = out / f"{vm}_{src}_{sub.replace('/', '_')}.tsv"
    for rd in reuse:  # finished file of an earlier run: take it instead of extracting again
        old = Path(rd) / fn.name
        if old.exists() and not fn.exists():
            old.rename(fn)
            stats = stats_from_tsv(fn)
            break
    else:
        stats = stats_from_tsv(fn) if (fn.exists() and reuse) else extract(vm, d, fn)
    h = hashlib.sha256()
    n = 0
    with open(fn, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += chunk.count(b"\n")
    return [src, vm, d, fn.name, str(n), h.hexdigest(), stats]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sources", default=str(HERE / "sources.tsv"))
    ap.add_argument("--only-source")
    ap.add_argument("--only-vm")
    ap.add_argument("--reuse", action="append", default=[], help="dir with finished TSVs of an earlier run (moved in)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = [l.rstrip("\n").split("\t") for l in open(a.sources)][1:]
    if a.only_source:
        rows = [r for r in rows if r[0] in a.only_source.split(",")]
    if a.only_vm:
        rows = [r for r in rows if r[1] in a.only_vm.split(",")]
    by_vm = {}
    for r in rows:
        by_vm.setdefault(r[1], []).append(r)

    def work(vm):
        res = {}
        for src, _, tree, sub in by_vm[vm]:
            try:
                res[(src, vm, sub)] = run_one(vm, src, tree, sub, out, a.reuse)
                print("ok", vm, sub, res[(src, vm, sub)][4], "rows", file=sys.stderr, flush=True)
            except Exception as e:  # keep going; reported at the end
                res[(src, vm, sub)] = e
                print("FAIL", vm, sub, e, file=sys.stderr, flush=True)
        return res

    with ThreadPoolExecutor(max_workers=len(by_vm)) as ex:
        results = {}
        for r in ex.map(work, by_vm):
            results.update(r)
    failed = 0
    lines = ["source\tvm\tdir\tfile\trows\tsha256\tstats"]
    for src, vm, _, sub in rows:
        r = results[(src, vm, sub)]
        if isinstance(r, Exception):
            failed += 1
        else:
            lines.append("\t".join(r))
    mf = out / "manifest.tsv"
    mf.write_text("\n".join(lines) + "\n")
    print(f"manifest {mf}: {len(lines) - 1} dirs, {failed} failed; host {socket.gethostname()}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
