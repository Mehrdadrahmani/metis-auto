/* RTL/LTR add-on for the TakRouter pages (served by Node.js). Loaded after the page's own scripts.
   1. Remembers the language in a cookie (tr_lang) so the Node server sends the right lang/dir on the next page.
   2. Inside right-to-left paragraphs, wraps left-to-right runs (prices, model names, "model = x") in
      <bdi dir="ltr">, so "$0.0007" is never shown as "0.0007$". Works on text the page adds later (new answers). */
(function () {
  "use strict";
  function remember(lang) {
    if (lang === "fa" || lang === "en") document.cookie = "tr_lang=" + lang + "; path=/; max-age=31536000; samesite=lax";
  }
  if (window.TR) {
    remember(window.TR.lang);
    if (typeof window.TR.onLang === "function") window.TR.onLang(remember);
  }

  var RTL_CHAR = /[֐-ࣿיִ-﷿ﹰ-﻿]/;
  var STRONG = /[A-Za-zÀ-ɏ֐-ࣿיִ-﷿ﹰ-﻿]/;
  var TOKEN = "[$€£]?[A-Za-z0-9](?:[A-Za-z0-9$€£%.,:/\\\\@#&+=_\\-]*[A-Za-z0-9%])?";
  var LTR_RUN = new RegExp("(" + TOKEN + "(?:\\s+(?:[=+*/-]\\s+)?" + TOKEN + ")*)", "g");
  var SCOPES = ".bubble, .answer, .col .b, .q, .opt, .raw, .save .sub";
  var BLOCKS = "p, li, h1, h2, h3, h4, blockquote, td, th, .bubble, .q, .opt, .raw, .save .sub";
  var SKIP = "pre, code, bdi, script, style, textarea, input, svg, [data-typing]";  // a typing answer is handled when it is drawn in full

  function isolateBlock(block) {
    var first = (block.textContent || "").match(STRONG);
    if (!first || !RTL_CHAR.test(first[0])) return;            // only right-to-left paragraphs need it
    var walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        return n.parentElement && n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var text = node.nodeValue;
      LTR_RUN.lastIndex = 0;
      if (!LTR_RUN.test(text)) return;
      var parts = text.split(LTR_RUN);
      var frag = document.createDocumentFragment();
      parts.forEach(function (s, i) {
        if (!s) return;
        if (i % 2) { var b = document.createElement("bdi"); b.dir = "ltr"; b.textContent = s; frag.appendChild(b); }
        else frag.appendChild(document.createTextNode(s));
      });
      node.parentNode.replaceChild(frag, node);
    });
  }

  function scan(root) {
    if (!(root instanceof Element)) return;
    var scopes = root.matches(SCOPES) ? [root] : [];
    root.querySelectorAll(SCOPES).forEach(function (e) { scopes.push(e); });
    var inside = root.closest && root.closest(SCOPES);
    if (inside && scopes.indexOf(inside) < 0) scopes.push(inside);
    scopes.forEach(function (scope) {
      var blocks = scope.matches(BLOCKS) ? [scope] : [];
      scope.querySelectorAll(BLOCKS).forEach(function (b) { blocks.push(b); });
      if (!blocks.length) blocks.push(scope);
      blocks.forEach(isolateBlock);
    });
  }

  // Text boxes: direction from the first letter typed (Persian -> rtl, English -> ltr); empty -> the page's
  // direction, so the placeholder and the cursor start on the right side. Boxes marked .ltr (keys, code) stay ltr.
  var FIELDS = 'textarea, input:not([type]), input[type="text"], input[type="search"], input[type="email"]';
  function fieldDir(f) {
    if (!f || !f.matches || !f.matches(FIELDS) || f.classList.contains("ltr")) return;
    var first = (f.value || "").match(STRONG);
    var d = first ? (RTL_CHAR.test(first[0]) ? "rtl" : "ltr") : (document.documentElement.dir || "rtl");
    if (f.getAttribute("dir") !== d) f.setAttribute("dir", d);
  }
  function allFields(root) { (root.querySelectorAll ? root.querySelectorAll(FIELDS) : []).forEach(fieldDir); }
  document.addEventListener("input", function (e) { fieldDir(e.target); }, true);
  document.addEventListener("focusin", function (e) { fieldDir(e.target); }, true);  // text set by a script (edit, ?q=)
  allFields(document);
  if (window.TR && typeof window.TR.onLang === "function") window.TR.onLang(function () { setTimeout(function () { allFields(document); }, 0); });
  window.TRfields = allFields;

  window.TRbidi = scan;  // for text drawn bit by bit (live typing): isolate the runs once, on the full text
  var busy = false;
  function run(nodes) {
    if (busy) return;
    busy = true;
    try { nodes.forEach(scan); }
    finally { busy = false; }
  }
  run([document.body]);
  new MutationObserver(function (records) {
    var added = [];
    records.forEach(function (r) {
      if (r.type === "characterData") { if (r.target.parentElement) added.push(r.target.parentElement); return; }
      r.addedNodes.forEach(function (n) { added.push(n.nodeType === 3 ? n.parentElement : n); if (n.nodeType === 1) { fieldDir(n); allFields(n); } });
    });
    // Our own edits trigger the observer again; isolated runs are skipped (they sit inside <bdi>).
    run(added.filter(Boolean));
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
})();
