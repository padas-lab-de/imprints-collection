"""Write results/E9/precision_sample.jsonl from results/E9/sample.json with manual judgements."""

import json

R = "/home/dinzinger/GitHub/imprints-collection/results/E9/"
s = json.load(open(R + "sample.json"))
bad = {
    25: "unrelated external page 'Rechtliches' of a medical chamber (ethics-committee guidelines), matched by the keyword 'rechtliches'",
}
doubt = {
    1: "external host dgx-mobility.de (site seems to have moved); text starts with a cookie banner",
    22: "full-body fallback; imprint data embedded in a page with navigation",
    45: "full-body fallback; imprint data embedded in a page with navigation",
    49: "'Rechtliche Hinweise' page that is both terms of use and provider information",
}
with open(R + "precision_sample.jsonl", "w") as f:
    for i, x in enumerate(s):
        x = dict(x, idx=i, judgement="bad" if i in bad else "correct", reason=bad.get(i), note=doubt.get(i))
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print(len(s) - len(bad), "/", len(s))
