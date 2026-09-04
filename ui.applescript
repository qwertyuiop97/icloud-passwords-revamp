#!/usr/bin/osascript
-- UI bridge for the iCloud Passwords Revamp Alfred workflow.
-- Never print a password, OTP, or field value.

on alfredNames()
	return {"Alfred", "Alfred 5", "Alfred 4", "Alfred Preferences"}
end alfredNames

on isAlfred(procName)
	repeat with n in alfredNames()
		if procName is (n as string) then return true
	end repeat
	return false
end isAlfred

on notify(theTitle, theMessage)
	display notification theMessage with title theTitle
end notify

on passwordsInstalled()
	return (do shell script "[ -d /System/Applications/Passwords.app ] && echo 1 || echo 0") is "1"
end passwordsInstalled

on refocusAlfred()
	tell application "System Events"
		repeat with n in my alfredNames()
			try
				if exists process (n as string) then
					set frontmost of process (n as string) to true
					return
				end if
			end try
		end repeat
	end tell
end refocusAlfred

on clickUnlock()
	tell application "System Events"
		tell process "Passwords"
			if not (exists window 1) then return false
			tell window 1
				try
					if exists button "Unlock" then
						click button "Unlock"
						return true
					end if
				end try
			end tell
		end tell
	end tell
	return false
end clickUnlock

on launchPasswordsHidden()
	do shell script "/usr/bin/open -g -a Passwords"
	tell application "System Events"
		repeat 40 times
			if exists process "Passwords" then exit repeat
			delay 0.1
		end repeat
	end tell
end launchPasswordsHidden

on hidePasswords()
	tell application "System Events"
		try
			set visible of process "Passwords" to false
		end try
	end tell
end hidePasswords

on raisePasswordsForAX()
	tell application "System Events"
		tell process "Passwords"
			try
				set visible to true
			end try
			set frontmost to true
		end tell
	end tell
end raisePasswordsForAX

on findSearchField()
	tell application "System Events"
		tell process "Passwords"
			if not (exists window 1) then return missing value
			try
				return text field 1 of group 2 of toolbar 1 of window 1
			end try
		end tell
	end tell
	return missing value
end findSearchField

on clickMenuItemNamed(itemName)
	tell application "System Events"
		tell process "Passwords"
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

on setSearch(theQuery)
	set sf to findSearchField()
	if sf is missing value then return false
	tell application "System Events"
		tell process "Passwords"
			-- Do not keystroke. That would type into Alfred if it is frontmost.
			try
				set value of attribute "AXFocused" of sf to true
			end try
			set value of sf to theQuery
			try
				perform action "AXConfirm" of sf
			end try
		end tell
	end tell
	delay 0.35
	return true
end setSearch

on collectRows()
	set collected to {}
	tell application "System Events"
		tell process "Passwords"
			tell outline 1 of scroll area 1 of group 2 of splitter group 1 of group 1 of window 1
				set n to count of rows
				if n > 40 then set n to 40
				repeat with i from 1 to n
					try
						tell UI element 1 of row i
							set siteName to (get value of static text 1) as string
							set userName to ""
							try
								set userName to (get value of static text 2) as string
							end try
							if siteName is not "" then set end of collected to siteName & tab & userName
						end tell
					end try
				end repeat
			end tell
		end tell
	end tell
	return collected
end collectRows

on selectFirstRow()
	tell application "System Events"
		tell process "Passwords"
			try
				tell outline 1 of scroll area 1 of group 2 of splitter group 1 of group 1 of window 1
					if (count of rows) ≥ 1 then
						select row 1
						click row 1
						delay 0.2
						return true
					end if
				end tell
			end try
		end tell
	end tell
	return false
end selectFirstRow

on copyKind(kind)
	set names to {}
	if kind is "username" then
		set names to {"Copy User Name", "Copy Username"}
	else if kind is "password" then
		set names to {"Copy Password"}
	else if kind is "otp" then
		set names to {"Copy Code", "Copy Verification Code"}
	end if
	repeat with n in names
		if clickMenuItemNamed(n as string) then return true
	end repeat
	return false
end copyKind

on prepareAccount(titleText, userText)
	launchPasswordsHidden()
	set q to titleText
	if userText is not "" then set q to titleText & " " & userText
	if not setSearch(q) then return "LOCKED"
	selectFirstRow()
	return "OK"
end prepareAccount

on inspectFrontFields()
	set out to ""
	tell application "System Events"
		set procName to name of first application process whose frontmost is true
		if my isAlfred(procName) then error "frontmost is Alfred"
		tell process procName
			if not (exists window 1) then return "STATUS" & tab & "NO_WINDOW"
			tell window 1
				with timeout of 4 seconds
					set flds to {}
					try
						set flds to every text field of entire contents
					end try
					repeat with f in flds
						set focusedFlag to "false"
						try
							if focused of f then set focusedFlag to "true"
						end try
						set r to ""
						set sr to ""
						set nm to ""
						set dsc to ""
						set ph to ""
						set ident to ""
						try
							set r to role of f as string
						end try
						try
							set sr to subrole of f as string
						end try
						try
							set nm to name of f as string
						end try
						try
							set dsc to description of f as string
						end try
						try
							set ph to (value of attribute "AXPlaceholderValue" of f) as string
						end try
						try
							set ident to (value of attribute "AXIdentifier" of f) as string
						end try
						-- Never emit the field value.
						set out to out & r & tab & sr & tab & nm & tab & dsc & tab & ph & tab & ident & tab & focusedFlag & linefeed
					end repeat
				end timeout
			end tell
		end tell
	end tell
	return out
