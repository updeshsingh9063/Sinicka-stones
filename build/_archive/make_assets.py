#!/usr/bin/env python3
"""
Builds the site's image and video assets from the client's own material.

Sources, in the priority order set in Phase A:
  1. The client's Third Space project film  -> real project photography
  2. site-extract/assets/brand-and-site/slab-photography  -> material swatches
  3. Black.pdf / White.pdf -> logo SVG (handled separately)

No stock imagery is used anywhere. Every frame below is Kroll's own completed
work, pulled from footage they supplied.

    python make_assets.py

Requires imageio-ffmpeg (bundles a static ffmpeg) and Pillow.
"""

import os, subprocess, shutil, glob
from PIL import Image, ImageOps
import imageio_ffmpeg

ROOT   = os.path.dirname(os.path.abspath(__file__))
PROJ   = os.path.dirname(ROOT)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VIDEO = os.path.join(PROJ, 'provided by client',
                     'kroll_interiors___third_space_-_london_uk (1080p).mp4')

# The Wimbledon film reached us only through WhatsApp, which recompressed it to
# 720p at 638 kb/s and burned a Fiverr preview mark into the top right. The
# encode in assets/video already crops that corner away, so stills are cut from
# the cleaned copy rather than the delivered file. Ask the client for the
# unwatermarked master and this can point straight at it.
VIDEO_WIM = os.path.join(ROOT, 'assets', 'video', 'wimbledon-720.mp4')
VIDEO_WIM_SRC = os.path.join(PROJ, 'WhatsApp Video 2026-09-14 at 10.05.10 AM.mp4')
WIM_CROP = 'crop=1152:648:0:72'
SLABS = os.path.join(PROJ, 'site-extract', 'assets', 'brand-and-site', 'slab-photography')

IMG = os.path.join(ROOT, 'assets', 'img')
VID = os.path.join(ROOT, 'assets', 'video')

# The client's own watermark sits bottom-left on every frame. Crops that would
# include it are nudged away from that corner.
WATERMARK_SAFE_LEFT = 0.06

RATIOS = {
    'hero':      (16, 9),
    'cinema':    (21, 9),
    'editorial': (3, 2),
    'detail':    (5, 4),
    'square':    (1, 1),
    'portrait':  (4, 5),
    'sector':    (4, 3),
}

# name -> (timestamp, ratio, focal 0-1 vertical, alt text)
FRAMES = [
    ('hero-stone-floor',       70.2, 'hero',      0.62,
     'Large-format stone flooring between marble-clad walls at Third Space, London'),
    ('third-space-corridor',   52.4, 'detail',    0.50,
     'Stone-lined corridor at Third Space, London, with pendant lighting'),
    ('third-space-corridor-w', 70.2, 'cinema',    0.55,
     'Polished stone floor running between marble-clad walls at Third Space, London'),
    ('third-space-reception',  50.3, 'hero',      0.55,
     'Reception floor and entry turnstiles in polished stone at Third Space, London'),
    ('terrazzo-edge',          64.2, 'editorial', 0.50,
     'Junction between terrazzo flooring and a dark stone threshold'),
    ('terrazzo-curve',         48.4, 'detail',    0.55,
     'Curved cut edge where terrazzo meets a stone border'),
    ('wet-room-ribbed',        58.3, 'portrait',  0.45,
     'Ribbed dark tiling to a shower enclosure at Third Space, London'),
    ('marble-veining',         66.2, 'square',    0.50,
     'Grey marble wall panel showing natural veining'),
    ('onyx-backlit',           34.3, 'square',    0.50,
     'Backlit amber onyx feature wall'),
    ('ribbed-tile-light',      32.4, 'square',    0.50,
     'Ribbed dark tiling with a recessed linear light'),
    ('gym-floor',              40.4, 'sector',    0.55,
     'Large-format tiled floor across the gym floor at Third Space, London'),
    ('changing-vanity',        24.3, 'sector',    0.50,
     'Vanity and changing area with stone surfaces at Third Space, London'),
    ('studio-stone',           22.4, 'editorial', 0.55,
     'Studio space with a tiled floor and full-height glazing'),
    ('third-space-sign',       20.3, 'editorial', 0.50,
     'Illuminated Third Space signage above the gym floor'),
    ('bar-ribbed',             60.3, 'editorial', 0.50,
     'Ribbed dark tiling to a bar counter at Third Space, London'),
    ('marble-wall-curve',      28.4, 'detail',    0.50,
     'Curved marble-clad wall with recessed lighting'),
    ('vanity-portrait',        24.6, 'portrait',  0.50,
     'Vanity with stone surfaces and mirror lighting at Third Space, London'),
    ('marble-corner',          72.4, 'portrait',  0.50,
     'Marble-clad corner with recessed lighting'),
    ('studio-stone-portrait',  46.4, 'portrait',  0.55,
     'Studio with a stone feature wall and timber floor'),
    ('dark-marble-ceiling',    30.4, 'detail',    0.45,
     'Dark marble wall and ceiling junction with linear lighting'),
    ('onyx-wall-wide',         18.4, 'editorial', 0.50,
     'Backlit amber onyx feature wall at Third Space, London'),
    ('shower-ribbed-wide',     58.6, 'editorial', 0.45,
     'Ribbed dark tiling to shower enclosures at Third Space, London'),
    ('reception-desk',         12.4, 'detail',    0.50,
     'Stone reception desk at the Third Space entrance'),
]

