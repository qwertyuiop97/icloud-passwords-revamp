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

install: build
	mkdir -p "$(INSTALL_DIR)/lib"
	cp -f info.plist search.py action.py ui.applescript titles.py icon.png "$(INSTALL_DIR)/"
	cp -f lib/*.py "$(INSTALL_DIR)/lib/"
	chmod +x "$(INSTALL_DIR)/search.py" "$(INSTALL_DIR)/action.py" "$(INSTALL_DIR)/ui.applescript"

uninstall:
	rm -rf "$(INSTALL_DIR)"
