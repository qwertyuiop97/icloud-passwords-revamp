#!/usr/bin/osascript -l JavaScript
// Background Passwords search. Does not open, focus, or unhide Passwords.

function kids(el) {
  try {
    return el.uiElements();
  } catch (e) {
    return [];
  }
}

function roleOf(el) {
  try {
    return String(el.role() || "");
  } catch (e) {
    return "";
  }
}

function subroleOf(el) {
  try {
    return String(el.subrole() || "");
  } catch (e) {
    return "";
  }
}

function isOutline(el) {
  const r = roleOf(el);
  return r === "AXOutline" || r === "AXTable" || r === "AXList";
}

function findSearchField(el, depth) {
  if (depth > 6) return null;
  if (isOutline(el)) return null;
  const role = roleOf(el);
  if (role === "AXSplitGroup") return null;
  const sub = subroleOf(el);
  if (role === "AXSearchField" || sub === "AXSearchField") return el;
  if (role === "AXTextField") {
    let blob = "";
    try {
      blob += String(el.description() || "");
    } catch (e) {}
    if (/search/i.test(blob) || !sub) return el;
  }
  const nodes = kids(el);
  for (let i = 0; i < nodes.length; i++) {
    const hit = findSearchField(nodes[i], depth + 1);
    if (hit) return hit;
  }
  return null;
}

function toolbarSearch(win) {
  try {
    const bars = win.toolbars();
    for (let i = 0; i < bars.length; i++) {
      const hit = findSearchField(bars[i], 0);
      if (hit) return hit;
    }
  } catch (e) {}
  return null;
}

function childCount(el) {
  try {
    return Number(el.attributes.byName("AXNumberOfChildren").value());
  } catch (e) {
    try {
      return el.rows().length;
    } catch (e2) {
      return kids(el).length;
    }
  }
}

function biggestOutline(el, depth, found) {
  if (depth > 8 || found.length >= 8) return;
  if (isOutline(el)) {
    found.push(el);
    return;
  }
  if (roleOf(el) === "AXToolbar") return;
  const nodes = kids(el);
  for (let i = 0; i < nodes.length; i++) {
    if (isOutline(nodes[i])) {
      found.push(nodes[i]);
      if (found.length >= 8) return;
      continue;
    }
    biggestOutline(nodes[i], depth + 1, found);
  }
}

function rowLine(row) {
  const texts = [];
  function collect(el, depth) {
    if (depth > 5 || texts.length >= 2) return;
    try {
      if (el.role() === "AXStaticText") {
        const v = String(el.value() || el.name() || "");
        if (v) texts.push(v);
      }
    } catch (e) {}
    const nodes = kids(el);
    for (let i = 0; i < nodes.length; i++) collect(nodes[i], depth + 1);
  }
  collect(row, 0);
  if (!texts.length) return null;
  return texts[0] + "\t" + (texts[1] || "");
}

function passwordsProc(se) {
  try {
    return se.processes.byName("Passwords");
  } catch (e) {
    return null;
  }
}

function findLiveSearch(proc) {
  let windows = [];
  try {
    windows = proc.windows();
  } catch (e) {
    return null;
  }
  for (let i = 0; i < windows.length; i++) {
    const hit = toolbarSearch(windows[i]);
    if (hit) return { win: windows[i], sf: hit };
  }
  return null;
}

function emitRows(win) {
  const found = [];
  biggestOutline(win, 0, found);
  let outline = null;
  let bestN = -1;
  for (let i = 0; i < found.length; i++) {
    const n = childCount(found[i]);
    if (n > bestN) {
      outline = found[i];
      bestN = n;
    }
  }
  if (!outline || bestN < 1) return "EMPTY";
  const n = Math.min(bestN, 15);
  const lines = ["OK"];
  for (let i = 0; i < n; i++) {
    let row = null;
    try {
      row = outline.rows.at(i);
    } catch (e) {
      try {
        row = outline.uiElements.at(i);
      } catch (e2) {}
    }
    if (!row) continue;
    const line = rowLine(row);
    if (line) lines.push(line);
  }
  return lines.join("\n");
}

function run(argv) {
  const se = Application("System Events");
  const proc = passwordsProc(se);
  if (argv.length && String(argv[0]) === "--state") {
    if (!proc) return "LOCKED";
    return findLiveSearch(proc) ? "UNLOCKED" : "LOCKED";
  }
  const query = argv.length ? String(argv[0]) : "";
  if (!query) return "EMPTY";
  if (!proc) return "LOCKED";
  const live = findLiveSearch(proc);
  if (!live) return "LOCKED";
  live.sf.value = query;
  delay(0.18);
  try {
    return emitRows(proc.windows[0]);
  } catch (e) {
    return emitRows(live.win);
  }
}