WIDTHS = [480, 800, 1280, 1920]


# Third Space Wimbledon. Note this is a COMMERCIAL leisure fit-out, not the
# private residence the case study was originally briefed around: the film
# shows locker bays, changing rooms and the gym floor, and carries Third Space
# signage throughout. Timestamps are against the cropped 720p encode.
WIM_FRAMES = [
    # Timestamps verified against a per-second timeline of the cropped encode.
    # The on-camera testimonial runs at 15-17, 25, 32-33, 46 and 57-58s; those
    # seconds are avoided deliberately so no still carries a person's face.
    ('wimb-changing-wide',   43.3, 'cinema',    0.50,
     'Changing room at Third Space Wimbledon with large-format porcelain flooring and terrazzo borders'),
    ('wimb-changing',        44.3, 'hero',      0.50,
     'Locker bays and bench seating over large-format porcelain flooring at Third Space Wimbledon'),
    ('wimb-changing-portrait', 43.3, 'portrait', 0.50,
     'Locker bays and bench seating at Third Space Wimbledon, shot along the changing room'),
    ('wimb-brass-curve',     11.3, 'cinema',    0.50,
     'Curved brass-toned tiled wall at Third Space Wimbledon'),
    ('wimb-brass-detail',    14.3, 'square',    0.50,
     'Close detail of large brass-toned square tiling with fine grout joints'),
    ('wimb-reception',       12.6, 'editorial', 0.50,
     'Reception desk in patterned brass tiling at Third Space Wimbledon'),
    ('wimb-green-tile',      23.3, 'detail',    0.50,
     'Glazed green tiling in stacked and stepped coursing at Third Space Wimbledon'),
    ('wimb-green-light',     34.6, 'portrait',  0.50,
     'Glazed green tiling beside a recessed linear light'),
    ('wimb-green-angle',     30.6, 'detail',    0.50,
     'Raking view along a glazed green tiled wall'),
    ('wimb-terrazzo',        28.6, 'square',    0.50,
     'Terrazzo surface showing aggregate detail'),
    ('wimb-corridor-rail',   26.6, 'portrait',  0.50,
     'Corridor with handrails and a green mosaic column at Third Space Wimbledon'),
    ('wimb-lockers',         48.6, 'editorial', 0.50,
     'Locker bay lit from above at Third Space Wimbledon'),
    ('wimb-corridor',        49.6, 'portrait',  0.50,
     'Locker corridor with large-format floor tiling and recessed lighting'),
    ('wimb-floor',           39.3, 'sector',    0.55,
     'Large-format porcelain floor running through the changing area'),
    ('wimb-vanity',          18.6, 'sector',    0.50,
     'Vanity counters and mirror lighting at Third Space Wimbledon'),
    ('wimb-sign',             6.2, 'cinema',    0.50,
     'Third Space lettering in brushed metal on a ribbed timber wall'),
    ('wimb-exterior',         2.6, 'editorial', 0.50,
     'Third Space entrance at Wimbledon Quarter'),
]


