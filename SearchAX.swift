import AppKit
import ApplicationServices
import Foundation

private func attr(_ el: AXUIElement, _ name: String) -> AnyObject? {
    var value: AnyObject?
    let err = AXUIElementCopyAttributeValue(el, name as CFString, &value)
    return err == .success ? value : nil
}

private func str(_ el: AXUIElement, _ name: String) -> String? {
    attr(el, name) as? String
}

private func children(_ el: AXUIElement) -> [AXUIElement] {
    attr(el, kAXChildrenAttribute as String) as? [AXUIElement] ?? []
}

private func roleOf(_ el: AXUIElement) -> String {
    str(el, kAXRoleAttribute as String) ?? ""
}

private func subroleOf(_ el: AXUIElement) -> String {
    str(el, kAXSubroleAttribute as String) ?? ""
}

private func isOutline(_ el: AXUIElement) -> Bool {
    let r = roleOf(el)
    return r == "AXOutline" || r == "AXTable" || r == "AXList"
}

private func numberOfChildren(_ el: AXUIElement) -> Int {
    if let n = attr(el, "AXNumberOfChildren") as? NSNumber {
        return n.intValue
    }
    return children(el).count
}

private func findSearchField(_ el: AXUIElement, depth: Int = 0) -> AXUIElement? {
    if depth > 6 { return nil }
    if isOutline(el) { return nil }
    let role = roleOf(el)
    if role == "AXSplitGroup" { return nil }
    let sub = subroleOf(el)
    if role == "AXSearchField" || sub == "AXSearchField" {
        return el
    }
    if role == "AXTextField" {
        let desc = str(el, kAXDescriptionAttribute as String) ?? ""
        let ph = str(el, "AXPlaceholderValue") ?? ""
        let blob = (desc + " " + ph).lowercased()
        if blob.contains("search") || sub.isEmpty {
            return el
        }
    }
    for child in children(el) {
        if let hit = findSearchField(child, depth: depth + 1) {
            return hit
        }
    }
    return nil
}

private func toolbarSearch(_ win: AXUIElement) -> AXUIElement? {
    for child in children(win) {
        if roleOf(child) == "AXToolbar" {
            if let sf = findSearchField(child) {
                return sf
            }
        }
    }
    return nil
}

private func findOutlines(_ el: AXUIElement, depth: Int = 0, limit: Int = 8, into out: inout [AXUIElement]) {
    if depth > 8 || out.count >= limit { return }
    if isOutline(el) {
        out.append(el)
        return
    }
    let role = roleOf(el)
    if role == "AXToolbar" { return }
    for child in children(el) {
        if isOutline(child) {
            out.append(child)
            if out.count >= limit { return }
            continue
        }
        findOutlines(child, depth: depth + 1, limit: limit, into: &out)
        if out.count >= limit { return }
    }
}

private func windows(of app: AXUIElement) -> [AXUIElement] {
    attr(app, kAXWindowsAttribute as String) as? [AXUIElement] ?? []
}

private func rowLine(_ row: AXUIElement) -> String? {
    var texts: [String] = []
    func collect(_ el: AXUIElement, depth: Int) {
        if depth > 5 || texts.count >= 2 { return }
        if roleOf(el) == "AXStaticText" {
            if let v = str(el, kAXValueAttribute as String), !v.isEmpty {
                texts.append(v)
            } else if let v = str(el, kAXTitleAttribute as String), !v.isEmpty {
                texts.append(v)
            }
        }
        for child in children(el) {
            collect(child, depth: depth + 1)
        }
    }
    collect(row, depth: 0)
    guard let site = texts.first, !site.isEmpty else { return nil }
    let user = texts.count > 1 ? texts[1] : ""
    return "\(site)\t\(user)"
}

private func isLockPhrase(_ text: String) -> Bool {
    let t = text.lowercased()
    return t.contains("passwords is locked") || t.contains("touch id or enter your password")
}

private func isLocked(_ el: AXUIElement, depth: Int = 0) -> Bool {
    if depth > 8 { return false }
    if isOutline(el) { return false }
    if roleOf(el) == "AXStaticText" {
        let v = str(el, kAXValueAttribute as String)
            ?? str(el, kAXTitleAttribute as String)
            ?? ""
        if isLockPhrase(v) { return true }
    }
    for child in children(el) {
        if isLocked(child, depth: depth + 1) { return true }
    }
    return false
}

