/* Learn Claude Code: interactive figures for the episode pages, built from the frozen runs next to each page
   (frozen/<run>/trace.jsonl: one line per model call, with the full request and reply). No libraries. */
(function () {
  "use strict";

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function load(path) {
    return fetch(path).then(function (r) { if (!r.ok) throw new Error(path); return r.text(); })
      .then(function (t) { return t.trim().split("\n").map(function (l) { return JSON.parse(l); }); });
  }
  function bubble(kind, who, body, isNew) {
    return '<div class="bubble ' + kind + (isNew ? " new" : "") + '"><span class="who">' + esc(who) + "</span>" + body + "</div>";
  }
  function blocks(content) {
    if (typeof content === "string") return [{ type: "text", text: content }];
    return content || [];
  }
  function show(block) {
    if (block.type === "text") return "<div>" + esc(block.text).replace(/\n/g, "<br>") + "</div>";
    if (block.type === "tool_use") return "<div>calls <b>" + esc(block.name) + "</b>:</div><pre><code>" + esc(block.input.command || JSON.stringify(block.input)) + "</code></pre>";
    if (block.type === "tool_result") {
      var c = typeof block.content === "string" ? block.content : (block.content || []).map(function (x) { return x.text || ""; }).join("");
      return "<pre><code>" + esc(c) + "</code></pre>";
    }
    return "";
  }

  // 1. step through one run: what the loop sends, what comes back, what the loop does with it
  function replay(root, c) {
    root.innerHTML = '<p class="note">Loading the run…</p>';
    load(c.run + "/trace.jsonl").then(function (calls) {
      var steps = [];      // each step adds one bubble and says what happened
      calls.forEach(function (call, i) {
        var msgs = call.request.messages, last = msgs[msgs.length - 1];
        if (i === 0) steps.push({ kind: "user", who: "you", body: blocks(last.content).map(show).join(""),
          note: "You type a question. The loop puts it in a list of messages." });
        steps.push({ kind: "send", round: i + 1, msgs: msgs.length, tokens: call.response.usage.input_tokens,
          note: "Round " + (i + 1) + ": the loop sends the model the system prompt, the bash tool's description and all " + msgs.length +
            " message" + (msgs.length > 1 ? "s" : "") + " so far (" + call.response.usage.input_tokens + " input tokens)." });
        var out = blocks(call.response.content);
        steps.push({ kind: "model", who: "model · stop_reason: " + call.response.stop_reason, body: out.map(show).join(""),
          note: call.response.stop_reason === "tool_use" ? "The model only writes a request to run a command. It cannot run anything itself." :
            "No tool call this time: stop_reason is end_turn, so the loop stops and prints the answer." });
        var next = calls[i + 1];
        if (next) {
          var res = next.request.messages[next.request.messages.length - 1];
          steps.push({ kind: "tool", who: "the loop runs bash", body: blocks(res.content).map(show).join(""),
            note: "The loop runs the command and appends the output as a tool_result. Then it goes round again." });
        }
      });
      var at = 0, max = steps.length;
      root.innerHTML = '<div class="row"><button class="back">Back</button><button class="next">Next step</button><span class="note count"></span></div>' +
        '<div class="chat"></div><p class="msg" aria-live="polite"></p><div class="meters"></div>';
      function draw() {
        var html = "", meters = "";
        steps.slice(0, at + 1).forEach(function (s, j) {
          if (s.kind === "send") {
            html += '<div class="note" style="text-align:center">— round ' + s.round + ": " + s.msgs + " message" + (s.msgs > 1 ? "s" : "") + " sent —</div>";
            meters += '<div class="meter"><span>round ' + s.round + '</span><span class="bar" style="width:' + Math.round(100 * s.tokens / c.scale) + '%"></span><span>' + s.tokens + "</span></div>";
          } else html += bubble(s.kind, s.who, s.body, j === at);
        });
        root.querySelector(".chat").innerHTML = html;
        root.querySelector(".meters").innerHTML = meters ? '<p class="note">Input tokens per round: everything is sent again each time.</p>' + meters : "";
        root.querySelector(".msg").textContent = steps[at].note;
        root.querySelector(".count").textContent = "step " + (at + 1) + " of " + max;
        root.querySelector(".back").disabled = at === 0;
        root.querySelector(".next").disabled = at === max - 1;
      }
      root.querySelector(".next").onclick = function () { at++; draw(); };
      root.querySelector(".back").onclick = function () { at--; draw(); };
      draw();
    }).catch(function () { root.innerHTML = '<p class="note">Could not load the run. It is in the code folder on GitHub.</p>'; });
  }

  // 2. a guess, answered by repeated real runs
  function bet(root, c) {
    root.innerHTML = '<p>' + esc(c.question) + '</p><div class="row choices"></div><div class="out"></div><p class="msg" aria-live="polite"></p>';
    var row = root.querySelector(".choices");
    c.options.forEach(function (o) {
      var b = document.createElement("button");
      b.type = "button"; b.innerHTML = esc(o.text); b.setAttribute("aria-pressed", "false");
      b.onclick = function () {
        row.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); x.disabled = true; });
        Promise.all(c.runs.map(function (r) { return load(r + "/trace.jsonl"); })).then(function (all) {
          var used = all.map(function (calls) {
            return blocks(calls[0].response.content).some(function (x) { return x.type === "tool_use"; });
          });
          var n = used.filter(Boolean).length, answer = n > all.length / 2 ? "yes" : "no";
          root.querySelector(".out").innerHTML = '<div class="row">' + all.map(function (calls, i) {
            var txt = blocks(calls[calls.length - 1].response.content).filter(function (x) { return x.type === "text"; }).map(function (x) { return x.text; }).join(" ");
            return '<span class="button" title="' + esc(txt) + '">run ' + (i + 1) + ": " + (used[i] ? "called bash" : "answered directly") + "</span>";
          }).join("") + "</div>";
          root.querySelector(".msg").innerHTML = '<span class="' + (o.id === answer ? "ok" : "bad") + '">' + (o.id === answer ? "Right. " : "Not this time. ") + "</span>" +
            n + " of " + all.length + " runs called bash. " + esc(c.explain);
        });
      };
      row.appendChild(b);
    });
  }

  var KINDS = { replay: replay, bet: bet };
  document.querySelectorAll("[data-lcc]").forEach(function (root) {
    try { KINDS[root.dataset.lcc](root, JSON.parse(root.dataset.config)); root.classList.add("widget"); }
    catch (e) { root.innerHTML = '<p class="note">This figure needs JavaScript.</p>'; }
  });
})();
