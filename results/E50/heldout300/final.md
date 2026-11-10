# E50 final configs: dev 500 and held-out 300

Frozen configs: results/E50/final_config.md. acc@L* (POI L*=2, WZ L*=3, address L*=1 = main_ok) with a 95% host-bootstrap CI; P = precision at L*; C = (tok in - cached in) + 10 x tok out per host. Dev and held-out are different hosts (not paired). e49 = E49 part (rendered DOM, E49 refs); e49_noimprint = E49 hosts with an empty imprint text (subset of e49); e51 = E51 part (static HTML, E51 refs).

## poi3 (acc@2)

| model | run | part | dev n | dev acc [95% CI] | dev P | dev C | held-out n | held-out acc [95% CI] | held-out P | held-out fail | held-out C |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | flat__gemma__r-short | all | 493 | 0.803 [0.767, 0.838] | 0.848 | 24851 | 292 | 0.760 [0.709, 0.808] | 0.810 | 0.000 | 24850 |
| gemma | flat__gemma__r-short | e49 | 199 | 0.799 [0.739, 0.854] | 0.855 | 24838 | 97 | 0.804 [0.722, 0.876] | 0.867 | 0.000 | 24793 |
| gemma | flat__gemma__r-short | e49_noimprint | 42 | 0.786 [0.643, 0.905] | 0.786 | 24361 | 28 | 0.679 [0.500, 0.857] | 0.792 | 0.000 | 24223 |
| gemma | flat__gemma__r-short | e51 | 294 | 0.806 [0.759, 0.854] | 0.843 | 24860 | 195 | 0.738 [0.677, 0.800] | 0.783 | 0.000 | 24878 |
| qwen | flat__qwen__r-low | all | 493 | 0.791 [0.755, 0.826] | 0.848 | 28942 | 292 | 0.753 [0.702, 0.801] | 0.815 | 0.000 | 28809 |
| qwen | flat__qwen__r-low | e49 | 199 | 0.809 [0.754, 0.864] | 0.875 | 28854 | 97 | 0.753 [0.670, 0.835] | 0.811 | 0.000 | 28720 |
| qwen | flat__qwen__r-low | e49_noimprint | 42 | 0.810 [0.690, 0.929] | 0.829 | 28020 | 28 | 0.643 [0.464, 0.821] | 0.750 | 0.000 | 27760 |
| qwen | flat__qwen__r-low | e51 | 294 | 0.779 [0.728, 0.827] | 0.830 | 29002 | 195 | 0.754 [0.692, 0.815] | 0.817 | 0.000 | 28854 |
| agentworld | flat__agentworld__r-short | all | 493 | 0.718 [0.680, 0.759] | 0.792 | 24909 | 292 | 0.712 [0.661, 0.764] | 0.776 | 0.000 | 24827 |
| agentworld | flat__agentworld__r-short | e49 | 199 | 0.719 [0.653, 0.779] | 0.803 | 24951 | 97 | 0.742 [0.649, 0.825] | 0.809 | 0.000 | 24800 |
| agentworld | flat__agentworld__r-short | e49_noimprint | 42 | 0.714 [0.571, 0.833] | 0.750 | 24580 | 28 | 0.571 [0.393, 0.750] | 0.696 | 0.000 | 24212 |
| agentworld | flat__agentworld__r-short | e51 | 294 | 0.718 [0.667, 0.769] | 0.784 | 24881 | 195 | 0.697 [0.631, 0.764] | 0.760 | 0.000 | 24840 |

## wz (acc@3)

