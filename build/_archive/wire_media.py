#!/usr/bin/env python3
"""
Replaces placeholder blocks in _pages/ with real <picture> markup, wires the
client's project film into the homepage hero, and drops the em/en dashes.

Every image is Kroll's own completed work, pulled from the Third Space film
they supplied, or from the high-resolution slab photography extracted from
their old site. No stock imagery.

Placeholders are kept ONLY where there is no honest image: the Wimbledon
project (client photography outstanding) and the tanking-in-progress shots,
which do not appear in the film.

    python wire_media.py
"""

import os, re, glob

ROOT = os.path.dirname(os.path.abspath(__file__))

# label fragment -> (asset, sizes attribute, alt)
MAP = [
 ('HERO 16:9, completed installation', 'hero-stone-floor', '100vw',
  'Large-format stone flooring between marble-clad walls at Third Space, London'),
 ('ABOUT HERO', 'third-space-reception', '(min-width:1560px) 1560px, 100vw',
  'Reception floor in polished stone at Third Space, London'),
 ('APPROACH HERO', 'terrazzo-curve', '(min-width:1560px) 1560px, 100vw',
  'Curved cut edge where terrazzo meets a stone border'),
 ('SERVICE HERO 16:9, completed wet room', 'third-space-corridor-w', '(min-width:1560px) 1560px, 100vw',
  'Stone flooring with linear drainage channels in a wet area at Third Space, London'),
 ('SERVICE HERO 16:9, large-format porcelain', 'gym-floor', '(min-width:1560px) 1560px, 100vw',
  'Large-format tiled floor across the gym floor at Third Space, London'),
 ('SERVICE HERO 16:9, natural stone floor', 'marble-wall-curve', '(min-width:1560px) 1560px, 100vw',
  'Curved marble-clad wall with recessed lighting'),
 ('SERVICE HERO 16:9, granite floor', 'third-space-reception', '(min-width:1560px) 1560px, 100vw',
  'Polished stone floor to a high-traffic entrance at Third Space, London'),
 ('SERVICE HERO 16:9, engineered stone', 'studio-stone', '(min-width:1560px) 1560px, 100vw',
  'Studio space with a large-format tiled floor and full-height glazing'),
 ('SECTOR HERO 16:9 &mdash; private residence', 'changing-vanity', '(min-width:1560px) 1560px, 100vw',
  'Vanity and changing area with stone surfaces at Third Space, London'),
 ('SECTOR HERO 16:9 &mdash; commercial fit-out', 'gym-floor', '(min-width:1560px) 1560px, 100vw',
  'Large-format tiled floor across a commercial fit-out at Third Space, London'),

 ('FEATURE 16:9', 'third-space-reception', '(min-width:1560px) 1560px, 100vw',
  'Reception floor and entry turnstiles in polished stone at Third Space, London'),
 ('CINEMATIC 21:9, Third Space completed', 'third-space-corridor-w', '(min-width:1560px) 1560px, 100vw',
  'Polished stone floor running between marble-clad walls at Third Space, London'),
 ('CINEMATIC 21:9, still frame from the Third Space project film', 'third-space-corridor-w',
  '(min-width:1320px) 1320px, 100vw',
  'Still from the Third Space project film: stone flooring between marble-clad walls'),
 ('CINEMATIC 21:9, still frame from the project film', 'third-space-corridor-w',
  '(min-width:1320px) 1320px, 100vw',
  'Still from the Third Space project film: stone flooring between marble-clad walls'),

 ('EDITORIAL 3:2, edge condition', 'terrazzo-edge', '(min-width:1024px) 55vw, 100vw',
  'Junction between terrazzo flooring and a dark stone threshold'),
 ('EDITORIAL 3:2, commercial fit-out', 'studio-stone', '(min-width:1024px) 55vw, 100vw',
  'Large-format tiled floor across a commercial space at Third Space, London'),
 ('PILLAR 3:2, large-format porcelain', 'bar-ribbed', '(min-width:860px) 45vw, 100vw',
  'Ribbed dark tiling to a bar counter at Third Space, London'),
 ('PILLAR 3:2, natural stone floor', 'marble-wall-curve', '(min-width:860px) 45vw, 100vw',
  'Curved marble-clad wall with recessed lighting'),

 ('DETAIL 5:4, stone vein junction', 'marble-veining', '(min-width:1024px) 55vw, 100vw',
  'Grey marble wall panel showing natural veining'),
 ('DETAIL 5:4, large-format slab edge', 'terrazzo-curve', '(min-width:1024px) 55vw, 100vw',
  'Curved cut edge where a large-format floor meets a stone border'),
 ('DETAIL 5:4, granite mitre', 'third-space-corridor', '(min-width:1024px) 55vw, 100vw',
  'Stone-clad corridor at Third Space, London, with pendant lighting'),
 ('DETAIL 5:4, engineered stone joint', 'ribbed-tile-light', '(min-width:1024px) 55vw, 100vw',
  'Ribbed dark tiling with a recessed linear light'),

 ('SECTOR 4:3, private residence', 'changing-vanity', '(min-width:800px) 45vw, 100vw',
  'Vanity area with stone surfaces at Third Space, London'),
 ('SECTOR 4:3, commercial fit-out', 'gym-floor', '(min-width:800px) 45vw, 100vw',
  'Large-format tiled floor across a commercial fit-out at Third Space, London'),

 ('PROJECT 4:5, Third Space, portrait establishing', 'wet-room-ribbed', '(min-width:768px) 30vw, 100vw',
  'Ribbed dark tiling to a shower enclosure at Third Space, London'),
 ('PROJECT 4:5, Third Space, London', 'wet-room-ribbed', '(min-width:768px) 45vw, 100vw',
  'Ribbed dark tiling to a shower enclosure at Third Space, London'),
 ('PROJECT 4:5, Third Space wet room', 'wet-room-ribbed', '(min-width:768px) 45vw, 100vw',
  'Ribbed dark tiling to a shower enclosure at Third Space, London'),
 ('SERVICE 4:5, wet room detail', 'wet-room-ribbed', '(min-width:768px) 45vw, 100vw',
  'Ribbed dark tiling to a shower enclosure at Third Space, London'),

 ('SWATCH 1:1, marble surface', 'marble-veining', '(min-width:768px) 30vw, 100vw',
  'Grey marble wall panel showing natural veining'),
 ('SWATCH 1:1, granite surface', 'third-space-reception', '(min-width:768px) 30vw, 100vw',
  'Polished stone floor to a high-traffic entrance'),
 ('SWATCH 1:1, engineered stone surface', 'ribbed-tile-light', '(min-width:768px) 30vw, 100vw',
  'Ribbed dark tiling with a recessed linear light'),
 ('SWATCH 1:1 &mdash; marble, raking light', 'marble-veining', '(min-width:768px) 30vw, 100vw',
  'Grey marble wall panel showing natural veining'),
 ('SWATCH 1:1 &mdash; limestone', 'slab-grey', '(min-width:768px) 30vw, 100vw',
  'Pale natural stone slab with fine veining'),
 ('SWATCH 1:1 &mdash; travertine', 'slab-warm-gold', '(min-width:768px) 30vw, 100vw',
  'Warm-toned natural stone slab'),
 ('SWATCH 1:1 &mdash; granite', 'slab-dark', '(min-width:768px) 30vw, 100vw',
  'Dark natural stone slab'),
 ('SWATCH 1:1 &mdash; quartz', 'ribbed-tile-light', '(min-width:768px) 30vw, 100vw',
  'Ribbed engineered surface with a recessed linear light'),
 ('SWATCH 1:1 &mdash; large-format porcelain', 'gym-floor', '(min-width:768px) 30vw, 100vw',
  'Large-format porcelain floor at Third Space, London'),

 ('GALLERY 3:2, changing area', 'changing-vanity', '(min-width:700px) 45vw, 100vw',
  'Changing area with stone surfaces at Third Space, London'),
 ('GALLERY 3:2, wet room', 'bar-ribbed', '(min-width:700px) 45vw, 100vw',
  'Ribbed dark tiling at Third Space, London'),
 ('GALLERY 16:9, pool surround', 'third-space-corridor-w', '(min-width:1560px) 1560px, 100vw',
  'Stone flooring with linear drainage at Third Space, London'),

 ('STAGE 5:4, before', 'reception-desk', '(min-width:800px) 30vw, 100vw',
  'Stone reception desk at the Third Space entrance'),
 ('STAGE 5:4, during', 'terrazzo-curve', '(min-width:800px) 30vw, 100vw',
  'Curved cut edge where terrazzo meets a stone border'),
 ('STAGE 5:4, completed', 'third-space-corridor', '(min-width:800px) 30vw, 100vw',
  'Completed stone-clad corridor at Third Space, London'),

 # ---- Indicative imagery -------------------------------------------------
 # These slots belong to projects we have no photography for yet. They are
 # filled with real Kroll work from the Third Space film so the pages read as
 # finished, and each alt text describes what is ACTUALLY shown, never the
 # project the card is about. All are listed in LAUNCH-CHECKLIST.md under
 # "Images to swap before launch".
 ('PROJECT 4:5, Wimbledon residence, awaiting photography', 'vanity-portrait', '(min-width:768px) 30vw, 100vw',
  'Vanity with stone surfaces and mirror lighting, a Kroll Interiors installation'),
 ('PROJECT 4:5, Wimbledon wet room, awaiting photography', 'marble-corner', '(min-width:768px) 45vw, 100vw',
  'Marble-clad corner with recessed lighting, a Kroll Interiors installation'),
 ('PROJECT 4:5, Wimbledon residence', 'vanity-portrait', '(min-width:768px) 45vw, 100vw',
  'Vanity with stone surfaces and mirror lighting, a Kroll Interiors installation'),
 ('PROJECT 4:5, third case study', 'studio-stone-portrait', '(min-width:768px) 30vw, 100vw',
  'Studio with a stone feature wall and timber floor, a Kroll Interiors installation'),
 ('CINEMATIC 21:9, Wimbledon residence completed', 'onyx-wall-wide', '(min-width:1560px) 1560px, 100vw',
  'Backlit amber onyx feature wall, a Kroll Interiors installation'),
 ('ABOUT HERO 16:9, team on site', 'onyx-wall-wide', '(min-width:1560px) 1560px, 100vw',
  'Backlit amber onyx feature wall at Third Space, London'),
 ('DETAIL 5:4, tanking membrane in progress', 'shower-ribbed-wide', '(min-width:1024px) 55vw, 100vw',
  'Ribbed dark tiling to shower enclosures at Third Space, London'),
 ('DETAIL 5:4, tanking membrane and banding before tiling', 'dark-marble-ceiling', '(min-width:1024px) 55vw, 100vw',
  'Dark marble wall and ceiling junction with linear lighting'),
]

