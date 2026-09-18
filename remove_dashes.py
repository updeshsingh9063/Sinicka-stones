#!/usr/bin/env python3
"""
Removes em dashes and en dashes from everything written for this project.

Deliberately narrow, after an earlier attempt corrupted source files:
  - it replaces ONLY the two dash characters, at the position they occur
  - it runs NO tidy-up regexes over the file afterwards
  - it never touches captured client data
  - it verifies Python still parses and CSS braces still balance

Excluded, because the dashes there are the client's real data rather than our
prose: site-extract/asset-manifest.csv (original filenames on their server) and
site-extract/content/*.txt (raw page scrapes).

In a CSV the replacement is a colon, never a comma, because an unquoted comma
would add a column.

    python remove_dashes.py --dry-run
    python remove_dashes.py
"""

import os, re, sys, ast

EM, EN = chr(8212), chr(8211)
DASH = EM + EN
NL = chr(10)
TAB = chr(9)

EXCLUDE_FILES = {'site-extract/asset-manifest.csv'}
EXCLUDE_DIRS = {'.git', 'site', 'assets', '_raw-html', '.claude-memory', 'provided by client'}
EXCLUDE_PATTERNS = ('site-extract/content/',)
EXTS = ('.html', '.md', '.css', '.js', '.py', '.txt', '.csv', '.htaccess')

TRAILING = re.compile('[ ' + TAB + ']*' + NL)


def replace_one(text, i, line_start, is_csv):
    """Return (replacement, chars_to_consume_after_the_dash).

    The caller strips any whitespace that preceded the dash, so we never leave
    a space sitting in front of the punctuation we insert.
    """
    before = text[:i]
    after = text[i + 1:]
    space_after = after[:1] == ' '

    # numeric range: 180-220ms, 18-20
    if re.search(r'\d\s?$', before) and re.match(r'\s?\d', after):
        return '-', 2 if space_after else 1

    # dash at the end of a line: drop it
    if TRAILING.match(after):
        return '', 1

    line_end = text.find(NL, i)
    line = text[line_start:line_end if line_end != -1 else len(text)]

    # Headings read better with a colon. CSVs must not gain a comma.
    sep = ':' if (is_csv or line.lstrip().startswith('#')) else ','

    # If the preceding text already ends in punctuation, the dash is redundant.
    if before.rstrip().endswith((',', ':', ';', '.', '!', '?')):
        return '', 2 if space_after else 1

    return sep, 2 if space_after else 1


def process(text, is_csv=False):
    out = []
    i = 0
    line_start = 0
    changed = 0
    while i < len(text):
        ch = text[i]
        if ch == NL:
            line_start = i + 1
        if ch in DASH:
            rep, consume = replace_one(text, i, line_start, is_csv)
            while out and out[-1] in (' ', TAB):
                out.pop()
            if rep:
                out.append(rep)
                out.append(' ')
            elif consume == 2:
                out.append(' ')
            i += consume
            changed += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out), changed


def targets():
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if not f.endswith(EXTS):
                continue
            p = os.path.join(root, f).replace(os.sep, '/')
            if p.startswith('./'):
                p = p[2:]
            if p in EXCLUDE_FILES or any(x in p for x in EXCLUDE_PATTERNS):
                continue
            yield p


def verify(path, original, new):
    """Return an error string if the change broke the file."""
    if path.endswith('.py'):
        try:
            ast.parse(new)
        except SyntaxError as e:
            return 'python syntax: %s' % e
    if path.endswith('.css'):
        s = re.sub(r'/\*.*?\*/', '', new, flags=re.S)
        if s.count('{') != s.count('}'):
            return 'unbalanced CSS braces'
    if path.endswith('.csv'):
        a = [len(l.split(',')) for l in original.split(NL) if l.strip()]
        b = [len(l.split(',')) for l in new.split(NL) if l.strip()]
        if a != b:
            return 'CSV column count changed'
    if path.endswith(('.html', '.js')):
        for pair in (('<picture>', '</picture>'), ('{', '}')):
            if path.endswith('.html') and pair[0] == '{':
                continue
            if new.count(pair[0]) != original.count(pair[0]):
                return 'structure changed near %s' % pair[0]
    return None


def main():
    dry = '--dry-run' in sys.argv
    total = files = 0
    for p in targets():
        try:
            t = open(p, encoding='utf-8').read()
        except Exception:
            continue
        if not any(d in t for d in DASH):
            continue
        new, n = process(t, p.endswith('.csv'))
        err = verify(p, t, new)
        if err:
            print('  SKIPPED %s: %s' % (p, err))
            continue
        if not dry:
            open(p, 'w', encoding='utf-8').write(new)
        total += n
        files += 1
        print('  %-56s %4d' % (p, n))
    print('\n%d dashes removed from %d files%s'
          % (total, files, ' (dry run)' if dry else ''))


if __name__ == '__main__':
    main()