| model | run | part | dev n | dev acc [95% CI] | dev P | dev C | held-out n | held-out acc [95% CI] | held-out P | held-out fail | held-out C |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | retrieve__gemma__r-none__c1500 | all | 493 | 0.751 [0.712, 0.789] | 0.763 | 3321 | 294 | 0.765 [0.718, 0.813] | 0.771 | 0.000 | 3316 |
| gemma | retrieve__gemma__r-none__c1500 | e49 | 199 | 0.734 [0.673, 0.794] | 0.741 | 3357 | 99 | 0.788 [0.707, 0.859] | 0.788 | 0.000 | 3360 |
| gemma | retrieve__gemma__r-none__c1500 | e49_noimprint | 42 | 0.738 [0.595, 0.857] | 0.756 | 3132 | 30 | 0.700 [0.533, 0.867] | 0.700 | 0.000 | 3129 |
| gemma | retrieve__gemma__r-none__c1500 | e51 | 294 | 0.762 [0.711, 0.810] | 0.778 | 3296 | 195 | 0.754 [0.692, 0.810] | 0.762 | 0.000 | 3294 |
| qwen | retrieve__qwen__r-none__c1500 | all | 493 | 0.744 [0.706, 0.781] | 0.758 | 3359 | 294 | 0.745 [0.690, 0.793] | 0.755 | 0.000 | 3352 |
| qwen | retrieve__qwen__r-none__c1500 | e49 | 199 | 0.734 [0.673, 0.794] | 0.749 | 3397 | 99 | 0.687 [0.596, 0.778] | 0.701 | 0.000 | 3399 |
| qwen | retrieve__qwen__r-none__c1500 | e49_noimprint | 42 | 0.833 [0.714, 0.929] | 0.875 | 3174 | 30 | 0.667 [0.500, 0.833] | 0.690 | 0.000 | 3182 |
| qwen | retrieve__qwen__r-none__c1500 | e51 | 294 | 0.752 [0.701, 0.803] | 0.765 | 3333 | 195 | 0.774 [0.718, 0.831] | 0.782 | 0.000 | 3328 |
| agentworld | retrieve__agentworld__r-none__c1500 | all | 493 | 0.714 [0.675, 0.755] | 0.726 | 3397 | 294 | 0.721 [0.667, 0.772] | 0.729 | 0.000 | 3383 |
| agentworld | retrieve__agentworld__r-none__c1500 | e49 | 199 | 0.683 [0.618, 0.749] | 0.694 | 3446 | 99 | 0.687 [0.596, 0.778] | 0.701 | 0.000 | 3411 |
| agentworld | retrieve__agentworld__r-none__c1500 | e49_noimprint | 42 | 0.667 [0.524, 0.810] | 0.700 | 3175 | 30 | 0.667 [0.500, 0.833] | 0.714 | 0.000 | 3198 |
| agentworld | retrieve__agentworld__r-none__c1500 | e51 | 294 | 0.735 [0.684, 0.786] | 0.747 | 3363 | 195 | 0.738 [0.677, 0.800] | 0.742 | 0.000 | 3369 |

## address (acc@1)

| model | run | part | dev n | dev acc [95% CI] | dev P | dev C | held-out n | held-out acc [95% CI] | held-out P | held-out fail | held-out C |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma | address__gemma__r-none__f-schema__mode-main | all | 500 | 0.970 [0.954, 0.984] | 0.970 | 1195 | 300 | 0.983 [0.967, 0.997] | 0.983 | 0.000 | 1170 |
| gemma | address__gemma__r-none__f-schema__mode-main | e49 | 200 | 0.970 [0.945, 0.990] | 0.970 | 1085 | 100 | 0.980 [0.950, 1.000] | 0.980 | 0.000 | 965 |
| gemma | address__gemma__r-none__f-schema__mode-main | e49_noimprint | 42 | 1.000 [1.000, 1.000] | 1.000 | 0 | 30 | 1.000 [1.000, 1.000] | 1.000 | 0.000 | 0 |
| gemma | address__gemma__r-none__f-schema__mode-main | e51 | 300 | 0.970 [0.950, 0.987] | 0.970 | 1268 | 200 | 0.985 [0.965, 1.000] | 0.985 | 0.000 | 1272 |
| qwen | address__qwen__r-none__f-schema__mode-main | all | 500 | 0.976 [0.962, 0.988] | 0.976 | 1499 | 300 | 0.980 [0.963, 0.993] | 0.980 | 0.000 | 1473 |
| qwen | address__qwen__r-none__f-schema__mode-main | e49 | 200 | 0.975 [0.950, 0.995] | 0.975 | 1345 | 100 | 0.980 [0.950, 1.000] | 0.980 | 0.000 | 1201 |
| qwen | address__qwen__r-none__f-schema__mode-main | e49_noimprint | 42 | 1.000 [1.000, 1.000] | 1.000 | 0 | 30 | 1.000 [1.000, 1.000] | 1.000 | 0.000 | 0 |
| qwen | address__qwen__r-none__f-schema__mode-main | e51 | 300 | 0.977 [0.957, 0.990] | 0.977 | 1601 | 200 | 0.980 [0.960, 0.995] | 0.980 | 0.000 | 1609 |
| agentworld | address__agentworld__r-none__f-schema__mode-main | all | 500 | 0.942 [0.920, 0.962] | 0.942 | 1339 | 300 | 0.957 [0.933, 0.977] | 0.957 | 0.000 | 1308 |
| agentworld | address__agentworld__r-none__f-schema__mode-main | e49 | 200 | 0.945 [0.915, 0.975] | 0.945 | 1213 | 100 | 0.950 [0.900, 0.990] | 0.950 | 0.000 | 1076 |
| agentworld | address__agentworld__r-none__f-schema__mode-main | e49_noimprint | 42 | 1.000 [1.000, 1.000] | 1.000 | 0 | 30 | 1.000 [1.000, 1.000] | 1.000 | 0.000 | 0 |
| agentworld | address__agentworld__r-none__f-schema__mode-main | e51 | 300 | 0.940 [0.913, 0.967] | 0.940 | 1423 | 200 | 0.960 [0.930, 0.985] | 0.960 | 0.000 | 1424 |

