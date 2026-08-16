/* The site's behaviour, all of it. No framework, no build step, no dependency.
 *
 * Six jobs:
 *   1. Wrap markdown tables in a scroll container, so a wide one cannot make the page scroll
 *      sideways. Done here rather than in the markdown because kramdown emits a bare <table>.
 *   2. Give every h2/h3 a copyable anchor.
 *   3. Drive the sidebar drawer below 900px, and replay the mascot when it is clicked.
 *   4. Build the "on this page" rail from the headings actually rendered.
 *   5. Highlight the section you are reading, in the sidebar and that rail.
 *   6. The ⌘K search palette.
 *
 * Everything degrades: with scripting off the page is a plain document with a plain sidebar, which
 * is the whole reason the sidebar is server-rendered Liquid and not built here. */
(function () {
  'use strict';

  var body = document.body;

  /* ---- 1. tables ------------------------------------------------------------------------------ */

  document.querySelectorAll('main table').forEach(function (t) {
    if (t.parentElement.classList.contains('tablewrap')) return;
    var box = document.createElement('div');
    box.className = 'tablewrap';
    t.parentNode.insertBefore(box, t);
    box.appendChild(t);
  });

  /* ---- 2. heading anchors --------------------------------------------------------------------- */

  document.querySelectorAll('main h2[id], main h3[id]').forEach(function (h) {
    var a = document.createElement('a');
    a.className = 'anchor';
    a.href = '#' + h.id;
    a.textContent = '#';
    a.setAttribute('aria-label', 'Link to this section');
    h.appendChild(a);
  });

  /* ---- 3. the drawer -------------------------------------------------------------------------- */

  var side = document.querySelector('.side');
  var burger = document.querySelector('[data-drawer]');
  var scrim = document.querySelector('.scrim');

  // Every page has a drawer now — on one with no sidebar it holds the site's own links, which below
  // 900px are the only copy. That was the bug: the link row was hidden on every page and the
  // hamburger appeared on none of them, so the landing page had no navigation on a phone at all.
  if (burger && !side) burger.hidden = true;   // belt and braces; both layouts ship a drawer
  if (scrim) scrim.hidden = false;

  // Where focus was before a panel took it, so Esc can put it back.
  var cameFrom = null;

  function trap(panel) {
    // Tab must not walk out of an open drawer or dialog into the page behind it.
    return function (e) {
      if (e.key !== 'Tab') return;
      var able = panel.querySelectorAll(
        'a[href], button:not([disabled]), input, [tabindex]:not([tabindex="-1"])'
      );
      if (!able.length) return;
      var first = able[0], last = able[able.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
  }

  var drawerTrap = side ? trap(side) : null;

  function openDrawer() {
    if (!side) return;
    cameFrom = document.activeElement;
    body.classList.add('drawer-open');
    if (burger) burger.setAttribute('aria-expanded', 'true');
    document.addEventListener('keydown', drawerTrap);
    var first = side.querySelector('a[href]');
    if (first) first.focus();
  }

  function closeDrawer() {
    if (!body.classList.contains('drawer-open')) return;
    body.classList.remove('drawer-open');
    if (burger) burger.setAttribute('aria-expanded', 'false');
    document.removeEventListener('keydown', drawerTrap);
    if (cameFrom && cameFrom.focus) cameFrom.focus();
  }

  // Toggle, not open. The hamburger stays visible while the drawer is out — it sits under the bar
  // now — so a second tap on it has to be the way back.
  if (burger) burger.addEventListener('click', function () {
    if (body.classList.contains('drawer-open')) closeDrawer();
    else openDrawer();
  });

  // Following a link inside the drawer must close it, or the reader lands on the section with the
  // drawer still over it.
  if (side) side.addEventListener('click', function (e) {
    if (e.target.closest('a[href]')) closeDrawer();
  });

  /* ---- 3b. the mascot, on request -------------------------------------------------------------
   *
   * The hero's mark plays once and then rests, which is the point — but a visitor who arrived mid-
   * animation, or who simply liked it, should be able to see it again. A GIF has no play() method, so
   * the replay is a refetch of the same bytes: clearing `src` and setting it back restarts the
   * animation from frame one, and the browser serves it from cache.
   *
   * Not wired up for a reader who asked for less motion: for them the <picture> resolved to a still
   * frame, and turning a still into an animation on a click is exactly what they asked not to happen. */

  var calm = matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-replay]').forEach(function (img) {
    if (calm.matches) return;
    img.addEventListener('click', function () {
      var src = img.src;
      img.src = '';
      img.src = src;
    });
  });

  /* ---- 4. on this page ------------------------------------------------------------------------
   *
   * Built from the headings that were actually rendered, rather than from a second server-side copy
   * of the same list. The sidebar's list has to be server-rendered — it names headings on pages the
   * browser has not loaded — but this one is about the page in front of you, so the DOM is the
   * better source and there is nothing to keep in step. */

  var toc = document.querySelector('[data-toc]');
  if (toc) {
    var own = document.querySelectorAll('.doc-body h2[id]');
    if (own.length > 1) {                   // one heading is not a table of contents
      var list = toc.querySelector('ul');
      own.forEach(function (h) {
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = '#' + h.id;
        // The heading text without the anchor link this script adds elsewhere.
        a.textContent = h.textContent.replace(/#$/, '').trim();
        li.appendChild(a);
        list.appendChild(li);
      });
      toc.hidden = false;
    }
  }

  /* ---- 5. what you are reading ---------------------------------------------------------------- */

  // Marked from the BOTTOM-most heading that has passed the top of the viewport, rather than from
  // whatever the observer fired about last. Scrolling fast fires several at once and the last one
  // is not reliably the lowest.
  var marks = [].slice.call(document.querySelectorAll('main h2[id], main h3[id]'));
  var rails = [].slice.call(document.querySelectorAll('.toc a[href^="#"], .side .steps a[href*="#"]'));

  if (marks.length && rails.length) {
    var byHash = {};
    rails.forEach(function (a) {
      var hash = a.getAttribute('href').split('#')[1];
      if (!hash) return;
      (byHash[hash] = byHash[hash] || []).push(a);
    });

    var tick = null;
    function spy() {
      tick = null;
      var line = (document.querySelector('.bar') || {}).offsetHeight || 52;
      var here = null;
      for (var i = 0; i < marks.length; i++) {
        if (marks[i].getBoundingClientRect().top <= line + 24) here = marks[i].id;
        else break;
      }
      rails.forEach(function (a) { a.classList.remove('here'); });
      if (here && byHash[here]) byHash[here].forEach(function (a) { a.classList.add('here'); });
    }
    addEventListener('scroll', function () {
      if (tick === null) tick = requestAnimationFrame(spy);
    }, { passive: true });
    spy();
  }

  /* ---- 6. search ------------------------------------------------------------------------------ */

  var panel = document.querySelector('.find-panel');
  var input = document.querySelector('[data-find-input]');
  var results = document.querySelector('[data-find-results]');
  var buttons = document.querySelectorAll('[data-find]');

  // Fetched on the first open, not on every page view: the index is tens of kilobytes and most
  // visits never search.
  var index = null;
  var loading = false;
  var base = (document.querySelector('link[rel=stylesheet]').getAttribute('href') || '')
    .replace(/\/assets\/site\.css.*$/, '');

  function load() {
    if (index || loading) return Promise.resolve();
    loading = true;
    return fetch(base + '/assets/search.json')
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (j) { index = Array.isArray(j) ? j : (j.items || []); })
      // No index yet, or offline. The palette says so rather than looking broken.
      .catch(function () { index = []; })
      .then(function () { loading = false; });
  }

  var panelTrap = panel ? trap(panel) : null;

  function openFind() {
    if (!panel) return;
    cameFrom = document.activeElement;
    panel.hidden = false;
    body.classList.add('find-open');
    document.addEventListener('keydown', panelTrap);
    input.value = '';
    results.innerHTML = '';
    input.focus();
    load().then(function () { if (body.classList.contains('find-open')) run(''); });
  }

  function closeFind() {
    if (!body.classList.contains('find-open')) return;
    body.classList.remove('find-open');
    document.removeEventListener('keydown', panelTrap);
    // Kept out of the tab order once shut, but not display:none'd until the fade is done.
    setTimeout(function () {
      if (!body.classList.contains('find-open')) panel.hidden = true;
    }, 200);
    if (cameFrom && cameFrom.focus) cameFrom.focus();
  }

  // Prefix beats substring, and a shorter name beats a longer one — so `to_str` puts `to_string`
  // above `option_to_string`, which is the whole reason anyone types four characters.
  function rank(item, q) {
    var name = (item.name || '').toLowerCase();
    if (!q) return 40;
    var at = name.indexOf(q);
    if (at === 0) return 100 - Math.min(name.length, 40);
    if (at > 0) return 60 - Math.min(name.length, 40);
    var where = (item.where || '').toLowerCase();
    var text = (item.text || '').toLowerCase();
    if (where.indexOf(q) >= 0 || text.indexOf(q) >= 0) return 20;
    return -1;
  }

  function run(raw) {
    var q = raw.trim().toLowerCase();
    if (!index || !index.length) {
      results.innerHTML = '<p class="find-empty">The search index has not been built yet. ' +
        'The <a href="' + base + '/reference/">reference</a> lists everything the language has.</p>';
      return;
    }
    var hits = index
      .map(function (i) { return { i: i, r: rank(i, q) }; })
      .filter(function (h) { return h.r >= 0; })
      .sort(function (a, b) { return b.r - a.r; })
      .slice(0, 40);

    if (!hits.length) {
      results.innerHTML = '<p class="find-empty">Nothing matches <strong>' +
        raw.replace(/[<&]/g, function (c) { return c === '<' ? '&lt;' : '&amp;'; }) +
        '</strong>.</p>';
      return;
    }

    results.innerHTML = hits.map(function (h) {
      var i = h.i;
      return '<a href="' + base + i.url + '">' +
        (i.kind ? '<span class="kind">' + i.kind + '</span>' : '') +
        '<span class="name">' + i.name + '</span>' +
        (i.where ? '<span class="where">' + i.where + '</span>' : '') +
        '</a>';
    }).join('');
    var first = results.querySelector('a');
    if (first) first.classList.add('on');
  }

  if (input) input.addEventListener('input', function () { run(input.value); });

  buttons.forEach(function (b) { b.addEventListener('click', openFind); });

  if (results) results.addEventListener('mousemove', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    results.querySelectorAll('a.on').forEach(function (x) { x.classList.remove('on'); });
    a.classList.add('on');
  });

  if (input) input.addEventListener('keydown', function (e) {
    var all = [].slice.call(results.querySelectorAll('a'));
    if (!all.length) return;
    var at = all.findIndex(function (a) { return a.classList.contains('on'); });
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      var next = e.key === 'ArrowDown'
        ? Math.min(at + 1, all.length - 1)
        : Math.max(at - 1, 0);
      all.forEach(function (a) { a.classList.remove('on'); });
      all[next].classList.add('on');
      all[next].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter' && at >= 0) {
      e.preventDefault();
      all[at].click();
    }
  });

  if (scrim) scrim.addEventListener('click', function () { closeDrawer(); closeFind(); });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); closeFind(); return; }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openFind(); return; }
    // A bare `/`, the way every documentation site does it — but not while someone is typing.
    if (e.key === '/' && !e.metaKey && !e.ctrlKey && !e.altKey) {
      var t = e.target;
      var typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
      if (!typing) { e.preventDefault(); openFind(); }
    }
  });

  // A drawer left open across the 900px boundary would be a panel floating over a page that has
  // room for it inline.
  var wide = matchMedia('(min-width: 901px)');
  var onWide = function (m) { if (m.matches) closeDrawer(); };
  if (wide.addEventListener) wide.addEventListener('change', onWide);
  else if (wide.addListener) wide.addListener(onWide);
})();
