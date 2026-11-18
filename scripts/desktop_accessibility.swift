// Native smoke-test driver. All reads and actions target the specified disposable launcher PID.
import AppKit
import ApplicationServices
import Foundation
let argv = CommandLine.arguments
guard argv.count >= 3, let pid = Int32(argv[1]) else { exit(2) }
guard AXIsProcessTrusted() else {
    FileHandle.standardError.write(Data("Accessibility access is required for the native test.\n".utf8))
    exit(3)
}
let running = NSRunningApplication(processIdentifier: pid)
_ = running?.activate(options: [])
Thread.sleep(forTimeInterval: 0.25)
let app = AXUIElementCreateApplication(pid)
func value(_ element: AXUIElement, _ key: CFString) -> CFTypeRef? {
    var result: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, key, &result) == .success else { return nil }
    return result
}
func nodes(_ element: AXUIElement, _ depth: Int = 0) -> [AXUIElement] {
    if depth > 25 { return [] }
    let children = value(element, kAXChildrenAttribute as CFString) as? [AXUIElement] ?? []
    return [element] + children.flatMap { nodes($0,depth+1) }
}
_ = AXUIElementSetAttributeValue(app,"AXEnhancedUserInterface" as CFString,kCFBooleanTrue)
let children = value(app,kAXChildrenAttribute as CFString) as? [AXUIElement] ?? []
let windows = children.filter { value($0,kAXRoleAttribute as CFString) as? String == "AXWindow" }
let all = windows.flatMap { nodes($0) }
func matches(_ e: AXUIElement, _ needle: String) -> Bool {
    [kAXTitleAttribute,kAXDescriptionAttribute,kAXValueAttribute].contains {
        (value(e,$0 as CFString) as? String) == needle
    }
}
let command = argv[2]
if command == "tree" {
    for e in all {
        let role = value(e,kAXRoleAttribute as CFString) as? String ?? ""
        let name = [kAXTitleAttribute,kAXDescriptionAttribute,kAXValueAttribute].compactMap{value(e,$0 as CFString) as? String}.joined(separator:" ")
        if !name.isEmpty && !name.contains("session=") {print(role + " " + String(name.prefix(130)))}
    }
    exit(0)
}
guard argv.count > 3 else { exit(2) }
if command == "key" {
    guard let key = UInt16(argv[3]) else{exit(2)}
    let flags: CGEventFlags = argv.count>4 && argv[4]=="path" ? [.maskCommand,.maskShift] : []
    for down in [true,false] {
        let ev=CGEvent(keyboardEventSource:nil,virtualKey:key,keyDown:down)!
        ev.flags=flags;ev.postToPid(pid)
    }
    exit(0)
}
if command == "type" {
    let chars=Array(argv[3].utf16)
    let ev=CGEvent(keyboardEventSource:nil,virtualKey:0,keyDown:true)!
    chars.withUnsafeBufferPointer{ev.keyboardSetUnicodeString(stringLength:$0.count,unicodeString:$0.baseAddress)}
    ev.postToPid(pid)
    let up=CGEvent(keyboardEventSource:nil,virtualKey:0,keyDown:false)!
    up.postToPid(pid)
    exit(0)
}
guard let target = all.first(where:{ matches($0,argv[3]) }) else { exit(1) }
if command == "press" {exit(AXUIElementPerformAction(target,kAXPressAction as CFString) == .success ? 0:4)}
exit(0)
