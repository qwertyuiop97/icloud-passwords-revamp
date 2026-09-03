#!/usr/bin/osascript
-- Drive the Passwords app (macOS Sequoia / Tahoe / Golden Gate) from Alfred.
-- Apple does not expose iCloud Keychain logins to `security` or AppleScript,
-- so this uses Accessibility, the Search field, and Edit-menu copy commands.

on envOr(n, fallback)
	set v to ""
	try
		set v to (system attribute n)
	end try
	if v is missing value or v is "" then return fallback
	return v
end envOr

on splitTab(s)
	set oldTID to AppleScript's text item delimiters
	set AppleScript's text item delimiters to tab
	set xs to text items of s
	set AppleScript's text item delimiters to oldTID
	return xs
end splitTab

on notify(theTitle, theMessage)
	display notification theMessage with title theTitle
end notify

on passwordsInstalled()
	return (do shell script "[ -d /System/Applications/Passwords.app ] && echo 1 || echo 0") is "1"
end passwordsInstalled

on openAccessibilitySettings()
	try
		do shell script "open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'"
	end try
end openAccessibilitySettings

on ensureAccessibility()
	try
		tell application "System Events"
			tell (first process whose frontmost is true)
				get UI elements
			end tell
		end tell
	on error errMsg number errNum
		if errNum is -1719 or errNum is -25211 or errNum is -25204 then
			openAccessibilitySettings()
			notify("Accessibility required", "Enable Alfred (and osascript if listed) in System Settings → Privacy & Security → Accessibility, then run this again.")
			error "Accessibility permission required" number errNum
		end if
		error errMsg number errNum
	end try
end ensureAccessibility

on clickMenuItemNamed(procName, itemName)
	if itemName is "" then return false
	tell application "System Events"
		tell process procName
			set frontmost to true
			repeat with mb in menu bar items of menu bar 1
				try
					tell menu 1 of mb
						if exists menu item itemName then
							set mi to menu item itemName
							if enabled of mi then
								click mi
								return true
							else
								return false
							end if
						end if
					end tell
				end try
			end repeat
		end tell
	end tell
	return false
end clickMenuItemNamed

on clickFirstNamed(procName, theName)
	if theName is "" then return false
	tell application "System Events"
		tell process procName
			if not (exists window 1) then return false
			tell window 1
				try
					click (first button whose name is theName)
					return true
				end try
				try
					click (first UI element of entire contents whose name is theName)
					return true
				end try
			end tell
		end tell
	end tell
	return false
end clickFirstNamed

on findSearchField(procName)
	try
		with timeout of 3 seconds
			tell application "System Events"
				tell process procName
					if not (exists window 1) then return missing value
					tell window 1
						try
							if exists (first text field whose subrole is "AXSearchField") then
								return first text field whose subrole is "AXSearchField"
							end if
						end try
						try
							set cands to (every text field of entire contents whose subrole is "AXSearchField")
							if (count of cands) > 0 then return item 1 of cands
						end try
					end tell
				end tell
			end tell
		end timeout
	end try
	return missing value
end findSearchField

on waitForUnlock(procName, unlockName)
	set unlocked to false
	set prompted to false
	repeat 150 times
		set sf to findSearchField(procName)
		if sf is not missing value then
			set unlocked to true
			exit repeat
		end if
		if not prompted then
			notify("Passwords", "Unlock Passwords with Touch ID or your password if asked.")
			set prompted to true
		end if
		tell application "System Events"
			if not (exists process procName) then
				delay 0.3
			else
				tell process procName
					set frontmost to true
					if exists window 1 then
						try
							if exists (button unlockName of window 1) then
								click button unlockName of window 1
							end if
						end try
					end if
				end tell
			end if
		end tell
		set sf to findSearchField(procName)
		if sf is not missing value then
			set unlocked to true
			exit repeat
		end if
		delay 0.3
	end repeat
	if not unlocked then
		notify("Unlock timed out", "Unlock Passwords, then run the keyword again.")
		error "Timed out waiting for Passwords to unlock" number 1
	end if
end waitForUnlock

on focusSearch(procName, searchName, theQuery)
	tell application "System Events"
		tell process procName
			set frontmost to true
		end tell
	end tell
	clickMenuItemNamed(procName, searchName)
	delay 0.12
	tell application "System Events"
		tell process procName
			keystroke "f" using command down
		end tell
	end tell
	delay 0.12
	set sf to findSearchField(procName)
	if sf is missing value then error "Could not find the Passwords search field" number 2
	tell application "System Events"
		tell process procName
			set frontmost to true
			try
				set focused of sf to true
			end try
			delay 0.08
			set value of sf to theQuery
			delay 0.08
			-- Nudge SwiftUI so the filter actually runs after an AX value set.
			key code 49
			delay 0.05
			key code 51
		end tell
	end tell
	delay 0.35
