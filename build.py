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
    HERE, "..", "border-builder-android", "app", "src", "main", "assets", "plants.json"
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
        "months": [m for m in (p.get("flowerMonths") or []) if m in MONTHS],
        "hardiness": p.get("hardiness") or {},
        "petSafe": "yes" if truthy(p.get("petSafe")) else ("no" if falsy(p.get("petSafe")) else "unknown"),
        "pollinator": truthy(p.get("pollinatorFriendly")),
        "citations": p.get("bloomCitations") or {},
    }


PLANTS = [norm(p) for p in RAW]
BY_SLUG = {p["slug"]: p for p in PLANTS}

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


def page(title, description, canonical, body, jsonld=None, depth=1, main_class=""):
    up = "../" * depth
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
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


def plant_page(p):
    canon = f"{BASE_URL}/plants/{p['slug']}.html"
    title = f"{p['common']} ({p['name']}) care and planting guide | {SITE_NAME}"
    months_txt = ", ".join(MONTH_LABEL[m] for m in p["months"]) or "varies by climate"
    desc = (f"{p['common']} ({p['name']}): {p['type']}, "
            f"{p['height']}cm tall, {aspect_words(p['aspect'])}, flowers {months_txt}. "
            "Plan a border with it in Border Builder.")[:300]

    style_links = " ".join(
        f'<a class="chip" href="../collections/{slugify("style-" + s)}.html">{e(STYLE_LABEL.get(s, s.title()))}</a>'
        for s in sorted(p["styles"]) if s in STYLE_LABEL
    )
    role_txt = ", ".join(ROLE_LABEL.get(r, r.lower()) for r in sorted(p["roles"])) or "border planting"
    rel = related(p)
    rel_html = "".join(
        f'<li><a href="{q["slug"]}.html"><b>{e(q["common"])}</b><span>{e(q["name"])}</span></a></li>'
        for q in rel
    )
    trail = [("Home", "/index.html"), ("Plants", "/plants/index.html"), (p["common"], None)]
    body = f"""
{crumb_html([("Home","../index.html"),("Plants","index.html"),(p["common"],None)])}
<header class="hero">
<h1>{e(p["common"])}</h1>
<p class="latin">{e(p["name"])}</p>
</header>
<p class="lead">{e(p["common"])} is a {e(p["type"])} for {e(role_txt)}, growing to about {p["height"]} cm.
It suits {e(aspect_words(p["aspect"]))} and flowers {e(months_txt)}.</p>
{fact_rows(p)}
<h2>Flowering through the year</h2>
{bloom_strip(p["months"])}
<h2>Garden styles</h2>
<p class="chips">{style_links or "Versatile across planting styles."}</p>
{cta(f"Place {p['common']} in a real border with the right spacing and neighbours - Border Builder draws the plan for you.", up="../")}
{citation_block(p["citations"])}
<h2>Similar plants</h2>
<ul class="grid">{rel_html}</ul>
"""
    ld = breadcrumbs(trail)
    return page(title, desc, canon, body, jsonld=ld, depth=1)


# --- collection pages ---------------------------------------------------------

def card(p):
    return (f'<li><a href="../plants/{p["slug"]}.html"><b>{e(p["common"])}</b>'
            f'<span>{e(p["name"])}</span></a></li>')


def collection_page(slug, h1, title, intro, members, related_links):
    canon = f"{BASE_URL}/collections/{slug}.html"
    desc = (intro + f" {len(members)} plants in Border Builder.")[:300]
    cards = "".join(card(p) for p in members)
    rel = "".join(f'<a class="chip" href="{e(href)}">{e(name)}</a>' for name, href in related_links)
    rel_block = f'<h2>Related collections</h2><p class="chips">{rel}</p>' if rel else ""
    body = f"""
{crumb_html([("Home","../index.html"),("Collections","index.html"),(h1,None)])}
<header class="hero"><h1>{e(h1)}</h1></header>
<p class="lead">{e(intro)}</p>
{cta("Pick from these and Border Builder arranges them into a planting plan: how many, where they go, and how the border reads through the seasons.", up="../")}
<h2>{len(members)} plants</h2>
<ul class="grid">{cards}</ul>
{rel_block}
"""
    item_list = {
        "@context": "https://schema.org", "@type": "ItemList",
        "numberOfItems": len(members),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": p["common"],
             "url": f"{BASE_URL}/plants/{p['slug']}.html"}
            for i, p in enumerate(members[:50])
        ],
    }
    return page(title, desc, canon, body, jsonld=item_list, depth=1)


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
    ("app-plan.webp", "Border Builder top-down planting plan with plant drifts and spacing"),
    ("app-move.webp", "Moving and swapping plants on the border map in Border Builder"),
    ("app-pdf.webp", "Border Builder shopping list exported as a PDF"),
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
    canon = f"{BASE_URL}/index.html"
    gallery = "".join(
        f'<img src="img/{src}" width="500" height="1084" loading="lazy" alt="{e(alt)}">'
        for src, alt in GALLERY
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
<h1>Know the bed before you dig</h1>
<p class="sub">See your border drawn out, painted as it will grow in, and flowering
across the year, before you buy a single plant.</p>
<div class="get">{store_buttons(up="")}{qr_figure()}</div>
</div>
<div class="hero-shot">
<img src="img/app-planted.webp" width="500" height="789"
alt="Border Builder showing a painted preview of a planted border">
</div>
</section>
<p class="trust">{len(PLANTS):,} plants, each checked against your climate. No account,
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

    urls = ["/index.html", "/plants/index.html", "/collections/index.html"]

    for p in PLANTS:
        write(f"plants/{p['slug']}.html", plant_page(p))
        urls.append(f"/plants/{p['slug']}.html")

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
        f'<ul class="grid">{az}</ul>', depth=1))

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
        sm.append(f"<url><loc>{e(BASE_URL + u)}</loc></url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

    print(f"plants: {len(PLANTS)}  collections: {len(coll_members)}  total urls: {len(urls)}")


if __name__ == "__main__":
    main()
