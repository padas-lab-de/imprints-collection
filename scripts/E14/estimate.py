"""E14: full-run estimate for depth 1, 2, 3 from 6,560,119 seeds (D16 B), same method as E10:
linear scale-up vs Heaps rarefaction. Inputs: measured per-round numbers (hard-coded from results/E14/analysis.txt).
Usage: python scripts/E14/estimate.py
"""
S = 6_560_119
# Heaps fits U = c * N^b (unique new candidates vs parents fetched)
fit = {0: (0.7156, 0.982), 1: (1.9480, 0.955), 2: (5.1996, 0.906)}
lin = {0: 11860 / 20000, 1: 15197 / 11969, 2: 31456 / 15197}   # new candidates per fetched host
dach = {1: 1020 / 11969, 2: 303 / 15197, 3: 80 / 10000}        # strict DACH imprints per fetched host
cc_share = {1: 1619 / 11969, 2: 1031 / 15197, 3: 379 / 10000}   # share of fetched hosts that are .de/.at/.ch
cc_dach = {1: 669 / 1619, 2: 187 / 1031, 3: 46 / 379}           # DACH imprints per fetched cc host
# cc children per cc parent (frontier_sample, non-unique, per landing-page-ok parent: 1.18 round 1, 1.14 round 2)
# unique/non-unique factor 0.55 (round 1: 1.27 unique vs 2.32 sampled) .. 1.0
cc_child = (1.14 * 0.55, 1.14)

res = {}
for mode in ("linear", "heaps"):
    F = {}
    F[1] = lin[0] * S if mode == "linear" else fit[0][0] * S ** fit[0][1]
    for k in (2, 3):
        p = F[k - 1]
        F[k] = lin[k - 1] * p if mode == "linear" else fit[k - 1][0] * p ** fit[k - 1][1]
    res[mode] = F
    print(f"\n== {mode}: all TLDs fetched at every depth ==")
    cum_f = cum_d = 0
    for k in (1, 2, 3):
        d = F[k] * dach[k]
        cum_f += F[k]
        cum_d += d
        print(f"depth {k}: fetch {F[k]:,.0f}  DACH imprints {d:,.0f}  | cumulative to depth {k}: fetch {cum_f:,.0f}, DACH {cum_d:,.0f}, per 1,000 fetched {1000*cum_d/cum_f:.0f}")
    # cc-only variant: depth 1 all TLDs, depth 2-3 only .de/.at/.ch
    print(f"-- {mode}: depth 1 all TLDs, depth 2-3 only .de/.at/.ch")
    f1, d1 = F[1], F[1] * dach[1]
    f2 = F[2] * cc_share[2]
    d2 = f2 * cc_dach[2]
    print(f"depth 2: fetch {f2:,.0f}  DACH {d2:,.0f}")
    out = []
    for cf in cc_child:
        # parents for depth 3: reachable-ish cc round-2 hosts (use all fetched cc hosts x cf)
        f3 = f2 * cf
        d3 = f3 * cc_dach[3]
        out.append((f3, d3))
        print(f"depth 3 (cc children per cc parent {cf:.2f}): fetch {f3:,.0f}  DACH {d3:,.0f}  | cumulative fetch {f1+f2+f3:,.0f}, DACH {d1+d2+d3:,.0f}")
