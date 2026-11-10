# Contributing

Start with a reproducible [bug report](https://github.com/shian493719730-art/snapper-assist/issues/new?template=bug_report.yml) or a small pull request. Preserve source-app focus, selection, existing drafts and clipboard ownership. Keep paid model calls explicitly user-triggered. Do not add account data or private app content to examples or fixtures.

## Build and verify

Use macOS 26+ with a macOS 26 SDK and Swift:

```sh
python3 desktop/build-native.py --output "$HOME/Library/Caches/SnapperAssist/build/Snapper Assist.app"
"$HOME/Library/Caches/SnapperAssist/build/Snapper Assist.app/Contents/MacOS/SnapperAssist" --self-test
python3 scripts/check_source.py
python3 scripts/test_preferences.py
python3 scripts/test_package_methods.py
```

The native checks include UTF16 selections, no-op AX writes, stale focus, guarded fallback, native Undo result verification, whitespace observations, prompt-boundary preservation, method applicability and memory-cache scope. The finished 0.8 app also runs 49 bundled/fresh-profile method checks. They do not prove real editor compatibility.

For actual native construction of domain-aware Chinese prompts, without launching app UI or a model:

```sh
swiftc -O desktop/native/SelectionCore.swift desktop/native/PromptPreparation.swift desktop/native/DomainMethods.swift desktop/native/PreferenceProbe.swift -o /tmp/snapper-preference-probe
python3 scripts/test_preferences.py --native-probe /tmp/snapper-preference-probe
```

Without that optional probe, the native routing test is explicitly skipped. The Python checks cover preference provenance, candidate confirmation, isolation, invalid data, atomic writes and preservation of local customizations. [Domain preferences](docs/preferences.md) documents current language/UI limits.

With your own compatible CLI login, the optional metadata-only startup check is:

```sh
swiftc -O desktop/native/RefinementLaunch.swift desktop/native/RefinementLaunchProbe.swift -o /tmp/snapper-refinement-probe
python3 desktop/test/refinement-startup.py --driver /tmp/snapper-refinement-probe
```

It initializes an ephemeral session and reads account/skill metadata without starting a model turn. It must never send `turn/start`. No paid request belongs in automated tests. Manual interaction checks use the [beta checklist](docs/testing.md), with actual and untested outcomes kept separate.

Rebuilding may change macOS permission identity. Avoid needless rebuilds while collecting live acceptance. The current public beta has no signed updater or notarization pipeline.

The 0.8 build compiles public recommendations and all domain choices into the app. It never reads the builder’s personal profile. The packaged executable also supports `--check-bundled-methods`, which tests fresh temporary preferences, all bundled choices and persistence without UI or model calls.
