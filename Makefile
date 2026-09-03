.PHONY: build install uninstall check test

ALFRED_WORKFLOWS := $(HOME)/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows
INSTALL_DIR := $(ALFRED_WORKFLOWS)/user.workflow.icloud-passwords-revamp

build:
	python3 build.py

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -v

check: test
	python3 -m py_compile search.py action.py build.py titles.py lib/*.py tests/*.py
	plutil -lint info.plist
	osacompile -o /tmp/icloud-passwords-revamp-check.scpt ui.applescript
	rm -f /tmp/icloud-passwords-revamp-check.scpt

install: build check
	mkdir -p "$(INSTALL_DIR)"
	python3 - <<'PY'
from pathlib import Path
import shutil
from build import WORKFLOW_FILES, ROOT
dest = Path.home() / "Library/Application Support/Alfred/Alfred.alfredpreferences/workflows/user.workflow.icloud-passwords-revamp"
for name in WORKFLOW_FILES:
    src = ROOT / name
    target = dest / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
PY

uninstall:
	rm -rf "$(INSTALL_DIR)"
