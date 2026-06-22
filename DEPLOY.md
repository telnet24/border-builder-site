# Deploying the Border Builder site

Static HTML on GitHub Pages. After any catalogue change, re-run `python3 build.py`
and commit. Nothing else regenerates.

## 1. Custom domain

You don't have one yet. Steps:

### Buy it
Any registrar works. Cheapest with no renewal markup:
- **Cloudflare Registrar** (at-cost, but you must move DNS to Cloudflare first)
- **Porkbun** or **Namecheap** (simple, ~$10-15/yr for `.com`, ~$14/yr for `.app`)

Name ideas: `borderbuilder.app`, `borderbuilder.garden`, `getborderbuilder.com`.
Note: a `.app` domain forces HTTPS (it's on the browser HSTS preload list).
GitHub Pages serves HTTPS for free, so `.app` is fine and looks on-brand with the
bundle id `com.borderbuilder`.

### Point it at GitHub Pages
At your registrar's DNS:
- **Apex** (`borderbuilder.app`): add four A records ->
  `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
  and four AAAA records ->
  `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
- **www** (`www.borderbuilder.app`): one CNAME -> `<your-github-username>.github.io`

Then in the Pages repo: **Settings -> Pages -> Custom domain**, enter the domain,
save (this commits a `CNAME` file), and tick **Enforce HTTPS** once the cert issues
(can take up to ~24h, usually minutes).

### Re-point the build
Edit `BASE_URL` at the top of `build.py` to your domain (e.g.
`https://borderbuilder.app`), then `python3 build.py` and commit. This makes the
`<link rel=canonical>` tags and `sitemap.xml` use the real domain - required for
correct indexing.

## 2. Google Search Console (the step that gets you indexed)

Domain is live at `https://borderbuilderapp.com`, DNS on Cloudflare, sitemap at
`https://borderbuilderapp.com/sitemap.xml` (~1,350 clean URLs).

### Verify the property (Domain property, recommended)
1. Go to **search.google.com/search-console**, sign in with your Google account.
2. Property dropdown (top-left) -> **Add property**.
3. Choose the **Domain** box on the left. Enter `borderbuilderapp.com` (no `https://`,
   no path). Click **Continue**.
4. It shows a **TXT record**, e.g. `google-site-verification=AbC123...`. Copy it.
5. Add it in Cloudflare: **dash.cloudflare.com -> borderbuilderapp.com -> DNS -> Records
   -> Add record**. Type **TXT**, Name `@`, Content = paste the whole
   `google-site-verification=...` string, TTL Auto. **Save**.
   (Or paste the string to me and I will add it via the Cloudflare API if your token is
   still active.)
6. Back in Search Console, click **Verify**. DNS can take a few minutes; if it fails,
   wait and retry.

*Alternative (no DNS):* choose **URL prefix**, enter `https://borderbuilderapp.com/`,
pick the **HTML file** method; I commit that file to the repo and push, then you Verify.

### Submit the sitemap (this starts indexing)
7. Left nav -> **Sitemaps**. Under "Add a new sitemap" enter `sitemap.xml` -> **Submit**.
   It should read "Success" and discover the URLs over the following hours/days.

### Prime the important pages
8. Use the **URL inspection** bar at the top. Paste, one at a time, your highest-value
   URLs and click **Request indexing** (rate-limited, do ~10):
   `https://borderbuilderapp.com/`, `/collections/plants-for-dry-shade`,
   `/collections/soil-clay`, `/collections/plants-for-dry-sunny-borders`, and a few top
   plant pages.

### Bing (10 minutes, real extra reach)
9. **bing.com/webmasters** -> add site -> **Import from Google Search Console** (carries
   the verification and sitemap in one click). Bing also feeds Copilot and some AI search.

### What to watch
- **Pages** (Indexing) report over 1-3 weeks: the "Indexed" count should climb. Watch
  "Crawled - currently not indexed" / "Discovered - not indexed"; a high share there means
  Google is judging pages low-value (the per-page content work is what mitigates that).
- **Performance** report: first impressions/clicks usually appear within 1-3 weeks.

### Honest expectations
Sitemap submission speeds up *discovery*, not ranking. Google still decides what gets
indexed and where it ranks. The unique, sourced per-plant content and the long-tail
intersection pages are why these have a real shot. This is a weeks-to-months slow burn on
a new domain, not a switch.

## 3. Re-generating
```
python3 build.py     # rewrites plants/, collections/, sitemap.xml, robots.txt
```
Hand-authored pages (`index.html`, `privacy.html`, `support.html`, `style.css`) are
never touched.