def run(args):
    subprocess.run(args, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def grab(ts, dest, source=None):
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-ss', str(ts),
         '-i', source or VIDEO, '-frames:v', '1', '-q:v', '1', dest, '-y'])


def crop_to(im, ratio, focal=0.5, avoid_watermark=False):
    """Centre-crop to the target ratio, biased vertically by `focal`."""
    tw, th = ratio
    target = tw / th
    w, h = im.size
    if w / h > target:                      # too wide, trim horizontally
        nw = int(h * target)
        left = (w - nw) // 2
        if avoid_watermark:
            left = max(left, int(w * WATERMARK_SAFE_LEFT))
            left = min(left, w - nw)
        im = im.crop((left, 0, left + nw, h))
    else:                                   # too tall, trim vertically
        nh = int(w / target)
        top = int((h - nh) * focal)
        top = max(0, min(top, h - nh))
        im = im.crop((0, top, w, top + nh))
    return im


def emit(im, name, alt_widths=WIDTHS):
    """Writes WebP + JPEG at each width, skipping upscales."""
    out = []
    for wdt in alt_widths:
        if wdt > im.width:
            continue
        r = im.resize((wdt, round(im.height * wdt / im.width)), Image.LANCZOS)
        r = ImageOps.exif_transpose(r).convert('RGB')
        # AVIF first: typically 30-50% smaller than WebP at matched quality.
        # Browsers pick the first <source> they understand, so order in the
        # markup is avif, webp, jpg.
        try:
            r.save(os.path.join(IMG, f'{name}-{wdt}.avif'), 'AVIF', quality=58)
        except Exception as e:
            print(f'    avif skipped for {name}-{wdt}: {e}')
        r.save(os.path.join(IMG, f'{name}-{wdt}.webp'), 'WEBP', quality=82, method=6)
        r.save(os.path.join(IMG, f'{name}-{wdt}.jpg'),  'JPEG', quality=84,
               optimize=True, progressive=True)
        out.append(wdt)
    return out


def build_frames(frames=None, source=None):
    tmp = os.path.join(ROOT, '.tmp-frames')
    os.makedirs(tmp, exist_ok=True)
    manifest = []
    for name, ts, ratio_key, focal, alt in (frames or FRAMES):
        raw = os.path.join(tmp, f'{name}.png')
        if not os.path.exists(raw):
            grab(ts, raw, source)
        im = Image.open(raw)
        im = crop_to(im, RATIOS[ratio_key], focal, avoid_watermark=(ratio_key in ('square', 'portrait')))
        widths = emit(im, name)
        manifest.append((name, ratio_key, im.size, widths, alt))
        print(f'  {name:<24} {ratio_key:<10} {im.size[0]}x{im.size[1]}  widths={widths}')
    shutil.rmtree(tmp, ignore_errors=True)
    return manifest


