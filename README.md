# Kroll Interiors, website v2

Specialist tiling and stone contractors, London. A full rebuild of
krollinteriors.co.uk as a static site: 18 pages, scroll driven, with the
company's own project footage playing inside the case studies.

This repository is the client preview build. Nothing here touches the live
WordPress site.

## Preview

The deployed preview is served from `build/site`, which is the finished static
output. To run it locally:

```bash
python build/build.py --prod
node "$HOME/.claude/skills/scrollcraft/scripts/serve.mjs" --root build/site --port 4500
```

Then open http://localhost:4500/

A plain `file://` open will not work. The page fetches each video clip as a
Blob and the browser blocks those fetches from the filesystem.

## Layout

| Path | What it holds |
| --- | --- |
| `build/site/` | The static output that gets deployed. Complete and self contained. |
| `build/_pages/` | Page sources that the build expands into `build/site`. |
| `build/_partials/` | Shared header, footer and section fragments. |
| `build/css/`, `build/js/` | Stylesheets and behaviour, minified into the output. |
| `build/assets/` | Full size source imagery before the build crops it. |
| `build/stock/` | `selection.json`, the slot to image mapping used by `make_stock.py`. |
| `build/_archive/` | The previous version, kept for reference only. |

## Deployment

Vercel, static, no build step. `vercel.json` sets the output directory to
`build/site`, keeps trailing slashes so the relative asset paths resolve, and
sends `X-Robots-Tag: noindex, nofollow` on every response.

That noindex header is deliberate. It stops search engines indexing the preview
domain as a duplicate of the client's real site. **Remove it when the site goes
live on krollinteriors.co.uk.**

## Not in this repository

Deliberately excluded, listed in `.gitignore`:

- the original client video masters
- `stock-originals/`, the licensed stock at full resolution, with the unused
  candidates and their provenance
- the packaged `.zip` builds
- the extracted copy of the old live site
- the studio's internal project records and working notes

The clips inside `build/site/assets/video/` are committed, because the deployed
site needs them.

## Imagery

Photography is licensed stock from Pexels and Unsplash. Every source URL and
licence is logged in the project records held by the studio. Every moving image
is Kroll's own footage. No image from the previous site is reused.
