# D26-depth2-tld-order

Issued 2026-10-29 (data-collection lead). Blocks: building the E22 depth-2 frontier (after frontier A's depth-1 crawl, about 1 day).

## Question
Depth 2 (D19 C: depth 3 across all TLDs): crawl all TLDs unordered, all TLDs with DACH TLDs first, or DACH TLDs only?

## Context (E22 TLD yield, 2026-10-29 ~06:00 UTC, scripts/E22/tld_yield.py)
- Sample: the first 352,168 depth-1 hosts of frontier A (15.5%; ic fetch shuffles the list, so the sample is random).
- Impressum found 9.9%; German-language Impressum (content_language deu) 8.65% of hosts; host_not_found 21.4%.
- .de/.at/.ch: 12.5% of hosts, 73.4% of German Impressum pages (.de 54.4%, .at 51.4%, .ch 33.7% per host).
- All other TLDs: 87.5% of hosts, 26.6% of German Impressum pages (.com 3.4% per host, 12.9% of all German pages; .org 1.9%; .it 0.9%).
- E16 seed baseline (aspe batches 0-2): German Impressum 46.5% of hosts; non-DACH TLDs 41% of hosts, 14% of German pages.
- Size: on aspe, 72.9k fetched depth-1 hosts list 284k unique linked hosts (before removing seeds, frontier A and platforms). Depth 2 is likely several million hosts.
- No money cost (own VMs); the cost is crawl time and storage.

## Options
- **A** All TLDs, unordered (as D19): complete; most crawl time goes to non-DACH hosts (~3% German Impressum per host).
- **B** All TLDs, in two lists: DACH TLDs (+ .eu/.info/.shop, >10% per host) first, the rest after. Same final coverage as A; if the crawl is stopped early, the stop loses the fewest German pages. Small change: frontier.py writes two lists.
- **C** DACH TLDs only at depth 2-3 (reverses D19): about 1/8 of the crawl; loses about a quarter of the German Impressum pages at that depth (and D16's DACH-address imprints on .com etc.).

**Recommend B:** keeps D19's coverage and makes any later stop cheap.

## Answer
(open)
