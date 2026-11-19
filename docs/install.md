# Install the beta

## Requirements

| Item | Current beta |
| --- | --- |
| Hardware | Apple-silicon Mac, M1 or newer |
| System | macOS 26 or newer |
| App permission | Accessibility for the installed copy |
| Local draft | No model account or network request required |
| Shared AI | Private invitation; billing currently disabled |

The ZIP is ad-hoc signed, not Developer-ID signed or notarized. Fresh-machine installation has not yet been verified. macOS may block the first launch. Record the exact message if blocked; do not disable system-wide security controls for this beta. [Apple's guidance](https://support.apple.com/102445).

1. Download the ZIP from the [release](https://github.com/shian493719730-art/snapper-assist/releases).
2. Unzip and move **Snapper Assist.app** to Applications or your own Applications folder before granting permission.
3. Open the app. Enable this copy in **System Settings → Privacy & Security → Accessibility**. Restart the helper if needed. The menu-bar S provides pause, restore and quit.
4. Try **⋯ → 使用本地草稿** first with the [public fixture](testing.md). Review, Replace, then click the helper's Undo button.
5. The package includes 14 domain recommendations and 17 methods. No Python or configuration scripts are needed. Choose a personal method in **menu-bar S → 领域方法** or **toolbar ⋯ → 领域方法**; for example **学术讨论 → 苏格拉底式提问**. Choose **跟随内置建议** to reset it. The next refinement uses the saved choice.

## If the switch is locked or enabling it has no effect

Open **S → 授权与设置…**. Starting the helper without effective permission also shows this guide. Use **打开辅助功能设置**, or follow **Apple menu → System Settings → Privacy & Security → Accessibility**. This is different from the Accessibility section in the settings sidebar.

Complete any password or Touch ID confirmation in macOS itself. Return to the helper and click **重新检查**: its actual trust check must say **已授权**. A lit system switch alone does not establish that the running copy has access.

If it still says **尚未生效**, use **在访达显示当前 App** to identify this copy. Remove only Snapper Assist from the permission list, then add that same installed copy with “+” and enable it. **复制应用路径** lets you paste its path into the file picker with ⌘⇧G. Do not select Preview. Recheck, restarting the helper if needed. Record the exact message if it remains blocked; do not reset other apps' permissions or enable Full Disk Access.

Ad-hoc builds may need renewed approval after an update. Keeping the installation path and Bundle ID stable reduces ambiguity but cannot guarantee continuity of macOS permission.

## AI mode

0.10 defaults to shared AI: friends do not need Codex, an API key, or the maintainer's login. Open **共享 AI 与邀请码…** from the permission guide or menu-bar S, paste a private invitation from the maintainer, and click **连接／保存选择**.

**Real model billing is currently disabled at the maintainer's request.** A successful connection says the invitation is connected but billing is off, with zero allowances. This verifies access, not successful AI generation. Use **⋯ → 使用本地草稿** to test replacement and Undo without a model request.

Invitations bind to one device, expire, and can be revoked. Once a budget is separately approved and the maintainer enables generation, only clicking AI refinement sends selected text and confirmed method preferences through the relay to TideVerse. The service normally selects methods and then refines in two model calls. Disabled shared mode does not silently fall back to another paid account.

**本机 Codex · 保留原有接入** remains an explicitly selected alternative for existing compatible local setups. It uses the prior fixed CLI path and file-backed login; this is not required for shared mode. See [shared-service details](shared-ai.zh-CN.md) and [Privacy](../PRIVACY.md).

## Updates and removal

Automatic updates and launch at login are not configured. Quit before replacing the app. A different ad-hoc build may require renewing Accessibility permission. To remove it, quit, remove the app and remove its Accessibility entry. Optional local state is described in [Privacy](../PRIVACY.md).
