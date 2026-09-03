# iCloud Passwords Revamp

Alfred 5 workflow for Apple’s Passwords app on macOS Sequoia, Tahoe, and Golden Gate.

Type `pw arizona` and matching logins appear under the query. The main text is the email or user name. The subtitle is the app, website, or URL. Return fills the login form in front of you.

This is an independent workflow, not a fork. It has to work for whoever installs it, against **their** iCloud Passwords vault. It never ships anyone’s logins.

## What ↩ does on a login page

On a page like University WebAuth (NetID + Password):

1. Type `pw arizona`
2. Pick the row whose main text is the right email / NetID
3. Return fills **NetID**, then **Password**

It will not paste a password into the NetID / email / user name field.

If only a user name field is focused, it fills the user name. If only a password field is focused, it fills the password.

## Setup

- macOS Sequoia 15 or later
- Alfred 5 with the Powerpack
- System Settings → Privacy & Security → Accessibility → **Alfred**
- Unlock Passwords with Touch ID the first time a search needs the vault

## Install

Download `iCloud-Passwords-Revamp.alfredworkflow` from
[Releases](https://github.com/qwertyuiop97/icloud-passwords-revamp/releases)
and double-click it.

From source:

```sh
python3 build.py
open dist/iCloud-Passwords-Revamp.alfredworkflow
```

## Use

| Input | Result |
| --- | --- |
| `pw` | Suggests logins for the current browser tab when possible |
| `pw arizona` | Every saved login whose site, URL, or email matches |
| ↩ | Fill user name then password |
| ⌘↩ | Copy password (marked concealed for clipboard history) |
| ⌥↩ | Copy verification code |
| ⌃↩ | Copy user name |
| ⇧↩ | Reveal the item in Passwords |

## Preferences

1. **Search keyword** (default `pw`)
2. **Current tab** — suggest logins for the open browser tab
3. **Fill both fields** — user name and password together on login forms
4. **Close after fill**

## Safety

- Password text never enters the Python process
- Alfred results contain site + user name only
- Paste of a password is refused unless the focused field is a password field
- Clipboard password copies are stamped `org.nspasteboard.ConcealedType`
- The clipboard is cleared after an auto-fill of a password

## Development

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -v
python3 build.py
```
