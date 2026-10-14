import Cocoa
import ScreenCaptureKit
import Vision
import CoreMedia
import CoreImage
import ImageIO
import UniformTypeIdentifiers

// MIT licensed. Local ScreenCaptureKit/Vision reader; see Send.swift for explicit sends.
func emit(_ event: [String: Any]) {
    var value = event
    value["at"] = ISO8601DateFormatter().string(from: Date())
    if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]),
       let string = String(data: data, encoding: .utf8) { print(string); fflush(stdout) }
}
func option(_ name: String, _ fallback: String) -> String {
    guard let i = CommandLine.arguments.firstIndex(of: name), i + 1 < CommandLine.arguments.count else { return fallback }
    return CommandLine.arguments[i + 1]
}
struct Line {
    let text: String
    let box: CGRect
    let confidence: Float
    var json: [String: Any] { ["text": text, "x": box.minX, "y": 1-box.maxY,
        "width": box.width, "height": box.height, "confidence": confidence] }
}
func recognize(_ image: CGImage) throws -> [Line] {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true
    try VNImageRequestHandler(cgImage: image).perform([request])
    return (request.results ?? []).compactMap {
        guard let text = $0.topCandidates(1).first else { return nil }
        return Line(text: text.string, box: $0.boundingBox, confidence: text.confidence)
    }.sorted { $0.box.midY > $1.box.midY }
}
// A small grayscale representation avoids re-running OCR on an unchanged panel.
func pixels(_ image: CGImage) -> [UInt8] {
    var data = [UInt8](repeating: 0, count: 200 * 160)
    data.withUnsafeMutableBytes { p in
        let context = CGContext(data: p.baseAddress, width: 200, height: 160,
            bitsPerComponent: 8, bytesPerRow: 200, space: CGColorSpaceCreateDeviceGray(), bitmapInfo: 0)!
        context.draw(image, in: CGRect(x: 0, y: 0, width: 200, height: 160))
    }
    return data
}
func difference(_ a: [UInt8], _ b: [UInt8]) -> Double {
    guard a.count == b.count, !a.isEmpty else { return .infinity }
    return zip(a,b).reduce(0.0) { $0 + Double(abs(Int($1.0)-Int($1.1))) } / Double(a.count)
}
func isBlank(_ data: [UInt8]) -> Bool {
    guard let lo = data.min(), let hi = data.max() else { return true }
    return Int(hi)-Int(lo) < 8
}
// Only reports an appended OCR sequence if previous visible context overlaps.
// Reflow, OCR corrections, scrolling and lack of overlap produce a reset instead.
func appendStart(old: [String], new: [String]) -> Int? {
    guard !old.isEmpty, !new.isEmpty else { return nil }
    for count in stride(from: min(old.count, new.count), through: 1, by: -1) {
        if Array(old.suffix(count)) == Array(new.prefix(count)) { return count }
    }
    return nil
}

final class CaptureSession: NSObject, SCStreamOutput, SCStreamDelegate, @unchecked Sendable {
    private let lock = NSLock()
    private let context = CIContext()
    private var image: CGImage?
    private var failure: Error?
    private var sequence = 0
    private var stream: SCStream?
    var key = ""
    func stream(_ stream: SCStream, didOutputSampleBuffer sample: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, sample.isValid, let pixel = sample.imageBuffer else { return }
        let input = CIImage(cvPixelBuffer: pixel)
        guard let frame = context.createCGImage(input, from: input.extent) else { return }
        lock.lock(); image = frame; sequence += 1; lock.unlock()
    }
    func stream(_ stream: SCStream, didStopWithError error: Error) {
        lock.lock(); failure = error; lock.unlock()
    }
    func serial() -> Int { lock.lock(); defer { lock.unlock() }; return sequence }
    func latest() throws -> CGImage? {
        lock.lock(); defer { lock.unlock() }
        if let failure { throw failure }
        return image
    }
    func start(window: SCWindow, display: SCDisplay, interval: Double) async throws {
        guard let app = window.owningApplication else { throw NSError(domain:"capture",code:1) }
        let config = SCStreamConfiguration()
        config.width = Int(window.frame.width); config.height = Int(window.frame.height)
        config.showsCursor = false
        config.minimumFrameInterval = CMTime(seconds: interval, preferredTimescale: 600)
        config.queueDepth = 3
        config.sourceRect = CGRect(x:window.frame.minX-display.frame.minX,
            y:window.frame.minY-display.frame.minY, width:window.frame.width, height:window.frame.height)
        // Reproducible macOS workaround: app-filter stream -> window-filter update.
        // Direct single-window streams and one-shot screenshots omit this WeChat window.
        let initial = SCContentFilter(display:display, including:[app], exceptingWindows:[])
        let active = SCStream(filter:initial, configuration:config, delegate:self)
        stream = active
        try active.addStreamOutput(self, type:.screen, sampleHandlerQueue:DispatchQueue(label:"wechat.frames"))
        try await active.startCapture()
        try await Task.sleep(for:.milliseconds(250))
        try await active.updateContentFilter(SCContentFilter(display:display, including:[window]))
        try await Task.sleep(for:.milliseconds(550))
    }
    func stop() async { if let stream { try? await stream.stopCapture() }; stream = nil }
}

