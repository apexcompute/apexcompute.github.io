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

  // a small dense solve (Gaussian elimination with pivoting); returns null when singular
  function gauss(A, b) {
    var m = b.length; A = A.map(function (r) { return r.slice(); }); b = b.slice();
    for (var c = 0; c < m; c++) {
      var p = c;
      for (var r = c + 1; r < m; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      if (Math.abs(A[p][c]) < 1e-12) return null;
      var t = A[c]; A[c] = A[p]; A[p] = t; t = b[c]; b[c] = b[p]; b[p] = t;
      for (r = c + 1; r < m; r++) { var f = A[r][c] / A[c][c]; for (var k = c; k < m; k++) A[r][k] -= f * A[c][k]; b[r] -= f * b[c]; }
    }
    var x = new Array(m).fill(0);
    for (c = m - 1; c >= 0; c--) { var s = b[c]; for (k = c + 1; k < m; k++) s -= A[c][k] * x[k]; x[c] = s / A[c][c]; }
    return x;
  }
  function r3(x) { return fmt(Math.round(x * 1000) / 1000); }
  function plainTable(M, hits, rowNames, colNames) {
    var h = '<div class="scroll"><table class="k"><tr><th></th>' + colNames.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr>";
    M.forEach(function (row, i) {
      h += "<tr><th>" + rowNames[i] + "</th>" + row.map(function (v, j) {
        return '<td style="min-width:2.8rem"' + (hits && hits[i][j] ? ' class="hit"' : "") + ">" + (v === null ? '<span style="color:var(--muted)">·</span>' : r3(v)) + "</td>";
      }).join("") + "</tr>";
    });
    return h + "</table></div>";
  }

  // E05: one slanted quadrilateral (k t = 1 W/K), its 4x4 small table by 1 point, 2x2 or 3x3 Gauss points on the unit square
  function quad(root, c) {
    var P = c.corners || [[0, 0], [4, 0], [5, 4], [0, 2]];
    var RULES = {
      one: { name: "1 point (center)", pts: [[0.5, 1]] },
      off: { name: "1 point at (0.25, 0.25)", pts: [[0.25, 1]], at: 0.25 },
      two: { name: "2 × 2", pts: [[0.5 - 0.5 / Math.sqrt(3), 0.5], [0.5 + 0.5 / Math.sqrt(3), 0.5]] },
      three: { name: "3 × 3", pts: [[0.5 - 0.5 * Math.sqrt(0.6), 5 / 18], [0.5, 8 / 18], [0.5 + 0.5 * Math.sqrt(0.6), 5 / 18]] } };
    var PAT = { checker: [1, -1, 1, -1], ramp: [0, 4, 5, 0] };
    function rule(key) {                                     // [xi, eta, weight]
      var r = RULES[key], out = [];
      if (r.at != null) return [[r.at, r.at, 1]];
      r.pts.forEach(function (a) { r.pts.forEach(function (b) { out.push([a[0], b[0], a[1] * b[1]]); }); });
      return out;
    }
    function small(key) {
      var K = [0, 1, 2, 3].map(function () { return [0, 0, 0, 0]; }), area = 0;
      rule(key).forEach(function (g) {
        var xi = g[0], et = g[1], w = g[2];
        var dxi = [-(1 - et), 1 - et, et, -et], det_ = [-(1 - xi), -xi, xi, 1 - xi];
        var J = [[0, 0], [0, 0]];
        for (var a = 0; a < 4; a++) { J[0][0] += dxi[a] * P[a][0]; J[0][1] += dxi[a] * P[a][1]; J[1][0] += det_[a] * P[a][0]; J[1][1] += det_[a] * P[a][1]; }
        var d = J[0][0] * J[1][1] - J[0][1] * J[1][0], bx = [], by = [];
        for (a = 0; a < 4; a++) { bx.push((J[1][1] * dxi[a] - J[0][1] * det_[a]) / d); by.push((-J[1][0] * dxi[a] + J[0][0] * det_[a]) / d); }
        for (a = 0; a < 4; a++) for (var b = 0; b < 4; b++) K[a][b] += (bx[a] * bx[b] + by[a] * by[b]) * d * w;
        area += d * w;
      });
      return { K: K, area: area };
    }
    function map(xi, et) {
      var N = [(1 - xi) * (1 - et), xi * (1 - et), xi * et, (1 - xi) * et], x = 0, y = 0;
      for (var a = 0; a < 4; a++) { x += N[a] * P[a][0]; y += N[a] * P[a][1]; }
      return [x, y];
    }
    root.innerHTML = '<div class="row"><span>corner temperatures:</span><button type="button" data-p="checker">checkerboard +1, −1, +1, −1</button><button type="button" data-p="ramp">ramp 0, 4, 5, 0 (T = x)</button></div>' +
      '<div class="row"><span>integration:</span>' + Object.keys(RULES).map(function (k) { return '<button type="button" data-r="' + k + '">' + RULES[k].name + "</button>"; }).join("") + "</div>" +
      '<div class="fig"></div><div class="tab"></div><p class="msg" aria-live="polite"></p>';
    var pat = c.start || "checker", rk = c.rule || "two";
    function draw() {
      var T = PAT[pat], S = small(rk);
      root.querySelectorAll("button[data-p]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.p === pat ? "true" : "false"); });
      root.querySelectorAll("button[data-r]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.r === rk ? "true" : "false"); });
      var W = 420, H = 290, sc = 52, ox = 80, oy = 258, X = function (p) { return ox + sc * p[0]; }, Y = function (p) { return oy - sc * p[1]; };
      var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="The slanted element, its corner temperatures and the integration points">';
      for (var i = 1; i < 4; i++) {                          // the reference square's lines, carried onto the element
        var a = [], b = [];
        for (var j = 0; j <= 10; j++) { a.push(map(i / 4, j / 10)); b.push(map(j / 10, i / 4)); }
        [a, b].forEach(function (L) { s += '<polyline points="' + L.map(function (p) { return X(p) + "," + Y(p); }).join(" ") + '" fill="none" stroke="var(--line)" stroke-width="1.5"/>'; });
      }
      s += '<polygon points="' + P.map(function (p) { return X(p) + "," + Y(p); }).join(" ") + '" fill="none" stroke="currentColor" stroke-width="2.5"/>';
      P.forEach(function (p, k) {
        var col = T[k] > 0 ? "var(--s2)" : T[k] < 0 ? "var(--s1)" : "var(--muted)", dx = p[0] > 2 ? 14 : -14;
        s += '<circle cx="' + X(p) + '" cy="' + Y(p) + '" r="6" fill="' + col + '"/>' +
          '<text x="' + (X(p) + dx) + '" y="' + (Y(p) + (p[1] > 1 ? -10 : 22)) + '" text-anchor="' + (dx > 0 ? "start" : "end") + '" font-size="15" fill="' + col + '">' + (k + 1) + ": " + fmt(T[k]) + "</text>";
      });
      rule(rk).forEach(function (g) { var q = map(g[0], g[1]); s += '<circle cx="' + X(q) + '" cy="' + Y(q) + '" r="5.5" fill="var(--accent)"/>'; });
      s += '<text x="8" y="20" font-size="14" fill="var(--muted)">corner: temperature (K above a base)</text>' +
        '<text x="8" y="40" font-size="14" fill="var(--accent)">● integration points</text></svg>';
      root.querySelector(".fig").innerHTML = s;
      var rows = Object.keys(RULES).map(function (k) {
        var R = small(k), KT = R.K.map(function (r) { return r[0] * T[0] + r[1] * T[1] + r[2] * T[2] + r[3] * T[3]; }), tkt = KT[0] * T[0] + KT[1] * T[1] + KT[2] * T[2] + KT[3] * T[3];
        return "<tr" + (k === rk ? ' style="font-weight:700"' : "") + "><td>" + RULES[k].name + "</td><td>" + r3(R.area) + "</td><td>" + KT.map(r3).join(", ") + "</td><td>" + r3(tkt) + "</td></tr>";
      }).join("");
      root.querySelector(".tab").innerHTML = '<div class="scroll"><table class="k"><tr><th>points</th><th>area (mm²)</th><th>K T (W)</th><th>Tᵀ K T (W·K)</th></tr>' + rows + "</table></div>";
      var KT = S.K.map(function (r) { return r[0] * T[0] + r[1] * T[1] + r[2] * T[2] + r[3] * T[3]; }), tkt = KT[0] * T[0] + KT[1] * T[1] + KT[2] * T[2] + KT[3] * T[3];
      root.querySelector(".msg").innerHTML = (Math.abs(tkt) < 1e-9 && pat === "checker" ? '<span class="bad">This rule sees nothing:</span> at the center both slopes of the checkerboard are 0, so the table says this pattern needs no heat at all.' :
        rk === "off" ? "Off-center, one point does see the checkerboard, but the area comes out " + r3(S.area) + " mm², not 13: one point with weight 1 takes the growth factor at (0.25, 0.25) for the whole element." :
        "T transpose K T = " + r3(tkt) + " W·K with " + RULES[rk].name + " points. Rows of K always add up to 0: equal corner temperatures need no heat.");
    }
    root.querySelectorAll("button[data-p]").forEach(function (b) { b.onclick = function () { pat = b.dataset.p; draw(); }; });
    root.querySelectorAll("button[data-r]").forEach(function (b) { b.onclick = function () { rk = b.dataset.r; draw(); }; });
    draw();
  }

  // E06: the two-square example (chip k t = 3, aluminum 4; 1 mm squares cut along one diagonal), the 6x6 big table one element at a time
  function tiny(root, c) {
    var X = [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]];
    var EL = c.elements || [[1, 2, 5, 3], [1, 5, 4, 3], [2, 3, 6, 4], [2, 6, 5, 4]];   // global nodes 1..6, then k t
    function small(e) {
      var p = e.slice(0, 3).map(function (n) { return X[n - 1]; }), kt = e[3];
      var a2 = (p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1]);
      var g = [0, 1, 2].map(function (i) { var j = (i + 1) % 3, k = (i + 2) % 3; return [(p[j][1] - p[k][1]) / a2, (p[k][0] - p[j][0]) / a2]; });
      return g.map(function (gi) { return g.map(function (gj) { return kt * (gi[0] * gj[0] + gi[1] * gj[1]) * a2 / 2; }); });
    }
    root.innerHTML = '<div class="row"><button class="prev">Back</button><button class="next">Add element 1</button></div><div class="fig"></div><div class="tab"></div><p class="msg" aria-live="polite"></p>';
    var step = 0;
    function draw() {
      var B = [], hits = [];
      for (var i = 0; i < 6; i++) { B.push(new Array(6).fill(null)); hits.push(new Array(6).fill(false)); }
      for (var e = 0; e < step; e++) {
        var k = small(EL[e]), g = EL[e].slice(0, 3);
        for (var a = 0; a < 3; a++) for (var b = 0; b < 3; b++) {
          B[g[a] - 1][g[b] - 1] = (B[g[a] - 1][g[b] - 1] || 0) + k[a][b];
          if (e === step - 1) hits[g[a] - 1][g[b] - 1] = true;
        }
      }
      var W = 420, H = 260, sc = 150, ox = 60, oy = 190, px = function (p) { return ox + sc * p[0]; }, py = function (p) { return oy - sc * p[1]; };
      var s = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Two squares cut into four triangles">';
      EL.forEach(function (el_, i) {
        var pts = el_.slice(0, 3).map(function (n) { return X[n - 1]; }), cx = (pts[0][0] + pts[1][0] + pts[2][0]) / 3, cy = (pts[0][1] + pts[1][1] + pts[2][1]) / 3;
        var on = i < step, cur = i === step - 1;
        s += '<polygon points="' + pts.map(function (p) { return px(p) + "," + py(p); }).join(" ") + '" fill="' + (on ? (el_[3] === 3 ? "var(--s3)" : "var(--s1)") : "transparent") +
          '" fill-opacity="' + (cur ? 0.45 : 0.18) + '" stroke="currentColor" stroke-width="' + (cur ? 3 : 1.5) + '"/>' +
          '<text x="' + px([cx]) + '" y="' + (py([0, cy]) + 5) + '" text-anchor="middle" font-size="15" fill="var(--muted)">e' + (i + 1) + "</text>";
      });
      X.forEach(function (p, i) { s += '<circle cx="' + px(p) + '" cy="' + py(p) + '" r="5" fill="currentColor"/><text x="' + (px(p) + (p[0] === 2 ? 12 : -12)) + '" y="' + (py(p) + (p[1] ? -8 : 20)) + '" text-anchor="middle" font-size="15">' + (i + 1) + "</text>"; });
      s += '<text x="' + ox + '" y="236" font-size="15" fill="var(--s3)">chip, k t = 3 W/K</text><text x="' + ox + '" y="256" font-size="15" fill="var(--s1)">aluminum, k t = 4 W/K</text></svg>';
      root.querySelector(".fig").innerHTML = s;
      var names = [1, 2, 3, 4, 5, 6];
      root.querySelector(".tab").innerHTML = plainTable(B, hits, names, names);
      root.querySelector(".prev").disabled = step === 0;
      root.querySelector(".next").disabled = step === EL.length;
      root.querySelector(".next").textContent = step < EL.length ? "Add element " + (step + 1) : "All elements in";
      var stored = B.flat().filter(function (v) { return v !== null; }).length;
      root.querySelector(".msg").innerHTML = step === 0 ? "An empty 6×6 big table. A dot means nothing has been added to that cell yet." :
        "Element " + step + ": local 1, 2, 3 are global " + EL[step - 1].slice(0, 3).join(", ") + ", so its nine numbers land where rows and columns " + EL[step - 1].slice(0, 3).join(", ") + " cross (highlighted)." +
        (step === EL.length ? " Stored cells: " + stored + " of 36. The other " + (36 - stored) + " never get an entry: those two nodes share no triangle, so the cell stays 0 for good." : "");
    }
    root.querySelector(".next").onclick = function () { step++; draw(); };
    root.querySelector(".prev").onclick = function () { step--; draw(); };
    draw();
  }

  // E06: a square plate of n x n squares cut the same way; how much of the full table is stored
  function sparsity(root, c) {
    root.innerHTML = '<div class="row"><label>squares per side <input type="range" min="2" max="200" step="1" value="' + (c.start || 10) + '"><output></output></label></div><div class="tab"></div><p class="msg" aria-live="polite"></p>';
    var inp = root.querySelector("input");
    function draw() {
      var n = +inp.value, N = (n + 1) * (n + 1), edges = 2 * n * (n + 1) + n * n, stored = N + 2 * edges, full = N * N;
      inp.nextElementSibling.textContent = n;
      root.querySelector(".tab").innerHTML = '<div class="scroll"><table class="k"><tr><th>nodes</th><th>cells in the full table</th><th>cells stored</th><th>share</th><th>full, 8 bytes a cell</th></tr><tr><td>' +
        N.toLocaleString("en-US") + "</td><td>" + full.toLocaleString("en-US") + "</td><td>" + stored.toLocaleString("en-US") + "</td><td>" + fmt(Math.round(stored / full * 1e5) / 1e3) + " %</td><td>" + fmt(Math.round(full * 8 / 1e5) / 10) + " MB</td></tr></table></div>";
      root.querySelector(".msg").innerHTML = "Every row holds at most 7 cells (a middle node and its 6 neighbours), so the stored cells grow like the nodes, while the full table grows like the nodes squared.";
    }
    inp.oninput = draw; draw();
  }

  // E07: the rod of episode 2 (2 elements, k A / h = 1 W/K, 40 W per element, left end at 20 °C); choose the right end, and a contact resistance in the middle
  function rodbc(root, c) {
    root.innerHTML = '<div class="row"><label>right end <select class="end"><option value="ins">insulated</option><option value="flux">given heat flow out</option><option value="air">air at 20 °C</option><option value="fix">fixed temperature</option></select></label>' +
      '<label class="v"><span></span><input type="range"><output></output></label></div>' +
      '<div class="row"><label><input type="checkbox" class="cr"> contact resistance at the middle node</label><label>A / R<sub>t</sub> <input type="range" class="a" min="0.5" max="10" step="0.5" value="2" style="width:6rem"><output>2</output> W/K</label></div>' +
      '<div class="tab"></div><p class="msg" aria-live="polite"></p>';
    var sel = root.querySelector(".end"), v = root.querySelector(".v input"), cr = root.querySelector(".cr"), ai = root.querySelector(".a");
    var SET = { ins: null, flux: ["heat out (W)", 0, 80, 5, 40], air: ["h<sub>c</sub> A (W/K)", 0, 10, 0.5, 2], fix: ["T at the end (°C)", 0, 120, 5, 20] };
    if (c.end) sel.value = c.end;
    function setSlider() {
      var s = SET[sel.value], lab = root.querySelector(".v");
      lab.style.display = s ? "" : "none";
      if (s) { lab.querySelector("span").innerHTML = s[0]; v.min = s[1]; v.max = s[2]; v.step = s[3]; v.value = s[4]; }
    }
    function draw() {
      var split = cr.checked, a = +ai.value, n = split ? 4 : 3, names = split ? ["1", "2", "2′", "3"] : ["1", "2", "3"], last = n - 1;
      ai.nextElementSibling.textContent = ai.value;
      if (SET[sel.value]) v.nextElementSibling.textContent = v.value;
      var K0 = split ? [[1, -1, 0, 0], [-1, 1 + a, -a, 0], [0, -a, a + 1, -1], [0, 0, -1, 1]] : [[1, -1, 0], [-1, 2, -1], [0, -1, 1]];
      var f0 = split ? [20, 20, 20, 20] : [20, 40, 20];
      var K = K0.map(function (r) { return r.slice(); }), f = f0.slice(), val = +v.value, end = sel.value;
      if (end === "flux") f[last] -= val;
      if (end === "air") { K[last][last] += val; f[last] += val * 20; }
      var hK = K.map(function (r, i) { return r.map(function (x, j) { return Math.abs(x - K0[i][j]) > 1e-12 || (end === "fix" && (i === last || j === last)); }); });
      var hf = [f.map(function (x, i) { return Math.abs(x - f0[i]) > 1e-12; })];
      var fixed = { 0: 20 }; if (end === "fix") fixed[last] = val;
      var free = [], A = [], b = [];
      for (var i = 0; i < n; i++) if (!(i in fixed)) free.push(i);
      free.forEach(function (i) { var s = f[i]; for (var j in fixed) s -= K[i][j] * fixed[j]; b.push(s); A.push(free.map(function (j) { return K[i][j]; })); });
      var x = gauss(A, b), T = new Array(n);
      for (var jj in fixed) T[jj] = fixed[jj];
      root.querySelector(".tab").innerHTML = '<div class="row" style="align-items:flex-start;gap:1.5rem"><div><b>big table (W/K)</b>' + plainTable(K, hK, names, names) +
        '</div><div><b>right-hand side (W)</b>' + plainTable([f], hf, [""], names) + "</div></div>";
      if (!x) { root.querySelector(".msg").innerHTML = '<span class="bad">No unique solution.</span>'; return; }
      free.forEach(function (i, k) { T[i] = x[k]; });
      // heat leaving at an end = what the node makes minus what its row of the conduction table sends inward
      var rowOut = function (i) { var s = f0[i]; for (var j = 0; j < n; j++) s -= K0[i][j] * T[j]; return s; };
      var outL = rowOut(0), outR = end === "fix" ? rowOut(last) : end === "flux" ? val : end === "air" ? val * (T[last] - 20) : 0;
      var changed = hK.flat().filter(Boolean).length, fch = hf[0].filter(Boolean).length;
      root.querySelector(".msg").innerHTML = "Temperatures (°C): " + T.map(function (t, i) { return "T" + names[i] + " = " + r3(t); }).join(", ") +
        ". Heat out: left end " + r3(outL) + " W, right end " + r3(outR) + " W, together " + r3(outL + outR) + " W of the 80 W made." +
        (end === "fix" ? " A fixed end crosses out row " + names[last] + " and column " + names[last] + " (highlighted): its column times the temperature moves to the right side." :
          " Changed by the right end: " + (changed ? changed + " cell" + (changed > 1 ? "s" : "") + " of the big table" : "no cell of the big table") + (fch ? " and " + fch + " cell of the right-hand side." : " and nothing on the right-hand side."));
    }
    sel.onchange = function () { setSlider(); draw(); };
    v.oninput = draw; cr.onchange = draw; ai.oninput = draw;
    setSlider(); draw();
  }

  var KINDS = { bet: bet, build: build, play: play, quiz: quiz, weak: weak, refine: refine, runge: runge, quad: quad, tiny: tiny, sparsity: sparsity, rodbc: rodbc };
  document.querySelectorAll("[data-fea]").forEach(function (root) {
    try { KINDS[root.dataset.fea](root, JSON.parse(root.dataset.config)); root.classList.add("widget"); }
    catch (e) { root.innerHTML = '<p class="note">This figure needs JavaScript.</p>'; }
  });
})();
