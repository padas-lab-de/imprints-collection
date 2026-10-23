# E11: Why the E9 fetcher finds 1.7x the external hosts of E4

Date: 2026-10-23. Branch `E11-external-host-discovery` (from `lead-record` 4f1523a). Question from E10 doubts: same 20k seeds, `discovered_external_hosts.txt` has 19,980 unique hosts (E4) against 34,771 (E9). Which change causes it, and which count is the right basis?

## Result

The E4 fetcher lost external links through a bug; the E9 count is the correct one.

E4 `discover_links` (commit fe4963b) stored the links of a landing page in a dict keyed by the URL **path**: `discovered_links[parsed_url.path] = (anchor, abs_url, host)`. Every external link with the same path overwrote the previous one; only the last link per path survived. External links almost always have the path `/` (or `/impressum`, `/datenschutz`), so a page with Facebook, Instagram, a partner site and a hosting-provider link `/` kept one of them. Since commit 5d5afa2 the dict is keyed by the full URL, so all links count. This is a fix, not a change of what is counted.

## What is counted (code diff, no difference between E4 and now)

- Only links on the landing page (`tree.body`, `<a href>`). The imprint page and the other keyword pages (privacy, contact, ...) are fetched afterwards but their links are never passed to `discover_links`. No probes contribute.
- Host = lower-cased `netloc` (port and userinfo kept, `www.` kept, no normalisation) in both versions; same `check_url(host, is_host=True)` filter; external means `host != base_host` (seed host, exact string) in both.
- Both skip links with empty path (`https://x.de` without slash).
- Differences that could matter but do not move the count here: `<base href>` (since 5d5afa2), fragment stripping, `get_anchor_text`. Img alt: not used in either.
- Redirects: `base_host` is the seed string, not the final host, in both. A seed `a.de` redirecting to `www.a.de` counts its own links to `www.a.de` as external in both versions.

## Measurement

The jsonl outputs contain no links, and `discovered_external_hosts.txt` has no seed association, so per-host attribution from the existing outputs is impossible. Aggregate facts from the outputs: records written 16,217 (E4) vs 16,129 (E9), so the number of pages reached is the same; lines 25,353 vs 41,853 (1.65x), unique 19,980 vs 34,771 (1.74x). More pages reached, imprint-page links or normalisation cannot explain a 1.7x with equal reach.

To settle it I fetched the landing pages of 100 random seed hosts once (`random.seed(11)`, 4 threads, 77 reachable) and ran three extractors on the same HTML (`scripts/E11/compare_discovery.py`, `scripts/E11/analyze.py`, output `results/E11/compare100.json`, untracked):

| Extractor | External hosts (sum over 77 hosts) | Unique |
|---|---|---|
| A: E4 code (fe4963b) | 112 | 111 |
| B: E4 code, dict keyed by full URL instead of path | 157 | 156 |
| C: current code | 157 | 156 |

- B and C give identical sets on all 77 hosts: the path key explains 100% of the difference, `base_href` and the other changes explain 0 here.
- A is a subset of C on all 77 hosts; 20 hosts lose links in A.
- Ratio C/A = 1.40 (bootstrap 95% CI 1.22-1.66). The full-run ratio of 1.65 (lines) lies inside the interval. Sample is small; the cause is exact, the size of the effect is only roughly confirmed.

## Which count for E10

Use E9 (current fetcher): 34,771 unique, 11,910 new non-platform hosts, 0.596 per seed host. The E4 figure (0.21 per seed) is an undercount caused by the bug and must not be used as the fallback. The shrink-by-65% scenario in the E10 doubts does not apply. The E10 full-round estimate stays unchanged: the E10 table (171,000 / 3.9 M / 3.6 M new hosts; 15,000-300,000 DACH-address imprints; middle guess 1-2 M hosts) already rests on E9. Remove the E4 discovery sentence from the E10 doubts, and the union of E4 and E9 as candidate source is harmless (E4 is almost a subset; 304 of the 35,075 hosts occur only in E4, crawl noise).

## Doubts

- Sample of 77 hosts; the E9 count could still contain a few links the E4 count rightly lacked only if the behaviour differed elsewhere, but A is a subset of C everywhere in the sample.
- E10 says E4 gave 4,200 new hosts against 11,910 (2.8x), more than the 1.74x of all unique hosts. Plausible because lost links are the singletons (links to own sub-sites with unique hosts), while widely linked hosts (facebook, google) survive in E4 and are in the seed list anyway; not measured.
- Own-host redirect effect (seed `a.de` to `www.a.de` counted as external) is present in both versions and inflates new-host candidates slightly; E10 collapsed `www.` pairs and checked the seed list, so the effect is small there.
