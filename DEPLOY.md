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

1. Go to **search.google.com/search-console**, sign in.
2. **Add property**:
   - With a custom domain: choose **Domain** property, enter the bare domain,
     verify by adding the TXT record it gives you at your registrar's DNS.
   - On the default `<user>.github.io` URL (no custom domain yet): choose
     **URL prefix** property and verify with the **HTML file** method - download
     the file it gives you, drop it in this folder, commit, confirm it loads at
     `https://<user>.github.io/google<...>.html`, then click Verify.
3. **Sitemaps** (left nav) -> enter `sitemap.xml` -> **Submit**. This hands Google
   all 1,371 URLs at once instead of waiting for it to crawl link by link.
4. **URL Inspection**: paste your 5-10 most important pages (home, a few popular
   collections like `collections/full-sun.html`, top plants) -> **Request
   indexing**. Primes the ones you care about most.
5. Check the **Pages** (coverage) and **Performance** reports weekly.

Also worth 10 minutes: **Bing Webmaster Tools** (bing.com/webmasters) - same
sitemap submit, and it imports directly from Search Console. Bing also feeds some
AI assistants' web search.

### Honest expectations
Sitemap submission speeds up *discovery*, not ranking. Google still decides what to
index and where it ranks. Unique, sourced per-plant data (the citations help) is why
these pages have a real shot. Realistically this is a weeks-to-months slow burn, not
a switch - the first impressions usually show in Search Console within 1-3 weeks.

## 3. Re-generating
```
python3 build.py     # rewrites plants/, collections/, sitemap.xml, robots.txt
```
Hand-authored pages (`index.html`, `privacy.html`, `support.html`, `style.css`) are
never touched.
