#!/usr/bin/env python3
"""
Kroll Interiors, static build.

Assembles _pages/*.html into site/ using the shared partials. Mirrors the
WordPress header.php / footer.php split exactly, so the transfer is mechanical:
_partials/header.html becomes header.php, footer.html becomes footer.php, and
each page body becomes a template part.

    python build.py            development
    python build.py --prod     concatenate and minify CSS/JS into one request

Output: site/ (open site/index.html directly, all links are relative)
"""

import os, re, sys, json, shutil, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, 'site')

BASE   = open(os.path.join(ROOT, '_partials', 'base.html'),   encoding='utf-8').read()
HEADER = open(os.path.join(ROOT, '_partials', 'header.html'), encoding='utf-8').read()
FOOTER = open(os.path.join(ROOT, '_partials', 'footer.html'), encoding='utf-8').read()

SITE = 'https://krollinteriors.co.uk'

# ---------------------------------------------------------------------------
# Organisation schema, emitted on every page.
# Type is HomeAndConstructionBusiness, not the bare Organization the current
# site uses. Street address, opening hours and registration number are stubbed
# pending client input (Phase A questions 1 to 4). Do NOT invent them.
# ---------------------------------------------------------------------------
ORG_SCHEMA = """  {
    "@type": "HomeAndConstructionBusiness",
    "@id": "%(site)s/#organization",
    "name": "Kroll Interiors",
    "legalName": "Kroll Interiors LTD",
    "url": "%(site)s/",
    "description": "Specialist tiling and stone contractors in London. Wall and floor tiling and stone work for private clients, developers and main contractors.",
    "email": "enquiries@krollinteriors.co.uk",
    "telephone": "+44 20 3633 0923",
    "areaServed": { "@type": "City", "name": "London" },
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "London",
      "addressRegion": "Greater London",
      "addressCountry": "GB"
    },
    "sameAs": [
      "https://www.facebook.com/krollinteriors18",
      "https://www.instagram.com/krollinteriorsuk/",
      "https://www.linkedin.com/company/kroll-interiors/"
    ]
  }""" % {'site': SITE}


