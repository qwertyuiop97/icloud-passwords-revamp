"""Passwords.app lock session. Search never hides or quits the app.

Measured on this host: the Passwords UI re-locks (no toolbar) while the
process is still running and the window is still visible but not frontmost.
com.apple.Passwords has no AutoLockTime (or similar) default. The login
keychain is no-timeout, which does not keep the Passwords UI unlocked.
sysadminctl reports screenLock delay is immediate.

There is no public API to keep the vault unlocked in the background.
Fill on Return may raise Passwords and can hit Touch ID after that UI lock.
"""

KEEP_RUNNING = True
NEVER_HIDE_ON_SEARCH = True
# Search metadata cache is only used after a live UNLOCKED probe.
SEARCH_CACHE_REQUIRES_UNLOCKED = True
