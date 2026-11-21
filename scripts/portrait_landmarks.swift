// Build-time macOS Vision helper, never called by the shipped game.
// Emits image-space normalized landmarks (origin at top left) and an 8-bit alpha matte.
import Foundation
import AppKit
import Vision
import CoreImage

let paths = Array(CommandLine.arguments.dropFirst())
guard paths.count == 3 else { exit(2) }
let url = URL(fileURLWithPath: paths[0])
guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { exit(3) }
let request = VNDetectFaceLandmarksRequest()
let handler = VNImageRequestHandler(cgImage: image)
try handler.perform([request])
if let face = request.results?.sorted(by: { $0.boundingBox.width > $1.boundingBox.width }).first,
   let marks = face.landmarks {
    let rect = face.boundingBox
    func points(_ region: VNFaceLandmarkRegion2D?) -> [[Double]] {
        guard let region = region else { return [] }
        return region.normalizedPoints.map { p in
            [rect.minX + Double(p.x)*rect.width, 1 - rect.minY - Double(p.y)*rect.height]
        }
    }
    let collection = [
        "leftPupil": points(marks.leftPupil), "rightPupil": points(marks.rightPupil),
        "leftEye": points(marks.leftEye), "rightEye": points(marks.rightEye),
        "leftBrow": points(marks.leftEyebrow), "rightBrow": points(marks.rightEyebrow),
        "nose": points(marks.nose), "lips": points(marks.outerLips), "jaw": points(marks.faceContour)
    ]
    let json = try JSONSerialization.data(withJSONObject: collection)
    try json.write(to: URL(fileURLWithPath: paths[1]))
}
let segment = VNGeneratePersonSegmentationRequest()
segment.qualityLevel = .accurate
segment.outputPixelFormat = kCVPixelFormatType_OneComponent8
try VNImageRequestHandler(cgImage: image).perform([segment])
if let matte = segment.results?.first?.pixelBuffer {
    let ci = CIImage(cvPixelBuffer: matte)
    let context = CIContext()
    try context.writePNGRepresentation(of: ci, to: URL(fileURLWithPath: paths[2]),
        format: .L8, colorSpace: CGColorSpaceCreateDeviceGray())
}