PAGES = [
    dict(path='/', out='index.html', src='home.html', ogtype='website',
         title='Specialist Tiling & Stone Contractors London | Kroll Interiors',
         desc='Specialist tiling and stone contractors in London. Ceramic, porcelain, natural stone and engineered stone for private clients, developers and main contractors. Approved Schluter tanking contractors.'),

    dict(path='/about/', out='about/index.html', src='about.html',
         title='About Kroll Interiors | London Tiling & Stone Contractors',
         desc='Kroll Interiors is a London-based tiling and stone contractor working across private homes and commercial fit-outs. NVQ Level 2 certified, fully insured, approved Schluter contractors.'),

    dict(path='/approach/', out='approach/index.html', src='approach.html',
         title='Our Approach | How Kroll Interiors Delivers Projects',
         desc='From brief and measured survey through setting out, material sourcing, substrate engineering and installation to snagging and handover. How Kroll Interiors runs a tiling and stone project.'),

    dict(path='/services/', out='services/index.html', src='services.html',
         title='Tiling & Stone Services London | Kroll Interiors',
         desc='Ceramic and porcelain tiling, natural stone, granite, engineered stone, and fully tanked bathrooms and wet rooms. Specialist installation across London.'),

    dict(path='/services/ceramic-porcelain-tiling/', service='Ceramic and porcelain tiling',
         out='services/ceramic-porcelain-tiling/index.html', src='svc-ceramic.html',
         title='Porcelain & Ceramic Tiling Contractors London | Kroll Interiors',
         desc='Large-format porcelain and ceramic tiling specialists in London. Slab installation, precision cutting, substrate preparation and movement joint detailing.'),

    dict(path='/services/natural-stone/', service='Natural stone installation',
         out='services/natural-stone/index.html', src='svc-stone.html',
         title='Natural Stone Installation London | Marble, Limestone & Travertine',
         desc='Natural stone installation across London. Marble, limestone, travertine and onyx, specified, sourced, set out and sealed by NVQ Level 2 certified installers.'),

    dict(path='/services/granite/', service='Granite installation',
         out='services/granite/index.html', src='svc-granite.html',
         title='Granite Installation London | Granite Flooring Contractors',
         desc='Granite flooring and cladding installation in London. Dense, hard-wearing stone for high-traffic residential and commercial floors, cut and set out to tolerance.'),

    dict(path='/services/engineered-stone/', service='Engineered stone installation',
         out='services/engineered-stone/index.html', src='svc-engineered.html',
         title='Quartz & Engineered Stone Installation London | Kroll Interiors',
         desc='Quartz, Dekton and Silestone installation in London. Engineered stone surfaces fitted by specialist contractors, with large-format handling, dry-lay and precision jointing.'),

    dict(path='/services/bathrooms-wet-rooms/', service='Wet room and bathroom tanking',
         out='services/bathrooms-wet-rooms/index.html', src='svc-wetroom.html',
         title='Wet Room Specialists London | Bathroom Tanking Contractors',
         desc='Fully tanked wet rooms and bathrooms in London. As approved Schluter contractors we install the waterproofing system as a continuous layer before any tile goes down.'),

    dict(path='/sectors/luxury-residential/', out='sectors/luxury-residential/index.html',
         src='sec-residential.html',
         title='Luxury Residential Tiling London | Kroll Interiors',
         desc='Tiling and stone work for private London homes. Bathrooms, wet rooms, kitchens, hallways and whole-house schemes, delivered with certified waterproofing and precise setting out.'),

    dict(path='/sectors/commercial/', out='sectors/commercial/index.html', src='sec-commercial.html',
         title='Commercial Tiling Contractors London | Fit-Out Specialists',
         desc='Commercial tiling and stone contractors in London. Pre-qualified, accredited and insured, working to the drawing and the programme. Recent work includes Kings Cross and WeLink Homes.'),

    dict(path='/projects/', out='projects/index.html', src='projects.html',
         title='Projects | Kroll Interiors Tiling & Stone, London',
         desc='Selected tiling and stone projects by Kroll Interiors across London, residential and commercial, from wet rooms to large-format commercial fit-outs.'),

    dict(path='/projects/third-space-london/', out='projects/third-space-london/index.html',
         src='case-third-space.html', ogtype='article',
         title='Third Space, London Case Study | Kroll Interiors',
         desc='Large-format porcelain and certified tanking to changing areas, wet rooms and pool surround at Third Space, London. A Kroll Interiors commercial case study.'),

    dict(path='/projects/wimbledon/', out='projects/wimbledon/index.html',
         src='case-wimbledon.html', ogtype='article',
         title='Third Space Wimbledon Case Study | Kroll Interiors',
         desc='Large-format porcelain, terrazzo and glazed ceramic across changing rooms, locker bays and circulation at Third Space Wimbledon. A Kroll Interiors commercial case study.'),

    dict(path='/materials/', out='materials/index.html', src='materials.html',
         title='Materials | Stone, Porcelain & Engineered Surfaces | Kroll Interiors',
         desc='Natural stone, granite, engineered stone, porcelain and ceramic. How each material behaves once it is on the wall, and what that means for substrate, adhesive and jointing.'),

    dict(path='/faq/', out='faq/index.html', src='faq.html',
         title='Frequently Asked Questions | Kroll Interiors',
         desc='Common questions about tanking systems, wet rooms, large-format tiling, working with architects and main contractors, and how Kroll Interiors quotes a project.'),

    dict(path='/contact/', out='contact/index.html', src='contact.html', close=False,
         title='Get a Quote | Contact Kroll Interiors, London',
         desc='Tell us about your project and we will come back with a measured quote. Call 020 3633 0923 or send drawings, photographs and a schedule through the form.'),

    dict(path='/privacy-policy/', out='privacy-policy/index.html', src='privacy.html',
         title='Privacy & Cookies | Kroll Interiors',
         desc='How Kroll Interiors collects, uses and protects personal data submitted through this website.'),
]


def breadcrumb_schema(p):
    """Built from the URL path, so it can never drift from the hierarchy."""
    parts = [x for x in p['path'].strip('/').split('/') if x]
    items = ['      {"@type": "ListItem", "position": 1, "name": "Home", '
             '"item": "%s/"}' % SITE]
    acc = ''
    for i, seg in enumerate(parts, start=2):
        acc += '/' + seg
        label = next((q['title'].split('|')[0].strip()
                      for q in PAGES if q['path'].rstrip('/') == acc),
                     seg.replace('-', ' ').title())
        items.append('      {"@type": "ListItem", "position": %d, "name": %s, "item": "%s%s/"}'
                     % (i, json.dumps(label), SITE, acc))
    return ('  {\n    "@type": "BreadcrumbList",\n    "@id": "%s%s#breadcrumb",\n'
            '    "itemListElement": [\n%s\n    ]\n  }' % (SITE, p['path'], ',\n'.join(items)))


