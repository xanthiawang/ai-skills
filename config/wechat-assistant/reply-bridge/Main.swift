import Cocoa
import CryptoKit

let base=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".local/share/wechat-assistant")
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
    NSApp.activate(ignoringOtherApps:true);return a.runModal()
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
    let (w,d)=try await targetWindow();let capture=CaptureSession()
    try await capture.start(window:w,display:d,interval:0.25)
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
    try JSONSerialization.data(withJSONObject:c,options:[.sortedKeys]).write(to:base.appendingPathComponent("reader-config.json"),options:.atomic)
    try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:base.appendingPathComponent("reader-config.json").path)
    _=dialog("权限与输入区已设置","接下来请在微信助手里说：给文件传输助手准备一条“微信助手代发测试”，让我Mac确认。先在Mac打开文件传输助手。你确认的真实试发通过后，其他联系人代发才会启用。")
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
    guard s["enabled"] as? Bool==true || testing else {throw fail("genuine_file_transfer_test_required_before_other_recipients")}
    let alias=payload["recipient_alias"] as? String ?? ""
    let explanation="收件人：\(label)\n联系人ID：\(id)\n微信号：\(alias.isEmpty ? "未提供" : alias)\n\n完整正文：\n\(text)\n\n请先在Mac打开并核对该收件人聊天，保存已有草稿并清空输入区。你在这里确认选中的联系人；程序只能核对窗口标题和当前微信账号，不能从截图证明联系人ID。发送过程中请勿操作微信。"
    guard dialog("确认这一条回复 · \(code)",explanation,["收件人与正文正确，发送","取消"]) == .alertFirstButtonReturn else {return}
    let current=try queue("validate",code:code)
    guard current["payload_hash"] as? String==hash else {throw fail("draft_changed_since_review")}
    _=try queue("claim",code:code)
    do {
        try await sendMessage(chat:label,text:text,id:code,top:top,stateDirectory:base.appendingPathComponent("reply-journals").path,expectedRoot:root,expectedSize:CGSize(width:width,height:height))
        _=try queue("ui-sent",code:code)
        _=try queue("verify",code:code)
        _=dialog("已代发并核对本机记录","\(label)\n\(text)\n此结果不代表对方已读。")
    } catch {
        _=try? queue("failed",code:code,reason:error.localizedDescription)
        throw error
    }
}
@main struct ReplyBridge {
    @MainActor static func main() {
        let app=NSApplication.shared;app.setActivationPolicy(.regular)
        Task { @MainActor in
            do {
                if CommandLine.arguments.contains("--setup") {try await configure()}
                else if let i=CommandLine.arguments.firstIndex(of:"--request"),i+1<CommandLine.arguments.count {try await review(CommandLine.arguments[i+1])}
                else {
                    if dialog("微信回复确认","首次设置需要辅助功能与屏幕录制，用于核对微信窗口并在你逐条确认后输入发送。回复草稿由微信助手准备。",["首次设置","关闭"]) == .alertFirstButtonReturn {try await configure()}
                }
            } catch { _=dialog("发送未完成",error.localizedDescription+"\n请查看微信，程序不会自动重试。") }
            app.terminate(nil)
        }
        app.run()
    }
}
