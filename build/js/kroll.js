/* ==========================================================================
   KROLL INTERIORS, kroll.js
   Progressive enhancement only. Without this file every page is complete:
   the nav is a list, the FAQ is <details>, the films have native controls,
   the cutaway renders exploded and labelled, and every reveal renders in
   place (see the no-JS floor in 11-base.css).

   Order at start-up:
     1. split headline lines (so the engine never measures half-split text)
     2. mount the scrollcraft engine (pins, pan rail, progress variables)
     3. start Lenis smooth scrolling
     4. everything else
   ========================================================================== */

(function () {
  'use strict';

  var doc = document.documentElement;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  var conn = navigator.connection || {};
  var saveData = conn.saveData === true || /(^|-)2g$/.test(conn.effectiveType || '');

  var clamp01 = function (x) { return x < 0 ? 0 : x > 1 ? 1 : x; };
  var each = function (sel, fn, root) { Array.prototype.forEach.call((root || document).querySelectorAll(sel), fn); };

  var lenis = null;
  var engine = null;

  /* ---- 1. line splitting ------------------------------------------------------
     Wraps each rendered line of a heading in a mask so it can rise into place.
     Inline emphasis (<em>) survives: each word inside it keeps its own <em>.
     Re-splits on width change, because line breaks move. */

  function splitLines(el) {
    if (!el.__kSource) el.__kSource = el.innerHTML;
    else el.innerHTML = el.__kSource;

    var words = [];
    (function walk(node, wrap) {
      Array.prototype.forEach.call(Array.prototype.slice.call(node.childNodes), function (n) {
        if (n.nodeType === 3) {
          n.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { words.push(' '); return; }
            var w = document.createElement('span');
            w.className = 'k-w';
            w.textContent = part;
            if (wrap) { var e = wrap.cloneNode(false); e.appendChild(w); words.push(e); }
            else words.push(w);
          });
        } else if (n.nodeType === 1) {
          walk(n, n);
        }
      });
    })(el, null);

    el.textContent = '';
    words.forEach(function (w) { el.appendChild(w === ' ' ? document.createTextNode(' ') : w); });

    var lines = [], cur = null, lastTop = null;
    words.forEach(function (w) {
      if (w === ' ') return;
      var top = w.offsetTop;
      if (lastTop === null || Math.abs(top - lastTop) > 3) { cur = []; lines.push(cur); lastTop = top; }
      cur.push(w);
    });

    el.textContent = '';
    lines.forEach(function (line, i) {
      var mask = document.createElement('span');
      mask.className = 'k-line';
      var inner = document.createElement('span');
      inner.className = 'k-line__i';
      inner.style.setProperty('--i', i);
      line.forEach(function (w, j) {
        if (j) inner.appendChild(document.createTextNode(' '));
        inner.appendChild(w);
      });
      mask.appendChild(inner);
      el.appendChild(mask);
      if (i < lines.length - 1) el.appendChild(document.createTextNode(' '));
    });
    el.classList.add('is-split');
  }

  function initLines() {
    var els = document.querySelectorAll('[data-k-lines]');
    if (!els.length) return;
    var run = function () { Array.prototype.forEach.call(els, splitLines); };
    var done = false;
    var go = function () { if (done) return; done = true; run(); };
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(go);
      setTimeout(go, 1400);   // a font that never settles must not hide a headline
    } else {
      go();
    }
    var w = innerWidth, t = null;
    addEventListener('resize', function () {
      if (innerWidth === w) return;
      w = innerWidth;
      clearTimeout(t);
      t = setTimeout(run, 180);
    });
    return go;
  }

  /* ---- entrances: lines, media reveals, fades. Fire once. ------------------------ */

  function initEntrances() {
    var items = document.querySelectorAll('[data-k-lines], [data-k-reveal], [data-k-fade]');
    if (!items.length) return;
    if (!('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(items, function (el) { el.classList.add('is-in'); });
      return;
    }
    // A media reveal starts fully clipped, and Chrome's IntersectionObserver
    // counts an element's own clip-path, so a clipped frame never reports as
    // intersecting and would never open. Observe its parent instead.
    var byTarget = new Map();
    function reveal(el) {
      // A heading waits for its split so the lines rise rather than pop.
      if (el.hasAttribute('data-k-lines') && !el.classList.contains('is-split')) {
        var wait = setInterval(function () {
          if (el.classList.contains('is-split')) { clearInterval(wait); requestAnimationFrame(function () { el.classList.add('is-in'); }); }
        }, 60);
        setTimeout(function () { clearInterval(wait); el.classList.add('is-in'); }, 1800);
      } else {
        el.classList.add('is-in');
      }
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        (byTarget.get(e.target) || []).forEach(reveal);
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.01 });
    Array.prototype.forEach.call(items, function (el) {
      var target = el.hasAttribute('data-k-reveal') && el.parentElement ? el.parentElement : el;
      if (!byTarget.has(target)) { byTarget.set(target, []); io.observe(target); }
      byTarget.get(target).push(el);
    });
  }

  /* ---- 3. smooth scroll ------------------------------------------------------------- */

  function initLenis() {
    if (reduce || typeof window.Lenis !== 'function') return;
    lenis = new window.Lenis({ lerp: 0.085, wheelMultiplier: 0.9, smoothWheel: true, autoRaf: true });

    // Same-page anchors glide, and land clear of the header.
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href*="#"]');
      if (!a || a.target) return;
      var url = new URL(a.href, location.href);
      if (url.pathname !== location.pathname || !url.hash || url.hash === '#') return;
      var target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
      if (!target) return;
      e.preventDefault();
      var header = document.querySelector('[data-header]');
      lenis.scrollTo(target, { offset: -((header && header.offsetHeight) || 0) - 16, duration: 1.4 });
      if (target.id === 'main') target.focus({ preventScroll: true });
    });
  }

  /* ---- header ------------------------------------------------------------------------ */

  function initHeader() {
    var header = document.querySelector('[data-header]');
    if (!header) return;
    var lastY = scrollY, ticking = false;
    function update() {
      var y = scrollY;
      header.classList.toggle('is-solid', y > 40);
      if (y > lastY + 6 && y > 320) header.classList.add('is-hidden');
      else if (y < lastY - 6 || y < 120) header.classList.remove('is-hidden');
      lastY = y;
      ticking = false;
    }
    addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    header.addEventListener('focusin', function () { header.classList.remove('is-hidden'); });
    update();
  }

  /* ---- services panel ------------------------------------------------------------------ */

  function initMega() {
    var toggle = document.querySelector('[data-mega-toggle]');
    var header = document.querySelector('[data-header]');
    if (!toggle) return;
    var panel = document.getElementById(toggle.getAttribute('aria-controls'));
    var group = toggle.closest('[data-mega]');
    if (!panel || !group) return;
    var timer = null;

    function setOpen(open) {
      toggle.setAttribute('aria-expanded', String(open));
      panel.hidden = !open;
      header.classList.toggle('is-open', open);
      if (open) header.classList.add('is-solid');
      else if (scrollY <= 40) header.classList.remove('is-solid');
    }

    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    toggle.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowDown') return;
      e.preventDefault();
      setOpen(true);
      var first = panel.querySelector('a');
      if (first) first.focus();
    });
    if (fine) {
      group.addEventListener('pointerenter', function () { clearTimeout(timer); setOpen(true); });
      group.addEventListener('pointerleave', function () {
        clearTimeout(timer);
        timer = setTimeout(function () { setOpen(false); }, 220);
      });
    }
    group.addEventListener('focusout', function (e) {
      if (!group.contains(e.relatedTarget)) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { setOpen(false); toggle.focus(); }
    });
    document.addEventListener('click', function (e) {
      if (!group.contains(e.target)) setOpen(false);
    });

    // Image preview follows the item under the pointer or focus.
    var imgs = panel.querySelectorAll('[data-mega-img]');
    each('[data-mega-item]', function (item) {
      var show = function () {
        var id = item.getAttribute('data-mega-item');
        Array.prototype.forEach.call(imgs, function (img) {
          img.classList.toggle('is-on', img.getAttribute('data-mega-img') === id);
        });
      };
      item.addEventListener('pointerenter', show);
      item.addEventListener('focus', show);
    }, panel);
  }

  /* ---- mobile menu ------------------------------------------------------------------------- */

  function initMenu() {
    var toggle = document.querySelector('[data-menu-toggle]');
    var menu = document.querySelector('[data-menu]');
    var header = document.querySelector('[data-header]');
    if (!toggle || !menu) return;
    each('.k-menu__list > li', function (li, i) { li.style.setProperty('--i', i); }, menu);

    function setOpen(open) {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.querySelector('[data-menu-label]').textContent = open ? 'Close' : 'Menu';
      menu.hidden = !open;
      menu.classList.toggle('is-open', open);
      header.classList.toggle('is-open', open);
      header.classList.toggle('is-solid', open || scrollY > 40);
      doc.style.overflow = open ? 'hidden' : '';
      if (lenis) { if (open) lenis.stop(); else lenis.start(); }
      if (open) { var first = menu.querySelector('a, summary'); if (first) first.focus({ preventScroll: true }); }
    }
    toggle.addEventListener('click', function () { setOpen(toggle.getAttribute('aria-expanded') !== 'true'); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { setOpen(false); toggle.focus(); }
    });
    matchMedia('(min-width: 1080px)').addEventListener('change', function (e) { if (e.matches) setOpen(false); });
  }

  /* ---- mobile dock ----------------------------------------------------------------------------- */

  function initDock() {
    var dock = document.querySelector('[data-dock]');
    if (!dock) return;
    var ticking = false;
    function update() {
      var max = doc.scrollHeight - innerHeight;
      var y = scrollY;
      dock.classList.toggle('is-visible', y > innerHeight * 0.9 && y < max - innerHeight * 0.6);
      ticking = false;
    }
    addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  /* ---- video loops -------------------------------------------------------------------------------
     Kroll's own project films, cut to short silent loops. The poster is the
     base layer; the clip is only fetched near the viewport, only plays while
     visible, and is never fetched at all under reduced motion or save-data. */

  function initLoops() {
    var vids = document.querySelectorAll('video[data-k-loop]');
    if (!vids.length || reduce || saveData || !('IntersectionObserver' in window)) return;

    var near = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var v = e.target;
        near.unobserve(v);
        Array.prototype.forEach.call(v.querySelectorAll('source[data-src]'), function (s) {
          s.src = s.getAttribute('data-src');
        });
        v.muted = true; v.defaultMuted = true; v.playsInline = true;
        v.load();
        v.__kReady = true;
        if (v.__kVisible) play(v);
      });
    }, { rootMargin: '400px 0px' });

    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        v.__kVisible = e.isIntersecting;
        if (!v.__kReady) return;
        if (e.isIntersecting) play(v); else v.pause();
      });
    }, { threshold: 0.05 });

    function play(v) {
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    }
    Array.prototype.forEach.call(vids, function (v) {
      v.addEventListener('playing', function () { v.classList.add('is-playing'); });
      near.observe(v); seen.observe(v);
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) return;
      Array.prototype.forEach.call(vids, function (v) { if (v.__kReady && v.__kVisible) play(v); });
    });
  }

  /* ---- film player ------------------------------------------------------------------------------------ */

  function initFilms() {
    each('[data-k-film]', function (film) {
      var cover = film.querySelector('.k-film__cover');
      var video = film.querySelector('video');
      if (!cover || !video) return;
      video.controls = false;
      cover.addEventListener('click', function () {
        film.classList.add('is-playing');
        video.controls = true;
        video.preload = 'auto';
        var p = video.play();
        if (p && p.catch) p.catch(function () {});
        video.focus({ preventScroll: true });
      });
    });
  }

  /* ---- list previews (services index) ---------------------------------------------------------------------- */

  function initPreviews() {
    each('[data-k-previews]', function (root) {
      var imgs = root.querySelectorAll('[data-k-preview-img]');
      each('[data-k-preview]', function (row) {
        var show = function () {
          var id = row.getAttribute('data-k-preview');
          Array.prototype.forEach.call(imgs, function (img) {
            img.classList.toggle('is-on', img.getAttribute('data-k-preview-img') === id);
          });
        };
        row.addEventListener('pointerenter', show);
        row.addEventListener('focus', show);
      }, root);
    });
  }

  /* ---- folio ------------------------------------------------------------------------------------------------- */

  function initFolio() {
    var folio = document.querySelector('[data-folio-ui]');
    var chapters = document.querySelectorAll('[data-folio]');
    if (!folio || chapters.length < 2 || !('IntersectionObserver' in window)) return;
    var numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'];
    var n = folio.querySelector('.k-folio__n');
    var t = folio.querySelector('.k-folio__t');
    var list = Array.prototype.slice.call(chapters);
    folio.classList.add('is-live');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var i = list.indexOf(e.target);
        n.textContent = numerals[i] || String(i + 1);
        t.textContent = e.target.getAttribute('data-folio');
      });
    }, { rootMargin: '-48% 0px -48% 0px' });
    list.forEach(function (c) { io.observe(c); });
  }

  /* ---- the build-up cutaway ------------------------------------------------------------------------------------
     Reads the pinned act's progress (the engine writes --sc-p inline on the
     section) and turns it into four joint separations. The floor peels from
     the top down, holds fully exploded, then closes back into one surface.
     Leader lines are drawn from each layer's projected corner, measured with
     getBoundingClientRect, so they stay attached however the rig is turned. */

  function initCut() {
    var el = document.querySelector('[data-k-cut]');
    if (!el) return;
    var stage = el.querySelector('.k-cut__stage');
    var rig = el.querySelector('.k-cut__rig');
    var list = el.querySelector('.k-cut__labels');
    var svg = el.querySelector('.k-cut__lines');
    var labels = Array.prototype.slice.call(el.querySelectorAll('[data-cut-label]'));
    var pins = [];
    each('.k-cut__layer', function (layer) {
      pins[parseInt(layer.getAttribute('data-layer'), 10)] = layer.querySelector('.k-cut__pin');
    }, el);
    var desk = matchMedia('(min-width: 1000px)');
    var NS = 'http://www.w3.org/2000/svg';
    var lines = labels.map(function () {
      var g = document.createElementNS(NS, 'g');
      var l = document.createElementNS(NS, 'line');
      var c = document.createElementNS(NS, 'circle');
      c.setAttribute('r', '2.5');
      g.appendChild(l); g.appendChild(c);
      svg.appendChild(g);
      return { g: g, l: l, c: c };
    });

    var colX = 0;
    function measureColumn() {
      list.classList.remove('is-placed');
      var sr = stage.getBoundingClientRect();
      colX = list.getBoundingClientRect().left - sr.left;
      if (desk.matches) list.classList.add('is-placed');
    }

    function place(sep) {
      var sr = stage.getBoundingClientRect();
      var rows = labels.map(function (lab, k) {
        var layer = parseInt(lab.getAttribute('data-cut-label'), 10);
        var r = pins[layer].getBoundingClientRect();
        return { lab: lab, k: k, x: r.left - sr.left, y: r.top - sr.top, on: lab.classList.contains('is-on') };
      });
      // Top of the stack reads first. Keep a minimum gap so labels never collide.
      var ordered = rows.slice().sort(function (a, b) { return a.y - b.y; });
      var minGap = 92, prev = -Infinity;
      ordered.forEach(function (row) {
        row.ly = Math.max(row.y, prev + minGap);
        prev = row.ly;
      });
      var overflow = prev - (sr.height - 48);
      if (overflow > 0) ordered.forEach(function (row) { row.ly -= overflow; });
      rows.forEach(function (row) {
        row.lab.style.left = colX + 'px';
        row.lab.style.top = row.ly + 'px';
        var L = lines[row.k];
        L.l.setAttribute('x1', row.x); L.l.setAttribute('y1', row.y);
        L.l.setAttribute('x2', colX - 14); L.l.setAttribute('y2', row.ly);
        L.c.setAttribute('cx', row.x); L.c.setAttribute('cy', row.y);
        L.g.style.opacity = row.on ? '1' : '0';
        L.g.style.transition = 'opacity 500ms';
      });
    }

    function seg(p, a, b) { return clamp01((p - a) / (b - a)); }
    function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

    function apply(p) {
      var back = ease(seg(p, 0.76, 0.93));
      var s4 = ease(seg(p, 0.05, 0.26)) * (1 - back);
      var s3 = ease(seg(p, 0.13, 0.34)) * (1 - back);
      var s2 = ease(seg(p, 0.21, 0.42)) * (1 - back);
      var s1 = ease(seg(p, 0.29, 0.50)) * (1 - back);
      var sep = [s1, s1, s2, s3, s4];   // by layer index: substrate shows with the board
      el.style.setProperty('--s1', s1.toFixed(4));
      el.style.setProperty('--s2', s2.toFixed(4));
      el.style.setProperty('--s3', s3.toFixed(4));
      el.style.setProperty('--s4', s4.toFixed(4));
      el.style.setProperty('--turn', (-47 + p * 11).toFixed(3) + 'deg');
      el.style.setProperty('--tilt', (59 - p * 5).toFixed(3) + 'deg');

      var current = -1;
      labels.forEach(function (lab) {
        var layer = parseInt(lab.getAttribute('data-cut-label'), 10);
        var on = sep[layer] > 0.5;
        lab.classList.toggle('is-on', on);
      });
      // On a phone only one label shows: the layer most recently exposed.
      if (p > 0.05 && p < 0.76) {
        current = p < 0.13 ? 4 : p < 0.21 ? 3 : p < 0.29 ? 2 : p < 0.40 ? 1 : 0;
      }
      labels.forEach(function (lab) {
        lab.classList.toggle('is-current', parseInt(lab.getAttribute('data-cut-label'), 10) === current);
      });
      el.classList.toggle('is-resolved', p > 0.86);
      if (desk.matches) place(sep);
    }

    if (reduce) {
      labels.forEach(function (lab) { lab.classList.add('is-on'); });
      measureColumn();
      if (desk.matches) place();
      addEventListener('resize', function () { measureColumn(); if (desk.matches) place(); });
      return;
    }

    // Start collapsed: the finished floor is the first thing seen.
    apply(0);
    measureColumn();

    var running = false, last = -1;
    function frame() {
      if (!running) return;
      var p = parseFloat(el.style.getPropertyValue('--sc-p'));
      if (isNaN(p)) p = 0;
      if (Math.abs(p - last) > 0.0004) { last = p; apply(p); }
      requestAnimationFrame(frame);
    }
    new IntersectionObserver(function (entries) {
      var on = entries[0].isIntersecting;
      if (on && !running) { running = true; last = -1; requestAnimationFrame(frame); }
      else if (!on) running = false;
    }, { rootMargin: '200px 0px' }).observe(el);

    var w = innerWidth;
    addEventListener('resize', function () {
      if (innerWidth === w) return;
      w = innerWidth;
      measureColumn();
      last = -1;
    });
  }

  /* ---- quote form ------------------------------------------------------------------------------------------------
     Progressive disclosure. Without JS all three fieldsets render and the
     form posts in one submission. */

  function initQuoteForm() {
    var form = document.querySelector('[data-quote-form]');
    if (!form) return;
    var timing = form.querySelector('[data-timing-field]');
    if (timing) timing.value = String(Date.now());

    var steps = form.querySelectorAll('[data-quote-step]');
    var tabs = form.querySelectorAll('[data-quote-steps] li');
    if (steps.length < 2) return;

    function show(i, focus) {
      Array.prototype.forEach.call(steps, function (s, n) { s.hidden = n !== i; });
      Array.prototype.forEach.call(tabs, function (t, n) {
        if (n === i) t.setAttribute('aria-current', 'step'); else t.removeAttribute('aria-current');
      });
      if (focus) {
        var f = steps[i].querySelector('input:not([type=hidden]), select, textarea');
        if (f) f.focus({ preventScroll: true });
        var top = form.getBoundingClientRect().top + scrollY - 140;
        if (lenis) lenis.scrollTo(top, { duration: 1 }); else scrollTo({ top: top, behavior: reduce ? 'auto' : 'smooth' });
      }
    }

    Array.prototype.forEach.call(steps, function (step, i) {
      var row = document.createElement('div');
      row.className = 'k-actions';
      if (i > 0) {
        var back = document.createElement('button');
        back.type = 'button';
        back.className = 'k-link';
        back.textContent = 'Back';
        back.addEventListener('click', function () { show(i - 1, true); });
        row.appendChild(back);
      }
      if (i < steps.length - 1) {
        var next = document.createElement('button');
        next.type = 'button';
        next.className = 'k-btn k-btn--solid';
        next.innerHTML = 'Continue <svg class="k-arrow" viewBox="0 0 18 11" aria-hidden="true"><path d="M0 5.5h16M11.5 1l4.5 4.5L11.5 10" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>';
        next.addEventListener('click', function () {
          var invalid = null;
          Array.prototype.forEach.call(step.querySelectorAll('[required]'), function (f) {
            if (!f.checkValidity() && !invalid) invalid = f;
          });
          if (invalid) { invalid.setAttribute('aria-invalid', 'true'); invalid.reportValidity(); return; }
          Array.prototype.forEach.call(step.querySelectorAll('[aria-invalid]'), function (f) { f.removeAttribute('aria-invalid'); });
          show(i + 1, true);
        });
        row.appendChild(next);
        step.appendChild(row);
      } else if (row.childNodes.length) {
        var submitRow = step.querySelector('[data-submit-row]');
        if (submitRow) submitRow.insertBefore(row.firstChild, submitRow.firstChild);
      }
    });
    show(0, false);

    each('.k-upload input[type="file"]', function (input) {
      input.addEventListener('change', function () {
        var title = input.closest('.k-upload').querySelector('.k-upload__title');
        var n = input.files ? input.files.length : 0;
        title.textContent = n === 0 ? 'Add files' : n === 1 ? input.files[0].name : n + ' files selected';
      });
    }, form);
  }

  /* ---- start ------------------------------------------------------------------------------------------------------- */

  function start() {
    var splitNow = initLines();
    if (splitNow && document.fonts && document.fonts.status === 'loaded') splitNow();

    if (window.ScrollCraft) engine = window.ScrollCraft.mount(document.body);
    initLenis();

    initHeader();
    initMega();
    initMenu();
    initDock();
    initEntrances();
    initLoops();
    initFilms();
    initPreviews();
    initFolio();
    initCut();
    initQuoteForm();

    // Pins are measured from document positions; anything that loads late
    // and changes height (a slow image without dimensions, a font swap) moves
    // them. Re-measure once everything has arrived.
    addEventListener('load', function () { if (engine) engine.layout(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
