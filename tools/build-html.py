"""Page builder for winnipegsd.com.

Rewrites every page's <head> into one identical, verified block and applies
the site-wide fixes (images, links, landmarks, labels, schema). It reads the
page-specific values (title, description, canonical, existing schema) from
each page, so re-running it is safe: run `python3 tools/build-html.py` from
the repo root after editing any page, then `python3 tools/check-site.py`.

Every tracking ID and key the site uses lives in the block below.
"""
import importlib.util
import json
import re
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# IDs AND KEYS (change them here only)
# ---------------------------------------------------------------------------
SITE = "https://winnipegsd.com"
SITE_NAME = "Winnipeg Sewer & Drain"
GTM_ID = "GTM-T2GJGN48"
GOOGLE_ADS_ID = "AW-18172707643"  # loaded directly for CallRail's Google Ads integration
CALLRAIL_SWAP = "https://cdn.callrail.com/companies/942559939/d0c1f8d88fce79747c4c/12/swap.js"
SEARCH_CONSOLE_TOKEN = "zcx1XDfJCPyUAQCl6fv2zF231eoT747knFELyVHzgm4"
PHONE_DISPLAY = "(204) 786-4060"
PHONE_TEL = "+12047864060"
SHARE_IMAGE = "/assets/og-share.jpg"
# GTM waits for the visitor's first tap, scroll or key press, or this many ms
# after the page finishes loading, whichever comes first. Lower it if GA4
# sessions drop after launch; set it to 0 to load GTM right at page load.
GTM_DELAY_MS = 2000
# Turnstile site key and the form endpoint live in interactive.js.

# Pages the builder should not touch (Search Console verification file).
SKIP = {"google09ee42e36b295892.html"}

# Pages that are blog posts: (date shown on the page, ISO date for schema).
BLOG_PREFIX = "blog-"

SERVICE_PAGES = {
    "drain-cleaning", "sewer-line-cleaning", "hydro-jetting",
    "sewer-camera-inspection", "frozen-sewer-thawing", "emergency-service",
}
PAGE_TYPES = {
    "contact": "ContactPage", "about": "AboutPage", "recent-updates": "CollectionPage",
    "services": "CollectionPage", "reviews": "WebPage", "faq": "FAQPage",
}

IMAGE_SIZES = json.loads((ROOT / "tools" / "image-sizes.json").read_text())
# Image widths come from tools/build-images.py so the two scripts never disagree.
_spec = importlib.util.spec_from_file_location("build_images", ROOT / "tools" / "build-images.py")
_images = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_images)
IMAGE_PLAN = _images.PLAN
FOLD = 800  # images starting below this many px get loading="lazy"

MONTHS = {m: i for i, m in enumerate(
    "January February March April May June July August September October November December".split(), 1)}


def meta(head, key):
    m = re.search(r'<meta\s+(?:name|property)="%s"\s+content="([^"]*)"' % re.escape(key), head)
    return unescape(m.group(1)) if m else ""


def attr(text):
    return escape(text, quote=True)


def page_url(slug):
    return SITE + "/" if slug == "index" else f"{SITE}/{slug}"


def short_title(title):
    return re.split(r"\s+(?:—|&mdash;|\|)\s+", title)[0].strip()


# ---------------------------------------------------------------------------
# HEAD
# ---------------------------------------------------------------------------
GTM_HEAD = """<script>
  /* GTM loads on first interaction or %(delay)s ms after load, so it doesn't block the page.
     Visitors who leave before either happens are not counted. */
  (function (w, d, id, delay) {
    w.dataLayer = w.dataLayer || [];
    w.dataLayer.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
    var done = false;
    var events = ["pointerdown", "touchstart", "keydown", "scroll"];
    function load() {
      if (done) return;
      done = true;
      events.forEach(function (e) { w.removeEventListener(e, load, { passive: true }); });
      var s = d.createElement("script");
      s.async = true;
      s.src = "https://www.googletagmanager.com/gtm.js?id=" + id;
      d.head.appendChild(s);
    }
    events.forEach(function (e) { w.addEventListener(e, load, { passive: true }); });
    w.addEventListener("load", function () { setTimeout(load, delay); });
  })(window, document, "%(gtm)s", %(delay)s);
</script>"""

