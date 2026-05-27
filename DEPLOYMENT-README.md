# WSD Website Deployment Guide

Everything you need to take this from a folder on your computer to a live website at winnipegsd.com, with tracking and lead-capture wired up properly.

## What's in this folder

The contents of `wsd-site/` are the deployable static site. Open `index.html` in any browser to preview locally before deploying.

Production prep already applied across all 14 pages:

- Favicon set generated from the WSD logo (16, 32, 48, 180, 192, 512px plus .ico and webmanifest)
- Google Tag Manager placeholder snippet installed in every page's head
- GTM noscript fallback installed at the top of every body
- Open Graph and Twitter Card meta tags for social sharing
- Canonical URLs pointing to winnipegsd.com
- LocalBusiness (Plumber) schema markup on the homepage for Google rich results
- robots.txt and sitemap.xml at the root
- Comment block above every `<form>` block explaining how to swap in the FSM embed
- Theme color set to WSD navy (#011538)

## Pre-launch checklist (do these before going live)

Six placeholders need real values swapped in. None are hard. Do them in this order.

### 1. Replace GTM container ID

Once you create the GTM container for WSD, do a project-wide find and replace:

- Find: `GTM-XXXXXXX`
- Replace with: your real GTM container ID (looks like `GTM-AB12CDE`)

This appears once in each page's head and once in each body's noscript fallback. 28 replacements total across 14 pages, all handled by one find and replace.

### 2. Replace the phone number

When WSD has their new line, do another project-wide find and replace:

- Find: `+12045550123`
- Replace with: the real number in international format, no spaces or dashes (e.g., `+12041234567`)

Then a second pass for the display version:

- Find: `(204) 555-0123`
- Replace with: the real display format (e.g., `(204) 123-4567`)

These two replacements cover both the `tel:` link href values and the visible button text across every page.

### 3. Add the real phone number to the homepage schema

Open `index.html`, find `REPLACE_WITH_REAL_PHONE_E164_FORMAT` inside the JSON-LD schema block, replace with the E.164 phone (e.g., `+12041234567`). This is what tells Google your business phone for the LocalBusiness rich result.

### 4. Swap in the FSM form embed

The current `<form>` blocks are visual placeholders. They don't submit anywhere. Each form is marked with a clearly visible comment block.

When the FSM (ServiceTitan, Jobber, Housecall Pro, whatever WSD uses) gives you the embed code, you have two paths.

If it's an iframe embed, replace the entire `<form>...</form>` block with:

```html
<div class="card" style="padding:0; overflow:hidden; border-left:4px solid var(--wsd-blue);">
  <iframe
    src="PASTE_FSM_IFRAME_URL_HERE"
    width="100%"
    height="720"
    frameborder="0"
    style="display:block;border:0;"
    title="Book a sewer or drain job">
  </iframe>
</div>
```

If it's a script and container embed, paste the FSM's `<script>` tag just before `</body>` in `index.html` and `contact.html`, and replace the form block with the FSM's target `<div>`.

Forms appear in `index.html` and `contact.html`. Both need the swap.

### 5. Update the email address (optional)

The placeholder email in the footer and contact page is `hello@winnipegsewerdrain.ca`. If WSD prefers a different address, search and replace that string.

### 6. Confirm hero image and OG sharing image

The default Open Graph image for most pages is `/assets/hero-image.png`. If WSD wants a different image to appear when the site is shared on Facebook, LinkedIn, or via SMS, drop a 1200x630 JPG into the assets folder and update the `og:image` reference in the relevant page's head.

## Deployment to Cloudflare Pages

The fast path. Five minutes start to finish.

### Option A: Drag and drop (simplest)

1. Sign in at dash.cloudflare.com
2. Workers and Pages, Create, Pages tab, Upload assets
3. Project name: `wsd-website` (this becomes your preview URL: `wsd-website.pages.dev`)
4. Drag the contents of `wsd-site/` into the upload area (everything: the HTML files, the assets folder, the favicon folder, the CSS files, the JS file, robots.txt, sitemap.xml)
5. Click Deploy. Cloudflare will publish in about 30 seconds.

### Option B: GitHub + auto-deploy (recommended long-term)

This is the version you want for ongoing edits. Push changes to GitHub, Cloudflare redeploys automatically.

1. Go to github.com, create a new private repository called `wsd-website`. Don't initialize with a README.
2. On your computer, in the `wsd-site/` folder, open a terminal and run:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/wsd-website.git
   git push -u origin main
   ```

   Or use GitHub Desktop: File, Add Local Repository, select `wsd-site/`, commit, publish.

3. In Cloudflare: Workers and Pages, Create, Pages tab, Connect to Git. Select your `wsd-website` repo.
4. Build settings: framework preset None, build command blank, build output directory `/`. Save and Deploy.
5. From now on, any push to the `main` branch auto-deploys to the live site in under a minute.

### Connecting the domain

In Cloudflare Pages, open the project, Custom domains, Set up a custom domain. Add both:

- `winnipegsd.com`
- `www.winnipegsd.com`

If winnipegsd.com is already on Cloudflare DNS, this is a single click and live in five minutes. If not, you'll need to add a CNAME at the current registrar pointing to your `.pages.dev` URL. Cloudflare gives you the exact CNAME value.

SSL certificate is automatic and free.

## Tracking setup

This is the AdEasy zone, but here is the order of operations for WSD.

### Create the GA4 property

In analytics.google.com: Admin, Create property, follow the prompts. Set timezone to America/Winnipeg, currency CAD. Note the measurement ID (looks like `G-XXXXXXXXXX`). Create these conversion events:

- `generate_lead` (when the form is submitted via FSM)
- `phone_call` (when the tracking phone is called, fed from CallRail webhook)
- `phone_click` (when a `tel:` link is clicked, fires immediately on click)

Mark all three as Key Events in GA4.

### Create the GTM container

In tagmanager.google.com: Create Account, Container name "WSD", target platform Web. Note the container ID (looks like `GTM-XXXXXXX`). Do the find and replace from Pre-launch step 1.

Set up these tags in GTM:

1. **GA4 Configuration tag**: paste your measurement ID, fires on All Pages
2. **Phone click event tag**: GA4 event `phone_click`, trigger on Click URL containing `tel:`
3. **Form submission event tag**: GA4 event `generate_lead`, trigger depending on the FSM embed type (iframe submit listener or success-state DOM change)
4. **CallRail tag**: paste the CallRail script (see below), fires on All Pages

Publish the container after testing in Preview mode.

### CallRail integration

Sign up at callrail.com, create a tracking number, point the destination to WSD's main business line. In CallRail dashboard:

- Set up source rules: one tracking number per traffic source (Google Ads, organic search, direct, GBP)
- Enable Dynamic Number Insertion (DNI) so visible numbers swap based on visitor source
- Connect to GA4 in CallRail's integrations panel so calls report as events in GA4
- Connect to Google Ads so calls report as conversions in Ads

The CallRail snippet goes in GTM as a custom HTML tag firing on All Pages. CallRail will provide the exact snippet in their setup wizard.

DNI handles the phone number swapping automatically. Your hardcoded `+1204...` phone numbers in the HTML become a default fallback if CallRail's JS hasn't loaded yet, which is the right behavior.

## Ongoing edit workflow

If you went with GitHub + Cloudflare (Option B above), this is your loop:

1. Open the local `wsd-site/` folder in any code editor (VS Code, Sublime, even a plain text editor)
2. Edit any HTML file directly. Plain HTML, no React, no build step.
3. Commit and push to GitHub
4. Cloudflare auto-deploys in 30 to 60 seconds
5. Refresh winnipegsd.com, change is live

For changes I should do for you, just send me what you want changed (in chat or as commits to the repo) and I'll edit the files. The whole site is in plain HTML now, so changes are fast.

For visual or structural changes that need design work, go back to Claude Design, make the changes there, re-export, and apply the same production prep to the new HTML files. The prep script lives in this project; we can re-run it on any future export.

### Preview deployments

Cloudflare Pages gives every non-main branch its own preview URL. So if you want to test a big change before going live, create a branch:

```bash
git checkout -b new-services-page
# make changes
git add . && git commit -m "Add new service: trenchless repair"
git push -u origin new-services-page
```

Cloudflare will deploy a preview at `new-services-page.wsd-website.pages.dev`. Send that to the client for sign-off. When approved, merge to main, it goes live.

## Files reference

```
wsd-site/
├── index.html                                         (homepage)
├── services.html                                      (all services overview)
├── drain-cleaning.html
├── sewer-line-cleaning.html
├── hydro-jetting.html
├── sewer-camera-inspection.html
├── frozen-sewer-thawing.html
├── property-managers.html                             (audience page)
├── restaurants.html                                   (audience page)
├── contact.html                                       (booking page, has the form)
├── recent-updates.html                                (blog index)
├── blog-basement-backup-first-10-minutes.html
├── blog-flat-quotes-vs-hourly.html
├── blog-wolseley-clay-tile.html
├── colors_and_type.css                                (brand colors, type scale)
├── styles.css                                         (component styles)
├── static-overrides.css                               (small static-mode overrides)
├── interactive.js                                     (FAQ accordion, header scroll, etc.)
├── robots.txt
├── sitemap.xml
├── assets/                                            (images)
└── favicon/                                           (generated favicon set)
```

## Total cost to run

- Cloudflare Pages hosting: $0
- Domain (winnipegsd.com renewal): about $12/year
- GA4: $0
- GTM: $0
- CallRail: starts at $45/month (10 numbers, 250 minutes) on the basic tier
- FSM form: whatever the client already pays for the FSM
- Total recurring: about $45/month all-in

Compared to a Webflow CMS plan at $29/month plus a Wix-style platform tax plus dev time to maintain, this is what the agency move actually looks like. Same repeatable stack for every static client site from now on.
