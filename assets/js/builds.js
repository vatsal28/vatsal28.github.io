/* Builds pages: copy-to-clipboard for prompts, table-of-contents highlight, taskbar clock.
   No dependencies. Works without JS too: prompts stay selectable text. */
(function () {
  'use strict';

  var status = document.getElementById('copy-status');
  var timers = new WeakMap();

  function announce(msg) {
    if (!status) return;
    status.textContent = '';
    window.setTimeout(function () { status.textContent = msg; }, 40);
  }

  function setState(btn, state) {
    var label = btn.querySelector('.copy-label');
    clearTimeout(timers.get(btn));
    if (state === 'copied') {
      btn.setAttribute('data-state', 'copied');
      label.textContent = 'Copied';
    } else if (state === 'manual') {
      btn.setAttribute('data-state', 'manual');
      label.textContent = 'Selected';
    } else {
      btn.removeAttribute('data-state');
      label.textContent = 'Copy';
      return;
    }
    timers.set(btn, window.setTimeout(function () { setState(btn, 'idle'); }, state === 'copied' ? 2000 : 4000));
  }

  // Fallback for browsers without the async Clipboard API (old iOS Safari, http:// pages, some webviews).
  function legacyCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('aria-hidden', 'true');
    ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;padding:0;border:0;opacity:0;font-size:16px;';
    ta.contentEditable = 'true'; // iOS only selects editable content
    ta.readOnly = false;
    document.body.appendChild(ta);
    var sel = window.getSelection();
    var saved = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
    var ok = false;
    try {
      ta.focus({ preventScroll: true });
      ta.select();
      ta.setSelectionRange(0, text.length);
      ok = document.execCommand('copy');
    } catch (e) {
      ok = false;
    }
    document.body.removeChild(ta);
    if (saved && sel) { sel.removeAllRanges(); sel.addRange(saved); }
    return ok;
  }

  function selectNode(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  function copyPrompt(btn) {
    var target = document.getElementById(btn.getAttribute('data-copy'));
    if (!target) return;
    var text = target.textContent;
    function done() { setState(btn, 'copied'); announce('Prompt copied to clipboard'); }
    function fallback() {
      if (legacyCopy(text)) { done(); return; }
      selectNode(target);
      setState(btn, 'manual');
      announce('Could not copy automatically. The prompt is selected: use your device\'s Copy.');
    }
    if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('button[data-copy]') : null;
    if (btn) copyPrompt(btn);
  });

  // Highlight the current section in the desktop table of contents.
  var side = document.querySelector('.toc-side');
  if (side && 'IntersectionObserver' in window) {
    var links = {};
    side.querySelectorAll('a[href^="#"]').forEach(function (a) { links[decodeURIComponent(a.hash.slice(1))] = a; });
    var heads = Array.prototype.filter.call(document.querySelectorAll('.prose h2[id], .prose h3[id]'), function (h) { return links[h.id]; });
    var current = null;
    var visible = new Set();
    function mark(id) {
      if (current === id) return;
      if (current && links[current]) links[current].removeAttribute('aria-current');
      current = id;
      if (id && links[id]) links[id].setAttribute('aria-current', 'true');
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) visible.add(en.target); else visible.delete(en.target); });
      var top = null;
      heads.forEach(function (h) { if (visible.has(h) && !top) top = h; });
      if (top) { mark(top.id); return; }
      // nothing visible: keep the last heading above the viewport
      var above = null;
      heads.forEach(function (h) { if (h.getBoundingClientRect().top < 120) above = h; });
      mark(above ? above.id : null);
    }, { rootMargin: '-72px 0px -55% 0px' });
    heads.forEach(function (h) { io.observe(h); });
  }

  // Close the mobile table of contents after picking a section.
  document.querySelectorAll('.toc-mobile a').forEach(function (a) {
    a.addEventListener('click', function () {
      var d = a.closest('details');
      if (d) d.open = false;
    });
  });

  var clock = document.getElementById('clock');
  if (clock) {
    var tick = function () {
      var now = new Date();
      clock.textContent = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
    };
    tick();
    window.setInterval(tick, 30000);
  }
})();
