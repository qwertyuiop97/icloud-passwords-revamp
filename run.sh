#!/bin/zsh
# Alfred Run Script entry point. cwd is the workflow folder.
set -euo pipefail

mode="${mode:-find}"
query="${1-}"

titles="$(/usr/bin/python3 ./titles.py)"
/usr/bin/osascript ./passwords.applescript "$mode" "$query" "$titles"