GTM_BODY = ('<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=%s" '
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>')

FONTS_URL = ("https://fonts.googleapis.com/css2?family=Bebas+Neue"
             "&amp;family=Poppins:wght@400;500;600;700&amp;display=swap")


def build_head(slug, old_head, schema_blocks, styles):
    title = unescape(re.search(r"<title>(.*?)</title>", old_head, re.S).group(1)).strip()
    desc = meta(old_head, "description")
    og_title = meta(old_head, "og:title") or title
    og_desc = meta(old_head, "og:description") or desc
    robots = meta(old_head, "robots")
    url = page_url(slug)
    is_blog = slug.startswith(BLOG_PREFIX)
    lines = [
        "<!-- Meta -->",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{attr(title)}</title>",
        f'<meta name="description" content="{attr(desc)}">',
    ]
    if slug != "404":  # the 404 page is served at many URLs, so it gets no canonical
        lines.append(f'<link rel="canonical" href="{url}">')
    if robots:
        lines.append(f'<meta name="robots" content="{attr(robots)}">')
    lines += [
        f'<meta name="google-site-verification" content="{SEARCH_CONSOLE_TOKEN}">',
        f'<meta property="og:type" content="{"article" if is_blog else "website"}">',
        f'<meta property="og:site_name" content="{attr(SITE_NAME)}">',
        '<meta property="og:locale" content="en_CA">',
    ]
    if slug != "404":
        lines.append(f'<meta property="og:url" content="{url}">')
    lines += [
        f'<meta property="og:title" content="{attr(og_title)}">',
        f'<meta property="og:description" content="{attr(og_desc)}">',
        f'<meta property="og:image" content="{SITE}{SHARE_IMAGE}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{attr(SITE_NAME)}: sewer and drain specialists in Winnipeg">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{attr(og_title)}">',
        f'<meta name="twitter:description" content="{attr(og_desc)}">',
        f'<meta name="twitter:image" content="{SITE}{SHARE_IMAGE}">',
        '<meta name="theme-color" content="#011538">',
        "",
        "<!-- Favicon -->",
        '<link rel="icon" href="/favicon.ico" sizes="48x48">',
        '<link rel="icon" href="/favicon/favicon-32x32.png" type="image/png" sizes="32x32">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<link rel="manifest" href="/favicon/site.webmanifest">',
        "",
        "<!-- Fonts -->",
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        f'<link rel="stylesheet" href="{FONTS_URL}">',
        "",
        "<!-- Stylesheets (same four on every page) -->",
        '<link rel="stylesheet" href="/colors_and_type.css">',
        '<link rel="stylesheet" href="/styles.css">',
        '<link rel="stylesheet" href="/responsive.css">',
        '<link rel="stylesheet" href="/static-overrides.css">',
    ]
    if slug == "index":
        lines += [
            '<link rel="preload" as="image" type="image/avif" fetchpriority="high" '
            'href="/assets/opt/hero-image-520.avif" '
            'imagesrcset="/assets/opt/hero-image-520.avif 520w, /assets/opt/hero-image-800.avif 800w" '
            f'imagesizes="{IMG_SIZES_HERO}">',
        ]
    for style in styles:
        lines += ["", style.strip()]
    lines += [
        "",
        "<!-- Tracking -->",
        GTM_HEAD % {"gtm": GTM_ID, "delay": GTM_DELAY_MS},
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_ADS_ID}"></script>',
        "<script>",
        "  window.dataLayer = window.dataLayer || [];",
        "  function gtag() { dataLayer.push(arguments); }",
        "  gtag(\"js\", new Date());",
        f"  gtag(\"config\", \"{GOOGLE_ADS_ID}\");",
        "</script>",
        '<link rel="preconnect" href="https://cdn.callrail.com">',
        f'<script async src="{CALLRAIL_SWAP}"></script>',
        "",
        "<!-- Schema -->",
    ]
    for block in schema_blocks:
        lines.append('<script type="application/ld+json">%s</script>'
                     % json.dumps(block, ensure_ascii=False, separators=(",", ":")))
    return "<head>\n" + "\n".join(lines) + "\n</head>"


IMG_SIZES_HERO = "(max-width: 640px) 260px, (max-width: 900px) 320px, 594px"


# ---------------------------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------------------------
BUSINESS_ID = SITE + "/#business"


def breadcrumb(slug, title):
    items = [("Home", SITE + "/")]
    if slug.startswith(BLOG_PREFIX):
        items.append(("Recent updates", page_url("recent-updates")))
    elif slug in SERVICE_PAGES:
        items.append(("Services", page_url("services")))
    items.append((title, page_url(slug)))
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": n, "item": u}
            for i, (n, u) in enumerate(items, 1)
        ],
    }


