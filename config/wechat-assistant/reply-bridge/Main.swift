import Cocoa
import ScreenCaptureKit
import CryptoKit

let base=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".local/share/wechat-assistant")
let nativeAttempt=UUID().uuidString
@MainActor var nativeLastPhase="not_started"
@MainActor func nativeStage(_ phase:String,_ fields:[String:Any]=[:]) throws {
    let folder=base.appendingPathComponent("capture-diagnostics",isDirectory:true)
    try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
    var value=fields;value["phase"]=phase;value["previous_phase"]=nativeLastPhase;nativeLastPhase=phase;value["at"]=ISO8601DateFormatter().string(from:Date())
    value["foreground"]=NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "unknown"
    let file=folder.appendingPathComponent("native-"+nativeAttempt+".json")
    try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]).write(to:file,options:.atomic)
    try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:file.path)
}
func object(_ url:URL) throws -> [String:Any] {
    guard let value=try JSONSerialization.jsonObject(with:Data(contentsOf:url)) as? [String:Any] else { throw fail("invalid_local_object") }
    return value
}
func config() throws -> [String:Any] {try object(base.appendingPathComponent("reader-config.json"))}
func queue(_ action:String,code:String,reason:String="") throws -> [String:Any] {
    let c=try config();guard let python=c["python"] as? String else {throw fail("python_not_configured")}
    let p=Process();p.executableURL=URL(fileURLWithPath:python)
    p.arguments=[base.appendingPathComponent("reply-bridge/reply_queue.py").path]
    let input=Pipe(),out=Pipe(),err=Pipe();p.standardInput=input;p.standardOutput=out;p.standardError=err
    try p.run();input.fileHandleForWriting.write(try JSONSerialization.data(withJSONObject:["action":action,"code":code,"failure_reason":String(reason.prefix(180))]));try input.fileHandleForWriting.close()
    let bytes=out.fileHandleForReading.readDataToEndOfFile();p.waitUntilExit()
    guard p.terminationStatus==0, let r=try JSONSerialization.jsonObject(with:bytes) as? [String:Any] else {throw fail("request_validation_or_readback_failed")}
    return r
}
@MainActor func dialog(_ title:String,_ text:String,_ buttons:[String]=["关闭"]) -> NSApplication.ModalResponse {
    let a=NSAlert();a.messageText=title;a.informativeText=text
    for b in buttons {a.addButton(withTitle:b)}
    if buttons.count>1 {a.buttons[0].keyEquivalent="";a.window.defaultButtonCell=nil}
    NSApp.activate(ignoringOtherApps:true)
    let response=a.runModal();a.window.orderOut(nil);return response
}
final class CalibrationView:NSImageView {
    var ratio:Double?
    override func mouseDown(with event:NSEvent) {
        let p=convert(event.locationInWindow,from:nil)
        ratio=1-Double(p.y/bounds.height)
        needsDisplay=true
    }
    override func draw(_ rect:NSRect) {
        super.draw(rect)
        if let r=ratio {
            NSColor.systemRed.setStroke();let path=NSBezierPath();path.move(to:NSPoint(x:0,y:bounds.height*(1-r)));path.line(to:NSPoint(x:bounds.width,y:bounds.height*(1-r)));path.lineWidth=2;path.stroke()
        }
    }
}
@MainActor func configure() async throws {
    if !CGPreflightScreenCaptureAccess() {_=CGRequestScreenCaptureAccess()}
    if !AXIsProcessTrusted() {_=AXIsProcessTrustedWithOptions([kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String:true] as CFDictionary)}
    guard CGPreflightScreenCaptureAccess(),AXIsProcessTrusted() else {
        _=dialog("需要本人授予权限","请在系统设置 → 隐私与安全中，为“微信回复确认”开启辅助功能和屏幕录制，再重新打开设置。权限用于核对微信窗口、在本人确认后输入发送。不会改变微信原版签名或SIP。")
        return
    }
    let c0=try config();let s0=c0["mac_sender"] as? [String:Any] ?? [:]
    let route=s0["capture_route"] as? String ?? "appCrop"
    guard let app=NSRunningApplication.runningApplications(withBundleIdentifier:"com.tencent.xinWeChat").first else {throw fail("wechat_not_running")}
    try await activateWeChat(app);try await Task.sleep(for:.milliseconds(350))
    let (w,d)=try await targetWindow();let capture=CaptureSession()
    try await capture.start(window:w,display:d,interval:0.25,route:route)
    let image=try await waitImage(capture);await capture.stop()
    let width=min(750,Double(image.width),520*Double(image.width)/Double(image.height)),height=width*Double(image.height)/Double(image.width)
    let view=CalibrationView(frame:NSRect(x:0,y:0,width:width,height:height))
    view.image=NSImage(cgImage:image,size:NSSize(width:width,height:height));view.imageScaling = .scaleProportionallyUpOrDown
    let a=NSAlert();a.messageText="点一下微信输入区的上边缘";a.informativeText="在本机预览中点击输入框与聊天记录之间的分界线，再保存。调整微信窗口尺寸或输入区高度后需重新设置。"
    a.accessoryView=view;a.addButton(withTitle:"保存设置");a.addButton(withTitle:"取消")
    NSApp.activate(ignoringOtherApps:true)
    guard a.runModal() == .alertFirstButtonReturn,let r=view.ratio,r>=0.45,r<=0.88 else {throw fail("calibration_not_completed")}
    var c=try config();var s=c["mac_sender"] as? [String:Any] ?? [:]
    s["permissions_confirmed"]=true;s["composer_top"]=r;s["window_width"]=w.frame.width;s["window_height"]=w.frame.height
    s["enabled"]=false;c["mac_sender"]=s
    s["capture_route"]=route;s["calibration_route"]=route;c["mac_sender"]=s
    try JSONSerialization.data(withJSONObject:c,options:[.sortedKeys]).write(to:base.appendingPathComponent("reader-config.json"),options:.atomic)
    try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:base.appendingPathComponent("reader-config.json").path)
    _=dialog("权限与输入区已设置","接下来请在微信助手里说：给文件传输助手准备一条“微信助手代发测试”，让我Mac确认。先在Mac打开文件传输助手。你确认的真实试发通过后，其他联系人代发才会启用。")
}
@MainActor func diagnoseCapture() async throws {
    guard CGPreflightScreenCaptureAccess(),AXIsProcessTrusted() else {throw fail("screen_recording_and_accessibility_permissions_required")}
    guard let app=NSRunningApplication.runningApplications(withBundleIdentifier:"com.tencent.xinWeChat").first,app.bundleURL?.path=="/Applications/WeChat.app" else {throw fail("original_wechat_required")}
    try await activateWeChat(app);try await Task.sleep(for:.milliseconds(350))
    let (w,d)=try await targetWindow()
    var results:[[String:Any]]=[];var selected:String?
    for route in ["visibleRegion","appThenWindow","appCrop","windowCrop","independentWindow"] {
        let capture=CaptureSession();var result:[String:Any]=["route":route,"header_verified":false]
        do {
            try await capture.start(window:w,display:d,interval:0.25,route:route)
            let frame=try await waitImage(capture)
            _=try chatLeft(frame,chat:"文件传输助手")
            try requireFrontmost(app.processIdentifier)
            let (current,_)=try await targetWindow()
            guard current.windowID==w.windowID,current.frame==w.frame else {throw fail("window_changed_during_diagnostics")}
            result["header_verified"]=true;selected=selected ?? route
        } catch {result["error"]=error.localizedDescription}
        result["frames"]=capture.diagnostics();await capture.stop();results.append(result)
        if selected != nil {break}
    }
    let folder=base.appendingPathComponent("capture-diagnostics",isDirectory:true)
    try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
    let file=folder.appendingPathComponent(UUID().uuidString+".json")
    try JSONSerialization.data(withJSONObject:results,options:[.sortedKeys]).write(to:file,options:.atomic)
    try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:file.path)
    guard let selected else {throw fail("all_scoped_capture_routes_failed; diagnostics_saved_locally")}
    var c=try config();var s=c["mac_sender"] as? [String:Any] ?? [:]
    s["capture_route"]=selected;s["enabled"]=false;s.removeValue(forKey:"calibration_route");c["mac_sender"]=s
    try JSONSerialization.data(withJSONObject:c,options:[.sortedKeys]).write(to:base.appendingPathComponent("reader-config.json"),options:.atomic)
    try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:base.appendingPathComponent("reader-config.json").path)
    _=dialog("已找到可用捕获方式",selected+"\n捕获范围限定为微信窗口矩形；可见区域模式在窗口被遮挡时停止。现在重新校准输入区。")
    try await configure()
}
@MainActor func review(_ code:String) async throws {
    let r=try queue("validate",code:code)
    guard let body=r["payload_json"] as? String,let hash=r["payload_hash"] as? String,digest(body)==hash,
          let payload=try JSONSerialization.jsonObject(with:Data(body.utf8)) as? [String:Any],
          let label=payload["recipient_label"] as? String,let id=payload["recipient_id"] as? String,
          let text=payload["text"] as? String,let root=payload["db_root"] as? String else {throw fail("immutable_preview_invalid")}
    let c=try config();guard let s=c["mac_sender"] as? [String:Any],s["permissions_confirmed"] as? Bool==true,
          let top=s["composer_top"] as? Double,let width=s["window_width"] as? Double,let height=s["window_height"] as? Double else {throw fail("setup_required")}
    let testing=id=="filehelper" && text=="微信助手代发测试"
    guard let route=s["capture_route"] as? String,s["calibration_route"] as? String==route else {throw fail("capture_route_requires_recalibration")}
    guard s["enabled"] as? Bool==true || testing else {throw fail("genuine_file_transfer_test_required_before_other_recipients")}
    let alias=payload["recipient_alias"] as? String ?? ""
    let explanation="收件人：\(label)\n联系人ID：\(id)\n微信号：\(alias.isEmpty ? "未提供" : alias)\n\n完整正文：\n\(text)\n\n请先在Mac打开并核对该收件人聊天，保存已有草稿并清空输入区。你在这里确认选中的联系人；程序只能核对窗口标题和当前微信账号，不能从截图证明联系人ID。发送过程中请勿操作微信。"
    guard dialog("确认这一条回复 · \(code)",explanation,["收件人与正文正确，发送","取消"]) == .alertFirstButtonReturn else {return}
    let current=try queue("validate",code:code)
    guard current["payload_hash"] as? String==hash else {throw fail("draft_changed_since_review")}
    _=try queue("claim",code:code)
    do {
        try await sendMessage(chat:label,text:text,id:code,top:top,stateDirectory:base.appendingPathComponent("reply-journals").path,expectedRoot:root,expectedSize:CGSize(width:width,height:height),route:route)
        _=try queue("ui-sent",code:code)
        _=try queue("verify",code:code)
        _=dialog("已代发并核对本机记录","\(label)\n\(text)\n此结果不代表对方已读。")
    } catch {
        _=try? queue("failed",code:code,reason:error.localizedDescription)
        throw error
    }
}
func chatAXWindow(_ pid:pid_t) throws -> AXUIElement {
    let app=AXUIElementCreateApplication(pid)
    func accepts(_ window:AXUIElement) -> Bool {
        var title:CFTypeRef?
        return AXUIElementCopyAttributeValue(window,kAXTitleAttribute as CFString,&title) == .success && ["微信","WeChat","Weixin"].contains(title as? String ?? "")
    }
    for attribute in [kAXFocusedWindowAttribute,kAXMainWindowAttribute] {
        var value:CFTypeRef?
        if AXUIElementCopyAttributeValue(app,attribute as CFString,&value) == .success,
           let value,CFGetTypeID(value)==AXUIElementGetTypeID() {
            let window=unsafeBitCast(value,to:AXUIElement.self)
            if accepts(window) {return window}
        }
    }
    var value:CFTypeRef?
    guard AXUIElementCopyAttributeValue(app,kAXWindowsAttribute as CFString,&value) == .success,
          let windows=value as? [AXUIElement] else {throw fail("main_window_list_missing")}
    let matches=windows.filter(accepts)
    guard matches.count==1 else {throw fail("expected_one_original_ax_chat_window")}
    return matches[0]
}
@MainActor func beginWeChatScreenshot() async throws {
    guard AXIsProcessTrusted() else {throw fail("accessibility_permission_required")}
    guard let app=NSRunningApplication.runningApplications(withBundleIdentifier:"com.tencent.xinWeChat").first,
          app.bundleURL?.path=="/Applications/WeChat.app" else {throw fail("original_wechat_required")}
    let c=try config()
    guard let root=c["db_root"] as? String else {throw fail("expected_account_missing")}
    try requireAccount(app.processIdentifier,root:root)
    try await activateWeChat(app)
    _=try chatAXWindow(app.processIdentifier)
    for down in [true,false] {
        try requireFrontmost(app.processIdentifier)
        guard let event=CGEvent(keyboardEventSource:nil,virtualKey:21,keyDown:down) else {throw fail("screenshot_shortcut_event_failed")}
        event.flags = .maskCommand
        event.post(tap:.cghidEventTap)
    }
    // Selection and completion stay manual until the overlay can be verified.
    try await Task.sleep(for:.milliseconds(700))
}
@MainActor func cancelWeChatScreenshot() async throws {
    guard !screenLocked(),AXIsProcessTrusted(),let app=NSRunningApplication.runningApplications(withBundleIdentifier:"com.tencent.xinWeChat").first,
          app.bundleURL?.path=="/Applications/WeChat.app" else {throw fail("original_unlocked_wechat_required")}
    let c=try config();guard let root=c["db_root"] as? String else {throw fail("expected_account_missing")}
    try requireAccount(app.processIdentifier,root:root);try await activateWeChat(app);try requireFrontmost(app.processIdentifier)
    for down in [true,false] {
        guard let event=CGEvent(keyboardEventSource:nil,virtualKey:53,keyDown:down) else {throw fail("screenshot_cancel_event_failed")}
        event.postToPid(app.processIdentifier)
    }
    try await Task.sleep(for:.milliseconds(350))
    try nativeStage("picker_cancelled")
}
func progressHUD(_ row:[String:Any]) -> CGRect? {
    guard let pid=row[kCGWindowOwnerPID as String] as? Int32,
          let app=NSRunningApplication(processIdentifier:pid),app.bundleIdentifier=="com.codeisland.app",
          let bounds=row[kCGWindowBounds as String] as? NSDictionary,
          let frame=CGRect(dictionaryRepresentation:bounds) else {return nil}
    guard let id=row[kCGWindowNumber as String] as? UInt32,
          let rows=CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] else {return nil}
    let visible=rows.filter {($0[kCGWindowOwnerPID as String] as? Int32)==pid && ($0[kCGWindowAlpha as String] as? Double ?? 1)>0}
    guard visible.count==1,(visible[0][kCGWindowNumber as String] as? UInt32)==id else {return nil}
    // A single visible CG window maps this observed system-dialog HUD to its exact ID.
    var queue=[AXUIElementCreateApplication(pid)],count=0,verified=false
    while !queue.isEmpty,count<40 {
        let node=queue.removeFirst();count += 1
        var value:CFTypeRef?,children:CFTypeRef?
        if AXUIElementCopyAttributeValue(node,kAXValueAttribute as CFString,&value) == .success,
           let text=value as? String,text.count<=80,text.range(of:"^[A-Za-z ]+ [0-9]+ / [0-9]+$",options:.regularExpression) != nil {verified=true}
        if AXUIElementCopyAttributeValue(node,kAXChildrenAttribute as CFString,&children) == .success,let next=children as? [AXUIElement] {queue.append(contentsOf:next.prefix(40-count))}
    }
    return verified ? frame : nil
}
@MainActor func nativePickerBitmap(_ picker:SCWindow,_ rect:CGRect,_ pid:pid_t) async throws -> CGImage {
    try nativeStage("picker_selection_start")
    let board=NSPasteboard.general
    var saved=[NSPasteboardItem](),total=0
    for item in board.pasteboardItems ?? [] {
        let copy=NSPasteboardItem()
        for type in item.types {
            guard let data=item.data(forType:type) else {throw fail("clipboard_promised_data_cannot_be_preserved")}
            total += data.count;guard total<=32*1024*1024 else {throw fail("clipboard_too_large_to_preserve")}
            guard copy.setData(data,forType:type) else {throw fail("clipboard_preservation_failed")}
        }
        saved.append(copy)
    }
    let before=board.changeCount
    let selected=rect.insetBy(dx:1,dy:1)
    func active() throws {
        try requireFrontmost(pid)
        guard let rows=CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]],
              let row=rows.first(where:{($0[kCGWindowNumber as String] as? UInt32)==picker.windowID}),
              (row[kCGWindowOwnerPID as String] as? Int32)==pid,
              let bounds=row[kCGWindowBounds as String] as? NSDictionary,
              let frame=CGRect(dictionaryRepresentation:bounds),frame==picker.frame else {throw fail("native_picker_identity_changed; no_return")}
    }
    try active()
    for (kind,point) in [(CGEventType.leftMouseDown,CGPoint(x:selected.minX,y:selected.minY)),
                         (.leftMouseDragged,CGPoint(x:selected.maxX,y:selected.maxY)),
                         (.leftMouseUp,CGPoint(x:selected.maxX,y:selected.maxY))] {
        try active()
        guard let event=CGEvent(mouseEventSource:nil,mouseType:kind,mouseCursorPosition:point,mouseButton:.left) else {throw fail("screenshot_selection_event_failed")}
        event.post(tap:.cghidEventTap);try await Task.sleep(for:.milliseconds(100))
    }
    try await Task.sleep(for:.milliseconds(300));try active()
    try nativeStage("picker_copy_start")
    for down in [true,false] {
        guard let key=CGEvent(keyboardEventSource:nil,virtualKey:8,keyDown:down) else {throw fail("screenshot_copy_event_failed")}
        key.flags = .maskCommand;key.post(tap:.cghidEventTap)
    }
    for _ in 0..<30 {
        if board.changeCount != before {break}
        try await Task.sleep(for:.milliseconds(100))
    }
    guard !screenLocked(),NSRunningApplication(processIdentifier:pid)?.bundleURL?.path=="/Applications/WeChat.app" else {throw fail("capture_process_or_session_changed")}
    guard board.changeCount != before,
          let data=board.data(forType:.png) ?? board.data(forType:.tiff),data.count<=16*1024*1024,
          let bitmap=NSBitmapImageRep(data:data),let image=bitmap.cgImage else {throw fail("no_fresh_picker_bitmap; no_return; clipboard_not_restored_without_capture_proof")}
    let scale=Double(image.width)/selected.width
    guard [1.0,2.0].contains(where:{abs(scale-$0)<=2/selected.width}),
          abs(Double(image.height)-selected.height*scale)<=2 else {throw fail("picker_bitmap_dimensions_mismatch; image_discarded")}
    if let source=board.string(forType:NSPasteboard.PasteboardType("org.nspasteboard.source")),source != "com.tencent.xinWeChat" {throw fail("picker_bitmap_source_mismatch; image_discarded")}
    try nativeStage("fresh_bitmap_verified",["width":image.width,"height":image.height])
    let capturedCount=board.changeCount,signature=SHA256.hash(data:data)
    // Restore only while this exact bitmap is still current; never overwrite a newer user copy.
    if board.changeCount==capturedCount,
       let current=board.data(forType:.png) ?? board.data(forType:.tiff),SHA256.hash(data:current)==signature {
        board.clearContents();if !saved.isEmpty, !board.writeObjects(saved) {throw fail("clipboard_restore_failed")}
    }
    return image
}
@MainActor func screenshotOverlayDiagnostic() async throws {
    try nativeStage("started")
    guard CGPreflightScreenCaptureAccess(),AXIsProcessTrusted() else {throw fail("screen_recording_and_accessibility_permissions_required")}
    let accountConfig=try config()
    guard let accountRoot=accountConfig["db_root"] as? String else {throw fail("expected_account_missing")}
    guard let app=NSRunningApplication.runningApplications(withBundleIdentifier:"com.tencent.xinWeChat").first,
          app.bundleURL?.path=="/Applications/WeChat.app" else {throw fail("original_wechat_required")}
    try await cancelWeChatScreenshot();try await activateWeChat(app)
    let window=try chatAXWindow(app.processIdentifier)
    var pos:CFTypeRef?,size:CFTypeRef?,title:CFTypeRef?
    guard AXUIElementCopyAttributeValue(window,kAXPositionAttribute as CFString,&pos) == .success,
          AXUIElementCopyAttributeValue(window,kAXSizeAttribute as CFString,&size) == .success,
          AXUIElementCopyAttributeValue(window,kAXTitleAttribute as CFString,&title) == .success,
          ["微信","WeChat","Weixin"].contains(title as? String ?? ""),
          let pos,let size,CFGetTypeID(pos)==AXValueGetTypeID(),CFGetTypeID(size)==AXValueGetTypeID() else {throw fail("focused_chat_geometry_missing")}
    var point=CGPoint.zero,dimensions=CGSize.zero
    guard AXValueGetValue(unsafeBitCast(pos,to:AXValue.self),.cgPoint,&point),
          AXValueGetValue(unsafeBitCast(size,to:AXValue.self),.cgSize,&dimensions) else {throw fail("focused_chat_geometry_missing")}
    let rect=CGRect(origin:point,size:dimensions)
    let before=try await SCShareableContent.excludingDesktopWindows(true,onScreenWindowsOnly:true)
    let oldIDs=Set(before.windows.map(\.windowID))
    guard before.displays.contains(where:{$0.frame.contains(rect)}) else {throw fail("chat_must_fit_one_display")}
    var found=false,lastObstruction="visible_chat_not_found",hud:[String:Any]?
    for _ in 0..<100 {
        try requireFrontmost(app.processIdentifier)
        guard let rows=CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] else {throw fail("window_inventory_missing")}
        var obstruction:String?
        for row in rows {
            guard let pid=row[kCGWindowOwnerPID as String] as? Int32,
                  let bounds=row[kCGWindowBounds as String] as? NSDictionary,
                  let frame=CGRect(dictionaryRepresentation:bounds) else {throw fail("window_bounds_missing")}
            if pid==app.processIdentifier,abs(frame.minX-rect.minX)<=1,abs(frame.minY-rect.minY)<=1,
               abs(frame.width-rect.width)<=1,abs(frame.height-rect.height)<=1 {found=true;break}
            if (row[kCGWindowAlpha as String] as? Double ?? 1)>0,frame.intersects(rect) {
                if hud==nil,progressHUD(row) != nil {hud=row;continue}
                let owner=NSRunningApplication(processIdentifier:pid)?.bundleIdentifier ?? "system"
                obstruction="chat_obscured_layer_\(row[kCGWindowLayer as String] as? Int ?? -1); owner=\(owner)";break
            }
        }
        if found,obstruction==nil {break}
        found=false;hud=nil;lastObstruction=obstruction ?? "visible_chat_not_found"
        try await Task.sleep(for:.milliseconds(200))
    }
    guard found else {throw fail(lastObstruction)}
    try nativeStage("region_checked")
    try await beginWeChatScreenshot()
    let after=try await SCShareableContent.excludingDesktopWindows(true,onScreenWindowsOnly:true)
    let overlays=after.windows.filter { !oldIDs.contains($0.windowID) && $0.owningApplication?.processID==app.processIdentifier && $0.frame.contains(rect) }
    guard overlays.count==1 else {throw fail("native_screenshot_overlay_not_unique; no_selection_or_return")}
    try nativeStage("picker_identified")
    try requireFrontmost(app.processIdentifier)
    // The owner-authorized native picker copies only this window region. Never press Return.
    var image=try await nativePickerBitmap(overlays[0],rect,app.processIdentifier)
    if let hud,let id=hud[kCGWindowNumber as String] as? UInt32,let pid=hud[kCGWindowOwnerPID as String] as? Int32,
       let originalFrame=progressHUD(hud) {
        guard let now=CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]],
              let same=now.first(where:{($0[kCGWindowNumber as String] as? UInt32)==id}),
              (same[kCGWindowOwnerPID as String] as? Int32)==pid,progressHUD(same)==originalFrame else {throw fail("progress_hud_changed; image_discarded")}
        let hidden=originalFrame.intersection(rect)
        guard let context=CGContext(data:nil,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,
              space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {throw fail("mask_context_failed")}
        context.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
        context.setFillColor(NSColor.gray.cgColor)
        let selected=rect.insetBy(dx:1,dy:1),scale=Double(image.width)/selected.width
        context.fill(CGRect(x:(hidden.minX-selected.minX)*scale,y:Double(image.height)-(hidden.maxY-selected.minY)*scale,width:hidden.width*scale,height:hidden.height*scale).insetBy(dx:-2,dy:-2))
        guard let masked=context.makeImage() else {throw fail("mask_image_failed")};image=masked
    } else if hud != nil {throw fail("progress_hud_not_verified; image_discarded")}
    guard !screenLocked() else {throw fail("screen_locked")}
    var currentPos:CFTypeRef?,currentSize:CFTypeRef?
    guard AXUIElementCopyAttributeValue(window,kAXPositionAttribute as CFString,&currentPos) == .success,
          AXUIElementCopyAttributeValue(window,kAXSizeAttribute as CFString,&currentSize) == .success,
          let currentPos,let currentSize,CFGetTypeID(currentPos)==AXValueGetTypeID(),CFGetTypeID(currentSize)==AXValueGetTypeID() else {throw fail("chat_geometry_changed")}
    var finalPoint=CGPoint.zero,finalSize=CGSize.zero
    guard AXValueGetValue(unsafeBitCast(currentPos,to:AXValue.self),.cgPoint,&finalPoint),
          AXValueGetValue(unsafeBitCast(currentSize,to:AXValue.self),.cgSize,&finalSize),finalPoint==point,finalSize==dimensions else {throw fail("chat_geometry_changed")}
    try requireAccount(app.processIdentifier,root:accountRoot)
    guard !isBlank(pixels(image)) else {throw fail("native_screenshot_overlay_blank; no_selection_or_return")}
    try nativeStage("preview_ready",["width":image.width,"height":image.height,"filehelper_header_verified":(try? chatLeft(image,chat:"文件传输助手")) != nil])
    let width=min(750,Double(image.width),520*Double(image.width)/Double(image.height)),height=width*Double(image.height)/Double(image.width)
    let view=NSImageView(frame:NSRect(x:0,y:0,width:width,height:height));view.image=NSImage(cgImage:image,size:NSSize(width:width,height:height));view.imageScaling = .scaleProportionallyUpOrDown
    let preview=NSAlert();preview.messageText="原生截图范围只读预览";preview.informativeText="没有输入或发送消息。灰色遮挡区不可核验。没有完成截图选区。图片不保存到文件。";preview.accessoryView=view;preview.addButton(withTitle:"关闭")
    NSApp.activate(ignoringOtherApps:true);_=preview.runModal();preview.window.orderOut(nil)
}
@main struct ReplyBridge {
    @MainActor static func main() {
        let app=NSApplication.shared;app.setActivationPolicy(.regular)
        Task { @MainActor in
            do {
                if CommandLine.arguments.contains("--cancel-screenshot") {try await cancelWeChatScreenshot()}
                else if CommandLine.arguments.contains("--snapshot-diagnose") {try await screenshotOverlayDiagnostic()}
                else if CommandLine.arguments.contains("--wechat-screenshot") {try await beginWeChatScreenshot()}
                else if CommandLine.arguments.contains("--setup") {try await configure()}
                else if CommandLine.arguments.contains("--diagnose") {try await diagnoseCapture()}
                else if let i=CommandLine.arguments.firstIndex(of:"--request"),i+1<CommandLine.arguments.count {try await review(CommandLine.arguments[i+1])}
                else {
                    let choice=dialog("微信回复确认","先在原版微信打开文件传输助手。“微信自带截图”只触发 ⌘4，框选和完成由你操作；不输入、不发送。",["检查窗口捕获","首次设置","微信自带截图","截图范围诊断","关闭"])
                    if choice == .alertFirstButtonReturn {try await diagnoseCapture()}
                    else if choice == .alertSecondButtonReturn {try await configure()}
                    else if choice.rawValue == NSApplication.ModalResponse.alertFirstButtonReturn.rawValue+2 {try await beginWeChatScreenshot()}
                    else if choice.rawValue == NSApplication.ModalResponse.alertFirstButtonReturn.rawValue+3 {try await screenshotOverlayDiagnostic()}
                }
            } catch {
                if CommandLine.arguments.contains("--snapshot-diagnose") {try? nativeStage("failed",["reason":error.localizedDescription])}
                _=dialog("发送未完成",error.localizedDescription+"\n请查看微信，程序不会自动重试。")
            }
            app.terminate(nil)
        }
        app.run()
    }
}
