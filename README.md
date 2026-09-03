# iCloud Passwords for Alfred

Alfred 5 workflow for Apple’s Passwords app on macOS Sequoia, Tahoe, and Golden Gate.

Search a site or account, then copy the first matching password, user name, or verification code.

Apple does not expose iCloud Keychain logins to `security`, AppleScript, or Shortcuts. This workflow opens Passwords, waits for Touch ID, searches, and uses the app’s own **Copy Password**, **Copy User Name**, and **Copy Code** menu commands.

This is an independent project. It is not a fork of older Safari preference-pane workflows, which Apple removed.

## Requirements

- macOS Sequoia 15 or later, including Tahoe and Golden Gate
- Alfred 5 with the Powerpack
- Accessibility permission for Alfred
- iCloud Keychain signed in

## Install

Download `iCloud-Passwords.alfredworkflow` from [Releases](https://github.com/qwertyuiop97/alfred-icloud-passwords/releases) and double-click it.

From source:

```sh
python3 build.py
open dist/iCloud-Passwords.alfredworkflow
```

On first use, unlock Passwords with Touch ID if asked, and allow Alfred to control the computer.

## Usage

| Keyword | Action |
| --- | --- |
| `p github` | Open Passwords and search for `github` |
| `fp github` | Copy the first result’s password and quit Passwords |
| `otp github` | Copy the first result’s verification code and quit Passwords |

Modifiers on `p`:

- **⌘↩** copy password
- **⌥↩** copy verification code
- **⌃↩** copy user name

## Preferences

Configure Workflow has four settings:

1. **Search keyword** (default `p`)
2. **Copy password keyword** (default `fp`)
3. **Copy OTP keyword** (default `otp`)
4. **Close after copy** (on by default)

## Permissions

System Settings → Privacy & Security → Accessibility → enable **Alfred**. If a prompt names `osascript`, enable that too.

The workflow never reads the keychain. It only drives the Passwords UI after you unlock it.

## Development

```sh
python3 build.py
make install
python3 titles.py
```