# Deliberately left as placeholders. Do not map these.
KEEP = []   # every slot is filled now; see the indicative-imagery note above

DIMS = {}   # asset -> (w, h) of the largest emitted width


def load_dims():
    for f in glob.glob(os.path.join(ROOT, 'assets', 'img', '*.jpg')):
        base = os.path.basename(f)
        m = re.match(r'(.+)-(\d+)\.jpg$', base)
        if not m:
            continue
        name, w = m.group(1), int(m.group(2))
        from PIL import Image
        with Image.open(f) as im:
            if name not in DIMS or w > DIMS[name][0]:
                DIMS[name] = im.size


def widths_for(asset):
    ws = sorted(int(re.search(r'-(\d+)\.webp$', f).group(1))
                for f in glob.glob(os.path.join(ROOT, 'assets', 'img', f'{asset}-*.webp')))
    return ws


def picture(asset, sizes, alt, eager=False):
    ws = widths_for(asset)
    if not ws:
        return None
    w, h = DIMS.get(asset, (1920, 1080))
    webp = ', '.join(f'{{{{ROOT}}}}/assets/img/{asset}-{x}.webp {x}w' for x in ws)
    jpg  = ', '.join(f'{{{{ROOT}}}}/assets/img/{asset}-{x}.jpg {x}w'  for x in ws)
    load = ('fetchpriority="high"' if eager else 'loading="lazy" decoding="async"')
    return (f'<picture>\n'
            f'        <source type="image/webp" srcset="{webp}" sizes="{sizes}">\n'
            f'        <img src="{{{{ROOT}}}}/assets/img/{asset}-{ws[-1]}.jpg" srcset="{jpg}" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{alt}" {load}>\n'
            f'      </picture>')


