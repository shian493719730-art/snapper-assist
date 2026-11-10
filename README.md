<div align="center">
  <img src="assets/icon.svg" width="96" alt="Snapper Assist icon">
  <h1>Snapper Assist</h1>
  <p><strong>A clearer prompt, right where you're writing.</strong></p>
  <p>Select text → refine → review → replace or undo.</p>
  <p>
    <a href="https://github.com/shian493719730-art/snapper-assist/releases/tag/v0.7.1-beta.1">Download the beta</a> ·
    <a href="docs/install.md">Install & AI setup</a> ·
    <a href="docs/testing.md">Test & report a bug</a> ·
    <a href="README.zh-CN.md">简体中文</a>
  </p>
  <p>macOS 26+ · Apple silicon · Native Swift/AppKit · MIT</p>
</div>

Snapper Assist turns selected text into a more actionable request without moving you into a separate editor. A small, non-activating Liquid Glass panel appears beside the selection. You decide whether to use AI, keep a local draft, apply the suggestion, or undo it.

**Public beta:** the current download is ad-hoc signed and not notarized. AI mode requires a compatible existing Codex CLI installation and your own saved login. Please read the [requirements](docs/install.md) before testing.

![Workflow diagram: select text, refine and review, then replace or undo](assets/workflow.svg)

## Get started

1. [Download the Apple-silicon beta ZIP](https://github.com/shian493719730-art/snapper-assist/releases/download/v0.7.1-beta.1/Snapper-Assist-0.7.1-macOS26-arm64-beta.zip), unzip it, and move **Snapper Assist.app** into Applications.
2. Enable that copy in **System Settings → Privacy & Security → Accessibility**.
3. Select a short, non-sensitive test request in TextEdit. Choose **⋯ → 使用本地草稿** to try a local draft without sending a model request.

When your own [AI setup](docs/install.md#ai-mode) is ready, click **AI 完善** once to generate a suggestion. The app currently uses Chinese interface labels; English input receives an English-oriented preparation scaffold.

## What it does

| Feature | What you control |
| --- | --- |
| Selection-side assistance | A compact panel beside your text; the source app keeps focus. |
| One-click AI refinement | Only your deliberate click starts generation. A spinner and elapsed time show that the request is still processing. |
| Local draft fallback | Six task families: study, coding, design, research, writing and general requests. No model request needed. |
| Review before writing | Inspect or copy the result. Nothing is replaced until you click Replace. |
| Guarded replace and undo | Validate the source, selection and actual resulting text. Verified pastes prefer the source app's native Undo. |
| Per-app controls | Disable the toolbar in an app, then restore it from the menu bar. |
| Traceable methods | Curated, attributed collaboration rules rather than a promise of a universal “perfect prompt.” |

The editing policy preserves stated facts and constraints, marks inferred requirements as unconfirmed, and asks only for consequential gaps. For relevant problem-solving tasks it favors available evidence and useful existing implementations, while allowing alternative decompositions and testable new approaches. The helper edits the request; it does not execute the selected task or automatically search GitHub.

## Privacy and account use

- Selecting text alone does not send it to a model.
- The selected text and relevant editing context are sent through your existing Codex account only when you click AI refinement. That uses your account's available usage.
- The current input's full text is read locally to verify a targeted edit. Undo state and the response cache stay in memory.
- Each AI call uses a temporary, isolated profile. It links your own saved CLI login without copying the credential contents, and disables project/skill/plugin discovery for this text-editing call.
- No developer account, chat history, personal project, research schedule or analytics service is bundled.

See [Privacy](PRIVACY.md) for temporary files and data boundaries.

## Current validation and limits

On the development Mac, the extracted beta passed **66 native regression checks** and strict signature verification. A user-assisted chat-input round confirmed first replacement without extra blank space, and native Undo restoring the exact original text and selection. AI generation and visible waiting status were also user-tested.

These results do **not** establish a fresh installation on every Mac or universal editor compatibility. Three-cycle stability, duplicate/stale/rapid selection cases, and complete TextEdit/Chrome interaction coverage remain open beta checks. Read-only, protected or inaccessible fields may only support copying. Windows and Intel Mac binaries are not provided. Model-quality, latency and novelty improvements have not been independently measured.

## Build from source

Requires an Apple-silicon Mac, macOS 26 SDK/Swift and the system signing tools.

```sh
python3 desktop/build-native.py --output "$HOME/Library/Caches/SnapperAssist/build/Snapper Assist.app"
"$HOME/Library/Caches/SnapperAssist/build/Snapper Assist.app/Contents/MacOS/SnapperAssist" --self-test
```

Rebuilding changes the ad-hoc identity and may require renewing the app's Accessibility permission. It does not authorize broader folder access. See [Contributing](CONTRIBUTING.md) for no-model checks.

## Help test the beta

Use the [test guide](docs/testing.md) and [bug report form](https://github.com/shian493719730-art/snapper-assist/issues/new?template=bug_report.yml). Include the Mac/OS, source app/version, exact steps and what actually happened. Leave untested cases untested, and use synthetic text in screenshots.

## Methods and acknowledgements

The local knowledge snapshot includes ideas attributed to Lauren Tan / pstack, Ethan Mollick, Addy Osmani, Simon Willison and other primary sources. Methods are selected by task; source inclusion is not proof of a general model-quality benefit. The beta ships a snapshot, not the developer's weekly research automation. [Method notes and source links](docs/methods.md).

The project is an independent implementation. [MIT license](LICENSE).