def visible_date(body):
    m = re.search(r"(%s) (\d{1,2}), (20\d\d)" % "|".join(MONTHS), body)
    if not m:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def fix_schema(slug, blocks, title, body):
    """Make URLs absolute, credit articles to the business, add missing types."""
    types = set()
    out = []
    for b in blocks:
        t = b.get("@type")
        types.add(t)
        if t == "BreadcrumbList":
            continue  # rebuilt below so it always matches the URL
        if t == "Article":
            img = str(b.get("image") or SHARE_IMAGE)
            b["image"] = img if img.startswith("http") else SITE + "/" + img.lstrip("/")
            b["mainEntityOfPage"] = {"@type": "WebPage", "@id": page_url(slug)}
            b["author"] = {"@type": "Organization", "@id": BUSINESS_ID, "name": SITE_NAME}
            b["publisher"] = {"@type": "Organization", "@id": BUSINESS_ID, "name": SITE_NAME,
                              "logo": {"@type": "ImageObject", "url": SITE + "/assets/wsd-logo-primary.png"}}
        out.append(b)
    if slug == "404":
        return []
    if slug == "index":
        if "WebSite" not in types:
            out.append({"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME,
                        "alternateName": "WSD", "url": SITE + "/"})
        return out
    if slug.startswith(BLOG_PREFIX) and "Article" not in types:
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        headline = re.sub(r"<[^>]+>", " ", h1.group(1)) if h1 else title
        art = {
            "@context": "https://schema.org", "@type": "Article",
            "headline": " ".join(unescape(headline).split()),
            "image": SITE + SHARE_IMAGE,
            "mainEntityOfPage": {"@type": "WebPage", "@id": page_url(slug)},
            "author": {"@type": "Organization", "@id": BUSINESS_ID, "name": SITE_NAME},
            "publisher": {"@type": "Organization", "@id": BUSINESS_ID, "name": SITE_NAME,
                          "logo": {"@type": "ImageObject", "url": SITE + "/assets/wsd-logo-primary.png"}},
        }
        date = visible_date(body)
        if date:  # only the date printed on the page; never a guess
            art["datePublished"] = date
        out.append(art)
    elif not (types & {"Article", "Service", "FAQPage", "WebPage", "ContactPage",
                       "AboutPage", "CollectionPage"}):
        out.append({"@context": "https://schema.org", "@type": PAGE_TYPES.get(slug, "WebPage"),
                    "name": title, "url": page_url(slug),
                    "isPartOf": {"@type": "WebSite", "url": SITE + "/"},
                    "about": {"@id": BUSINESS_ID}})
    out.append(breadcrumb(slug, title))
    return out


# ---------------------------------------------------------------------------
# BODY
# ---------------------------------------------------------------------------
def local_pages():
    return {p.stem for p in ROOT.glob("*.html")}


def fix_links(html, pages):
    def repl(m):
        target, frag = m.group(2), m.group(3) or ""
        if target not in pages:
            return m.group(0)
        path = "/" if target == "index" else "/" + target
        return f'{m.group(1)}"{path}{frag}"'
    return re.sub(r'(href=)"(?:\./|/)?([a-z0-9-]+)\.html(#[^"]*)?"', repl, html)


def picture(img, slug, counters):
    src = re.search(r'src="([^"]+)"', img).group(1)
    name = src.split("/")[-1]
    if name not in IMAGE_PLAN:
        return img
    idx = counters.get(src, 0)
    counters[src] = idx + 1
    measured = IMAGE_SIZES.get(f"{slug}|{src}|{idx}", {})
    stem = name.rsplit(".", 1)[0]
    widths = IMAGE_PLAN[name]
    is_hero = name == "hero-image.jpg"
    if is_hero:
        sizes = IMG_SIZES_HERO
    else:
        phone = measured.get("m") or 376
        desk = measured.get("d") or 934
        sizes = f"(max-width: 640px) {max(phone, 1)}px, {max(desk, 1)}px"
    from PIL import Image  # local import keeps the script light when images aren't touched
    with Image.open(ROOT / src.lstrip("/")) as im:
        w, h = im.size
    new = re.sub(r'\s(?:width|height|decoding)="[^"]*"', "", img)
    new = new.replace("<img ", f'<img width="{w}" height="{h}" decoding="async" ', 1)
    new = new.replace('src="assets/', 'src="/assets/')
    top = min(measured.get("top_m", 0), measured.get("top_d", 0))
    if is_hero:
        new = new.replace("<img ", '<img fetchpriority="high" ', 1)
    elif "loading=" not in new and top > FOLD:
        new = new.replace("<img ", '<img loading="lazy" ', 1)
    sources = "".join(
        f'<source type="image/{fmt}" srcset="'
        + ", ".join(f"/assets/opt/{stem}-{x}.{fmt} {x}w" for x in widths)
        + f'" sizes="{sizes}">'
        for fmt in ("avif", "webp")
    )
    return f'<picture style="display:contents">{sources}{new}</picture>'


