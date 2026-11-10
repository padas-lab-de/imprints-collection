# E49 poi3 rerun (D51 B on schema poi_v3)

Date 2026-11-10. Inputs: dev set 200 hosts, refs `results/E49/refs/poi_v3.jsonl` (v3 and migrated) and `refs/poi.jsonl` (v2 native). Innkube only, no paid cost. Hosts scored are those common to all runs. acc = strict accuracy with both paths truncated to the level (`acc_trunc`), P = precision among covered, cov@2 = coverage at level 2. tok = prompt / completion tokens per host. Abst = prediction `main` null; err = failed replies (also counted as abstentions).

## All hosts (n=200)

| run | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | s/host | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen38-27b flat think both / v2 native | 199 | 10 | 1 | 0.942 | 0.874 | 0.894 | 0.799 | 0.973 | 25.92 | 13566 | 756 |
| qwen38-27b flat think both / v2 migrated to v3 | 199 | 10 | 1 | 0.942 | 0.896 | 0.894 | 0.819 | 0.973 | 25.92 | 13566 | 756 |
| qwen38-27b flat think both / v3 native | 199 | 10 | 1 | 0.921 | 0.824 | 0.874 | 0.754 | 0.973 | 10.25 | 12551 | 601 |
| gemma4-31b-it flat reason both / v3 native | 199 | 3 | 0 | 0.898 | 0.818 | 0.884 | 0.769 | 1.000 | 11.73 | 12767 | 65 |

## Offline subset (online_only false) (n=173)

| run | n | abst | err | P@1 | P@2 | acc@1 | acc@2 | cov@2 | s/host | tok in | tok out |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen38-27b flat think both / v2 native | 172 | 2 | 1 | 0.971 | 0.893 | 0.959 | 0.872 | 0.994 | 20.93 | 13544 | 622 |
| qwen38-27b flat think both / v2 migrated to v3 | 172 | 2 | 1 | 0.971 | 0.911 | 0.959 | 0.890 | 0.994 | 20.93 | 13544 | 622 |
| qwen38-27b flat think both / v3 native | 172 | 1 | 0 | 0.947 | 0.833 | 0.942 | 0.814 | 0.994 | 8.14 | 12529 | 473 |
| gemma4-31b-it flat reason both / v3 native | 172 | 0 | 0 | 0.924 | 0.834 | 0.924 | 0.820 | 1.000 | 11.7 | 12747 | 65 |

## Top 10 confusion pairs at level 2 (qwen v3 native, ref -> pred)

Hosts with a reference reaching level 2: 187. Abstained: 5. Predicted level 1 only: 0. Wrong at level 2 (both reach it): 32.

| n | reference (level 2) | prediction (level 2) | same root |
|---|---|---|---|
| 3 | Manufacturer or Factory (Business and Professional Services) | Industrial Equipment Supplier (Business and Professional Services) | yes |
| 2 | Wholesaler (Business and Professional Services) | Automotive Retail (Retail) | no |
| 2 | Manufacturer or Factory (Business and Professional Services) | Scientific Equipment Supplier (Business and Professional Services) | yes |
| 1 | Laboratory (Business and Professional Services) | Organization (Community and Government) | no |
| 1 | Technology Business (Business and Professional Services) | Event Service (Business and Professional Services) | yes |
| 1 | Manufacturer or Factory (Business and Professional Services) | Refrigeration and Ice Supplier (Business and Professional Services) | yes |
| 1 | Education (Community and Government) | Library (Community and Government) | yes |
| 1 | Manufacturer or Factory (Business and Professional Services) | Metals Supplier (Business and Professional Services) | yes |
| 1 | Government Building (Community and Government) | Research Station (Business and Professional Services) | no |
| 1 | Wholesaler (Business and Professional Services) | Import and Export Service (Business and Professional Services) | yes |
## Reading

- Configs: qwen38-27b flat, think on, input both, predict to level 2 (D51 B) and gemma4-31b-it flat, reason short, input both. All on innkube (free). Run tags: `flat__qwen__both__dmax__nt-path__think`, `flat__gemma__both__dmax__nt-path__reason` (predictions in `preds/poi3/`, migrated v2 predictions in `migrated/poi3/`).
- Levels are scored to the full tree depth (max 3); only L1 and L2 are shown. Single-child chains are extended by the scorer.
- Does P@2 stay >= 0.8 for qwen? Yes on v3 native: 0.824 (all hosts) and 0.833 (offline). It is lower than on v2 (0.874 / 0.893) and lower than the v2 predictions migrated to v3 (0.896 / 0.911). acc@2 (strict) drops from 0.799 to 0.754 (all) and from 0.872 to 0.814 (offline).
- Schema effect vs model drift: migrating the v2 predictions to v3 ids and scoring against the v3 refs gives a higher score than v2 native (P@2 +0.022, acc@2 +0.020), so the v3 schema and refs are not harder in themselves. The v3-native run is 0.07 below the migrated run at P@2. The gap is therefore caused by the model choosing among v3 candidates (753 English nodes, 388 at level 3, finer sub-classes under Business and Professional Services) and by the English-named prompt, not by the reference change. The v2 migrated run and the v3 native run share the same host set; each has 10 abstentions, 5 of them on the same hosts, so part of the gap is run-to-run model variation.
- Differences between runs are small in absolute terms (n=199, 1 host = 0.005); a P@2 gap of 0.07 is about 14 hosts of 187.
- The dominant L2 confusions in qwen v3 are inside Business and Professional Services: Manufacturer or Factory, Wholesaler and Laboratory are predicted as a specific supplier class (Industrial Equipment Supplier, Scientific Equipment Supplier, Metals Supplier, Refrigeration and Ice Supplier). These are near-synonym sibling classes; the 32 wrong L2 predictions are mostly 1 host per pair.
- Gemma has no v2 run with the same setting (the stage-2 gemma runs are `home reason` and `both think`). A `home reason` v3 run for a matched comparison was started but not finished (the innkube endpoint was slow), so it is not in the tables.
- s/host: the v3 values (qwen 10.3, gemma 11.7) are wall time per host in a run that was resumed several times and partly served from the response cache; they are not comparable to the v2 values (25.9 for qwen). Use the token columns for cost. The v2 migrated rows repeat the v2 latency and tokens.
