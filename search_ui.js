#!/usr/bin/osascript -l JavaScript
// Read Passwords search results. Prints site\tusername lines. No secrets.

function kids(el) {
  try {
    return el.uiElements();
  } catch (e) {
    return [];
  }
}

function toolbarSearch(win) {
  try {
    const groups = win.toolbars[0].groups();
    for (let i = 0; i < groups.length; i++) {
      const tfs = kids(groups[i]);
      for (let j = 0; j < tfs.length; j++) {
        try {
          if (tfs[j].subrole() === "AXSearchField") return tfs[j];
        } catch (e) {}
      }
    }
  } catch (e) {}
  return null;
}

function resultOutline(win) {
  try {
    return win.groups[0].splitterGroups[0].groups[1].scrollAreas[0].outlines[0];
  } catch (e) {
    return null;
  }
}

function rowPair(row) {
  try {
    const cell = kids(row)[0];
    const texts = [];
    const parts = kids(cell);
    for (let i = 0; i < parts.length; i++) {
      try {
        if (parts[i].role() === "AXStaticText") {
          const v = String(parts[i].value() || "");
          if (v) texts.push(v);
        }
      } catch (e) {}
    }
    if (!texts.length) return null;
    return texts[0] + "\t" + (texts[1] || "");
  } catch (e) {
    return null;
  }
}

function run(argv) {
  const query = argv.length ? String(argv[0]) : "";
  if (!query) return "EMPTY";
  const se = Application("System Events");
  const procs = se.processes.whose({ name: "Passwords" });
  if (!procs.length) {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;
    app.doShellScript("/usr/bin/open -g -a Passwords");
    delay(0.4);
  }
  const proc = se.processes.byName("Passwords");
  let win;
  try {
    win = proc.windows[0];
  } catch (e) {
    proc.frontmost = true;
    delay(0.25);
    try {
      win = proc.windows[0];
    } catch (e2) {
      return "LOCKED";
    }
  }
  let sf = toolbarSearch(win);
  if (!sf) {
    proc.frontmost = true;
    delay(0.25);
    sf = toolbarSearch(proc.windows[0]);
    if (!sf) return "LOCKED";
    win = proc.windows[0];
  }
  sf.value = query;
  delay(0.2);
  const outline = resultOutline(proc.windows[0]);
  if (!outline) return "EMPTY";
  const rows = kids(outline);
  const n = Math.min(rows.length, 12);
  const lines = ["OK"];
  for (let i = 0; i < n; i++) {
    const pair = rowPair(rows[i]);
    if (pair) lines.push(pair);
  }
  try {
    proc.visible = false;
  } catch (e) {}
  try {
    se.processes.byName("Alfred 5").frontmost = true;
  } catch (e) {
    try {
      se.processes.byName("Alfred").frontmost = true;
    } catch (e2) {}
  }
  return lines.join("\n");
}