end focusSearch

on selectFirstResult(procName)
	tell application "System Events"
		tell process procName
			set frontmost to true
			try
				tell window 1
					set tbls to every table of entire contents
					if (count of tbls) > 0 then
						tell item 1 of tbls
							if (count of rows) ≥ 1 then
								set selected of row 1 to true
								click row 1
								delay 0.2
								return
							end if
						end tell
					end if
				end tell
			end try
			try
				tell window 1
					set outlines to every outline of entire contents
					if (count of outlines) > 0 then
						tell item 1 of outlines
							if (count of rows) ≥ 1 then
								set selected of row 1 to true
								click row 1
								delay 0.2
								return
							end if
						end tell
					end if
				end tell
			end try
			key code 125
			delay 0.12
			key code 36
			delay 0.25
		end tell
	end tell
end selectFirstResult

on run argv
	with timeout of 90 seconds
		if (count of argv) < 1 then error "usage: mode [query] [titles]"
		set mode to item 1 of argv
		set theQuery to ""
		if (count of argv) ≥ 2 then set theQuery to item 2 of argv
		set titlesRaw to ""
		if (count of argv) ≥ 3 then set titlesRaw to item 3 of argv
		
		set copyPassword to "Copy Password"
		set copyUserName to "Copy User Name"
		set copyCode to "Copy Code"
		set searchName to "Search"
		set unlockName to "Unlock"
		set allPasswordsName to "All Passwords"
		if titlesRaw is not "" then
			set titleParts to splitTab(titlesRaw)
			if (count of titleParts) ≥ 1 then set copyPassword to item 1 of titleParts
			if (count of titleParts) ≥ 2 then set copyUserName to item 2 of titleParts
			if (count of titleParts) ≥ 3 then set copyCode to item 3 of titleParts
			if (count of titleParts) ≥ 4 then set searchName to item 4 of titleParts
			if (count of titleParts) ≥ 5 then set unlockName to item 5 of titleParts
			if (count of titleParts) ≥ 6 then set allPasswordsName to item 6 of titleParts
		end if
		
		set closeAfter to (envOr("close_after_copy", "1") is "1")
		
		if not passwordsInstalled() then
			notify("Passwords app missing", "This workflow needs the Passwords app (macOS Sequoia or later).")
			return
		end if
		
		if theQuery is "" and mode is not "find" then
			notify("Query required", "Type a site or account name after the keyword.")
			return
		end if
		
		with timeout of 8 seconds
			ensureAccessibility()
		end timeout
		
		tell application "Passwords" to activate
		delay 0.2
		
		tell application "System Events"
			repeat 50 times
				if exists process "Passwords" then exit repeat
				delay 0.1
			end repeat
			if not (exists process "Passwords") then error "Passwords did not launch" number 3
		end tell
		
		waitForUnlock("Passwords", unlockName)
		try
			clickFirstNamed("Passwords", allPasswordsName)
			delay 0.15
		end try
		focusSearch("Passwords", searchName, theQuery)
		
		if mode is "find" then return
		
		selectFirstResult("Passwords")
		delay 0.25
		
		set copied to false
		if mode is "password" then
			set copied to clickMenuItemNamed("Passwords", copyPassword)
			if copied then
				notify("Password copied", theQuery)
			else
				notify("No entry found", "No password matched “" & theQuery & "”.")
			end if
		else if mode is "otp" then
			set copied to clickMenuItemNamed("Passwords", copyCode)
			if not copied then set copied to clickMenuItemNamed("Passwords", "Copy Verification Code")
			if copied then
				notify("Copied verification code", theQuery)
			else
				notify("No verification code", "The first result for “" & theQuery & "” has no OTP, or nothing matched.")
			end if
		else if mode is "username" then
			set copied to clickMenuItemNamed("Passwords", copyUserName)
			if copied then
				notify("User name copied", theQuery)
			else
				notify("No entry found", "No user name matched “" & theQuery & "”.")
			end if
		else
			error "Unknown mode: " & mode number 4
		end if
		
		if copied and closeAfter then
			tell application "Passwords" to quit
		end if
	end timeout
end run