def build_swatches():
    """Material swatches from the 2560px slab photography already extracted
    from the old site. High-resolution and genuinely good, the one part of
    that 616 MB library worth carrying over."""
    picks = [
        ('slab-warm-gold',  '14-scaled.jpg',   'Gold and black veined stone slab'),
        ('slab-grey',       '19-scaled.jpg',   'Grey natural stone slab with fine veining'),
        ('slab-dark',       '16-1-scaled.jpg', 'Dark natural stone slab'),
    ]
    out = []
    for name, src, alt in picks:
        p = os.path.join(SLABS, src)
        if not os.path.exists(p):
            cands = sorted(glob.glob(os.path.join(SLABS, '*.jpg')))
            if not cands:
                print(f'  slab source missing, skipped: {src}')
                continue
            p = cands[len(out) % len(cands)]
        im = crop_to(Image.open(p), RATIOS['square'], 0.5)
        widths = emit(im, name, [480, 800, 1280])
        out.append((name, 'square', im.size, widths, alt))
        print(f'  {name:<24} {"square":<10} {im.size[0]}x{im.size[1]}  <- {os.path.basename(p)}')
    return out


# Material photography from the 2560px slab library. These are stone, not
# projects, so they carry no claim about whose work they are. Service and
# sector pages previously reused a handful of soft project stills as
# decoration, which is what made the site look padded and put a Wimbledon
# photo on the London case study. Material slots now pull from here instead.
#
# name -> (source file, ratio, alt text)
MATERIALS = [
    ('stone-gold-black',     '14-scaled.jpg',        'cinema',
     'Gold and black veined granite slab'),
    ('stone-gold-vein',      '6-1-scaled.jpg',       'cinema',
     'Warm veined granite slab in large format'),
    ('stone-white-amber',    '20-3-scaled.jpg',      'editorial',
     'White quartzite with amber and gold crystalline veining'),
    ('stone-dark-gold',      '26-3-scaled.jpg',      'editorial',
     'Dark stone slab shot through with gold veining'),
    ('stone-calacatta',      'e51fa868b96d8ec4cd8ba197b3b15bd4-scaled.jpg', 'editorial',
     'White marble slab with fine grey veining'),
    ('stone-yard',           '96fea247340503906ceb7a43463db252-scaled.jpg', 'editorial',
     'Stone slabs racked in the yard ready for selection'),
    ('stone-dark-gold-wide', '29-1-scaled.jpg',      'editorial',
     'Dark granite slab with warm gold movement'),
    ('stone-emperador',      '2-1-scaled.jpg',       'portrait',
     'Brown marble with white veining'),
    ('stone-onyx-green',     'bbc2d80ff3ff496a67113af1c5371150-scaled.jpg', 'portrait',
     'Green onyx slab with translucent banding'),
    ('stone-quartzite-cream','aaa-scaled.jpg',       'portrait',
     'Cream quartzite slab with soft movement'),
    ('stone-black-gold',     '4-2-scaled.jpg',       'detail',
     'Black granite with gold crystalline inclusions'),
    ('stone-green-slate',    '9-1-scaled.jpg',       'detail',
     'Green and blue slate with natural cleft texture'),
    ('stone-onyx-amber',     '4ee96cfc85b258eac1321c26aabb00e7-scaled.jpg', 'detail',
     'Amber onyx with translucent veining'),
    ('stone-onyx-brown',     '1531e3292766ae885b9ff4fda79e111e-scaled.jpg', 'detail',
     'Brown onyx with warm translucent banding'),
    ('stone-speckled-grey',  '17-3-scaled.jpg',      'square',
     'Speckled grey granite slab'),
    ('stone-white-inclusion','18-1-scaled.jpg',      'square',
     'Pale stone slab with dark mineral inclusions'),
    ('stone-travertine',     '7fdde343d6be458757b3f39161b7de2b-scaled.jpg', 'square',
     'Cream travertine slab with fine banding'),
]


def build_materials():
    """Material photography at full width. The sources are 2560px, so unlike
    the swatches these are not capped at 1280 and can carry a hero slot."""
    out = []
    for name, src, ratio_key, alt in MATERIALS:
        p = os.path.join(SLABS, src)
        if not os.path.exists(p):
            print(f'  material source missing, skipped: {src}')
            continue
        im = crop_to(Image.open(p), RATIOS[ratio_key], 0.5)
        widths = emit(im, name)
        out.append((name, ratio_key, im.size, widths, alt))
        print(f'  {name:<24} {ratio_key:<10} {im.size[0]}x{im.size[1]}  widths={widths}')
    return out


