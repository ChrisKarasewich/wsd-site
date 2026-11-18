# wsd-site

The website for Winnipeg Sewer & Drain at https://winnipegsd.com. Plain static HTML, CSS, JS and images, built and maintained by AdEasy.

This repo is the source of truth for the live site. Every change starts from the files here, never from an older zip or export, so fixes made since then aren't lost.

## How deploys work

Every commit to `main` deploys automatically through Cloudflare Workers (static assets) in a minute or two. Nothing is built on the server.

- `wrangler.jsonc` tells Cloudflare to serve the repo root, give every page an extensionless URL (`/services` serves `services.html`, and `/services.html` redirects to `/services`), and show `404.html` for unknown URLs.
- `.assetsignore` keeps repo-only files (this README, `tools/`, `wrangler.jsonc`, old duplicate images) off the live site.
- `_redirects` holds 301s from old or mistaken URLs. Keep its rules permanently.
- `_headers` sets cache times.
- To roll back a bad upload: Cloudflare dashboard, Workers & Pages, wsd-site, Deployments, then roll back to the previous one.

## Folder map

| Path | What it is |
| --- | --- |
| `*.html` | One file per page. The URL is the file name without `.html` |
| `colors_and_type.css`, `styles.css`, `responsive.css`, `static-overrides.css` | The four stylesheets every page loads, in that order |
| `interactive.js` | Header, FAQ accordions, mobile menu, booking form and Turnstile |
| `assets/` | Original images. File names never change once live |
| `assets/opt/` | AVIF and WebP copies made by `tools/build-images.py`. Don't edit by hand |
| `favicon/`, `favicon.ico`, `apple-touch-icon.png` | Browser and phone icons |
| `sitemap.xml`, `robots.txt`, `llms.txt` | For search engines and AI assistants |
| `tools/` | Build and check scripts (not deployed) |

## Tracking and IDs

All IDs live in the block at the top of `tools/build-html.py`, which writes the same head into every page.

| What | ID |
| --- | --- |
| Google Tag Manager | `GTM-T2GJGN48` (loads on first interaction or 2 s after page load) |
| Google Ads tag | `AW-18172707643` (loaded directly for CallRail's Google Ads integration) |
| CallRail | company `942559939`, `swap.js` loaded async |
| Search Console | verified by meta tag and `google09ee42e36b295892.html` |
| Turnstile site key | in `interactive.js` (the secret key lives only in the Apps Script) |
| Form endpoint | Google Apps Script URL in `interactive.js` |

## How the booking form works

`interactive.js` adds a Cloudflare Turnstile check to every booking form, then posts the form and the Turnstile token to the Google Apps Script. The script checks the token with Cloudflare, writes the row to the "WSD Website Form Submissions" Sheet and sends the email. The post uses `no-cors`, so the page can't see the script's answer: the visitor goes to `/thank-you` even if the script rejected or lost the lead. Test with a real submission after any change to the form, Turnstile or the script.

## Making changes

Use the scripts from the repo root (Python 3 with Pillow installed):

1. Edit the page or CSS.
2. New or replaced image: put it in `assets/`, add it to `PLAN` in `tools/build-images.py`, run `python3 tools/build-images.py`.
3. Run `python3 tools/build-html.py`. It rewrites each page's head, wraps images, fixes links, labels and schema. Safe to run any number of times.
4. Run `python3 tools/check-site.py`. Upload only when it prints PASS.
5. Add a line to `CHANGELOG.md`.

### Adding a page

1. Copy the closest existing page and rename it (lowercase, hyphens: `new-page.html`).
2. Change its `<title>` (50 to 60 characters) and meta description (140 to 160 characters).
3. Add its URL to `sitemap.xml` with today's date in `<lastmod>`, and link to it from the nav or footer if it belongs there.
4. Run steps 3 and 4 above. The builder adds the canonical, share tags, favicon, tracking and breadcrumb schema.

### Removing or renaming a page

Delete or rename the file in GitHub by hand (uploads never delete anything), add a `_redirects` line from the old URL to its closest new page, and update `sitemap.xml`.