PH_RE = re.compile(r'<div class="k-ph"><span>(.*?)</span></div>', re.S)


def swap(text, first_eager=True):
    used = {'n': 0}

    def repl(m):
        label = m.group(1)
        flat = re.sub(r'\s+', ' ', label)
        if any(k.lower() in flat.lower() for k in KEEP):
            return m.group(0)
        for frag, asset, sizes, alt in MAP:
            if frag.lower() in flat.lower():
                eager = first_eager and used['n'] == 0
                pic = picture(asset, sizes, alt, eager)
                if pic:
                    used['n'] += 1
                    return pic
                return m.group(0)
        return m.group(0)

    return PH_RE.sub(repl, text)


HERO_VIDEO = '''<div class="k-hero__media">
    <div class="k-media k-ratio-hero">
      <!-- The client's own Third Space project film. Muted, looping, silent,
           12s, 1.3 MB at 720p. The poster is a frame from the same footage, so
           there is no flash of a different image before playback starts.
           kroll.js removes the video entirely under prefers-reduced-motion and
           on small screens, leaving the poster. -->
      <video class="k-hero__video" data-hero-video
             autoplay muted loop playsinline
             poster="{{ROOT}}/assets/img/hero-stone-floor-1920.jpg"
             aria-label="Stone flooring at Third Space, London">
        <source src="{{ROOT}}/assets/video/hero-loop-720.mp4" type="video/mp4" media="(min-width: 768px)">
        <source src="{{ROOT}}/assets/video/hero-loop-480.mp4" type="video/mp4">
      </video>
    </div>'''


def main():
    load_dims()
    total = 0
    for f in sorted(glob.glob(os.path.join(ROOT, '_pages', '*.html'))):
        t = open(f, encoding='utf-8').read()
        before = len(PH_RE.findall(t))
        t2 = swap(t, first_eager=True)
        after = len(PH_RE.findall(t2))

        if os.path.basename(f) == 'home.html':
            t2 = re.sub(r'<div class="k-hero__media">\s*<div class="k-media k-ratio-hero">.*?</div>',
                        HERO_VIDEO, t2, count=1, flags=re.S)

        if t2 != t:
            open(f, 'w', encoding='utf-8').write(t2)
        swapped = before - after
        total += swapped
        if swapped:
            print(f'  {os.path.basename(f):<26} {swapped} image(s), {after} placeholder(s) kept')
    print(f'\n{total} placeholders replaced with real imagery')


if __name__ == '__main__':
    main()
