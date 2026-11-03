# hub/ — the public hub website, captcharena.org (build-order step 9, all seven sections at v1)

Agent-facing. Static site: [Zola](https://www.getzola.org) 0.23.6 builds `site/` inside the image (stage 1, fails on
any broken internal link or anchor), [nginx-unprivileged](https://github.com/nginx/docker-nginx-unprivileged) serves
it (stage 2). No secrets, no state, no third-party scripts. www.captcharena.org → 301 → apex, inside nginx.

## Layout

| Path | What |
|---|---|
| `site/config.toml` | base URL, nav, breadcrumb names, the summary URL and warm-up date |
| `site/content/<section>/` | Markdown pages, one folder per section: learn, play, scoreboard, browser-score, defend, build, research, about, contact. Front matter: `title`, `description` (meta), `weight`, `[extra] checked = "YYYY-MM-DD"`, optional `status = "coming"`, `script = "<file in assets>"` |
| `site/templates/` | `base.html` (head: canonical, Open Graph, CSP-safe assets with content hashes), `page.html`, `section.html`, `components.html` |
| `site/templates/components.html` | Zola 0.23 components (shortcodes are gone in 0.23): `{% <coming> %}…{% </coming> %}`, `{% <note> %}…{% </note> %}` (block form on their own lines only; the one-line form breaks the HTML), `{{ <live_summary /> }}`, `{{ <doors /> }}` |
| `site/static/assets/live-summary.js` | the only script: fetches `https://measure.captcharena.org/api/summary` (needs CORS `Access-Control-Allow-Origin: https://captcharena.org` on that endpoint) and renders any lanes table it finds; on any failure the static warm-up text stays |
| `site/static/.well-known/security.txt` | copied by the Dockerfile (Zola skips hidden folders); Contact → /contact/; Expires 2027-11-01 |
| `nginx/` | server config, security headers (CSP `default-src 'none'; script-src 'self'; connect-src https://measure.captcharena.org; …`), www redirect, `/health` |
| `tools/check_site.py` | crawls the live site: status, headers, one `<h1>`, meta description, canonical, OG tags, no inline script, every internal link and anchor |
| `tools/convert_shortcodes.py` | rewrites old `{% x() %}…{% end %}` syntax to components |
| `tools/og-card.html` | source of `site/static/assets/og-card.png` (rendered with Playwright, 1200×630) |

## Content rules (from the brief and `../CLAUDE.md`)

Every fact dated and sourced; neutral; no vendor logos or images; no solver-as-a-service; no bypass recipes; our own
agents' ~85-attempt record is **not** published (the essay is unpublished pending the owner's check — the Build
"per-kind playbook" is marked coming for that reason). One `<h1>` per page (the template's title).

## Build, check, deploy

- Local check: `docker run --rm -u $(id -u):$(id -g) -v $PWD/site:/site -w /site ghcr.io/getzola/zola:v0.23.6 check --skip-external-links`
- Local serve: `docker compose up -d --build` → http://127.0.0.1:8310
- Deploy (committed tree only): `deploy-tool deploy captcha-hub <this folder> 8310 --health /health --host www.captcharena.org`, then the same with `--host captcharena.org` (last, so the health line watches the apex; both ingress rules stay).
- DNS: proxied CNAMEs `captcharena.org` and `www` → the tunnel (Cloudflare API, zone token in the secret store).
- Verify: `python3 tools/check_site.py https://captcharena.org/`