def fix_images(html, slug):
    counters = {}

    def repl(m):
        if m.group(0).startswith("<picture"):
            # Already wrapped on an earlier run: just keep the instance count in step.
            src = re.search(r'<img [^>]*src="/?([^"]+)"', m.group(0)).group(1)
            counters[src] = counters.get(src, 0) + 1
            return m.group(0)
        return picture(m.group(0), slug, counters)
    return re.sub(r"<picture\b.*?</picture>|<img [^>]*>", repl, html, flags=re.S)


def fix_labels(html, slug):
    def form_repl(fm):
        form = fm.group(0)

        def field(m):
            label_attrs, text, control, rest = m.groups()
            name = re.search(r'name="([^"]+)"', rest)
            if not name or " for=" in label_attrs:
                return m.group(0)
            fid = f"wsd-{slug}-{name.group(1).replace('_', '-')}"
            if " id=" not in rest:
                rest = f' id="{fid}"' + rest
            return f'<label{label_attrs} for="{fid}">{text}</label><{control}{rest}'
        return re.sub(r'<label( class="field__label")>(.*?)</label><(input|select|textarea)([^>]*)',
                      field, form)
    return re.sub(r"<form\b.*?</form>", form_repl, html, flags=re.S)


def fix_landmarks(html):
    if 'class="skip-link"' not in html:
        html = re.sub(r"(<body[^>]*>(?:\n<noscript><iframe[^>]*></iframe></noscript>)?)",
                      r'\1\n<a class="skip-link" href="#main">Skip to content</a>', html, count=1)
    if "<main" not in html:
        html = html.replace("</header>", '</header><main id="main">', 1)
        i = html.rfind("<footer")
        html = html[:i] + "</main>" + html[i:]
    else:
        html = re.sub(r"<main(?![^>]*\bid=)", '<main id="main"', html, count=1)
    html = re.sub(r"<nav(?![^>]*aria-label)", '<nav aria-label="Primary"', html, count=1)
    return html


def fix_gtm_noscript(html):
    html = re.sub(r"\s*<!-- Google Tag Manager \(noscript\) -->\s*", "\n", html)
    html = re.sub(r"\s*<!-- End Google Tag Manager \(noscript\) -->\s*", "\n", html)
    html = re.sub(r'<noscript><iframe src="https://www\.googletagmanager\.com/ns\.html\?id=[^"]*"[^>]*></iframe></noscript>\s*',
                  "", html)
    return re.sub(r"(<body[^>]*>)", r"\1\n" + GTM_BODY % GTM_ID, html, count=1)


def fix_placeholders(html):
    html = html.replace("(204) 555-0123", PHONE_DISPLAY).replace("tel:+12045550123", "tel:" + PHONE_TEL)
    return html.replace("GTM-XXXXXXX", GTM_ID)


# ---------------------------------------------------------------------------
def build_page(path, pages):
    slug = path.stem
    html = path.read_text()
    head_m = re.search(r"<head>(.*?)</head>", html, re.S)
    old_head = head_m.group(1)
    schema = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', old_head, re.S):
        data = json.loads(raw)
        schema.extend(data if isinstance(data, list) else [data])
    styles = re.findall(r"<style\b.*?</style>", old_head, re.S)
    body = html[head_m.end():]
    title = short_title(unescape(re.search(r"<title>(.*?)</title>", old_head, re.S).group(1)))
    schema = fix_schema(slug, schema, title, body)
    head = build_head(slug, old_head, schema, styles)

    body = fix_placeholders(body)
    body = fix_gtm_noscript(body)
    body = fix_landmarks(body)
    body = fix_labels(body, slug)
    body = fix_images(body, slug)
    body = fix_links(body, pages)
    body = body.replace('src="interactive.js"', 'src="/interactive.js"')
    out = '<!doctype html>\n<html lang="en-CA">\n' + head + body
    path.write_text(out)


def main():
    pages = local_pages() - {s[:-5] for s in SKIP}
    for path in sorted(ROOT.glob("*.html")):
        if path.name in SKIP:
            continue
        build_page(path, pages)
        print("built", path.name)


if __name__ == "__main__":
    main()
