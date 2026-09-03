.PHONY: build install uninstall check

ALFRED_WORKFLOWS := $(HOME)/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows
INSTALL_DIR := $(ALFRED_WORKFLOWS)/user.workflow.icloud-passwords-2026

build:
	python3 build.py

check:
	python3 -m py_compile titles.py build.py
	python3 titles.py >/dev/null
	plutil -lint info.plist
	osacompile -o /tmp/icloud-passwords-check.scpt passwords.applescript
	rm -f /tmp/icloud-passwords-check.scpt

install: build check
	mkdir -p "$(INSTALL_DIR)"
	cp -f info.plist passwords.applescript titles.py icon.png "$(INSTALL_DIR)/"
	chmod +x "$(INSTALL_DIR)/titles.py" "$(INSTALL_DIR)/run.sh" "$(INSTALL_DIR)/passwords.applescript"

uninstall:
	rm -rf "$(INSTALL_DIR)"
