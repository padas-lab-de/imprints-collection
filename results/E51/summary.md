# E51 summary: prompt-study sample with reference labels

Status: done 2026-11-10 (branch E51-prompt-study-sample, 17896fe; lead-verified: validator 0 errors, 0 overlap with gold and E49, agreement.json matches, examples checked). Use: tuning (dev2) and test (heldout2) data for E50. These are reference labels, not gold labels.

## 1. Source
E16 seed crawl, /home/dinzinger/imprints-raw-vm/E16/{apfel,aspe,lorbeer,mispel}/seeds/imprints_batch*.jsonl.gz (`ic fetch` output: host, homepage HTML, imprint HTML). Excluded: datasets/gold/, results/E49/dev_hosts.txt, results/E49/heldout/hosts.txt (1,006 normalized hosts). Overlap: 0. No crawl, no web fetch, no paid API, no innkube.

## 2. Sampling
`python3 -I scripts/E51/build_sample.py --root .` Seed 51. Pool 3,256,728 hosts with an imprint; excluded 715; random, no filter. 300 dev2, 200 heldout2.

| | dev2 | heldout2 |
|---|---|---|
| homepage empty | 3 | 2 |
| homepage <300 chars | 33 | 25 |
| homepage truncated | 47 | 28 |
| imprint truncated | 27 | 26 |
| homepage chars p10/p50/p90 | 229/2,143/5,910 | 198/1,913/5,915 |
| imprint chars p10/p50/p90 | 429/2,321/5,772 | 354/2,145/5,809 |
| deu/eng/other | 273/20/7 | 181/17/2 |

Source: results/E51/sample_stats.json.

## 3. Input form
Fields as in E49 build_dev.py. Static HTML -> resiliparse extract_plain_text(main_content=True) -> E49 clean_text -> 6,000-char budget. E49 inputs use the rendered DOM: do not pool E51 and E49 numbers without a note. Inputs (untracked): datasets/E51/{dev2,heldout2,e49}_inputs.jsonl.

## 4. Method
topic_spec.md (R1-R7 of results/E49/labelling_spec.md), address_spec.md. Two sonnet passes per task, opus adjudication (adjudication/decisions_*.jsonl). Build: refs_build.py. Validate: refs_validate.py (0 errors; address fields verbatim unless flagged; not_verbatim 0).

## 5. Agreement (results/E51/agreement.json)
| task | n | A=B exact / strict | lenient |
|---|---|---|---|
| POI v3 dev2 | 300 | 244 | 276 |
| POI v3 heldout2 | 200 | 157 | 180 |
| WZ dev2 | 300 | 250 | 277 |
| WZ heldout2 | 200 | 160 | 178 |
| address dev2 | 300 | 291 | |
| address heldout2 | 200 | 198 | |
| address E49 | 300 | 298 | |

Adjudication picks (A / B / new): POI dev2 22/34/0, POI heldout2 17/26/0, WZ dev2 23/27/0, WZ heldout2 16/23/1, address dev2 3/6/0, heldout2 1/1/0, E49 1/1/0.
Refs: main null POI 6/5, WZ 6/5 (dev2/heldout2); online_only POI 41/22. Addresses with a main address: dev2 282 (no_imprint 7, imprint_without_address 11), heldout2 191 (5, 4), E49 205 (77, 18).

## 6. Conventions (in addition to R1-R7)
- Performer without a POI node: arts root + extra general-entertainment; WZ 90.20 leaf.
- Heilpraktiker: alternative-medicine-clinic; for psychotherapy: mental-health-service + extra alternative-medicine-clinic, WZ 86.93.0.
- Amateur music association or choir: WZ 94.99.2 + extra 90.20.3. Party or voter group: POI organization.
- Shops are not online_only. R1 with a coherent operator: label the operator.
- WZ klasse with one child: write the leaf. Kita with undecided age range: 85.10.
- POI and WZ refs of one host are kept consistent.

## 7. Weak spots
- Passes A and B use the same model and brief: not independent; A=B is an upper bound.
- POI v3 has no nodes for parties, musicians, choirs, podcasts, diving schools, stonemasons (root or inner node used).
- R4 online_only unclear for web shops and web apps; R2 unclear for career sites, redirects, closed businesses.
- 72 of the 300 E49 hosts have an empty imprint text in the E49 inputs (rendered gold captures) -> address refs no_imprint.
- Placeholder imprints and parked or for-sale domains are flagged or set to null.
