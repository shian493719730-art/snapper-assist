# Install the beta

## Requirements

| Item | Current beta |
| --- | --- |
| Hardware | Apple-silicon Mac, M1 or newer |
| System | macOS 26 or newer |
| App permission | Accessibility for the installed copy |
| Local draft | No model account or network request required |
| AI | Compatible existing Codex CLI, saved file login and available account usage |

The ZIP is ad-hoc signed, not Developer-ID signed or notarized. Fresh-machine installation has not yet been verified. macOS may block the first launch. Record the exact message if blocked; do not disable system-wide security controls for this beta. [Apple's guidance](https://support.apple.com/102445).

1. Download the ZIP from the [release](https://github.com/shian493719730-art/snapper-assist/releases/tag/v0.8.0-beta.1).
2. Unzip and move **Snapper Assist.app** to Applications or your own Applications folder before granting permission.
3. Open the app. Enable this copy in **System Settings → Privacy & Security → Accessibility**. Restart the helper if needed. The menu-bar S provides pause, restore and quit.
4. Try **⋯ → 使用本地草稿** first with the [public fixture](testing.md). Review, Replace, then click the helper's Undo button.
5. The 0.8 package already includes 14 domain recommendations and 17 methods. No Python or configuration scripts are needed. Choose a personal method in **menu-bar S → 领域方法** or **toolbar ⋯ → 领域方法**; for example **学术讨论 → 苏格拉底式提问**. Choose **跟随内置建议** to reset it. The next refinement uses the saved choice.

## AI mode

This beta currently looks for the CLI at this fixed path:

```text
/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex
```

It uses your own saved `~/.codex/auth.json`, or the corresponding file under an inherited `CODEX_HOME`. The development machine tested CLI `0.166.0-alpha.6`; other versions, installation layouts and keychain-only credentials have not been validated. Having a different Codex installation is not enough to establish compatibility with this build. You can still test local drafts if this setup is unavailable.

Use your own account. Do not copy someone else's `auth.json`, password or API key. An unavailable CLI/login leaves the local draft available; the helper does not configure a new API key or switch accounts.

With a compatible setup, selecting text and clicking **AI 完善** starts one explicit request using your account usage. Observe the spinner and elapsed seconds, then review the result. Selection alone never starts generation. A repeated, unchanged request in the same field can return the short-lived memory cache.

If a Documents-folder or Full Disk Access prompt appears, cancel and report it. The selected-text workflow does not need that broader access.

## Updates and removal

Automatic updates and launch at login are not configured. Quit before replacing the app. A different ad-hoc build may require renewing Accessibility permission. To remove it, quit, remove the app and remove its Accessibility entry. Optional local state is described in [Privacy](../PRIVACY.md).
