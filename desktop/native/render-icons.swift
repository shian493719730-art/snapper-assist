import AppKit
let destination=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
try FileManager.default.createDirectory(at:destination,withIntermediateDirectories:true)
for variant in ["studio","assist"] {
    let set=destination.appendingPathComponent("snapper-\(variant).iconset",isDirectory:true);try FileManager.default.createDirectory(at:set,withIntermediateDirectories:true)
    for size in [16,32,128,256,512] {for scale in [1,2] {
        let pixels=size*scale,canvas=NSImage(size:NSSize(width:pixels,height:pixels));canvas.lockFocus();let context=NSGraphicsContext.current!.cgContext;context.scaleBy(x:CGFloat(pixels)/1024,y:CGFloat(pixels)/1024)
        let dark=variant=="studio",background=dark ? NSColor(srgbRed:0.12,green:0.21,blue:0.28,alpha:1):NSColor(srgbRed:0.94,green:0.93,blue:0.90,alpha:1)
        background.setFill();NSBezierPath(roundedRect:NSRect(x:40,y:40,width:944,height:944),xRadius:211,yRadius:211).fill()
        let mark=NSBezierPath();mark.move(to:NSPoint(x:705,y:712));mark.curve(to:NSPoint(x:402,y:750),controlPoint1:NSPoint(x:630,y:786),controlPoint2:NSPoint(x:475,y:800));mark.curve(to:NSPoint(x:349,y:561),controlPoint1:NSPoint(x:316,y:695),controlPoint2:NSPoint(x:310,y:611));mark.curve(to:NSPoint(x:620,y:445),controlPoint1:NSPoint(x:389,y:509),controlPoint2:NSPoint(x:554,y:489));mark.curve(to:NSPoint(x:617,y:291),controlPoint1:NSPoint(x:701,y:392),controlPoint2:NSPoint(x:696,y:326));mark.curve(to:NSPoint(x:310,y:314),controlPoint1:NSPoint(x:527,y:253),controlPoint2:NSPoint(x:389,y:252));mark.lineWidth=89;mark.lineCapStyle = .round;mark.lineJoinStyle = .round
        (dark ? NSColor(srgbRed:0.97,green:0.97,blue:0.94,alpha:1):NSColor(srgbRed:0.18,green:0.26,blue:0.31,alpha:1)).setStroke();mark.stroke()
        NSColor(srgbRed:0.87,green:0.38,blue:0.24,alpha:1).setFill();let dot=NSRect(x:dark ? 734:718,y:dark ? 257:700,width:83,height:83);NSBezierPath(ovalIn:dot).fill()
        if !dark {let cursor=NSBezierPath();cursor.move(to:NSPoint(x:775,y:430));cursor.line(to:NSPoint(x:775,y:563));cursor.lineWidth=20;NSColor(srgbRed:0.18,green:0.26,blue:0.31,alpha:1).setStroke();cursor.stroke()}
        canvas.unlockFocus();let rep=NSBitmapImageRep(data:canvas.tiffRepresentation!)!;let data=rep.representation(using:.png,properties:[:])!;try data.write(to:set.appendingPathComponent("icon_\(size)x\(size)\(scale==2 ? "@2x":"").png"))
    }}
}