def service_schema(p):
    return ('  {\n    "@type": "Service",\n    "@id": "%s%s#service",\n'
            '    "name": %s,\n    "serviceType": %s,\n'
            '    "provider": { "@id": "%s/#organization" },\n'
            '    "areaServed": { "@type": "City", "name": "London" },\n'
            '    "url": "%s%s"\n  }'
            % (SITE, p['path'], json.dumps(p['service']), json.dumps(p['service']),
               SITE, SITE, p['path']))


def faq_schema(content):
    """Reads the <details> blocks already in the page, so the markup and the
    structured data cannot disagree. Change the copy and the schema follows."""
    pairs = re.findall(
        r'<summary class="k-faq__q">(.*?)<span class="k-faq__icon".*?</summary>\s*'
        r'<div class="k-faq__a"><p>(.*?)</p></div>', content, re.S)
    if not pairs:
        return ''

    def strip(s):
        return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()

    qs = ',\n'.join(
        '      {"@type": "Question", "name": %s, "acceptedAnswer": '
        '{"@type": "Answer", "text": %s}}' % (json.dumps(strip(q)), json.dumps(strip(a)))
        for q, a in pairs)
    return '  {\n    "@type": "FAQPage",\n    "mainEntity": [\n%s\n    ]\n  }' % qs


# ---------------------------------------------------------------------------
# Image shortcode.
#
#   {{img slot=interior-res crop=p sizes="(min-width:900px) 45vw, 100vw"}}
#   {{img slot=hero-stone crop=h sizes="100vw" eager alt="Override text"}}
#
# Expands to <picture> with AVIF, WebP and JPEG srcsets built from whatever
# widths make_stock.py actually produced (assets/img/manifest.json), so a page
# can never reference a file that does not exist. Alt text comes from the
# manifest, which records what each photograph shows; `alt=""` marks an image
# decorative. `eager` is for the one above-the-fold image per page.
# ---------------------------------------------------------------------------
IMG_MANIFEST_PATH = os.path.join(ROOT, 'assets', 'img', 'manifest.json')
IMG_MANIFEST = (json.load(open(IMG_MANIFEST_PATH, encoding='utf-8'))
                if os.path.exists(IMG_MANIFEST_PATH) else {})
IMG_TAG = re.compile(r'\{\{img\s+([^}]*)\}\}')
IMG_ATTR = re.compile(r'([a-z]+)(=(?:"([^"]*)"|(\S+)))?')
MISSING_IMAGES = []


def expand_img(m):
    attrs = {}
    for k, has_value, quoted, bare in IMG_ATTR.findall(m.group(1)):
        attrs[k] = (quoted if quoted or bare == '' else bare) if has_value else True
    key = '%s-%s' % (attrs['slot'], attrs['crop'])
    entry = IMG_MANIFEST.get(key)
    if not entry:
        MISSING_IMAGES.append(key)
        return '<!-- MISSING IMAGE %s -->' % key
    widths = entry['widths']
    base = '{{ROOT}}/assets/img/' + key
    sizes = attrs.get('sizes', '100vw')
    alt = attrs['alt'] if isinstance(attrs.get('alt'), str) else entry['alt']
    eager = attrs.get('eager') is True
    largest = widths[-1]
    fallback = next((w for w in widths if w >= 1200), largest)
    srcset = lambda ext: ', '.join('%s-%d.%s %dw' % (base, w, ext, w) for w in widths)
    loading = 'fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
    return ('<picture>'
            '<source type="image/avif" srcset="%s" sizes="%s">'
            '<source type="image/webp" srcset="%s" sizes="%s">'
            '<img src="%s-%d.jpg" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" %s>'
            '</picture>') % (srcset('avif'), sizes, srcset('webp'), sizes,
                             base, fallback, srcset('jpg'), sizes,
                             entry['width'], entry['height'], html.escape(alt, quote=True), loading)


def build_page(p):
    src = os.path.join(ROOT, '_pages', p['src'])
    if not os.path.exists(src):
        print('  MISSING _pages/%s, skipped' % p['src'])
        return False
    content = open(src, encoding='utf-8').read()

    depth = p['out'].count('/')
    root = '.' if depth == 0 else '/'.join(['..'] * depth)

    schema_body = ORG_SCHEMA + ',\n' + breadcrumb_schema(p)
    if p.get('service'):
        schema_body += ',\n' + service_schema(p)
    faq = faq_schema(content)
    if faq:
        schema_body += ',\n' + faq
    schema = ('<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n'
              '  "@graph": [\n' + schema_body + '\n  ]\n}\n</script>')

    page = BASE
    page = page.replace('{{TITLE}}',       html.escape(p['title'], quote=True))
    page = page.replace('{{DESCRIPTION}}', html.escape(p['desc'],  quote=True))
    page = page.replace('{{PATH}}',        p['path'])
    page = page.replace('{{OGTYPE}}',      p.get('ogtype', 'website'))
    page = page.replace('{{SCHEMA}}',      schema)
    footer = FOOTER
    if p.get('close') is False:
        footer = re.sub(r'<!--CLOSE-->.*?<!--/CLOSE-->', '', footer, flags=re.S)
    page = page.replace('{{HEADER}}',      HEADER)
    page = page.replace('{{FOOTER}}',      footer)
    page = page.replace('{{CONTENT}}',     content)

    for key in ('approach', 'projects', 'materials', 'about'):
        marker = '{{CUR_%s}}' % key
        page = page.replace(marker,
                            ' aria-current="page"' if p['path'].startswith('/' + key) else '')

    # Image tags are expanded after assembly so the shared partials can use
    # them too, and before {{ROOT}} is resolved.
    page = IMG_TAG.sub(expand_img, page)
    page = page.replace('{{ROOT}}', root)

    dest = os.path.join(OUT, p['out'])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(page)
    return True


