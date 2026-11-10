# 安装内测版

需要 **Apple 芯片 Mac（M1 或更新）及 macOS 26+**。当前不支持 Windows、Intel Mac。

1. 从 [Release](https://github.com/shian493719730-art/snapper-assist/releases/tag/v0.8.0-beta.1) 下载 ZIP 并解压，将 Snapper Assist.app 移到“应用程序”或自己的 Applications 文件夹。
2. 打开应用，在“系统设置 → 隐私与安全性 → 辅助功能”中添加并开启这份应用，必要时退出后重新打开。菜单栏 S 提供暂停、恢复与退出。
3. 先在文本编辑中使用 [测试文字](testing.zh-CN.md)，选中后从“⋯ → 使用本地草稿”开始，不会调用模型。
4. 0.8 已默认加载 14 类领域建议和 17 种可选方法，无需下载配方、安装 Python 或改配置。要选择个人习惯，打开“菜单栏 S → 领域方法”或“浮条 ⋯ → 领域方法”；如“学术讨论 → 苏格拉底式提问”。选“跟随内置建议”恢复默认，下次完善即生效。

安装包为 ad-hoc 签名，尚未做 Developer ID 签名和 Apple 公证，新电脑首次安装未实测。macOS 可能阻止首次打开；请记录准确提示，不要为内测关闭全局安全保护。[Apple 官方说明](https://support.apple.com/zh-cn/102445)。

## AI 功能

此版本固定寻找以下 CLI：

```text
/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex
```

使用本人 `~/.codex/auth.json`，或进程继承的 `CODEX_HOME` 下的对应文件登录。开发机只验证过 CLI `0.166.0-alpha.6`；其他版本、安装路径及仅钥匙串登录未验证。安装了其他布局的 Codex 并不表示此版本 AI 一定可用。不满足条件时可先测试本地草稿。

请使用自己的账号，不要复制他人的 auth.json、密码或 API key。应用不会自动配置新 API key 或切换账号。AI 不可用时，本地草稿仍可使用。

点击“AI 完善”才发出请求，使用本人账号用量。应看到旋转加载标记与已等待秒数，返回后先检查，再决定替换。同一字段、相同请求可能使用短期内存缓存；仅选中文字不会请求模型。

若出现文稿文件夹或完全磁盘访问授权，先取消并反馈，不为测试扩大权限。

## 更新与移除

尚未配置自动更新或开机启动。更新前先退出；不同 ad-hoc 构建可能要求重新确认辅助功能权限。移除时退出、删除 App 并移除辅助功能条目。可选本地状态位置见 [隐私说明](../PRIVACY.md)。