private func pressUnlock(_ el: AXUIElement, depth: Int = 0) -> Bool {
    if depth > 8 { return false }
    if isOutline(el) { return false }
    if roleOf(el) == "AXButton" {
        let sub = subroleOf(el)
        if !sub.contains("Close") && !sub.contains("FullScreen") && !sub.contains("Minimize")
            && !sub.contains("Zoom")
        {
            return AXUIElementPerformAction(el, kAXPressAction as CFString) == .success
        }
    }
    for child in children(el) {
        if pressUnlock(child, depth: depth + 1) { return true }
    }
    return false
}

private func commandF() {
    let src = CGEventSource(stateID: .hidSystemState)
    let down = CGEvent(keyboardEventSource: src, virtualKey: 0x03, keyDown: true)
    let up = CGEvent(keyboardEventSource: src, virtualKey: 0x03, keyDown: false)
    down?.flags = .maskCommand
    up?.flags = .maskCommand
    down?.post(tap: .cghidEventTap)
    up?.post(tap: .cghidEventTap)
}

private func promptTrust() -> Bool {
    if AXIsProcessTrusted() { return true }
    let key = kAXTrustedCheckOptionPrompt.takeUnretainedValue()
    AXIsProcessTrustedWithOptions([key: true] as CFDictionary)
    return AXIsProcessTrusted()
}

private func passwordsApp() -> NSRunningApplication? {
    NSRunningApplication.runningApplications(withBundleIdentifier: "com.apple.Passwords").first
}

private func launchPasswords() {
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/bin/open")
    task.arguments = ["-g", "-a", "Passwords"]
    try? task.run()
    task.waitUntilExit()
}

private func activatePasswords() {
    if passwordsApp() == nil {
        launchPasswords()
        usleep(350_000)
    }
    guard let running = passwordsApp() else { return }
    running.unhide()
    running.activate()
    let script = NSAppleScript(
        source: "tell application \"System Events\" to set frontmost of process \"Passwords\" to true"
    )
    script?.executeAndReturnError(nil)
    usleep(150_000)
}

private func axApp() -> AXUIElement? {
    passwordsApp().map { AXUIElementCreateApplication($0.processIdentifier) }
}

private func activateAlfred() {
    let ids = ["com.runningwithcrayons.Alfred", "com.runningwithcrayons.Alfred-3"]
    for id in ids {
        if let app = NSRunningApplication.runningApplications(withBundleIdentifier: id).first {
            app.activate()
            return
        }
    }
}

private func windowIsLocked(_ win: AXUIElement) -> Bool {
    let kids = children(win)
    if kids.contains(where: { roleOf($0) == "AXToolbar" }) {
        return false
    }
    return kids.contains { isLocked($0) }
}

private func pickOutline(_ win: AXUIElement) -> AXUIElement? {
    var outlines: [AXUIElement] = []
    findOutlines(win, into: &outlines)
    return outlines.max(by: { numberOfChildren($0) < numberOfChildren($1) })
}

func main() {
    if !promptTrust() {
        fputs("NEED_AX\n", stdout)
        return
    }
    let query = CommandLine.arguments.dropFirst().joined(separator: " ")
        .trimmingCharacters(in: .whitespacesAndNewlines)
    guard !query.isEmpty else {
        fputs("EMPTY\n", stdout)
        return
    }

    activatePasswords()
    var search: AXUIElement?
    var win: AXUIElement?

    for step in 0..<12 {
        guard let app = axApp() else {
            usleep(80_000)
            continue
        }
        let wins = windows(of: app)
        for candidate in wins {
            if windowIsLocked(candidate) {
                _ = pressUnlock(candidate)
                continue
            }
            if let sf = toolbarSearch(candidate) {
                search = sf
                win = candidate
                break
            }
        }
        if search != nil { break }
        if step == 4 {
            activatePasswords()
        }
        if step == 8 {
            activatePasswords()
            commandF()
        }
        usleep(80_000)
    }

    guard let search, let win else {
        activateAlfred()
        fputs("LOCKED\n", stdout)
        return
    }

    AXUIElementSetAttributeValue(search, kAXFocusedAttribute as CFString, kCFBooleanTrue)
    AXUIElementSetAttributeValue(search, kAXValueAttribute as CFString, query as CFString)
    usleep(180_000)

    var outline = pickOutline(win)
    if outline == nil || numberOfChildren(outline!) == 0 {
        usleep(180_000)
        if let app = axApp(), let current = windows(of: app).first {
            outline = pickOutline(current)
        }
    }
    guard let outline, numberOfChildren(outline) > 0 else {
        activateAlfred()
        fputs("EMPTY\n", stdout)
        return
    }

    let rows = children(outline)
    fputs("OK\n", stdout)
    var n = 0
    for row in rows.prefix(20) {
        if let line = rowLine(row) {
            fputs(line + "\n", stdout)
            n += 1
        }
    }
    activateAlfred()
}

main()
