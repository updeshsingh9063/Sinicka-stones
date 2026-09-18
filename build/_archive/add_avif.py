#!/usr/bin/env python3
"""
Two jobs:

1. Adds an AVIF <source> to every existing <picture> in _pages/.
   Order in the markup is avif, webp, jpg: the browser takes the first type it
   understands. AVIF runs about 60% smaller than the JPEG baseline here.

2. Rebuilds the homepage hero so the still image is a responsive <picture>
   rather than a <video poster>. The poster attribute takes a single URL, so
   the old markup pushed a 1920px JPEG to phones even though kroll.js removes
   the video on small screens. Now the picture is always the base layer and
   kroll.js inserts the video over it only when it is actually going to play.

    python add_avif.py
"""

import os, re, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(ROOT, 'assets', 'img')


def widths(asset, ext):
    out = []
    for f in glob.glob(os.path.join(IMG, f'{asset}-*.{ext}')):
        m = re.search(r'-(\d+)\.' + ext + '$', os.path.basename(f))
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


SOURCE_RE = re.compile(
    r'(\s*)<source type="image/webp" srcset="([^"]*)" sizes="([^"]*)">')


def add_avif(text):
    """Insert an avif <source> immediately before each webp one."""
    def repl(m):
        indent, srcset, sizes = m.group(1), m.group(2), m.group(3)
        asset = None
        first = re.search(r'assets/img/([A-Za-z0-9\-]+)-\d+\.webp', srcset)
        if first:
            asset = first.group(1)
        if not asset:
            return m.group(0)
        ws = widths(asset, 'avif')
        if not ws:
            return m.group(0)
        avif = ', '.join(
            '{{ROOT}}/assets/img/%s-%d.avif %dw' % (asset, w, w) for w in ws)
        return ('%s<source type="image/avif" srcset="%s" sizes="%s">%s'
                % (indent, avif, sizes, m.group(0)))
    return SOURCE_RE.sub(repl, text)


HERO_OLD = re.compile(
    r'<div class="k-media k-ratio-hero">\s*<!--.*?-->\s*'
    r'<video class="k-hero__video".*?</video>\s*</div>', re.S)

HERO_NEW = '''<div class="k-media k-ratio-hero" data-hero-slot>
      <!-- Base layer: a responsive still, always rendered. kroll.js inserts the
           looping film over the top only when it will actually play, so phones
           and reduced-motion visitors download neither the video nor an
           oversized poster. Sources are listed avif, webp, jpg. -->
      <picture>
        <source type="image/avif" srcset="AVIF" sizes="100vw">
        <source type="image/webp" srcset="WEBP" sizes="100vw">
        <img src="{{ROOT}}/assets/img/hero-stone-floor-1920.jpg" srcset="JPG" sizes="100vw"
             width="1920" height="1080"
             alt="Large-format stone flooring between marble-clad walls at Third Space, London"
             fetchpriority="high" decoding="async">
      </picture>
    </div>'''


def rebuild_hero(text):
    if 'data-hero-slot' in text:
        return text, False
    m = HERO_OLD.search(text)
    if not m:
        return text, False
    a = ', '.join('{{ROOT}}/assets/img/hero-stone-floor-%d.avif %dw' % (w, w)
                  for w in widths('hero-stone-floor', 'avif'))
    w_ = ', '.join('{{ROOT}}/assets/img/hero-stone-floor-%d.webp %dw' % (w, w)
                   for w in widths('hero-stone-floor', 'webp'))
    j = ', '.join('{{ROOT}}/assets/img/hero-stone-floor-%d.jpg %dw' % (w, w)
                  for w in widths('hero-stone-floor', 'jpg'))
    new = HERO_NEW.replace('AVIF', a).replace('WEBP', w_).replace('JPG', j)
    return text[:m.start()] + new + text[m.end():], True


def main():
    n_avif = n_hero = 0
    for f in sorted(glob.glob(os.path.join(ROOT, '_pages', '*.html'))):
        t = open(f, encoding='utf-8').read()
        before = t.count('image/avif')
        t = add_avif(t)
        added = t.count('image/avif') - before

        t, hero = rebuild_hero(t)
        if hero:
            n_hero += 1

        if added or hero:
            open(f, 'w', encoding='utf-8').write(t)
            n_avif += added
            bits = []
            if added:
                bits.append('%d avif source(s)' % added)
            if hero:
                bits.append('hero rebuilt')
            print('  %-26s %s' % (os.path.basename(f), ', '.join(bits)))
    print('\n%d avif sources added, %d hero(s) rebuilt' % (n_avif, n_hero))


if __name__ == '__main__':
    main()
