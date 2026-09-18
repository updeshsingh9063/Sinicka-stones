#!/usr/bin/env python3
"""
Cuts the case-study film strips from Kroll's own project films.

Every clip is one uninterrupted shot (cut points found with ffmpeg scene
detection, 2026-09-17), slowed to half speed with motion interpolation, then
played forward and back so the loop has no jump. Silent, H.264, faststart.
Also writes a poster frame for each clip and for the two existing 12-second
project loops.

    python make_clips.py

The Wimbledon source is still the WhatsApp copy, so it is cropped away from
the Fiverr preview mark (WIM_CROP, same as make_assets.py). Swap in the
unwatermarked master when it arrives and drop the crop.
"""

import os, sys, subprocess
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(ROOT)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(ROOT, 'assets', 'video')

LONDON = os.path.join(PROJ, 'provided by client', 'kroll_interiors___third_space_-_london_uk (1080p).mp4')
WIMBLEDON = os.path.join(PROJ, 'WhatsApp Video 2026-09-14 at 10.05.10 AM.mp4')
WIM_CROP = 'crop=1152:648:0:72,'

# name, source, crop, start, end, width, what the shot shows (used as caption)
# Every range was checked frame by frame on 2026-09-17: single shot, no people,
# no signage-only frames. Both films contain on-camera interviews; none of
# those frames may be cut into a loop without the speaker's permission.
CLIPS = [
    ('ts-reception', LONDON, '', 10.75, 11.95, 1280, 'Stone reception desk'),
    ('ts-amber',     LONDON, '', 16.15, 18.00, 960,  'Amber textured tiling to locker fronts'),
    ('ts-drainage',  LONDON, '', 69.75, 71.60, 1280, 'Stone floor with linear drainage in a wet area'),
    ('ts-entrance',  LONDON, '', 49.50, 51.50, 960,  'Polished floor through the entrance'),
    ('ts-green',     LONDON, '', 27.55, 29.10, 960,  'Glazed green tiling to a curved return'),
    ('ts-vein',      LONDON, '', 65.55, 66.90, 960,  'Veined stone with a metal inlay'),
    ('wb-changing',  WIMBLEDON, WIM_CROP, 41.30, 45.50, 1152, 'Changing room over large-format porcelain'),
    ('wb-green',     WIMBLEDON, WIM_CROP, 22.40, 24.50, 960,  'Glazed green ceramic, stacked and stepped'),
    ('wb-lockers',   WIMBLEDON, WIM_CROP, 46.90, 50.60, 960,  'Locker bays along the changing room'),
    ('wb-floor',     WIMBLEDON, WIM_CROP, 37.80, 40.80, 960,  'Large-format floor and circulation'),
    ('wb-brass',     WIMBLEDON, WIM_CROP, 13.20, 14.90, 960,  'Brass-toned tiling at the entrance'),
]

# Project reels for the cards and case-study plates: slowed shots joined by
# short crossfades. Replaces hero-loop and wimb-loop, which both open on or
# contain an interview.
REELS = [
    ('ts-reel', LONDON, '', [(69.75, 71.60), (10.75, 11.95), (65.55, 66.90), (49.50, 51.50)], [1920, 1280]),
    ('wb-reel', WIMBLEDON, WIM_CROP, [(41.30, 45.50), (46.90, 50.60), (22.40, 24.50), (13.20, 14.90)], [1152]),
]


def run(args):
    r = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode:
        raise SystemExit('ffmpeg failed:\n' + r.stderr.decode('utf-8', 'replace')[-2000:])


def clip(name, src, crop, a, b, width, _caption):
    dest = os.path.join(OUT, 'clips', name + '.mp4')
    graph = ('[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS,%sscale=%d:-2:flags=lanczos,'
             'minterpolate=fps=50:mi_mode=mci:mc_mode=aobmc:vsbmc=1,setpts=N/25/TB,'
             'split[f][r0];[r0]reverse[r];[f][r]concat=n=2:v=1:a=0,fps=25,format=yuv420p[v]'
             % (a, b, crop, width))
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
         '-filter_complex', graph, '-map', '[v]', '-an',
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-profile:v', 'high',
         '-movflags', '+faststart', dest])
    poster(dest, os.path.join(OUT, 'clips', name + '.jpg'), 0.2)
    print('  %-14s %5.0f KB' % (name, os.path.getsize(dest) / 1024))


def reel(name, src, crop, ranges, widths):
    xf = 0.7   # crossfade, seconds of output
    for width in widths:
        dest = os.path.join(OUT, '%s-%d.mp4' % (name, width))
        # One seeked input per shot: no split, so nothing is buffered while a
        # later branch waits for its start time.
        inputs, parts = [], []
        for i, (a, b) in enumerate(ranges):
            inputs += ['-ss', '%.3f' % a, '-t', '%.3f' % (b - a), '-i', src]
            parts.append('[%d:v]setpts=PTS-STARTPTS,%sscale=%d:-2:flags=lanczos,'
                         'minterpolate=fps=50:mi_mode=mci:mc_mode=aobmc:vsbmc=1,setpts=N/25/TB,fps=25,'
                         'format=yuv420p,settb=AVTB[s%d]' % (i, crop, width, i))
        acc, length = 's0', (ranges[0][1] - ranges[0][0]) * 2
        for i in range(1, len(ranges)):
            out = 'x%d' % i
            parts.append('[%s][s%d]xfade=transition=fade:duration=%.2f:offset=%.3f[%s]'
                         % (acc, i, xf, length - xf, out))
            length += (ranges[i][1] - ranges[i][0]) * 2 - xf
            acc = out
        parts.append('[%s]format=yuv420p[vout]' % acc)   # xfade hands back 4:4:4
        run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y'] + inputs +
            ['-filter_complex', ';'.join(parts), '-map', '[vout]', '-an',
             '-c:v', 'libx264', '-preset', 'slow', '-crf', '26' if width > 1200 else '27',
             '-profile:v', 'high', '-movflags', '+faststart', dest])
        print('  %-14s %5.0f KB  %.1fs' % (os.path.basename(dest), os.path.getsize(dest) / 1024, length))
    poster(dest, os.path.join(OUT, name + '.jpg'), 0.3)


def poster(video, dest, t):
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(t), '-i', video,
         '-frames:v', '1', '-q:v', '3', dest])


if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'clips'), exist_ok=True)
    only = sys.argv[1:]
    print('film strip clips:')
    for c in CLIPS:
        if not only or 'clips' in only:
            clip(*c)
    print('project reels:')
    for r in REELS:
        reel(*r)
    poster(os.path.join(OUT, 'third-space-1080.mp4'), os.path.join(OUT, 'third-space-poster.jpg'), 70.4)
    poster(os.path.join(OUT, 'wimbledon-720.mp4'), os.path.join(OUT, 'wimbledon-poster.jpg'), 43.8)
    print('posters written')
