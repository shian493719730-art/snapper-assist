import Foundation

struct AccessibilityHelp {
    let trusted: Bool
    let appPath: String
    var status: String { trusted ? "已授权 · 可以读取主动选区" : "尚未生效 · 需要确认当前这份应用" }
    var steps: String {
        if trusted {
            return "辅助功能已被系统确认。\n\n在可编辑文字中选中一段内容，稍等片刻即可看到浮条。仅选中文字不发送 AI 请求；点击替换才写入。\n\n若某个软件没有浮条，检查是否暂停或在该应用中禁用；只读字段可能只支持复制。"
        }
        return "1  打开「隐私与安全性 → 辅助功能」\n注意：不是设置侧边栏中用于视觉、听觉的“辅助功能”。\n\n2  添加下面这份 Snapper Assist 并开启\n需要密码或触控 ID 时，请在 macOS 窗口中自行确认。\n\n3  返回这里点“重新检查”\n本页变为“已授权”，才表示这份应用真正生效。"
    }
    var recovery: String {
        "开关已打开，仍显示未生效？更新后可能需要重新关联应用：只移除列表中的 Snapper Assist，再用“＋”添加下面的当前 App 并开启；完成后重新检查，必要时退出助手再打开。不要为此开启完全磁盘访问或重置其他应用权限。"
    }
    static let settingsURL = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
    static let manualPath = "Apple 菜单 → 系统设置 → 隐私与安全性 → 辅助功能"
}
