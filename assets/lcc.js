/* Learn Claude Code: interactive figures for the episode pages, built from the frozen runs next to each page
   (frozen/<run>/trace.jsonl: one line per model call, with the full request and reply). No libraries. */
(function () {
  "use strict";

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function load(path) {
    return fetch(path).then(function (r) { if (!r.ok) throw new Error(path); return r.text(); })
      .then(function (t) { return t.trim().split("\n").map(function (l) { return JSON.parse(l); }); });
  }
  function loadText(path) {
    return fetch(path).then(function (r) { if (!r.ok) throw new Error(path); return r.text(); })
      .then(function (s) { return s.replace(/\x1b\[[0-9;]*m/g, ""); });
  }
  // what the program printed between running a tool and the next round: the permission gates (s03 and later);
  // with hooks (s04 and later) also the lines the hooks print around a tool: [HOOK] tool(...), [AUDIT], [readonly]
  function gates(log, hooks) {
    var out = [], parts = log.split(/─+ Round \d+: sent to the model ─+/);
    var pat = hooks ? /^\[(permission|blocked|AUDIT|readonly)\]|^\[HOOK\] (?!Stop:|UserPromptSubmit:)|^\s+(Tool:|Allow\?)/ :
      /^\[(permission|blocked)\]|^\s+(Tool:|Allow\?)/;
    parts.slice(1).forEach(function (p) {
      var lines = p.split("\n").filter(function (l) { return pat.test(l); });
      out.push(lines.join("\n"));
    });
    return out;                        // out[i] = gate lines printed after the model call i + 1
  }
  // what the hooks around one tool call did, from the lines they printed (s04 and later)
  function hookStep(g) {
    var audit = /\[AUDIT\]/.test(g);
    if (/Allow\? \[y\/N\] n/.test(g) || (/Allow\?/.test(g) && !/Allow\? \[y\/N\] y/.test(g)))
      return { who: "PreToolUse: the permission hook asks you", denied: true,
        note: "The answer is n. The permission hook returns \"Permission denied by user\". That is not None, so trigger_hooks returns at once: the log hook behind it is never called, and no [HOOK] line is printed for this call." };
    if (/\[readonly\]/.test(g))
      return { who: "PreToolUse: log hook, then the read-only hook", denied: true,
        note: "The log hook is first in line, so it prints its line. Then the read-only hook returns text: the call is blocked and the tool never runs, so there is no [AUDIT] line." };
    if (/\[blocked\]/.test(g))
      return { who: "PreToolUse: the deny list", denied: true, note: "Blocked before anyone is asked." };
    if (/Allow\? \[y\/N\] y/.test(g))
      return { who: "PreToolUse: the permission hook asks you", denied: false,
        note: "The answer is y, so the permission hook returns None and the next hook in line, the log hook, prints its line. Then the tool runs." + (audit ? " After it, the audit hook adds its line." : "") };
    return { who: "PreToolUse" + (audit ? " and PostToolUse" : "") + " hooks", denied: false,
      note: "The permission hook lets it through without a word. The log hook prints its line before the tool runs" + (audit ? ", and the audit hook adds one after it." : ".") };
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
    if (block.type === "tool_use" && block.input && Array.isArray(block.input.todos))      // todo_write (s05 and later): the list it sends
      return "<div>calls <b>" + esc(block.name) + "</b> with this list:</div><pre><code>" + esc(block.input.todos.map(function (t) {
        return (t.status === "completed" ? "[x] " : t.status === "in_progress" ? "[>] " : "[ ] ") + t.content; }).join("\n")) + "</code></pre>";
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
    Promise.all([load(c.run + "/trace.jsonl"), c.gate ? loadText(c.run + "/terminal.log") : Promise.resolve("")]).then(function (got) {
      var calls = got[0], gl = c.gate ? gates(got[1], c.hooks) : [];
      var steps = [];      // each step adds one bubble and says what happened
      calls.forEach(function (call, i) {
        var msgs = call.request.messages, last = msgs[msgs.length - 1];
        if (i === 0) steps.push({ kind: "user", who: "you", body: blocks(last.content).map(show).join(""),
          note: "You type a question. The loop puts it in a list of messages." });
        steps.push({ kind: "send", round: i + 1, msgs: msgs.length, tokens: call.response.usage.input_tokens,
          note: "Round " + (i + 1) + ": the loop sends the model the system prompt, " + ((call.request.tools || []).length > 1 ? "the descriptions of its " + call.request.tools.length + " tools" : "the bash tool's description") + " and all " + msgs.length +
            " message" + (msgs.length > 1 ? "s" : "") + " so far (" + call.response.usage.input_tokens + " input tokens)." });
        var out = blocks(call.response.content);
        steps.push({ kind: "model", who: "model · stop_reason: " + call.response.stop_reason, body: out.map(show).join(""),
          note: call.response.stop_reason === "tool_use" ? "The model only writes a request to use a tool (" + out.filter(function (b) { return b.type === "tool_use"; }).map(function (b) { return b.name; }).join(", ") + "). It cannot run anything itself." :
            "No tool call this time: stop_reason is end_turn, so the loop stops and prints the answer." });
        var next = calls[i + 1];
        var denied = false;
        if (c.hooks && gl[i] !== undefined && call.response.stop_reason === "tool_use") {
          var h = hookStep(gl[i] || "");
          denied = h.denied;
          steps.push({ kind: "tool", who: h.who, body: gl[i] ? "<pre><code>" + esc(gl[i]) + "</code></pre>" : "<div>No hook printed anything.</div>", note: h.note });
        } else if (c.gate && gl[i] !== undefined && call.response.stop_reason === "tool_use") {
          var g = gl[i] || "";
          denied = /\[blocked\]/.test(g) || (/Allow\?/.test(g) && !/Allow\? \[y\/N\] y/.test(g));
          steps.push({ kind: "tool", who: /\[blocked\]/.test(g) ? "gate 1: the deny list" : /Allow\?/.test(g) ? "gate 2: the program asks you" : "the gates let it through",
            body: g ? "<pre><code>" + esc(g) + "</code></pre>" : "<div>No gate matched, so the tool runs without asking.</div>",
            note: /\[blocked\]/.test(g) ? "Blocked before anyone is asked: the command is on the deny list." :
              /Allow\? \[y\/N\] y/.test(g) ? "The program stops and asks. The answer is y, so the command runs." :
              /Allow\?/.test(g) ? "The program stops and asks. The answer is n, so nothing runs and the model gets \"Permission denied.\"" : "Nothing matched, so it runs." });
        }
        if (next) {
          var res = next.request.messages[next.request.messages.length - 1];
          var names = out.filter(function (b) { return b.type === "tool_use"; }).map(function (b) { return b.name; });
          var added = blocks(res.content).filter(function (b) { return b.type === "text"; }).map(function (b) { return b.text; }).join(" ");
          steps.push({ kind: "tool", who: denied ? "nothing runs: the loop sends back" : "the loop runs " + names.join(", "), body: blocks(res.content).map(show).join(""),
            note: denied ? (c.hooks ? "The tool never ran. The text the hook returned goes back as the tool_result, and the loop goes round again." :
              "The tool never ran. The loop appends \"Permission denied.\" as the tool_result and goes round again.") :
              "The loop runs " + names.join(", ") + " and appends the output as a tool_result." +
              (added ? " After the tool results, the program adds one more text block of its own: " + added : "") + " Then it goes round again." });
        }
      });
      if (c.hooks) {
        var stop = (got[1].match(/\[HOOK\] Stop: .*/g) || []).pop();
        if (stop) steps.push({ kind: "tool", who: "Stop hook", body: "<pre><code>" + esc(stop) + "</code></pre>",
          note: "Right before the loop ends, the Stop hook prints how many tool results are in messages, refused ones included." });
      }
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

  // 3. a guess with several buckets, answered by counting what the repeated runs did (rule fixed before the runs)
  function tally(root, c) {
    root.innerHTML = '<p>' + esc(c.question) + '</p><div class="row choices"></div><div class="out"></div><p class="msg" aria-live="polite"></p>';
    var row = root.querySelector(".choices");
    c.options.forEach(function (o) {
      var b = document.createElement("button");
      b.type = "button"; b.innerHTML = "<b>" + esc(o.id) + "</b> " + esc(o.text); b.setAttribute("aria-pressed", "false");
      b.onclick = function () {
        row.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); x.disabled = true; });
        Promise.all(c.runs.map(function (r) { return Promise.all([load(r + "/trace.jsonl"), c.rule === "asked" || c.rule === "logged" ? loadText(r + "/terminal.log") : ""]); })).then(function (got) {
          var all = got.map(function (g) { return g[0]; });
          var seqs = all.map(function (calls) {
            var s = [];
            calls.forEach(function (call) { blocks(call.response.content).forEach(function (x) { if (x.type === "tool_use") s.push(x.name); }); });
            return s;
          });
          var cmds = all.map(function (calls) {
            var s = [];
            calls.forEach(function (call) { blocks(call.response.content).forEach(function (x) { if (x.type === "tool_use") s.push(x.input.command || x.name); }); });
            return s;
          });
          // "logged": where the log hook's line for c.tool came, against the approval question (s04 and later)
          var where = c.rule === "logged" ? got.map(function (g) {
            var a = g[1].indexOf("Allow? [y/N]"), k = g[1].indexOf("[HOOK] " + c.tool + "(");
            return k < 0 ? "none" : a >= 0 && k < a ? "before" : "after";
          }) : null;
          // "followup" (s06 and later): after the next question, does the parent (the calls that can see c.parent) call a tool?
          var follow = c.rule === "followup" ? all.map(function (calls) {
            var used = [];
            calls.forEach(function (call) {
              var asked = call.request.messages.filter(function (m) { return m.role === "user" && typeof m.content === "string"; }).length;
              var parent = (call.request.tools || []).some(function (t) { return t.name === c.parent; });
              if (parent && asked >= 2) blocks(call.response.content).forEach(function (x) { if (x.type === "tool_use") used.push(x.name + " " + (x.input.path || x.input.command || x.input.prompt || "")); });
            });
            return used;
          }) : null;
          var plans = c.rule === "plan" ? all.map(function (calls) {
            var last = null;
            calls.forEach(function (call) { blocks(call.response.content).forEach(function (x) { if (x.type === "tool_use" && x.input && Array.isArray(x.input.todos)) last = x.input.todos; }); });
            return last ? { done: last.filter(function (t) { return t.status === "completed"; }).length, n: last.length } : null;
          }) : null;
          var hit = follow ? follow.map(function (u) { return u.length > 0; }) : plans ? plans.map(function (p) { return !!p && p.done === 0; }) : c.rule === "asked" ? got.map(function (g) { return /Allow\? \[y\/N\]/.test(g[1]); }) :
            where ? where.map(function (w) { return w !== "none"; }) :
            seqs.map(function (s) { return s.length > 0 && s.every(function (n) { return n === c.only; }); });
          var n = hit.filter(Boolean).length, answer;
          if (where) {
            var most = ["none", "before", "after"].sort(function (x, y) {
              return where.filter(function (w) { return w === y; }).length - where.filter(function (w) { return w === x; }).length; })[0];
            answer = c.options.filter(function (o) { return o.where === most; })[0].id;
          } else answer = c.options.filter(function (o) { return n >= o.min && n <= o.max; })[0].id;
          root.querySelector(".out").innerHTML = '<div class="row">' + seqs.map(function (s, i) {
            return '<span class="button">run ' + (i + 1) + ": " + (follow ? (follow[i].length ? esc(follow[i].join(" → ")) : "answered directly") : plans ? (plans[i] ? "plan " + plans[i].done + "/" + plans[i].n + " completed" : "no plan") + " · " + all[i].length + " model calls" : where ? esc(cmds[i].join(" → ") || "no tool call") + (where[i] === "none" ? " · no log line" : " · log line " + where[i] + " the approval") :
              c.rule === "asked" ? esc(cmds[i].join(" → ") || "no tool call") + (hit[i] ? " · asked" : " · not asked") :
              esc(s.join(" → ")) + (hit[i] ? " (" + esc(c.only) + " only)" : "")) + "</span>";
          }).join("") + "</div>";
          root.querySelector(".msg").innerHTML = '<span class="' + (o.id === answer ? "ok" : "bad") + '">' + (o.id === answer ? "Right. " : "The answer is " + answer + ". ") + "</span>" +
            n + " of " + all.length + (follow ? " runs called a tool. " : plans ? " runs ended with no item completed. " : where ? " runs printed the log line. " : c.rule === "asked" ? " runs stopped to ask. " : " runs used " + esc(c.only) + " only. ") + esc(c.explain);
        });
      };
      row.appendChild(b);
    });
  }

  // 4. every model call of a few runs as bars of input tokens; the calls that can see c.parent are the parent's, the
  //    others the subagent's (s06 and later); "parent only" shows what the parent itself carries
  function calls(root, c) {
    root.innerHTML = '<p class="note">Loading the runs…</p>';
    Promise.all(c.runs.map(function (r) { return load(r.run + "/trace.jsonl"); })).then(function (all) {
      var only = false;
      root.innerHTML = '<div class="row"><button class="all" aria-pressed="true">Every model call</button><button class="par" aria-pressed="false">The parent&apos;s calls only</button></div>' +
        '<div class="out"></div><p class="msg" aria-live="polite"></p>';
      function draw() {
        var html = "", sums = [];
        all.forEach(function (list, k) {
          var tot = 0, par = 0, q = 0;
          html += "<h3>" + esc(c.runs[k].label) + "</h3>";
          list.forEach(function (call, i) {
            var parent = (call.request.tools || []).some(function (t) { return t.name === c.parent; });
            var asked = call.request.messages.filter(function (m) { return m.role === "user" && typeof m.content === "string"; }).length;
            if (parent) q = asked;
            var t = call.response.usage.input_tokens;
            tot += t; if (parent) par += t;
            if (only && !parent) return;
            html += '<div class="meter" style="grid-template-columns:10rem 1fr 3.5rem"><span>call ' + (i + 1) + " · " + (parent ? "parent" : "subagent") + " · Q" + q +
              '</span><span class="bar" style="width:' + Math.round(100 * t / c.scale) + '%"></span><span>' + t + "</span></div>";
          });
          sums.push(esc(c.runs[k].label) + ": " + (only ? par + " input tokens in the parent's calls" : tot + " input tokens in all"));
        });
        root.querySelector(".out").innerHTML = html;
        root.querySelector(".msg").innerHTML = sums.join("; ") + ". " + esc(only ? c.explainParent : c.explainAll);
        root.querySelector(".all").setAttribute("aria-pressed", only ? "false" : "true");
        root.querySelector(".par").setAttribute("aria-pressed", only ? "true" : "false");
      }
      root.querySelector(".all").onclick = function () { only = false; draw(); };
      root.querySelector(".par").onclick = function () { only = true; draw(); };
      draw();
    }).catch(function () { root.innerHTML = '<p class="note">Could not load the runs. They are in the code folder on GitHub.</p>'; });
  }

  var KINDS = { replay: replay, bet: bet, tally: tally, calls: calls };
  document.querySelectorAll("[data-lcc]").forEach(function (root) {
    try { KINDS[root.dataset.lcc](root, JSON.parse(root.dataset.config)); root.classList.add("widget"); }
    catch (e) { root.innerHTML = '<p class="note">This figure needs JavaScript.</p>'; }
  });
})();
