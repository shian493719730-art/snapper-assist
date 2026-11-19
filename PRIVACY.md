# Privacy and permissions

Snapper Assist uses macOS Accessibility to observe the focused app's selected text and source field. Full input text is read locally for exact edit verification, so a successful write cannot be inferred from an API return code alone. This permission is system-wide; grant it only to a copy you trust.

Selection, undo text and the small response cache remain in app memory. Copy/compatibility-paste temporarily uses the system clipboard and restores it only while the app still owns that clipboard change; a newer user copy takes precedence.

When the user clicks AI refinement, selected text, candidate Skill descriptions, confirmed method preferences and the selected editing instructions are passed to the existing Codex CLI. This uses the tester's own account and provider data policy. The helper does not promise cloud zero retention. Selection alone and local drafts do not issue a model request.

An AI invocation creates a private temporary profile and schema/result files, removed on normal completion or cancellation. The profile links the user's existing file-backed CLI login without copying its contents. Project documents, skill/plugin discovery and unrelated tools are disabled for this invocation. Missing credentials fail back to the local draft. A crash may leave temporary files until OS cleanup; the app does not claim every path is disk-free.

Optional local state:

- `~/.codex/agent-learning-loop/selection-status.json`: version, permissions, counts, strategy, restoration equality/length deltas and source-field dimensions. No selected text or clipboard contents.
- `~/.codex/agent-learning-loop/knowledge.json` and `prompt-recipes.json`, if present: optional local method overrides. Otherwise packaged snapshots are used.
- `~/.codex/agent-learning-loop/domain-preferences.json`, when domain preferences are configured: method choices and provenance, per-domain “follow suggestion” flags, plus optional manual feedback counts; no selected text or chat history. The app menu saves choices here without a model request. Existing feedback and unrelated profile fields are preserved. See [domain preferences](docs/preferences.md).
- App preferences under `local.snapper.assist`: pause and per-app exclusions.

The release contains no developer credential, chat, private project, scheduled task or analytics backend. Weekly research automation is not installed by the app. Folder scanning and Full Disk Access are not required for the selected-text workflow. Report unexpected requests without posting private data.


## Skill-aware refinement

After a deliberate AI request, the app reads ordinary local Skill instruction files under `.codex/skills` and `.codex/skills/.system`, skipping symbolic links into other projects. Bundled public method cards remain available even when local Skills exist. The first model pass receives the original selection, candidate descriptions and confirmed domain method IDs. Only the selected instruction bodies (up to four) accompany the second pass. Skill scripts are not run and the selected task is not executed. The local prefab draft is no longer sent as the AI editing basis. These AI calls use the existing Codex login only after the user clicks; this update's automated checks did not send paid generation requests.
