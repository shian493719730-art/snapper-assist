# Contributing

Start with a reproducible [bug report](https://github.com/shian493719730-art/snapper-assist/issues/new?template=bug_report.yml) or a small pull request. Preserve source-app focus, selection, existing drafts and clipboard ownership. Keep paid model calls explicitly user-triggered. Do not add account data or private app content to examples or fixtures.

## Build and verify

Use macOS 26+ with a macOS 26 SDK and Swift:

```sh
python3 desktop/build-native.py --output "$HOME/Library/Caches/SnapperAssist/build/Snapper Assist.app"
"$HOME/Library/Caches/SnapperAssist/build/Snapper Assist.app/Contents/MacOS/SnapperAssist" --self-test
python3 scripts/check_source.py
```

The native checks include UTF16 selections, no-op AX writes, stale focus, guarded fallback, native Undo result verification, whitespace observations, prompt-boundary preservation, method applicability and memory-cache scope. They do not prove real editor compatibility.

With your own compatible CLI login, the optional metadata-only startup check is:

```sh
swiftc -O desktop/native/RefinementLaunch.swift desktop/native/RefinementLaunchProbe.swift -o /tmp/snapper-refinement-probe
python3 desktop/test/refinement-startup.py --driver /tmp/snapper-refinement-probe
```

It initializes an ephemeral session and reads account/skill metadata without starting a model turn. It must never send `turn/start`. No paid request belongs in automated tests. Manual interaction checks use the [beta checklist](docs/testing.md), with actual and untested outcomes kept separate.

Rebuilding may change macOS permission identity. Avoid needless rebuilds while collecting live acceptance. The current public beta has no signed updater or notarization pipeline.