end inspectFrontFields

on focusedIsSecure()
	tell application "System Events"
		set procName to name of first application process whose frontmost is true
		tell process procName
			tell window 1
				try
					set f to first text field whose focused is true
					try
						if subrole of f is "AXSecureTextField" then return true
					end try
					try
						if role of f is "AXSecureTextField" then return true
					end try
				end try
			end tell
		end tell
	end tell
	return false
end focusedIsSecure

on doPaste(kind)
	tell application "System Events"
		set procName to name of first application process whose frontmost is true
		if my isAlfred(procName) then error "refusing to paste into Alfred"
		set secure to my focusedIsSecure()
		if kind is "password" then
			if not secure then error "refusing to paste password into a non-password field"
		else if kind is "username" then
			if secure then error "refusing to paste user name into a password field"
		end if
		keystroke "a" using command down
		delay 0.05
		keystroke "v" using command down
	end tell
	return "OK"
end doPaste

on frontmostNonAlfred()
	tell application "System Events"
		set procName to name of first application process whose frontmost is true
		if not my isAlfred(procName) then return procName
		repeat with p in application processes
			try
				if visible of p is true and my isAlfred(name of p as string) is false then
					if (count of windows of p) > 0 then
						-- skip helper processes; prefer ones with a focused window
						try
							if frontmost of p then return name of p as string
						end try
					end if
				end if
			end try
		end repeat
		return procName
	end tell
end frontmostNonAlfred

on stampConcealed()
	do shell script "/usr/bin/osascript -l JavaScript -e 'ObjC.import(\"AppKit\"); const pb = $.NSPasteboard.generalPasteboard; pb.setStringForType(\"\", \"org.nspasteboard.ConcealedType\"); pb.setStringForType(\"\", \"org.nspasteboard.AutoGeneratedType\");'"
end stampConcealed

on clearClip()
	do shell script "/usr/bin/pbcopy </dev/null"
end clearClip

on run argv
	if (count of argv) < 1 then error "usage: mode ..."
	set mode to item 1 of argv
	
	if mode is "search" then
		if not passwordsInstalled() then
			return "NO_APP"
		end if
		set q to ""
		if (count of argv) ≥ 2 then set q to item 2 of argv
		if q is "" then return "EMPTY"
		try
			tell application "System Events" to get UI elements of (first process whose frontmost is true)
		on error
			return "NEED_AX"
		end try
		launchPasswordsHidden()
		try
			with timeout of 4 seconds
				if findSearchField() is missing value then
					raisePasswordsForAX()
					delay 0.2
				end if
				if findSearchField() is missing value then
					-- First-run unlock. Leave Passwords visible for Touch ID.
					return "LOCKED"
				end if
				if not setSearch(q) then return "LOCKED"
				set rows to collectRows()
			end timeout
		on error
			my refocusAlfred()
			return "LOCKED"
		end try
		hidePasswords()
		my refocusAlfred()
		if (count of rows) is 0 then return "EMPTY"
		set out to "OK" & linefeed
		set n to 0
		repeat with rowLine in rows
			set out to out & rowLine & linefeed
			set n to n + 1
			if n ≥ 40 then exit repeat
		end repeat
		return out
	end if
	
	if mode is "inspect" then
		try
			return "OK" & linefeed & inspectFrontFields()
		on error errMsg
			return "ERROR" & linefeed & "STATUS" & tab & "ERROR"
		end try
	end if
	
	if mode is "copy" then
		if (count of argv) < 4 then error "usage: copy kind title username"
		set kind to item 2 of argv
		set titleText to item 3 of argv
		set userText to item 4 of argv
		set prep to prepareAccount(titleText, userText)
		if prep is not "OK" then return prep
		tell application "System Events" to tell process "Passwords" to set frontmost to true
		delay 0.15
		if copyKind(kind) then
			return "OK"
		else
			return "MISS"
		end if
	end if
	
	if mode is "reveal" then
		set titleText to item 2 of argv
		set userText to ""
		if (count of argv) ≥ 3 then set userText to item 3 of argv
		launchPasswordsHidden()
		tell application "Passwords" to activate
		prepareAccount(titleText, userText)
		return "OK"
	end if
	
	if mode is "frontmost" then
		return frontmostNonAlfred()
	end if
	
	if mode is "activate" then
		set appName to item 2 of argv
		tell application "System Events" to tell process appName to set frontmost to true
		return "OK"
	end if
	
	if mode is "paste" then
		return doPaste(item 2 of argv)
	end if
	
	if mode is "conceal" then
		stampConcealed()
		return "OK"
	end if
	
	if mode is "clearclip" then
		clearClip()
		return "OK"
	end if
	
	if mode is "quit" then
		tell application "Passwords" to quit
		return "OK"
	end if
	
	error "unknown mode " & mode
end run