CSS_ORDER = ['00-fonts.css', 'scrollcraft.css', '10-tokens.css', '11-base.css',
             '12-layout.css', '13-chrome.css', '14-components.css', '15-home.css']


def minify_css(src):
    """Conservative. Comments, redundant whitespace, and the last semicolon in
    a block. Deliberately does not rewrite selectors or values."""
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    src = re.sub(r'\s+', ' ', src)
    # Never strip the space BEFORE a colon: in a selector it is a descendant
    # combinator, and `.sc-stage :is(video)` would become `.sc-stage:is(video)`.
    src = re.sub(r'\s*([{};,>])\s*', r'\1', src)
    src = re.sub(r':\s+', ':', src)
    src = re.sub(r';}', '}', src)
    return src.strip()


# NOTE: there is deliberately no JS minifier here.
#
# An earlier one stripped only the first line of each block comment, leaving
# the body as bare text. The result failed to parse on line 1, so NO script
# ran in the production build at all: no nav, no reveals, no hero video. It
# went unnoticed because the dev build serves the unminified file.
#
# kroll.js is 10 KB. Gzip or Brotli on the server does the real work, and a
# hand-rolled minifier that has to understand strings, regex literals and
# comments is not worth that saving. The file ships as written.


def build_production():
    css = '\n'.join(open(os.path.join(ROOT, 'css', f), encoding='utf-8').read()
                    for f in CSS_ORDER)
    mini = minify_css(css)
    open(os.path.join(OUT, 'css', 'kroll.min.css'), 'w', encoding='utf-8').write(mini)

    # Collapses the eight <link> tags into one. Must start at 00-fonts, which
    # is the first stylesheet in CSS_ORDER, and end at the last one.
    link_block = re.compile(
        r'(<link rel="stylesheet" href="[^"]*?/css/00-fonts\.css">.*?'
        r'<link rel="stylesheet" href="[^"]*?/css/15-home\.css">)', re.S)

    for root, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith('.html'):
                continue
            path = os.path.join(root, f)
            t = open(path, encoding='utf-8').read()
            m = link_block.search(t)
            if m:
                prefix = re.search(r'href="([^"]*?)/css/00-fonts\.css"', m.group(1)).group(1)
                t = t.replace(m.group(1),
                              '<link rel="stylesheet" href="%s/css/kroll.min.css">' % prefix)
            open(path, 'w', encoding='utf-8').write(t)

    print('production: css %dK to %dK (%d%% smaller), %d requests to 1'
          % (len(css) / 1024, len(mini) / 1024,
             100 - len(mini) * 100 // len(css), len(CSS_ORDER)))


def main():
    prod = '--prod' in sys.argv

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    for d in ('css', 'js', 'assets'):
        s = os.path.join(ROOT, d)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(OUT, d),
                            ignore=shutil.ignore_patterns('manifest.json', '*.md'))

    built = sum(1 for p in PAGES if build_page(p))
    print('built %d/%d pages -> site/' % (built, len(PAGES)))
    if MISSING_IMAGES:
        print('  WARNING: %d image references not in manifest: %s'
              % (len(MISSING_IMAGES), ', '.join(sorted(set(MISSING_IMAGES)))))

    if prod:
        build_production()

    urls = '\n'.join('  <url><loc>%s%s</loc></url>' % (SITE, p['path']) for p in PAGES)
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + '\n</urlset>\n')

    open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nDisallow: /wp-admin/\nAllow: /wp-admin/admin-ajax.php\n\n'
        'Sitemap: %s/sitemap.xml\n' % SITE)

    print('wrote sitemap.xml, robots.txt')


if __name__ == '__main__':
    main()
