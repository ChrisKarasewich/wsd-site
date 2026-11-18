"""Pre-upload checks for winnipegsd.com.

Run `python3 tools/check-site.py` from the repo root before uploading.
It prints FAIL lines for anything that would break the live site or its
tracking, and exits with an error if any are found.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GTM_ID = "GTM-T2GJGN48"
REAL_PHONE = "786-4060"
STYLESHEETS = ["/colors_and_type.css", "/styles.css", "/responsive.css", "/static-overrides.css"]
SKIP = {"google09ee42e36b295892.html"}
# Files that are fine to have no links pointing at them.
STANDALONE = {"robots.txt", "sitemap.xml", "llms.txt", "404.html", "_redirects", "_headers",
              "wrangler.jsonc", ".assetsignore", ".gitignore", ".gitattributes", "README.md",
              "CHANGELOG.md", "DEPLOYMENT-README.md", "favicon.ico", "apple-touch-icon.png",
              "google09ee42e36b295892.html",
              # Kept at their old URLs because they may be linked from outside the site.
              "og-share.png", "wsd-logo.jpeg", "wsd-wordmark.png",
              "favicon-16x16.png", "favicon-48x48.png"}
PLACEHOLDERS = re.compile(r"GTM-XXXX|555-\d{4}|example\.com|lorem ipsum|TODO|\bXXX\b", re.I)

failures = []


def fail(page, msg):
    failures.append(f"FAIL {page}: {msg}")


class Strict(HTMLParser):
    def error(self, message):  # pragma: no cover
        raise ValueError(message)


def resolve(ref, page):
    ref = ref.split("#")[0].split("?")[0]
    if ref.startswith("https://winnipegsd.com/"):
        ref = ref[len("https://winnipegsd.com"):]
    if not ref or re.match(r"^(https?:|mailto:|tel:|data:|javascript:|//)", ref):
        return None
    path = ROOT / ref.lstrip("/") if ref.startswith("/") else (ROOT / page).parent / ref
    if ref in ("/", ""):
        return ROOT / "index.html"
    if path.is_file():
        return path
    if path.with_name(path.name + ".html").is_file():
        return path.with_name(path.name + ".html")
    return False


referenced = set()
pages = sorted(p for p in ROOT.glob("*.html") if p.name not in SKIP)
for page in pages:
    name = page.name
    html = page.read_text()
    Strict().feed(html)
    head = html.split("</head>")[0]

    if html.count(GTM_ID) < 2:
        fail(name, "GTM container missing from head or body")
    for sheet in STYLESHEETS:
        if f'href="{sheet}"' not in head:
            fail(name, f"missing stylesheet {sheet}")
    if "@import" in html:
        fail(name, "@import found")
    if m := PLACEHOLDERS.search(html):
        fail(name, f"placeholder text: {m.group(0)}")
    for tel in re.findall(r"\(204\) \d{3}-\d{4}", html):
        if REAL_PHONE not in tel and "000-0000" not in tel:
            fail(name, f"unexpected phone number {tel}")
    for tag in ("<title>", 'name="description"', 'property="og:image"', 'rel="icon"', "swap.js"):
        if tag not in head:
            fail(name, f"head is missing {tag}")
    if name != "404.html":
        for tag in ('rel="canonical"', 'property="og:url"'):
            if tag not in head:
                fail(name, f"head is missing {tag}")
        canon = re.search(r'rel="canonical" href="https://winnipegsd\.com(/[^"]*)"', head)
        expected = "/" if name == "index.html" else "/" + name[:-5]
        if not canon or canon.group(1) != expected:
            fail(name, f"canonical should be {expected}")
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(raw)
        except ValueError as e:
            fail(name, f"invalid JSON-LD: {e}")
    if 'id="main"' not in html or 'class="skip-link"' not in html:
        fail(name, "missing <main id=\"main\"> or skip link")
    for form in re.findall(r"<form\b.*?</form>", html, re.S):
        for fid in re.findall(r'<(?:input|select|textarea)[^>]*\bid="([^"]+)"', form):
            if f'for="{fid}"' not in form:
                fail(name, f"form control {fid} has no label")
        if re.search(r'<label class="field__label">', form):
            fail(name, "form label without for=")
    for img in re.findall(r"<img [^>]*>", html):
        if "width=" not in img or "height=" not in img:
            fail(name, f"img without width/height: {img[:80]}")
        if "alt=" not in img:
            fail(name, f"img without alt: {img[:80]}")
    refs = re.findall(r'(?:href|src)="([^"]+)"', html)
    refs += re.findall(r'content="(https://winnipegsd\.com/[^"]+)"', html)
    for srcset in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', html):
        refs += [part.strip().split(" ")[0] for part in srcset.split(",")]
    for ref in refs:
        target = resolve(ref, name)
        if target is False:
            fail(name, f"broken reference {ref}")
        elif target:
            referenced.add(target.resolve())
            if ref.endswith(".html"):
                fail(name, f"link points at a redirect: {ref}")

for css in ROOT.glob("*.css"):
    for ref in re.findall(r"url\(['\"]?([^'\")]+)", css.read_text()):
        target = resolve(ref, css.name)
        if target:
            referenced.add(target.resolve())
for ref in re.findall(r"""['"](/?assets/[^'"]+)['"]""", (ROOT / "interactive.js").read_text()):
    if (target := resolve(ref, "interactive.js")):
        referenced.add(target.resolve())
for line in (ROOT / "favicon" / "site.webmanifest").read_text().splitlines():
    if (m := re.search(r'"src": "([^"]+)"', line)):
        referenced.add(resolve(m.group(1), "x").resolve())

ignored = [l.strip().strip("/") for l in (ROOT / ".assetsignore").read_text().splitlines()
           if l.strip() and not l.startswith("#")]
unreferenced = []
for f in ROOT.rglob("*"):
    rel = f.relative_to(ROOT)
    if not f.is_file() or any(str(rel).startswith(i) for i in ignored) or rel.parts[0] == ".git":
        continue
    if f.suffix == ".html" or f.name in STANDALONE or f.resolve() in referenced:
        continue
    unreferenced.append(str(rel))
for f in sorted(unreferenced):
    fail("repo", f"unreferenced file (delete it, or it ships with every deploy): {f}")

print("\n".join(failures) if failures else f"PASS: {len(pages)} pages checked, no problems found")
sys.exit(1 if failures else 0)
