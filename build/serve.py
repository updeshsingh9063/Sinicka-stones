#!/usr/bin/env python3
"""Local preview server for site/.

python -m http.server answers Range requests with a plain 200 and the whole
file. Browsers tolerate that for small assets but it is not how a real host
behaves, and it is a known cause of <video> stalling on its first frame during
local testing. This adds proper 206 handling so what you see locally matches
what ships.

    python serve.py [port]
"""
import os, re, sys, functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site')


class RangeHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      '.woff2': 'font/woff2', '.avif': 'image/avif',
                      '.webp': 'image/webp', '.mp4': 'video/mp4'}

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-store')
        SimpleHTTPRequestHandler.end_headers(self)

    def send_head(self):
        rng = self.headers.get('Range')
        if not rng:
            return SimpleHTTPRequestHandler.send_head(self)
        m = re.match(r'bytes=(\d*)-(\d*)$', rng.strip())
        path = self.translate_path(self.path)
        if not m or not os.path.isfile(path):
            return SimpleHTTPRequestHandler.send_head(self)

        size = os.path.getsize(path)
        start, end = m.group(1), m.group(2)
        if start == '':                       # suffix range: last N bytes
            start = max(0, size - int(end)); end = size - 1
        else:
            start = int(start)
            end = int(end) if end else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416, 'Requested Range Not Satisfiable')
            return None

        f = open(path, 'rb'); f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        return _Bounded(f, end - start + 1)


class _Bounded:
    """File wrapper that stops at the end of the requested range."""
    def __init__(self, f, remaining): self.f, self.remaining = f, remaining
    def read(self, n=-1):
        if self.remaining <= 0: return b''
        if n < 0 or n > self.remaining: n = self.remaining
        data = self.f.read(n); self.remaining -= len(data); return data
    def close(self): self.f.close()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    handler = functools.partial(RangeHandler, directory=ROOT)
    print(f'serving {ROOT} on http://127.0.0.1:{port}  (Range supported)')
    ThreadingHTTPServer(('127.0.0.1', port), handler).serve_forever()
