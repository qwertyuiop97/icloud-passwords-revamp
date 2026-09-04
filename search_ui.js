#!/usr/bin/osascript -l JavaScript
// Fast Passwords search for Alfred. Metadata only. Never walk outline rows
// while looking for the search field.

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

function isLocked(el, depth) {
  if (depth > 8) return false;
  if (isOutline(el)) return false;
  try {
    if (el.role() === "AXStaticText") {
      const v = String(el.value() || el.name() || "").toLowerCase();
      if (v.indexOf("passwords is locked") >= 0) return true;
      if (v.indexOf("touch id or enter your password") >= 0) return true;
    }
  } catch (e) {}
  const nodes = kids(el);
  for (let i = 0; i < nodes.length; i++) {
    if (isLocked(nodes[i], depth + 1)) return true;
  }
  return false;
}

function pressUnlock(el, depth) {
  if (depth > 8) return false;
  if (isOutline(el)) return false;
  try {
    if (el.role() === "AXButton") {
      const sub = subroleOf(el);
      if (
        sub.indexOf("Close") < 0 &&
        sub.indexOf("FullScreen") < 0 &&
        sub.indexOf("Minimize") < 0 &&
        sub.indexOf("Zoom") < 0
      ) {
        try {
          el.actions.byName("AXPress").perform();
          return true;
        } catch (e) {
          try {
            el.click();
            return true;
          } catch (e2) {}
        }
      }
    }
  } catch (e) {}
  const nodes = kids(el);
  for (let i = 0; i < nodes.length; i++) {
    if (pressUnlock(nodes[i], depth + 1)) return true;
  }
  return false;
}

function alfredFront() {
  const se = Application("System Events");
  try {
    se.processes.byName("Alfred 5").frontmost = true;
  } catch (e) {
    try {
      se.processes.byName("Alfred").frontmost = true;
    } catch (e2) {}
  }
}

function passwordsProc(se) {
  try {
    const proc = se.processes.byName("Passwords");
    try {
      proc.visible = true;
    } catch (e) {}
    return proc;
  } catch (e) {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;
    app.doShellScript("/usr/bin/open -g -a Passwords");
    delay(0.35);
    try {
      const proc = se.processes.byName("Passwords");
      try {
        proc.visible = true;
      } catch (e2) {}
      return proc;
    } catch (e3) {
      return null;
    }
  }
}

function run(argv) {
  const query = argv.length ? String(argv[0]) : "";
  if (!query) return "EMPTY";
  const se = Application("System Events");
  const proc = passwordsProc(se);
  if (!proc) return "LOCKED";
  try {
    proc.frontmost = true;
  } catch (e) {}
  delay(0.15);

  let sf = null;
  let win = null;
  for (let step = 0; step < 12; step++) {
    let windows = [];
    try {
      windows = proc.windows();
    } catch (e) {
      windows = [];
    }
    for (let i = 0; i < windows.length; i++) {
      const candidate = windows[i];
      let hasToolbar = false;
      try {
        hasToolbar = candidate.toolbars().length > 0;
      } catch (e) {}
      if (!hasToolbar && isLocked(candidate, 0)) {
        pressUnlock(candidate, 0);
        continue;
      }
      const hit = toolbarSearch(candidate);
      if (hit) {
        sf = hit;
        win = candidate;
        break;
      }
    }
    if (sf) break;
    if (step === 5 || step === 9) {
      try {
        proc.frontmost = true;
        se.keystroke("f", { using: "command down" });
      } catch (e) {}
    }
    delay(0.09);
  }

  if (!sf) {
    alfredFront();
    return "LOCKED";
  }

  try {
    sf.focused = true;
  } catch (e) {}
  sf.value = query;
  delay(0.2);

  try {
    win = proc.windows[0];
  } catch (e) {}
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
  alfredFront();
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
