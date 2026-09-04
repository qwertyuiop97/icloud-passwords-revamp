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

private func find(
    _ el: AXUIElement,
    role: String,
    subrole: String? = nil,
    depth: Int = 0
) -> AXUIElement? {
    if depth > 14 { return nil }
    if str(el, kAXRoleAttribute as String) == role {
        if subrole == nil || str(el, kAXSubroleAttribute as String) == subrole {
            return el
        }
    }
    for child in children(el) {
        if let hit = find(child, role: role, subrole: subrole, depth: depth + 1) {
            return hit
        }
    }
    return nil
}

private func findAll(
    _ el: AXUIElement,
    role: String,
    depth: Int = 0,
    limit: Int = 8,
    into out: inout [AXUIElement]
) {
    if depth > 12 || out.count >= limit { return }
    if str(el, kAXRoleAttribute as String) == role {
        out.append(el)
        if out.count >= limit { return }
    }
    for child in children(el) {
        findAll(child, role: role, depth: depth + 1, limit: limit, into: &out)
        if out.count >= limit { return }
    }
}

private func passwordsElement() -> AXUIElement? {
    let running = NSRunningApplication.runningApplications(withBundleIdentifier: "com.apple.Passwords")
    if let app = running.first {
        return AXUIElementCreateApplication(app.processIdentifier)
    }
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/bin/open")
    task.arguments = ["-g", "-a", "Passwords"]
    try? task.run()
    task.waitUntilExit()
    usleep(350_000)
    return NSRunningApplication.runningApplications(withBundleIdentifier: "com.apple.Passwords")
        .first
        .map { AXUIElementCreateApplication($0.processIdentifier) }
}

private func window(_ app: AXUIElement) -> AXUIElement? {
    let wins = attr(app, kAXWindowsAttribute as String) as? [AXUIElement]
    return wins?.first
}

private func rowLine(_ row: AXUIElement) -> String? {
    var texts: [String] = []
    func collect(_ el: AXUIElement, depth: Int) {
        if depth > 5 || texts.count >= 2 { return }
        if str(el, kAXRoleAttribute as String) == "AXStaticText" {
            if let v = str(el, kAXValueAttribute as String), !v.isEmpty {
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

func main() {
    let query = CommandLine.arguments.dropFirst().joined(separator: " ")
        .trimmingCharacters(in: .whitespacesAndNewlines)
    guard !query.isEmpty else {
        fputs("EMPTY\n", stdout)
        return
    }
    guard let app = passwordsElement(), let win = window(app) else {
        fputs("LOCKED\n", stdout)
        return
    }
    guard let search = find(win, role: "AXTextField", subrole: "AXSearchField") else {
        fputs("LOCKED\n", stdout)
        return
    }
    AXUIElementSetAttributeValue(search, kAXValueAttribute as CFString, query as CFString)
    usleep(180_000)
    var outlines: [AXUIElement] = []
    findAll(win, role: "AXOutline", limit: 12, into: &outlines)
    let outline = outlines.max(by: { children($0).count < children($1).count })
    guard let outline, children(outline).count > 0 else {
        fputs("EMPTY\n", stdout)
        return
    }
    let rows = children(outline)
    if ProcessInfo.processInfo.environment["SEARCHAX_DEBUG"] != nil {
        fputs("outlines=\(outlines.count) rows=\(rows.count)\n", stderr)
    }
    fputs("OK\n", stdout)
    var n = 0
    for row in rows {
        if n >= 20 { break }
        if let line = rowLine(row) {
            fputs(line + "\n", stdout)
            n += 1
        }
    }
}

main()