def build_video():
    """Two encodes:
       hero-loop, 12s, silent, small, muted autoplay behind the hero
       film, the full 84s piece for the modal, at two rungs
    """
    os.makedirs(VID, exist_ok=True)

    # Hero loop: 44-56s runs through the corridor and wet room: the most
    # material-forward stretch in the film, and it cuts cleanly at both ends.
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-ss', '60', '-t', '12',
         '-i', VIDEO, '-an',
         '-vf', 'scale=1280:-2',
         '-c:v', 'libx264', '-profile:v', 'high', '-crf', '26',
         '-preset', 'slow', '-movflags', '+faststart', '-pix_fmt', 'yuv420p',
         os.path.join(VID, 'hero-loop-720.mp4'), '-y'])

    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-ss', '60', '-t', '12',
         '-i', VIDEO, '-an', '-vf', 'scale=640:-2',
         '-c:v', 'libx264', '-crf', '28', '-preset', 'slow',
         '-movflags', '+faststart', '-pix_fmt', 'yuv420p',
         os.path.join(VID, 'hero-loop-480.mp4'), '-y'])

    for label, scale, crf in (('1080', 1920, 23), ('720', 1280, 25)):
        run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-i', VIDEO,
             '-vf', f'scale={scale}:-2',
             '-c:v', 'libx264', '-profile:v', 'high', '-crf', str(crf),
             '-preset', 'slow', '-c:a', 'aac', '-b:a', '128k',
             '-movflags', '+faststart', '-pix_fmt', 'yuv420p',
             os.path.join(VID, f'third-space-{label}.mp4'), '-y'])

    # Wimbledon, from the WhatsApp copy, cropped to drop the Fiverr mark.
    # CRF is tighter than the tier default because the source is already
    # heavily recompressed and we do not want to stack generation loss.
    if os.path.exists(VIDEO_WIM_SRC):
        for label, scale, crf, ab in (('720', 1280, 23, '128k'), ('480', 854, 26, '96k')):
            run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-i', VIDEO_WIM_SRC,
                 '-vf', f'{WIM_CROP},scale={scale}:-2',
                 '-c:v', 'libx264', '-profile:v', 'high', '-crf', str(crf),
                 '-preset', 'slow', '-c:a', 'aac', '-b:a', ab,
                 '-movflags', '+faststart', '-pix_fmt', 'yuv420p',
                 os.path.join(VID, f'wimbledon-{label}.mp4'), '-y'])

    for f in sorted(os.listdir(VID)):
        size = os.path.getsize(os.path.join(VID, f)) / 1048576
        print(f'  {f:<28} {size:6.1f} MB')


if __name__ == '__main__':
    import sys
    images_only = '--images-only' in sys.argv
    os.makedirs(IMG, exist_ok=True)
    print('frames from the Third Space London film:')
    m = build_frames()
    print('\nframes from the Third Space Wimbledon film:')
    m += build_frames(WIM_FRAMES, VIDEO_WIM)
    print('\nmaterial swatches from extracted slab photography:')
    m += build_swatches()
    print('\nvideo encodes:')
    build_video()

    with open(os.path.join(ROOT, 'assets', 'ALT-TEXT.md'), 'w', encoding='utf-8') as f:
        f.write('# Image alt text\n\nGenerated by make_assets.py. '
                'Every image is the client\'s own work.\n\n'
                '| Asset | Ratio | Alt text |\n|---|---|---|\n')
        for name, ratio, size, widths, alt in m:
            f.write(f'| `{name}` | {ratio} | {alt} |\n')
    print(f'\nwrote {len(m)} assets + ALT-TEXT.md')
