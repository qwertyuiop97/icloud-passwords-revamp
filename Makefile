.PHONY: build install uninstall check test searchax

ALFRED_WORKFLOWS := $(HOME)/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows
INSTALL_DIR := $(ALFRED_WORKFLOWS)/user.workflow.icloud-passwords-revamp

searchax: SearchAX.swift
	swiftc -O -o searchax SearchAX.swift -framework AppKit -framework ApplicationServices
	codesign --force --sign - --identifier com.qwertyuiop97.icloud-passwords-revamp.searchax searchax

build:
	python3 build.py

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -v

check: test
	python3 -m py_compile search.py action.py build.py titles.py lib/*.py tests/*.py
	plutil -lint info.plist
	osacompile -o /tmp/icloud-passwords-revamp-check.scpt ui.applescript
	rm -f /tmp/icloud-passwords-revamp-check.scpt

install: searchax build
	mkdir -p "$(INSTALL_DIR)/lib"
	cp -f info.plist search.py action.py ui.applescript search_ui.js searchax titles.py icon.png "$(INSTALL_DIR)/"
	chmod +x "$(INSTALL_DIR)/searchax" "$(INSTALL_DIR)/search_ui.js"
	cp -f lib/*.py "$(INSTALL_DIR)/lib/"
	chmod +x "$(INSTALL_DIR)/search.py" "$(INSTALL_DIR)/action.py" "$(INSTALL_DIR)/ui.applescript"

uninstall:
	rm -rf "$(INSTALL_DIR)"
