"""E10: build the new-host candidate list from discovered_external_hosts.txt files.

Steps: lowercase/strip, dedupe, `ic clean-hosts` filter (check_url is_host), drop seed hosts
(exact and www.-variant), drop platforms, collapse www/non-www pairs, report counts by TLD.
Usage: python candidates.py OUT_DIR  (reads E4 and E9 discovered files and seed_hosts.txt.gz)
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

from ic.utils.filter_utils import check_url

R = Path("/home/dinzinger/GitHub/imprints-collection")
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
SRC = {
    "E4": R / "datasets/E4/random20k/discovered_external_hosts.txt",
    "E9": R / "datasets/E9/random20k/discovered_external_hosts.txt",
}

# User-site hosts (github.io, wordpress.com subdomains, blogspot, wixsite, netlify, ...) are NOT dropped: they are real small sites.
# Platforms: label -> tokens. A token ending in "." matches a dot-delimited host label
# (facebook. matches www.facebook.com and facebook.de); other tokens match host or suffix.
PLATFORMS = {
    "social": [
        "facebook.", "fb.com", "fb.me", "instagram.", "twitter.", "x.com", "t.co", "linkedin.",
        "xing.", "youtube.", "youtu.be", "tiktok.", "pinterest.", "snapchat.", "whatsapp.",
        "telegram.", "t.me", "tumblr.", "reddit.", "vimeo.", "flickr.", "threads.net", "bsky.",
        "mastodon.", "discord.", "medium.com", "wa.me", "kununu.", "yelp.", "tripadvisor.",
        "trustpilot.", "holidaycheck.", "jameda.", "linktr.ee", "spotify.", "soundcloud.",
        "twitch.", "vk.com", "weibo.",
    ],
    "google_microsoft_apple_amazon": [
        "google.", "goo.gl", "gstatic.", "googleapis.", "googletagmanager.", "doubleclick.",
        "microsoft.", "office.com", "office365.", "live.com", "outlook.", "bing.com", "apple.com",
        "icloud.", "amazon.", "amzn.", "cloudfront.", "windows.net", "amazonaws.com",
    ],
    "app_stores": ["itunes.", "appstore.", "microsoftstore.", "samsung.com", "huawei."],
    "cdn_infra_builders_marketplaces": [
        "cloudflare.", "akamai", "fastly.", "jsdelivr.", "unpkg.", "cdnjs.", "bootstrapcdn.",
        "fontawesome.", "typekit.", "wp.com", "gravatar.", "wordpress.com", "w3.org", "schema.org",
        "creativecommons.", "paypal.", "stripe.", "klarna.", "gitlab.", "sourceforge.",
        "wikipedia.", "wikimedia.", "archive.org", "mailchimp.", "list-manage.", "sendinblue.",
        "sibforms.", "firebaseapp.",
        "weebly.",
        "shopify.", "godaddy.", "ionos.", "1und1.", "strato.", "hosteurope.",
        "domainfactory.", "cookiebot.", "usercentrics.", "etracker.", "econda.", "matomo.",
        "hotjar.", "zendesk.", "calendly.", "typeform.", "eventbrite.", "booking.com", "airbnb.",
        "ebay.", "etsy.", "kleinanzeigen.",
    ],
}


def platform(host):
    for label, toks in PLATFORMS.items():
        for t in toks:
            if t.endswith("."):
                if host.startswith(t) or ("." + t) in host:
                    return label, t
            elif host == t or host.endswith("." + t):
                return label, t
    return None


def tld(h):
    return h.rsplit(".", 1)[-1]


def variants(h):
    return {h[4:]} if h.startswith("www.") else {"www." + h}


with gzip.open(R / "seed_hosts.txt.gz", "rt", encoding="utf-8") as f:
    seeds = {l.strip().lower() for l in f if l.strip()}
print("seeds", len(seeds))

stats = {"seed_hosts": len(seeds)}
raw = {}
for k, p in SRC.items():
    lines = [l.strip().lower() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    raw[k] = lines
    stats[f"{k}_lines"] = len(lines)
    stats[f"{k}_unique"] = len(set(lines))
union = set(raw["E4"]) | set(raw["E9"])
stats["union_unique"] = len(union)
clean = {h for h in union if check_url(h, is_host=True)}
stats["after_clean_hosts_filter"] = len(clean)
exact_seed = {h for h in clean if h in seeds}
stats["in_seed_exact"] = len(exact_seed)
www_seed = {h for h in clean - exact_seed if variants(h) & seeds}
stats["in_seed_www_variant"] = len(www_seed)
new = clean - exact_seed - www_seed
stats["new_not_in_seed"] = len(new)
plat = {}
keep = set()
for h in sorted(new):
    p = platform(h)
    if p:
        plat[h] = p
    else:
        keep.add(h)
stats["dropped_platforms"] = len(plat)
final = {h for h in keep if not (h.startswith("www.") and h[4:] in keep)}
stats["www_pair_collapsed"] = len(keep) - len(final)
stats["final_candidates"] = len(final)
print(json.dumps(stats, indent=1))

(out / "candidate_hosts.txt").write_text("\n".join(sorted(final)) + "\n")
(out / "dropped_platforms.tsv").write_text(
    "".join(f"{h}\t{l}\t{s}\n" for h, (l, s) in sorted(plat.items()))
)
tl = Counter(tld(h) for h in new)
(out / "tld_before_platform_filter.tsv").write_text("".join(f"{t}\t{c}\n" for t, c in tl.most_common()))
tf = Counter(tld(h) for h in final)
(out / "tld_final.tsv").write_text("".join(f"{t}\t{c}\n" for t, c in tf.most_common()))
(out / "candidate_stats.json").write_text(json.dumps(stats, indent=1))
print("platform labels", Counter(l for l, s in plat.values()))
print("platform tokens", Counter(s for l, s in plat.values()).most_common(40))
print("TLD final", tf.most_common(25))

# Per-run discovery rate (E9 only = current fetcher, one run over the 20k seeds)
for k in ("E4", "E9"):
    s = set(raw[k])
    c = {h for h in s if check_url(h, True)}
    n = {h for h in c if h not in seeds and not (variants(h) & seeds)}
    pn = {h for h in n if not platform(h)}
    print(k, "unique", len(s), "clean", len(c), "new", len(n), "new non-platform", len(pn))
    stats[f"{k}_new"] = len(n)
    stats[f"{k}_new_nonplatform"] = len(pn)
(out / "candidate_stats.json").write_text(json.dumps(stats, indent=1))

# Occurrence counts (number of seed hosts linking to a new host) for the E9 run, for rarefaction
occ = Counter(h for h in raw["E9"] if check_url(h, True))
new9 = {h for h in occ if h not in seeds and not (variants(h) & seeds) and not platform(h)}
(out / "e9_new_occurrences.tsv").write_text("".join(f"{h}\t{occ[h]}\n" for h in sorted(new9)))
