/* Finite Elements from Scratch: interactive figures for the episode pages.
   Each widget is a <div data-fea="..."> with its settings as JSON in data-config. No libraries. */
(function () {
  "use strict";
  var COLORS = ["c1", "c2", "c3", "c1", "c2", "c3"];

  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (html != null) e.innerHTML = html;
    return e;
  }
  function fmt(x) {
    var r = Math.round(x * 1000) / 1000;
    return (Object.is(r, -0) ? 0 : r).toString().replace("-", "−");
  }

  // springs: [{a: node, b: node, k: N/mm}], nodes numbered from 1
  function assemble(n, springs) {
    var K = [], parts = [];
    for (var i = 0; i < n; i++) { K.push(new Array(n).fill(0)); parts.push([]); for (var j = 0; j < n; j++) parts[i].push([]); }
    springs.forEach(function (s, idx) {
      var e = [[s.a - 1, s.a - 1, s.k], [s.a - 1, s.b - 1, -s.k], [s.b - 1, s.a - 1, -s.k], [s.b - 1, s.b - 1, s.k]];
      e.forEach(function (t) { K[t[0]][t[1]] += t[2]; if (s.k) parts[t[0]][t[1]].push([idx, t[2]]); });
    });
    return { K: K, parts: parts };
  }

  // node 1 pinned (u1 = 0), force F on the last node; Gaussian elimination on the rest
  function solve(K, F) {
    var n = K.length, m = n - 1, A = [], b = [];
    for (var i = 1; i < n; i++) { A.push(K[i].slice(1)); b.push(i === n - 1 ? F : 0); }
    for (var c = 0; c < m; c++) {
      var p = c;
      for (var r = c + 1; r < m; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      if (Math.abs(A[p][c]) < 1e-12) return null;
      var t = A[c]; A[c] = A[p]; A[p] = t; t = b[c]; b[c] = b[p]; b[p] = t;
      for (r = c + 1; r < m; r++) {
        var f = A[r][c] / A[c][c];
        for (var k = c; k < m; k++) A[r][k] -= f * A[c][k];
        b[r] -= f * b[c];
      }
    }
    var x = new Array(m).fill(0);
    for (c = m - 1; c >= 0; c--) {
      var s = b[c];
      for (k = c + 1; k < m; k++) s -= A[c][k] * x[k];
      x[c] = s / A[c][c];
    }
    return [0].concat(x);
  }

  function table(K, parts, hits, showParts) {
    var n = K.length, h = '<div class="scroll"><table class="k"><tr><th></th>';
    for (var j = 0; j < n; j++) h += "<th>" + (j + 1) + "</th>";
    h += "</tr>";
    for (var i = 0; i < n; i++) {
      h += "<tr><th>" + (i + 1) + "</th>";
      for (j = 0; j < n; j++) {
        var cell = fmt(K[i][j]), p = parts[i][j], sub = "";
        if (showParts && p.length > 1)
          sub = "<small>" + p.map(function (q) { return '<span class="' + COLORS[q[0]] + '">' + fmt(q[1]) + "</span>"; }).join(" + ") + "</small>";
        var cls = hits && hits[i][j] ? ' class="hit"' : "";
        var color = p.length === 1 ? ' style="color:var(--s' + ((p[0][0] % 3) + 1) + ')"' : "";
        h += "<td" + cls + color + ">" + cell + sub + "</td>";
      }
      h += "</tr>";
    }
    return h + "</table></div>";
  }

  function chain(springs, opts) {
    opts = opts || {};
    var n = springs.length + 1, W = 640, H = 120, x0 = 60, gap = (W - 130) / springs.length, y = 60;
    var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Spring chain">';
    s += '<line x1="' + (x0 - 16) + '" y1="25" x2="' + (x0 - 16) + '" y2="95" stroke="currentColor" stroke-width="5"/>';
    springs.forEach(function (sp, i) {
      var xa = x0 + i * gap, xb = xa + gap, pts = [[xa, y], [xa + 12, y]], z = 10;
      for (var t = 0; t < z; t++) pts.push([xa + 12 + (t + 0.5) * (gap - 24) / z, y + (t % 2 ? 10 : -10)]);
      pts.push([xb - 12, y], [xb, y]);
      var cls = opts.selected === i ? "var(--s2)" : (sp.k ? "currentColor" : "var(--line)");
      s += '<g data-spring="' + i + '" style="cursor:' + (opts.click ? "pointer" : "default") + '">' +
        '<rect x="' + xa + '" y="' + (y - 30) + '" width="' + gap + '" height="60" fill="transparent"/>' +
        '<polyline points="' + pts.map(function (p) { return p.join(","); }).join(" ") + '" fill="none" stroke="' + cls +
        '" stroke-width="' + (opts.selected === i ? 3.5 : 2) + '"' + (sp.k ? "" : ' stroke-dasharray="4 4"') + "/>" +
        '<text x="' + (xa + gap / 2) + '" y="' + (y - 22) + '" text-anchor="middle" font-size="15" fill="' + cls + '">k' + (i + 1) + " = " + fmt(sp.k) + "</text></g>";
    });
    for (var i = 0; i < n; i++) {
      var xn = x0 + i * gap + (opts.u ? Math.min(opts.u[i] || 0, 40) * 1.2 : 0);
      s += '<circle cx="' + xn + '" cy="' + y + '" r="6" fill="var(--card)" stroke="currentColor" stroke-width="2"/>' +
        '<text x="' + xn + '" y="' + (y + 28) + '" text-anchor="middle" font-size="14" fill="var(--muted)">' + (i + 1) + "</text>";
    }
    var xe = x0 + (n - 1) * gap;
    s += '<line x1="' + (xe + 10) + '" y1="' + y + '" x2="' + (xe + 55) + '" y2="' + y + '" stroke="currentColor" stroke-width="2.5" marker-end="url(#ah)"/>' +
      '<text x="' + (xe + 33) + '" y="' + (y - 10) + '" text-anchor="middle" font-size="14">' + fmt(opts.F || 60) + ' N</text>' +
      '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>';
    return s + "</svg>";
  }

  function diff(A, B) {
    return A.map(function (r, i) { return r.map(function (v, j) { return Math.abs(v - B[i][j]) > 1e-9; }); });
  }
  function springsOf(c) { return c.k.map(function (k, i) { return { a: i + 1, b: i + 2, k: k }; }); }

  // 1. the guess: pick A-D, then double the chosen spring and see which cells changed
  function bet(root, c) {
    var base = springsOf(c), n = base.length + 1, picked = null;
    root.innerHTML = chain(base, { selected: c.change, F: c.F }) +
      '<div class="row choices"></div><div class="row"><button class="go" disabled>Double k' + (c.change + 1) + " and check</button></div>" +
      '<div class="out"></div><p class="msg" aria-live="polite"></p>';
    var row = root.querySelector(".choices");
    c.options.forEach(function (o) {
      var b = el("button", { type: "button", "aria-pressed": "false" }, "<b>" + o.id + "</b> " + o.text);
      b.onclick = function () {
        picked = o.id;
        row.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        root.querySelector(".go").disabled = false;
      };
      row.appendChild(b);
    });
    root.querySelector(".go").onclick = function () {
      var after = base.map(function (s, i) { return { a: s.a, b: s.b, k: i === c.change ? s.k * 2 : s.k }; });
      var A = assemble(n, base), B = assemble(n, after), hits = diff(A.K, B.K);
      var count = hits.flat().filter(Boolean).length;
      root.querySelector(".out").innerHTML = '<div class="row" style="align-items:flex-start;gap:1.5rem">' +
        "<div><b>before</b>" + table(A.K, A.parts, null, false) + "</div><div><b>after</b>" + table(B.K, B.parts, hits, false) + "</div></div>";
      var right = picked === c.answer;
      root.querySelector(".msg").innerHTML = '<span class="' + (right ? "ok" : "bad") + '">' + (right ? "Right: " : "Not quite: ") +
        "</span>" + count + " of " + n * n + " cells change. " + c.explain[picked];
    };
  }

  // 2. assembly one spring at a time
  function build(root, c) {
    var all = springsOf(c), n = all.length + 1, step = 0;
    root.innerHTML = '<div class="row"><button class="prev">Back</button><button class="next">Add spring 1</button><span class="note"></span></div><div class="fig"></div><div class="tab"></div><p class="msg"></p>';
    function draw() {
      var used = all.map(function (s, i) { return i < step ? s : { a: s.a, b: s.b, k: 0 }; });
      var A = assemble(n, used);
      root.querySelector(".fig").innerHTML = chain(all.map(function (s, i) { return i < step ? s : { a: s.a, b: s.b, k: 0 }; }), { selected: step - 1, F: c.F });
      root.querySelector(".tab").innerHTML = table(A.K, A.parts, null, true);
      root.querySelector(".prev").disabled = step === 0;
      root.querySelector(".next").disabled = step === all.length;
      root.querySelector(".next").textContent = step < all.length ? "Add spring " + (step + 1) : "All springs in";
      root.querySelector(".msg").innerHTML = step === 0 ? "An empty 4×4 table: row i is the force at node i, column j multiplies how far node j moves." :
        "Spring " + step + " joins nodes " + all[step - 1].a + " and " + all[step - 1].b + ": its 2×2 table [k, −k; −k, k] lands where rows and columns " +
        all[step - 1].a + " and " + all[step - 1].b + " cross." + (step === all.length ? " Cells with two colours collect two springs: that is assembly." : "");
    }
    root.querySelector(".next").onclick = function () { step++; draw(); };
    root.querySelector(".prev").onclick = function () { step--; draw(); };
    draw();
  }

  // 3. free play: stiffness sliders, the table and the solved displacements
  function play(root, c) {
    var k = c.k.slice(), n = k.length + 1, ref = assemble(n, springsOf(c)).K;
    var sl = k.map(function (v, i) {
      return '<label><span class="c' + (i + 1) + '">k' + (i + 1) + '</span><input type="range" min="0" max="120" step="10" value="' + v + '" data-i="' + i + '"><output>' + v + "</output></label>";
    }).join("");
    root.innerHTML = '<div class="row">' + sl + '<button class="reset">Reset</button></div><div class="fig"></div><div class="tab"></div><p class="msg"></p>';
    function draw() {
      var sp = k.map(function (v, i) { return { a: i + 1, b: i + 2, k: v }; }), A = assemble(n, sp), u = solve(A.K, c.F);
      root.querySelector(".fig").innerHTML = chain(sp, { F: c.F, u: u });
      root.querySelector(".tab").innerHTML = table(A.K, A.parts, diff(ref, A.K), true);
      root.querySelector(".msg").innerHTML = u ? "Node 1 pinned. Displacements (mm): " + u.map(function (x, i) { return "u" + (i + 1) + " = " + fmt(x); }).join(", ") +
        ". Highlighted cells differ from the episode's table." :
        '<span class="bad">No unique solution:</span> a spring with k = 0 cuts the chain, so the nodes after it are held by nothing.';
    }
    root.querySelectorAll("input").forEach(function (inp) {
      inp.oninput = function () { k[+inp.dataset.i] = +inp.value; inp.nextElementSibling.textContent = inp.value; draw(); };
    });
    root.querySelector(".reset").onclick = function () {
      k = c.k.slice();
      root.querySelectorAll("input").forEach(function (inp, i) { inp.value = k[i]; inp.nextElementSibling.textContent = k[i]; });
      draw();
    };
    draw();
  }

  // generic guess: options, then the explanation for the one picked (and an optional figure kind to draw after)
  function quiz(root, c) {
    var picked = null;
    root.innerHTML = '<div class="row choices"></div><div class="row"><button class="go" disabled>Check</button></div><div class="out"></div><p class="msg" aria-live="polite"></p>';
    var row = root.querySelector(".choices");
    c.options.forEach(function (o) {
      var b = el("button", { type: "button", "aria-pressed": "false" }, "<b>" + o.id + "</b> " + o.text);
      b.onclick = function () {
        picked = o.id;
        row.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        root.querySelector(".go").disabled = false;
      };
      row.appendChild(b);
    });
    root.querySelector(".go").onclick = function () {
      var right = picked === c.answer;
      root.querySelector(".msg").innerHTML = '<span class="' + (right ? "ok" : "bad") + '">' + (right ? "Right. " : "Not quite. The answer is " + c.answer + ". ") +
        "</span>" + c.explain[picked] + (c.after ? " " + c.after : "");
      if (c.figure && KINDS[c.figure.kind]) { var d = el("div"); root.querySelector(".out").innerHTML = ""; root.querySelector(".out").appendChild(d); KINDS[c.figure.kind](d, c.figure); }
    };
  }

  // a 1D bar: exact temperature (dashed) and the broken line through the nodes (solid), on x in [0, L] cm
  function barPlot(c, nodesT, extra) {
    var W = 640, H = 300, L = c.L, lo = c.tmin, hi = c.tmax, px = function (x) { return 60 + (W - 90) * x / L; },
      py = function (T) { return H - 40 - (H - 70) * (T - lo) / (hi - lo); }, s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Temperature along the bar">';
    for (var T = lo; T <= hi; T += 10) s += '<line x1="60" x2="' + (W - 30) + '" y1="' + py(T) + '" y2="' + py(T) + '" stroke="var(--line)"/><text x="52" y="' + (py(T) + 5) + '" text-anchor="end" font-size="13" fill="var(--muted)">' + T + "</text>";
    for (var x = 0; x <= L; x++) s += '<text x="' + px(x) + '" y="' + (H - 18) + '" text-anchor="middle" font-size="13" fill="var(--muted)">' + x + "</text>";
    s += '<text x="' + (W - 30) + '" y="' + (H - 2) + '" text-anchor="end" font-size="13" fill="var(--muted)">x (cm)</text><text x="14" y="22" font-size="13" fill="var(--muted)">T (°C)</text>';
    var ex = [];
    for (var i = 0; i <= 80; i++) { var xx = L * i / 80; ex.push(px(xx) + "," + py(c.exact(xx))); }
    s += '<polyline points="' + ex.join(" ") + '" fill="none" stroke="var(--muted)" stroke-width="2" stroke-dasharray="6 5"/>';
    var n = nodesT.length - 1, pts = nodesT.map(function (T, i) { return px(L * i / n) + "," + py(T); });
    s += '<polyline points="' + pts.join(" ") + '" fill="none" stroke="var(--accent)" stroke-width="3"/>';
    nodesT.forEach(function (T, i) { s += '<circle cx="' + px(L * i / n) + '" cy="' + py(T) + '" r="5" fill="var(--accent)"/>'; });
    return s + (extra || "") + '<text x="' + (W - 34) + '" y="40" text-anchor="end" font-size="13" fill="var(--muted)">dashed: exact · solid: broken line</text></svg>';
  }

  // E02: move T2 and watch the middle hat's scale: heat leaving node 2 by the slopes vs heat the hat collects
  function weak(root, c) {
    var kAh = c.kAh, load = c.load, Tl = c.tl, Tr = c.tr, L = 4, q = c.q;
    var exact = function (x) { return Tl + (Tr - Tl) * x / L + q * x * (L - x); };
    root.innerHTML = '<div class="row"><label>T2 <input type="range" min="20" max="70" step="1" value="' + (c.start || 30) + '"><output></output> °C</label>' +
      '<label>right end <select><option value="20">20 °C</option><option value="40">40 °C</option></select></label></div><div class="fig"></div><p class="msg" aria-live="polite"></p>';
    var inp = root.querySelector("input"), sel = root.querySelector("select");
    function draw() {
      var T2 = +inp.value; Tr = +sel.value;
      inp.nextElementSibling.textContent = T2;
      root.querySelector(".fig").innerHTML = barPlot({ L: L, tmin: 20, tmax: 70, exact: exact }, [Tl, T2, Tr]);
      var out = kAh * (T2 - Tl) + kAh * (T2 - Tr), bal = Math.abs(out - load) < 1e-9;
      root.querySelector(".msg").innerHTML = "Middle hat N2: heat flowing away from node 2 by the slopes = " + kAh + " × (" + T2 + " − " + Tl + ") + " + kAh + " × (" + T2 + " − " + Tr + ") = <b>" + fmt(out) +
        " W</b>; heat the hat collects from the bar = <b>" + load + " W</b>. " + (bal ? '<span class="ok">Balanced: this is the T2 the weak form picks. The exact curve passes through the same point, ' + fmt(exact(2)) + " °C.</span>" :
        (out < load ? "Too little leaves: raise T2." : "Too much leaves: lower T2."));
    }
    inp.oninput = draw; sel.onchange = draw; draw();
  }

  // E03: cut the 4 cm bar into n elements; hat loads, Dirichlet ends, solve; compare with the exact curve
  function refine(root, c) {
    var L = 4, kA = 2, Tl = 20, Tr = 20;                     // kA in W·cm/K, q in W/cm
    var Q = { uniform: function (x) { return 20; }, middle: function (x) { return x >= 1 && x <= 3 ? 40 : 0; } };
    var EX = { uniform: function (x) { return 20 + 5 * x * (L - x); },
      middle: function (x) { return x < 1 ? 20 + 20 * x : x > 3 ? 20 + 20 * (L - x) : 50 - 10 * (x - 2) * (x - 2); } };
    function fem(n, src) {
      var h = L / n, k = kA / h, f = new Array(n + 1).fill(0), m = 400;
      for (var e = 0; e < n; e++) for (var s = 0; s < m; s++) {           // midpoint rule for the hat loads
        var x = e * h + (s + 0.5) * h / m, w = h / m * Q[src](x), u = (x - e * h) / h;
        f[e] += w * (1 - u); f[e + 1] += w * u;
      }
      var N = n - 1, a = [], b = [], cc = [], d = [];                    // interior nodes 1..n-1, tridiagonal
      for (var i = 1; i < n; i++) { a.push(-k); b.push(2 * k); cc.push(-k); d.push(f[i] + (i === 1 ? k * Tl : 0) + (i === n - 1 ? k * Tr : 0)); }
      for (i = 1; i < N; i++) { var w2 = a[i] / b[i - 1]; b[i] -= w2 * cc[i - 1]; d[i] -= w2 * d[i - 1]; }
      var T = new Array(N); T[N - 1] = d[N - 1] / b[N - 1];
      for (i = N - 2; i >= 0; i--) T[i] = (d[i] - cc[i] * T[i + 1]) / b[i];
      return [Tl].concat(T, [Tr]);
    }
    function errs(n, src) {
      var T = fem(n, src), h = L / n, en = 0, em = 0;
      T.forEach(function (v, i) { en = Math.max(en, Math.abs(v - EX[src](i * h))); });
      for (var e = 0; e < n; e++) em = Math.max(em, Math.abs((T[e] + T[e + 1]) / 2 - EX[src]((e + 0.5) * h)));
      return [T, en, em];
    }
    root.innerHTML = '<div class="row"><span>elements:</span>' + [2, 4, 8, 16].map(function (n) { return '<button type="button" data-n="' + n + '">' + n + "</button>"; }).join("") +
      '<label>heat <select><option value="uniform">whole bar</option><option value="middle">middle half only</option></select></label></div><div class="fig"></div><div class="tab"></div><p class="msg" aria-live="polite"></p>';
    var n = c.start || 4, sel = root.querySelector("select");
    function draw() {
      var src = sel.value, r = errs(n, src);
      root.querySelectorAll("button[data-n]").forEach(function (b) { b.setAttribute("aria-pressed", +b.dataset.n === n ? "true" : "false"); });
      root.querySelector(".fig").innerHTML = barPlot({ L: L, tmin: 20, tmax: 60, exact: EX[src] }, r[0]);
      var rows = [2, 4, 8, 16].map(function (m, j, all) {
        var e = errs(m, src), prev = j ? errs(all[j - 1], src)[2] : null;
        return "<tr" + (m === n ? ' style="font-weight:700"' : "") + "><td>" + m + "</td><td>" + fmt(L / m) + "</td><td>" + fmt(e[1]) + "</td><td>" + fmt(e[2]) + "</td><td>" + (prev ? fmt(e[2] / prev) : "–") + "</td></tr>";
      }).join("");
      root.querySelector(".tab").innerHTML = '<div class="scroll"><table class="k"><tr><th>n</th><th>h (cm)</th><th>largest error at nodes (K)</th><th>at element middles (K)</th><th>ratio</th></tr>' + rows + "</table></div>";
      root.querySelector(".msg").innerHTML = "Node temperatures: " + r[0].map(function (v) { return fmt(Math.round(v * 1000) / 1000); }).join(", ") + " °C.";
    }
    root.querySelectorAll("button[data-n]").forEach(function (b) { b.onclick = function () { n = +b.dataset.n; draw(); }; });
    sel.onchange = draw; draw();
  }

  // E04: the same node values joined by straight pieces, or by one high-degree curve (equal or Chebyshev spacing)
  function runge(root, c) {
    var L = 4;
    function exact(w) {
      var a = 2 - w / 2, b = 2 + w / 2;
      return function (x) {
        if (x > 2) x = L - x;
        return x <= a ? 20 + 20 * x : 20 + 20 * a + 20 * (x - a) - (20 / w) * (x - a) * (x - a);
      };
    }
    function nodes(n, cheb) {
      var xs = [];
      for (var i = 0; i < n; i++) xs.push(cheb ? 2 - 2 * Math.cos(Math.PI * i / (n - 1)) : L * i / (n - 1));
      return xs;
    }
    function lagrange(xs, ys, x) {
      var s = 0;
      for (var i = 0; i < xs.length; i++) {
        var p = ys[i];
        for (var j = 0; j < xs.length; j++) if (j !== i) p *= (x - xs[j]) / (xs[i] - xs[j]);
        s += p;
      }
      return s;
    }
    function linear(xs, ys, x) {
      for (var i = 0; i < xs.length - 1; i++) if (x <= xs[i + 1]) return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]);
      return ys[ys.length - 1];
    }
    root.innerHTML = '<div class="row"><label>nodes <input type="range" min="3" max="17" step="2" value="' + (c.start || 11) + '"><output></output></label>' +
      '<label>spacing <select class="sp"><option value="eq">equal</option><option value="ch">Chebyshev (crowded at the ends)</option></select></label>' +
      '<label>heater <select class="hw"><option value="0.4">0.4 cm</option><option value="1.6">1.6 cm</option><option value="4">whole bar</option></select></label></div>' +
      '<div class="fig"></div><p class="msg" aria-live="polite"></p>';
    var inp = root.querySelector("input"), sp = root.querySelector(".sp"), hw = root.querySelector(".hw");
    function draw() {
      var n = +inp.value, ex = exact(+hw.value), xs = nodes(n, sp.value === "ch"), ys = xs.map(ex);
      inp.nextElementSibling.textContent = n;
      var W = 640, H = 320, lo = 0, hi = 80, px = function (x) { return 60 + (W - 90) * x / L; },
        py = function (T) { return H - 40 - (H - 70) * (Math.max(lo - 20, Math.min(hi + 20, T)) - lo) / (hi - lo); };
      var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Exact temperature, straight pieces and one curve"><defs><clipPath id="rc"><rect x="60" y="30" width="' + (W - 90) + '" height="' + (H - 70) + '"/></clipPath></defs>';
      for (var T = lo; T <= hi; T += 20) s += '<line x1="60" x2="' + (W - 30) + '" y1="' + py(T) + '" y2="' + py(T) + '" stroke="var(--line)"/><text x="52" y="' + (py(T) + 5) + '" text-anchor="end" font-size="13" fill="var(--muted)">' + T + "</text>";
      for (var x = 0; x <= L; x++) s += '<text x="' + px(x) + '" y="' + (H - 18) + '" text-anchor="middle" font-size="13" fill="var(--muted)">' + x + "</text>";
      var pe = [], pl = [], pc = [], el = 0, ec = 0, at = 0;
      for (var k = 0; k <= 2000; k++) {
        var xx = L * k / 2000, te = ex(xx), tl = linear(xs, ys, xx), tc = lagrange(xs, ys, xx);
        el = Math.max(el, Math.abs(tl - te));
        if (Math.abs(tc - te) > ec) { ec = Math.abs(tc - te); at = xx; }
        if (k % 4 === 0) { pe.push(px(xx) + "," + py(te)); pl.push(px(xx) + "," + py(tl)); pc.push(px(xx) + "," + py(tc)); }
      }
      s += '<g clip-path="url(#rc)"><polyline points="' + pe.join(" ") + '" fill="none" stroke="var(--muted)" stroke-width="2" stroke-dasharray="6 5"/>' +
        '<polyline points="' + pl.join(" ") + '" fill="none" stroke="var(--accent)" stroke-width="2.5"/>' +
        '<polyline points="' + pc.join(" ") + '" fill="none" stroke="var(--s2)" stroke-width="2.5"/></g>';
      xs.forEach(function (xn, i) { s += '<circle cx="' + px(xn) + '" cy="' + py(ys[i]) + '" r="4" fill="var(--fg)"/>'; });
      s += '<text x="' + (W - 34) + '" y="24" text-anchor="end" font-size="13"><tspan fill="var(--muted)">dashed: exact · </tspan><tspan fill="var(--accent)">straight pieces · </tspan><tspan fill="var(--s2)">one degree-' + (n - 1) + " curve</tspan></text></svg>";
      root.querySelector(".fig").innerHTML = s;
      root.querySelector(".msg").innerHTML = "Largest error: straight pieces <b>" + fmt(Math.round(el * 1000) / 1000) + " K</b>; one degree-" + (n - 1) + ' curve <b class="c2">' +
        fmt(Math.round(ec * 1000) / 1000) + " K</b>" + (ec > 0.01 ? " (at x = " + fmt(Math.round(at * 100) / 100) + " cm)" : "") + ". Both use the same " + n + " node values.";
    }
    inp.oninput = draw; sp.onchange = draw; hw.onchange = draw; draw();
  }

  var KINDS = { bet: bet, build: build, play: play, quiz: quiz, weak: weak, refine: refine, runge: runge };
  document.querySelectorAll("[data-fea]").forEach(function (root) {
    try { KINDS[root.dataset.fea](root, JSON.parse(root.dataset.config)); root.classList.add("widget"); }
    catch (e) { root.innerHTML = '<p class="note">This figure needs JavaScript.</p>'; }
  });
})();
