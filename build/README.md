# Kroll Interiors: Build

Version 2, the premium redesign (2026-09-17). Static HTML, no framework, no page builder. The
v1 stylesheets, images and video loops are kept in `_archive/` and in the git history.

    python build.py            development build into site/
    python build.py --prod     one minified stylesheet
    python make_stock.py       photographs from stock/selection.json
    python make_clips.py       film strips and project reels from the client's films

Serve `site/` over HTTP to review it (video loops are fetched, which `file://` blocks):
`node <scrollcraft>/scripts/serve.mjs --root site --port 4500`.

## Design

Chaptered editorial on an architectural black ground, with paper-white reading chapters that cut in
hard. Newsreader (variable, optical size) for display, Jost for text, one accent derived from the
logo's inner arc. Brief, feeling curve and signature move: `../scrollcraft/builds/kroll/BRIEF.md`.

| File | Purpose |
|---|---|
| `css/00-fonts.css` | Self-hosted Newsreader (upright + italic, variable) and Jost |
| `css/scrollcraft.css` | Scroll engine stylesheet. **Do not edit**, it is the mechanism |
| `css/10-tokens.css` | Colour roles for the night, surface and paper grounds; type ramp |
| `css/11-base.css` | Type, links, the no-JS floor, Lenis plumbing, page transitions |
| `css/12-layout.css` | Wrap, chapters, 12-column grid, sticky columns |
| `css/13-chrome.css` | Header, services panel, mobile menu, folio, close, footer, dock |
| `css/14-components.css` | Buttons, reveals, plates, index rows, specs, tables, FAQ, films, forms |
| `css/15-home.css` | Homepage title page and the build-up cutaway |
| `js/scrollcraft.js` | Scroll engine: pins, pan rail, progress variables. **Do not edit** |
| `js/vendor/lenis.min.js` | Smooth scrolling (Lenis 1.3.4, MIT). Off under reduced motion |
| `js/kroll.js` | Everything site-specific, progressive enhancement only |

### Motion vocabulary

| Where | What |
|---|---|
| Homepage title page | Pinned. A slit of stone under the headline opens to a full plate as you scroll |
| Every heading | Lines rise out of their own masks once the face has loaded |
| Page plates | Arrive inset to the gutter and open to full bleed at mid-screen |
| Figures | Frame opens from its base; the photograph settles from a closer crop, then drifts |
| **Build-up cutaway** | The signature move. A CSS 3D floor build-up lifts apart layer by layer, labels and leader lines track each layer, then it closes into one surface |
| Materials rail | Pinned, travels sideways |
| Projects | Kroll's own film, slowed, looping only while on screen |
| Services panel, services index | Image preview follows the pointer or keyboard focus |
| Navigation between pages | Native cross-document view transitions |

Reduced motion: no smooth scrolling, no pins, no position changes, no video fetched; the cutaway
renders exploded with every layer labelled. Without JavaScript every page is complete.

## Images

**Stock is used for materials, craft and interiors only.** It never appears on a case study and is
never captioned as Kroll's work. Case studies, project cards and project reels use Kroll's own
films exclusively.

`{{img slot=... crop=... sizes="..."}}` in `_pages/` is expanded by `build.py` into a `<picture>`
with AVIF, WebP and JPEG sources, using only widths that `make_stock.py` actually produced
(`assets/img/manifest.json`). A reference to a missing crop fails loudly in the build output.
Provenance for every photograph: `../project-docs/STOCK-LICENCES.md`.

## Video

| File | Use |
|---|---|
| `ts-reel-1920/1280.mp4`, `wb-reel-1152.mp4` | Project reels: slowed shots with crossfades, no people |
| `clips/*.mp4` | Case-study film strips: one shot each, slowed, forward and back |
| `third-space-1080/720.mp4`, `wimbledon-720/480.mp4` | Full films, play on request |

Both films contain on-camera interviews. No frame of an interview is cut into a loop: the
Wimbledon film's testimonial needs the speaker's permission first. The old 12-second loops opened on
interviews and are archived.

## House style

No em dashes or en dashes in copy. Use commas, colons or full stops. No invented statistics, no
"award-winning" or superlative claims without written evidence (see Phase B claims discipline).

## Why there is no JS minifier

An earlier one stripped only the first line of each block comment, so the production script failed
to parse and nothing ran. Gzip or Brotli on the server does the real work. If minification is ever
wanted, use terser in CI with `node --check` as a gate. The CSS minifier keeps the space before a
colon, which in a selector is a descendant combinator.
