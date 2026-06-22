#!/usr/bin/env python3
"""Static SEO site generator for Border Builder.

Reads the app's plant catalogue (plants.json) and emits:
  - plants/<slug>.html   one profile page per plant (the long tail)
  - collections/<slug>.html   faceted "plants for X" pages (the search-intent pages)
  - plants/index.html, collections/index.html   browse hubs
  - sitemap.xml, robots.txt

Hand-authored pages (index.html, privacy.html, support.html, style.css) are never
touched. Generated pages reuse style.css for the palette and add content.css.

Re-run any time the catalogue changes:  python3 build.py
"""

import html
import json
import os
import re
import shutil

# --- config: edit these three for your deploy ---------------------------------
BASE_URL = "https://borderbuilderapp.com"  # production origin, no trailing slash
APP_STORE_URL = "https://apps.apple.com/app/id6774342720"  # blank hides the button
PLAY_STORE_URL = ""  # set when Android ships: https://play.google.com/store/apps/details?id=com.borderbuilder.borderbuilder
# ------------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOGUE = os.path.join(
    HERE, "..", "border-builder-ios", "BorderBuilder", "BorderBuilder", "Resources", "plants.json"
)
SITE_NAME = "Border Builder"

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_LABEL = dict(zip(MONTHS, "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()))


def slugify(text):
    text = text.lower().replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def e(text):
    return html.escape(str(text), quote=True)


def truthy(v):
    return v is True or (isinstance(v, str) and v.strip().upper() in {"Y", "TRUE", "YES"})


def falsy(v):
    return v is False or (isinstance(v, str) and v.strip().upper().startswith("N"))


# --- load + normalise ---------------------------------------------------------

with open(CATALOGUE) as fh:
    RAW = json.load(fh)


def norm(p):
    return {
        "name": p["name"],
        "common": p.get("commonName") or p["name"],
        "slug": slugify(p["name"]),
        "type": p.get("plantType", "plant"),
        "height": p.get("matureHeightCm"),
        "spread": p.get("spreadCm"),
        "evergreen": bool(p.get("evergreen")),
        "aspect": set(p.get("aspectTolerance") or []),
        "soil": set(p.get("soilTolerance") or []),
        "styles": set(p.get("styles") or []),
        "roles": set(p.get("roleCapabilities") or []),
        "colours": set(p.get("flowerColours") or []),
        "regions": set(p.get("regions") or []),
        "months": [m for m in (p.get("flowerMonths") or []) if m in MONTHS],
        "hardiness": p.get("hardiness") or {},
        "petSafe": "yes" if truthy(p.get("petSafe")) else ("no" if falsy(p.get("petSafe")) else "unknown"),
        "pollinator": truthy(p.get("pollinatorFriendly")),
        "citations": p.get("bloomCitations") or {},
    }


PLANTS = [norm(p) for p in RAW]
BY_SLUG = {p["slug"]: p for p in PLANTS}

# Per-collection guidance prose (authored, ~110 words each), keyed by slug.
GUIDANCE = {}
_guide_path = os.path.join(HERE, "category-intros.json")
if os.path.exists(_guide_path):
    with open(_guide_path) as _gf:
        GUIDANCE = json.load(_gf)

TYPE_LABEL = {
    "perennial": "Perennials", "shrub": "Shrubs", "bulb": "Bulbs",
    "grass": "Ornamental grasses", "annual": "Annuals", "climber": "Climbers",
}
COLOUR_LABEL = {
    "WHITE": "white", "PINK": "pink", "PURPLE": "purple", "YELLOW": "yellow",
    "BLUE": "blue", "RED": "red", "GREEN": "green", "ORANGE": "orange",
}
STYLE_LABEL = {
    "COTTAGE": "Cottage garden", "WILDLIFE": "Wildlife garden", "NATIVE": "Native",
    "WOODLAND": "Woodland", "MODERN": "Modern", "FOUNDATION": "Foundation planting",
    "SHADE_COTTAGE": "Shade cottage", "XERISCAPE": "Xeriscape (low-water)",
    "MEADOW": "Meadow", "COASTAL": "Coastal", "FORMAL": "Formal",
    "MEDITERRANEAN": "Mediterranean",
}
ROLE_LABEL = {
    "MID_BORDER": "mid-border", "EDGING": "edging", "FOCAL": "focal point",
    "STRUCTURE": "structure", "GROUNDCOVER": "groundcover", "BULB_LAYER": "bulb layer",
}

# --- chrome -------------------------------------------------------------------

def store_buttons(up=""):
    btns = []
    if APP_STORE_URL:
        btns.append(
            f'<a class="badge" href="{e(APP_STORE_URL)}" '
            f'aria-label="Download Border Builder on the App Store">'
            f'<img src="{up}appstore-badge.svg" alt="Download on the App Store" '
            f'width="143" height="48"></a>'
        )
    if PLAY_STORE_URL:
        btns.append(
            f'<a class="badge" href="{e(PLAY_STORE_URL)}" '
            f'aria-label="Get Border Builder on Google Play">'
            f'<img src="{up}googleplay-badge.svg" alt="Get it on Google Play" '
            f'width="161" height="48"></a>'
        )
    if not btns:
        btns.append('<a class="store" href="/">Get Border Builder</a>')
    return '<div class="stores">' + "".join(btns) + "</div>"


def cta(line, up=""):
    return f'<section class="cta"><p>{e(line)}</p>{store_buttons(up)}</section>'


def page(title, description, canonical, body, jsonld=None, depth=1, main_class="", robots=None):
    up = "../" * depth
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    robots_meta = f'\n<meta name="robots" content="{robots}">' if robots else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">{robots_meta}
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(canonical)}">
<link rel="stylesheet" href="{up}style.css">
<link rel="stylesheet" href="{up}content.css">
{ld}
</head>
<body>
<main class="{main_class}">
<a class="brand" href="{up}index.html">{SITE_NAME}</a>
{body}
<footer>
<nav><a href="{up}plants/index.html">All plants</a><a href="{up}collections/index.html">Collections</a><a href="{up}privacy.html">Privacy</a><a href="{up}support.html">Support</a></nav>
&copy; 2026 {SITE_NAME}
</footer>
</main>
</body>
</html>
"""


def breadcrumbs(trail):
    items = []
    for i, (name, href) in enumerate(trail):
        node = {"@type": "ListItem", "position": i + 1, "name": name}
        if href:
            node["item"] = BASE_URL + href
        items.append(node)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def crumb_html(trail):
    parts = " &rsaquo; ".join(
        f'<a href="{e(href)}">{e(name)}</a>' if href else e(name) for name, href in trail
    )
    return f'<nav class="crumbs">{parts}</nav>'


# --- plant profile ------------------------------------------------------------

def aspect_words(aspect):
    if "NORTH" in aspect and len(aspect) <= 2:
        return "shade and partial shade"
    if "SOUTH" in aspect or "WEST" in aspect:
        return "full sun" + (" to partial shade" if "EAST" in aspect or "NORTH" in aspect else "")
    return "partial shade"


def hardiness_line(h):
    bits = []
    if h.get("usdaMin") and h.get("usdaMax"):
        bits.append(f"USDA {h['usdaMin']}-{h['usdaMax']}")
    elif h.get("usdaMin"):
        bits.append(f"USDA {h['usdaMin']}+")
    if h.get("rhs"):
        bits.append(f"RHS {h['rhs'].upper()}")
    return ", ".join(bits) or "Not specified"


def bloom_strip(months):
    cells = []
    active = set(months)
    for m in MONTHS:
        on = "on" if m in active else ""
        cells.append(f'<span class="m {on}" title="{MONTH_LABEL[m]}">{MONTH_LABEL[m][0]}</span>')
    return f'<div class="bloom" aria-label="Flowering months">{"".join(cells)}</div>'


def fact_rows(p):
    rows = [
        ("Type", e(p["type"].capitalize())),
        ("Mature height", f'{p["height"]} cm' if p["height"] else "-"),
        ("Spread", f'{p["spread"]} cm' if p["spread"] else "-"),
        ("Aspect", e(aspect_words(p["aspect"]))),
        ("Foliage", "Evergreen" if p["evergreen"] else "Deciduous"),
        ("Hardiness", e(hardiness_line(p["hardiness"]))),
        ("Pollinator-friendly", {"yes": "Yes", "no": "No", "unknown": "-"}.get("yes" if p["pollinator"] else "no")),
        ("Pet-safe", {"yes": "Yes", "no": "No", "unknown": "Not confirmed"}[p["petSafe"]]),
    ]
    trs = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    return f"<table class=facts><tbody>{trs}</tbody></table>"


def related(p, n=8):
    pool = [q for q in PLANTS if q["slug"] != p["slug"] and (q["type"] == p["type"]) and (p["styles"] & q["styles"])]
    pool = sorted(pool, key=lambda q: -len(p["styles"] & q["styles"]))[:n]
    if len(pool) < n:
        extra = [q for q in PLANTS if q["type"] == p["type"] and q not in pool and q["slug"] != p["slug"]]
        pool += extra[: n - len(pool)]
    return pool


def citation_block(cit):
    seen, lines = set(), []
    for v in cit.values():
        for part in str(v).split(";"):
            part = part.strip()
            if part and part not in seen:
                seen.add(part)
                lines.append(part)
    if not lines:
        return ""
    items = "".join(f"<li>{e(x)}</li>" for x in lines[:6])
    return f'<section class="sources"><h2>Sources</h2><p>Bloom timing and hardiness drawn from:</p><ul>{items}</ul></section>'


SOIL_WORD = {"LOAM": "loam", "CLAY": "clay", "SANDY": "sandy soil", "CHALK": "chalk",
             "ACID": "acid soil", "WET": "moist ground"}


def soil_phrase(soil):
    order = ["CLAY", "LOAM", "SANDY", "CHALK", "ACID", "WET"]
    words = [SOIL_WORD[s] for s in order if s in soil]
    if not words:
        return "most soils"
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " or " + words[-1]


def placement_sentence(p):
    h = p["height"] or 0
    roles = p["roles"]
    if "STRUCTURE" in roles or "FOCAL" in roles or h >= 120:
        where = "toward the back of a border, or on its own as a focal point with room around it"
    elif "EDGING" in roles or "GROUNDCOVER" in roles or h < 40:
        where = "along the front edge, where a low, spreading habit reads best"
    else:
        where = "through the middle of a border, between taller structure behind and edging in front"
    return f"At around {p['height']} cm, it sits best {where}."


def spacing_sentence(p):
    s = p["spread"]
    if not s:
        return ""
    txt = f"Give it about {s} cm of room to spread"
    if s <= 50:
        per_m = round(100.0 / s)
        if per_m >= 2:
            txt += f", roughly {per_m} to the metre when planted in a drift"
    return txt + "."


def hardiness_sentence(p):
    h = p["hardiness"]
    bits = []
    if h.get("usdaMin") and h.get("usdaMax"):
        bits.append(f"hardy across USDA zones {h['usdaMin']} to {h['usdaMax']}")
    if h.get("rhs"):
        bits.append(f"rated {h['rhs'].upper()} by the RHS")
    if not bits:
        return ""
    return "It is " + " and ".join(bits) + ", so check it suits your area before planting."


_COMP = {}


def companions(p, n=6):
    if p["slug"] not in _COMP:
        scored = []
        for q in PLANTS:
            if q["slug"] == p["slug"]:
                continue
            if not (p["aspect"] & q["aspect"]) or not (p["soil"] & q["soil"]):
                continue
            shared = len(p["styles"] & q["styles"])
            if shared == 0:
                continue
            if p["regions"] and q["regions"] and not (p["regions"] & q["regions"]):
                continue
            role_complement = 1 if (q["roles"] - p["roles"]) else 0
            season_extend = 1 if (set(q["months"]) - set(p["months"])) else 0
            scored.append((shared * 2 + role_complement + season_extend, q))
        scored.sort(key=lambda x: (-x[0], x[1]["common"].lower()))
        _COMP[p["slug"]] = [q for _, q in scored]
    return _COMP[p["slug"]][:n]


def companion_reason(p, q):
    hp, hq = p["height"] or 0, q["height"] or 0
    if hq >= hp + 40 and ("STRUCTURE" in q["roles"] or "FOCAL" in q["roles"]):
        return "for height behind it"
    if hq + 40 <= hp or (q["roles"] & {"EDGING", "GROUNDCOVER"}):
        return "to edge in front"
    if set(q["months"]) - set(p["months"]):
        return "to flower when it does not"
    return "as a partner at the same level"


def care_notes(p):
    notes = []
    if p["evergreen"]:
        notes.append("Evergreen, so it keeps the border furnished through winter.")
    if "WET" in p["soil"] and not (p["soil"] & {"SANDY", "CHALK"}):
        notes.append("It copes with ground that stays wet, which most border plants will not.")
    if "ACID" in p["soil"] and "CHALK" not in p["soil"]:
        notes.append("It tolerates acid soil but dislikes shallow chalk.")
    if p["aspect"] and "NORTH" in p["aspect"]:
        notes.append("It tolerates a shaded, north-facing spot.")
    if p["petSafe"] == "no":
        notes.append("Not recorded as pet-safe; site it away from pets that graze if that matters to you.")
    if p["pollinator"]:
        notes.append("Its flowers are valued by bees and other pollinators.")
    return notes


def indexable_plant(p):
    return bool(p["height"] and p["roles"] and (p["months"] or p["evergreen"])
                and len(companions(p)) >= 3)


FOUND_IN = [
    (("aspect", "SOUTH"), "full-sun", "full sun"),
    (("aspect", "NORTH"), "shade", "shade"),
    (("soil", "CLAY"), "soil-clay", "clay soil"),
    (("soil", "SANDY"), "soil-sandy", "sandy soil"),
    (("soil", "CHALK"), "soil-chalk", "chalk soil"),
    (("soil", "ACID"), "soil-acid", "acid soil"),
    (("soil", "WET"), "soil-wet", "wet soil"),
    (("evergreen", True), "evergreen", "evergreen plants"),
    (("pollinator", True), "pollinator-friendly", "pollinator-friendly plants"),
    (("petSafe", "yes"), "pet-safe", "pet-safe plants"),
]


def found_in_links(p):
    out = []
    for (field, val), slug, label in FOUND_IN:
        cur = p[field]
        hit = (val in cur) if isinstance(cur, set) else (cur == val or cur is val)
        if hit:
            out.append(f'<a href="../collections/{slug}.html">{e(label)}</a>')
    return out


def plant_page(p):
    canon = f"{BASE_URL}/plants/{p['slug']}.html"
    months_txt = ", ".join(MONTH_LABEL[m] for m in p["months"]) or "varies by climate"
    aspect_txt = aspect_words(p["aspect"])
    soil_txt = soil_phrase(p["soil"])
    article = "an" if (p["type"][:1].lower() in "aeiou") else "a"
    role_txt = ", ".join(ROLE_LABEL.get(r, r.lower()) for r in sorted(p["roles"])) or "border planting"

    title = f"{p['common']} ({p['name']}): size, soil and where to plant it | {SITE_NAME}"
    desc = (f"{p['common']} ({p['name']}), {article} {p['type']} for {aspect_txt} and {soil_txt}. "
            f"About {p['height']}cm, flowers {months_txt}; placement, companions and sources.")[:200]

    plant_para = " ".join(x for x in [placement_sentence(p), spacing_sentence(p),
                                       hardiness_sentence(p)] if x)
    comp_html = "".join(
        f'<li><a href="{q["slug"]}.html"><b>{e(q["common"])}</b>'
        f'<span>{e(companion_reason(p, q))}</span></a></li>'
        for q in companions(p, 6)
    )
    notes = care_notes(p)
    notes_html = ("<h2>Worth knowing</h2><ul class=\"notes\">"
                  + "".join(f"<li>{e(x)}</li>" for x in notes) + "</ul>") if notes else ""
    style_links = " ".join(
        f'<a class="chip" href="../collections/{slugify("style-" + s)}.html">{e(STYLE_LABEL.get(s, s.title()))}</a>'
        for s in sorted(p["styles"]) if s in STYLE_LABEL
    )
    found = found_in_links(p)
    found_html = (f'<p class="found">It appears in our lists of {", ".join(found[:6])}.</p>'
                  if found else "")

    trail = [("Home", "/index.html"), ("Plants", "/plants/index.html"), (p["common"], None)]
    body = f"""
{crumb_html([("Home","../index.html"),("Plants","index.html"),(p["common"],None)])}
<header class="hero">
<h1>{e(p["common"])}</h1>
<p class="latin">{e(p["name"])}</p>
</header>
<p class="lead">{e(p["common"])} is {article} {e(p["type"])} for {e(role_txt)}, suited to
{e(aspect_txt)} and {e(soil_txt)}, flowering {e(months_txt)}.</p>
{fact_rows(p)}
<h2>Where to use it in a border</h2>
<p>{e(plant_para)}</p>
{found_html}
<h2>Flowering through the year</h2>
{bloom_strip(p["months"])}
{notes_html}
<h2>Good companions</h2>
<p>Plants that share its conditions and style, chosen to complement its place in the border:</p>
<ul class="grid">{comp_html}</ul>
<h2>Garden styles</h2>
<p class="chips">{style_links or "Versatile across planting styles."}</p>
{cta(f"See {p['common']} set in a full border, with spacing and companions worked out for your own conditions, in Border Builder.", up="../")}
{citation_block(p["citations"])}
"""
    bc = breadcrumbs(trail)
    bc.pop("@context", None)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article",
         "headline": f"{p['common']} ({p['name']}): planting guide",
         "about": p["common"], "datePublished": "2026-06-22", "dateModified": "2026-06-22",
         "author": {"@type": "Organization", "name": SITE_NAME},
         "publisher": {"@type": "Organization", "name": SITE_NAME,
                       "logo": {"@type": "ImageObject", "url": BASE_URL + "/favicon.svg"}}},
        bc,
    ]}
    robots = None if indexable_plant(p) else "noindex,follow"
    return page(title, desc, canon, body, jsonld=ld, depth=1, robots=robots)


# --- collection pages ---------------------------------------------------------

def card(p):
    return (f'<li><a href="../plants/{p["slug"]}.html"><b>{e(p["common"])}</b>'
            f'<span>{e(p["name"])}</span></a></li>')


def collection_page(slug, h1, title, intro, members, related_links):
    canon = f"{BASE_URL}/collections/{slug}.html"
    desc = (intro + f" {len(members)} plants, with size, aspect and bloom time for each.")[:200]
    cards = "".join(card(p) for p in members)
    rel = "".join(f'<a class="chip" href="{e(href)}">{e(name)}</a>' for name, href in related_links)
    rel_block = f'<h2>Related collections</h2><p class="chips">{rel}</p>' if rel else ""
    guide = GUIDANCE.get(slug, "")
    guide_html = "".join(f"<p>{e(par.strip())}</p>" for par in guide.split("\n\n") if par.strip())
    trail = [("Home", "/index.html"), ("Collections", "/collections/index.html"), (h1, None)]
    body = f"""
{crumb_html([("Home","../index.html"),("Collections","index.html"),(h1,None)])}
<header class="hero"><h1>{e(h1)}</h1></header>
<p class="lead">{e(intro)}</p>
{guide_html}
<h2>{len(members)} plants for this</h2>
<ul class="grid">{cards}</ul>
{cta(f"Pick what you like and Border Builder turns it into a full plan: how many of each, where they go, and how the border reads through the seasons.", up="../")}
{rel_block}
"""
    bc = breadcrumbs(trail)
    bc.pop("@context", None)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": h1, "url": canon,
         "description": intro,
         "mainEntity": {"@type": "ItemList", "numberOfItems": len(members),
                        "itemListElement": [
                            {"@type": "ListItem", "position": i + 1, "name": p["common"],
                             "url": f"{BASE_URL}/plants/{p['slug']}.html"}
                            for i, p in enumerate(members[:50])]}},
        bc,
    ]}
    return page(title, desc, canon, body, jsonld=ld, depth=1)


def by_height(p, lo, hi):
    h = p["height"]
    return h is not None and lo <= h < hi


COLLECTIONS = []  # (slug, h1, title, intro, predicate)


def add(slug, h1, intro, pred):
    COLLECTIONS.append((slug, h1, f"{h1} | {SITE_NAME}", intro, pred))


# plant type
for t, label in TYPE_LABEL.items():
    add(f"type-{t}", f"{label} for borders",
        f"{label} that work in a planted border, with mature size, aspect and bloom time for each.",
        lambda p, t=t: p["type"] == t)
# aspect
add("full-sun", "Plants for full sun",
    "Sun-loving plants for a south or west-facing border.",
    lambda p: bool(p["aspect"] & {"SOUTH", "WEST"}))
add("shade", "Plants for shade",
    "Plants that tolerate a north-facing or shaded border.",
    lambda p: "NORTH" in p["aspect"])
add("partial-shade", "Plants for partial shade",
    "Plants for an east-facing border or dappled light.",
    lambda p: "EAST" in p["aspect"])
# soil
for soil, label in [("CLAY", "clay soil"), ("SANDY", "sandy soil"), ("CHALK", "chalk soil"),
                    ("ACID", "acid soil"), ("WET", "wet soil")]:
    add(f"soil-{soil.lower()}", f"Plants for {label}",
        f"Plants that cope with {label}, with size and aspect for each.",
        lambda p, soil=soil: soil in p["soil"])
# attributes
add("evergreen", "Evergreen plants",
    "Plants that hold their leaves through winter for year-round border structure.",
    lambda p: p["evergreen"])
add("pollinator-friendly", "Pollinator-friendly plants",
    "Plants that feed bees, butterflies and other pollinators.",
    lambda p: p["pollinator"])
add("pet-safe", "Pet-safe plants",
    "Plants recorded as non-toxic to cats and dogs. Always confirm before planting.",
    lambda p: p["petSafe"] == "yes")
# colour
for col, label in COLOUR_LABEL.items():
    add(f"colour-{label}", f"{label.capitalize()}-flowering plants",
        f"Plants with {label} flowers for a colour-themed border.",
        lambda p, col=col: col in p["colours"])
# style
for s, label in STYLE_LABEL.items():
    add(slugify("style-" + s), f"{label} plants",
        f"Plants suited to a {label.lower()} planting scheme.",
        lambda p, s=s: s in p["styles"])
# height bands
add("low-edging", "Low and edging plants (under 40cm)",
    "Compact plants for the front of a border or edging a path.",
    lambda p: by_height(p, 0, 40))
add("mid-border", "Mid-border plants (40-100cm)",
    "Medium-height plants for the middle of a border.",
    lambda p: by_height(p, 40, 100))
add("tall-back", "Tall back-of-border plants (over 100cm)",
    "Tall plants for height and a backdrop at the back of a border.",
    lambda p: by_height(p, 100, 10000))
# high-value combos (curated, not a cartesian explosion)
add("shrubs-for-shade", "Shrubs for shade",
    "Shrubs that grow in a north-facing or shaded border.",
    lambda p: p["type"] == "shrub" and "NORTH" in p["aspect"])
add("perennials-for-full-sun", "Perennials for full sun",
    "Sun-loving perennials for a hot, bright border.",
    lambda p: p["type"] == "perennial" and bool(p["aspect"] & {"SOUTH", "WEST"}))
add("pollinator-plants-for-shade", "Pollinator plants for shade",
    "Shade-tolerant plants that still feed pollinators.",
    lambda p: p["pollinator"] and "NORTH" in p["aspect"])
add("evergreen-shrubs", "Evergreen shrubs",
    "Evergreen shrubs for permanent border structure.",
    lambda p: p["type"] == "shrub" and p["evergreen"])
add("plants-for-clay-shade", "Plants for clay soil in shade",
    "Tough plants for the hardest spot: heavy clay in shade.",
    lambda p: "CLAY" in p["soil"] and "NORTH" in p["aspect"])

# index of slug -> (h1, href) for related-collection cross-linking
COLL_INDEX = {slug: (h1, f"{slug}.html") for slug, h1, *_ in COLLECTIONS}


def related_for(slug, h1):
    # link a few thematically-adjacent collections
    picks = []
    for s2, h2, *_ in COLLECTIONS:
        if s2 == slug:
            continue
        a, b = slug.split("-")[0], s2.split("-")[0]
        if a == b or h1.split()[0] == h2.split()[0]:
            picks.append((h2, f"{s2}.html"))
    return picks[:6]


# --- emit ---------------------------------------------------------------------

FEATURED = [
    ("full-sun", "For full sun", "South or west-facing beds"),
    ("shade", "For shade", "North-facing and shaded spots"),
    ("soil-clay", "For clay soil", "Copes with heavy clay"),
    ("pollinator-friendly", "Pollinator-friendly", "Feeds bees and butterflies"),
    ("evergreen", "Evergreen", "Year-round structure"),
    ("style-cottage", "Cottage garden", "Relaxed, informal planting"),
    ("style-wildlife", "Wildlife garden", "Supports garden wildlife"),
    ("type-shrub", "Shrubs", "The backbone of a border"),
]


LIBRARY_LINKS = [
    ("full-sun", "Full sun"), ("shade", "Shade"), ("partial-shade", "Partial shade"),
    ("soil-clay", "Clay soil"), ("soil-sandy", "Sandy soil"), ("soil-chalk", "Chalk soil"),
    ("soil-wet", "Wet soil"), ("evergreen", "Evergreen"),
    ("pollinator-friendly", "Pollinator-friendly"), ("pet-safe", "Pet-safe"),
    ("low-edging", "Edging and front"), ("tall-back", "Back of border"),
    ("style-cottage", "Cottage garden"), ("style-wildlife", "Wildlife garden"),
    ("style-mediterranean", "Mediterranean"), ("type-shrub", "Shrubs"),
    ("type-perennial", "Perennials"), ("type-grass", "Ornamental grasses"),
]

GALLERY = [
    ("app-plan.webp", "Border Builder's top-down planting plan", "A complete plan, designed for you"),
    ("app-move.webp", "Moving and swapping plants on the map", "Move and swap until it is yours"),
    ("app-pdf.webp", "The shopping list exported as a PDF", "A shopping list for the nursery"),
]

STEPS = [
    ("1", "Describe your spot", "Tell it your bed size, aspect, soil and the look you want."),
    ("2", "Get your plan", "Every plant is chosen for your conditions and placed by role, with quantities."),
    ("3", "Plant it", "Take the drift map and the shopping list out to the garden."),
]


def qr_figure():
    return ('<figure class="qr"><img src="img/appstore-qr.svg" width="92" height="92" '
            'alt="QR code to download Border Builder on the App Store">'
            '<figcaption>Scan to download</figcaption></figure>')


def homepage_page():
    canon = f"{BASE_URL}/"
    gallery = "".join(
        f'<figure><img src="img/{src}" width="500" height="789" loading="lazy" alt="{e(alt)}">'
        f'<figcaption>{e(cap)}</figcaption></figure>'
        for src, alt, cap in GALLERY
    )
    steps = "".join(
        f'<div class="step"><span class="n">{n}</span><b>{e(t)}</b><span>{e(d)}</span></div>'
        for n, t, d in STEPS
    )
    tags = "".join(
        f'<a href="collections/{slug}.html">{e(label)}</a>' for slug, label in LIBRARY_LINKS
    )
    body = f"""
<section class="hero">
<div class="hero-copy">
<h1>Plan a garden border that blooms all year</h1>
<p class="sub">Border Builder is a garden border planner for iPhone and iPad. See your
border drawn out, painted as it will grow in, and flowering across the year, before you
buy a single plant.</p>
<div class="get">{store_buttons(up="")}{qr_figure()}</div>
<p class="get-note">Free to download. No account, no ads.</p>
</div>
<div class="hero-shot">
<img src="img/app-planted.webp" width="500" height="789"
alt="Border Builder showing a painted preview of a planted border">
</div>
</section>
<p class="trust">{len(PLANTS):,} plants, with hardiness and climate data built in. No account,
nothing tracked, works offline.</p>
<section class="block">
<h2>From a few details to a border you can build</h2>
<div class="gallery">{gallery}</div>
</section>
<section class="block">
<h2>How it works</h2>
<div class="steps">{steps}</div>
</section>
<section class="block">
<h2>Explore {len(PLANTS):,} plants</h2>
<p>Browse the catalogue by what you actually search for, then plan a border with what you find.</p>
<nav class="tags">{tags}</nav>
<p class="chips"><a class="chip" href="collections/index.html">All collections</a>
<a class="chip" href="plants/index.html">Every plant</a></p>
</section>
<section class="block">
<h2>Free, with an optional Pro unlock</h2>
<p>Designing a border and viewing the full plan, the drift map, the elevation and the
bloom timeline is free, with no account and nothing tracked. A one-time Pro purchase
saves unlimited borders, lets you edit the planting and re-plan around a month, and
exports the shopping list and PDF.</p>
</section>
<section class="endcta">
<h2>Design your border this weekend</h2>
<div class="get">{store_buttons(up="")}{qr_figure()}</div>
</section>
"""
    graph = [
        {"@type": "WebSite", "name": SITE_NAME, "url": BASE_URL + "/"},
        {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL + "/",
         "logo": BASE_URL + "/favicon.svg",
         "sameAs": [APP_STORE_URL] if APP_STORE_URL else []},
        {"@type": "MobileApplication", "name": "Border Builder: Garden Planner",
         "operatingSystem": "iOS", "applicationCategory": "LifestyleApplication",
         "url": BASE_URL + "/", "downloadUrl": APP_STORE_URL,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
    ]
    ld = {"@context": "https://schema.org", "@graph": graph}
    return page("Border Builder: garden border planner for iPhone and iPad",
                "Border Builder turns your bed's size, aspect, soil and style into a "
                "complete planting plan with a drift map, bloom timeline and shopping list. "
                "Free on the App Store. Browse 1,300+ plants by sun, soil and style.",
                canon, body, jsonld=ld, depth=0, main_class="home")


def write(relpath, content):
    full = os.path.join(HERE, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as fh:
        fh.write(content)


def main():
    for d in ("plants", "collections"):
        p = os.path.join(HERE, d)
        if os.path.isdir(p):
            shutil.rmtree(p)

    urls = ["/", "/collections/index.html"]
    indexed = 0

    for p in PLANTS:
        write(f"plants/{p['slug']}.html", plant_page(p))
        if indexable_plant(p):
            urls.append(f"/plants/{p['slug']}.html")
            indexed += 1

    coll_members = {}
    for slug, h1, title, intro, pred in COLLECTIONS:
        members = sorted([p for p in PLANTS if pred(p)], key=lambda p: p["common"].lower())
        if not members:
            continue
        coll_members[slug] = (h1, members)
        related_links = related_for(slug, h1)
        write(f"collections/{slug}.html",
              collection_page(slug, h1, title, intro, members, related_links))
        urls.append(f"/collections/{slug}.html")

    # browse hubs
    az = "".join(card(p) for p in sorted(PLANTS, key=lambda p: p["common"].lower()))
    write("plants/index.html", page(
        f"All plants ({len(PLANTS):,}) | {SITE_NAME}",
        f"Browse all {len(PLANTS):,} plants in Border Builder with size, aspect and bloom time.",
        f"{BASE_URL}/plants/index.html",
        f'{crumb_html([("Home","../index.html"),("Plants",None)])}'
        f'<header class="hero"><h1>All plants</h1></header>'
        f'<p class="lead">Every plant Border Builder can place in a border - {len(PLANTS):,} in all.</p>'
        f'<ul class="grid">{az}</ul>', depth=1, robots="noindex,follow"))

    coll_cards = "".join(
        f'<li><a href="{slug}.html"><b>{e(h1)}</b><span>{len(members)} plants</span></a></li>'
        for slug, (h1, members) in sorted(coll_members.items(), key=lambda kv: kv[1][0])
    )
    write("collections/index.html", page(
        f"Plant collections | {SITE_NAME}",
        "Curated plant lists by sun, soil, colour, style and more - then plan a border with Border Builder.",
        f"{BASE_URL}/collections/index.html",
        f'{crumb_html([("Home","../index.html"),("Collections",None)])}'
        f'<header class="hero"><h1>Plant collections</h1></header>'
        f'<p class="lead">Plants grouped by the things you actually search for: sun, soil, colour, style and size.</p>'
        f'<ul class="grid wide">{coll_cards}</ul>', depth=1))

    # homepage (replaces the old hand-authored stub: adds App Store CTA + paths
    # into the plant guides, the site's highest-authority internal links)
    write("index.html", homepage_page())

    # sitemap + robots
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"<url><loc>{e(BASE_URL + u)}</loc><lastmod>2026-06-22</lastmod></url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

    print(f"plants: {len(PLANTS)} ({indexed} indexed)  collections: {len(coll_members)}  sitemap urls: {len(urls)}")


if __name__ == "__main__":
    main()
