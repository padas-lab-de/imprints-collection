import re

HOST_FILTER = [
    "simone-melzer.de",
    "radiohost.de",
    "hoerradar.de",
    "streamabc.net",
    "finanzpoint-pure-energien.de",
    "www.blog.de",
    "nicsell.com",
    "reisenessenlachen.de",
    "kentuya-seelenkunst.de",
    "brennbergerbuam.de",
    "hypnosolution-niedersachsen.de",
    "dascafeleklosterlechfeld.de",
    "sanitaetshaus-brandschert.de",
    "ambestenbewertet.de",
    "telekom-profis.de",
    "homepagemodules.de",
    "apotheken-website-vorschau.de",
    "emailsys1a.net",
    "stream.radio-pv.com",
    "eins.stream.laut.fm",
    "triggerfmhartmut.ice.infomaniak.ch",
    "office.radio-zoom.de",
    "safelinks.protection.outlook.com",
    "vorschau-apotheken-website.de",
    "brunch-lunch-dinner.de",
    "unterkunft.de",
    "spcast.eu",
    "radiohost.de",
    "stream.meifm.de",
    "youtube.",
    "whatsapp.",
    "facebook.",
    "instagram.",
    "google.",
    "spotify.",
    "apple.",
    "tiktok.",
    "pinterest.",
    "twitter.",
    "linkedin.",
    "xing.",
    "tumblr.",
    "flickr.",
    "vimeo.",
    "reddit.",
    "quora.",
    "snapchat.",
    "wechat.",
    "telegram.",
    "discord.",
    "twitch.",
    "yahoo.",
    "bing.",
    "deezer.",
    "amazon.",
    "ebay.",
    "yelp.",
    "paypal.",
    "jimdo.",
    "t.me",
    "wikipedia.",
    "youtu.be",
    "g.co",
    "g.page",
    "x.com",
    "goo.gl",
    "bit.ly",
    "tinyurl.com",
    "wa.me",
    "amzn.to",
    "fb.me",
    "lnkd.in",
    "t.co",
    "www.wordpress.com",
    "wordpress.org",
    "shopify.com",
    "cookiedatabase.org",
    "ermoeglicher.de",
    "linktr.ee",
    "about.me",
    "bsky.app",
    "mastodon.social",
    "github.com",
    "mywebsite-editor.com",
    "streamabc.net",
    "radio.rojc.eu",
    "tripadvisor.",
    "sibforms.com",
    "logineonrw-lms.de",
    ".moodle.",
    ".fuxnoten.",
    "download.",
    ".hotelseipel.de",
    ".hotel-mix.de",
    ".unterkunft-niedersachsen.de",
    ".vm.",
    "businesscoaching-pflege.de",
    "deb-kiel.de",
    "elecacsgroup.de",
    "dmkm2015.de",
    "bandcamp.com",
    "gutscheinebro.de",
]


def check_url(url: str, is_host: bool = False) -> bool:
    if is_host:
        if "http" in url or ":" in url:
            return False

    for s in ['"', "%", "+", "-", "<", ">", "."]:
        if url.startswith(s):
            return False

    if re.match(r"^\d{5,}", url):
        return False

    if re.match(r"^[\dabcde-]{8,}", url):
        return False

    if (
        not " " in url
        and not "{" in url
        and not "}" in url
        and "." in url
        and any(c.isalpha() for c in url)
    ):
        filtered = False
        for filter in HOST_FILTER:
            if filter in url:
                filtered = True
                break
        return not filtered
    return False
