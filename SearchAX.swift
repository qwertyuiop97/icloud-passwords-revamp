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
    if roleOf(el) == "AXToolbar" { return }
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

private func passwordsApp() -> NSRunningApplication? {
    NSRunningApplication.runningApplications(withBundleIdentifier: "com.apple.Passwords").first
}

private func axApp() -> AXUIElement? {
    passwordsApp().map { AXUIElementCreateApplication($0.processIdentifier) }
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

private func searchField() -> (AXUIElement, AXUIElement)? {
    guard let app = axApp() else { return nil }
    for win in windows(of: app) {
        if windowIsLocked(win) { return nil }
        if let sf = toolbarSearch(win) {
            return (win, sf)
        }
    }
    return nil
}

private func stateToken() -> String {
    if passwordsApp() == nil { return "LOCKED" }
    if searchField() != nil { return "UNLOCKED" }
    return "LOCKED"
}

private func emitRows(win: AXUIElement) {
    guard let outline = pickOutline(win), numberOfChildren(outline) > 0 else {
        fputs("EMPTY\n", stdout)
        return
    }
    fputs("OK\n", stdout)
    for row in children(outline).prefix(20) {
        if let line = rowLine(row) {
            fputs(line + "\n", stdout)
        }
    }
}

func main() {
    if !AXIsProcessTrusted() {
        fputs("NEED_AX\n", stdout)
        return
    }
    let args = CommandLine.arguments.dropFirst().map { $0 }
    if args.first == "--state" {
        fputs(stateToken() + "\n", stdout)
        return
    }
    let query = args.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
    guard !query.isEmpty else {
        fputs("EMPTY\n", stdout)
        return
    }
    guard let (win, search) = searchField() else {
        fputs("LOCKED\n", stdout)
        return
    }
    AXUIElementSetAttributeValue(search, kAXValueAttribute as CFString, query as CFString)
    usleep(180_000)
    var current = win
    if let app = axApp(), let next = windows(of: app).first {
        current = next
    }
    emitRows(win: current)
}

main()
