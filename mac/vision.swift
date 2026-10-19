import AppKit
import Vision

// Local OCR only. No network, credentials or browser internals.
if CommandLine.arguments.count != 2 {
    fputs("Usage: vision IMAGE | --frontmost\n", stderr)
    exit(2)
}
if CommandLine.arguments[1] == "--frontmost" {
    print(NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "")
    exit(0)
}
if CommandLine.arguments[1] == "--window" {
    guard let app = NSWorkspace.shared.frontmostApplication,
          let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]],
          let window = windows.first(where: {
              let frame = $0[kCGWindowBounds as String] as? [String: Any]
              let width = frame?["Width"] as? Double ?? 0
              let height = frame?["Height"] as? Double ?? 0
              return ($0[kCGWindowOwnerPID as String] as? Int32) == app.processIdentifier &&
              ($0[kCGWindowLayer as String] as? Int) == 0 && width >= 700 && height >= 500
          }),
          let bounds = window[kCGWindowBounds as String] as? [String: Any]
    else { print("null"); exit(0) }
    let output: [String: Any] = ["app": app.bundleIdentifier ?? "", "id": window[kCGWindowNumber as String] ?? 0,
        "x": bounds["X"] ?? 0, "y": bounds["Y"] ?? 0,
        "width": bounds["Width"] ?? 0, "height": bounds["Height"] ?? 0]
    let data = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
    print(String(data: data, encoding: .utf8)!)
    exit(0)
}
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
let supported = try request.supportedRecognitionLanguages()
request.recognitionLanguages = ["tr-TR", "en-US"].filter { supported.contains($0) }
try VNImageRequestHandler(url: url).perform([request])
var words: [[String: Any]] = []
for result in request.results ?? [] {
    guard let candidate = result.topCandidates(1).first else { continue }
    let text = candidate.string
    // Word boxes allow buttons in the same OCR line to remain separate targets.
    let regex = try NSRegularExpression(pattern: "\\S+")
    for match in regex.matches(in: text, range: NSRange(text.startIndex..., in: text)) {
        guard let range = Range(match.range, in: text),
              let box = try candidate.boundingBox(for: range)?.boundingBox else { continue }
        words.append(["text": String(text[range]), "confidence": candidate.confidence,
                      "x": box.minX, "y": 1 - box.maxY,
                      "w": box.width, "h": box.height])
    }
}
let data = try JSONSerialization.data(withJSONObject: words, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
