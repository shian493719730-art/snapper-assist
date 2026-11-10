# Five-minute beta test

Use only synthetic text. Do not send the test message. Local tests need no AI request.

```text
Before [keep A🙂]
Help me make a study plan🙂. Keep my existing materials. Do not send messages.
After [keep B]
```

1. In TextEdit, select only the middle line, excluding its newline. Choose **⋯ → 使用本地草稿**.
2. Review and click **替换选中文字**. Only the middle selection should change; surrounding lines and emoji stay intact. Check for blank space outside the suggested text.
3. Click the helper's **撤回上次替换** button, not keyboard Undo. The full original text and original selection should return, without extra blank space.
4. Deselect and reselect the same fragment. Repeat Replace → helper Undo for three rounds. Record each round independently.
5. Repeat in a browser's ordinary input and a rich-text field, retaining bold/italic text outside the selection. Do not assume one app proves another.

Extra cases: select only the second occurrence of repeated text; change the source/selection after opening a draft; rapidly alternate two selections; disable and restore the app through the helper's menu. Stale results should never overwrite a new selection.

AI is optional and uses your own compatible account setup. With a non-sensitive selection, click **AI 完善** once. Check visible waiting status, a returned suggestion and absence of extra folder-access prompts. Do not grant Documents or Full Disk Access merely to complete the test.

## Record the result

| Environment / case | Expected | Actual | Status |
| --- | --- | --- | --- |
| Mac/chip and macOS version | Meets release requirements | Fill in | Untested |
| App + source app/version | Identified | Fill in | Untested |
| First Replace | Exact selection only, no extra blank area | Fill in | Untested |
| Helper Undo | Exact original text and selection | Fill in | Untested |
| Rounds 2–3 | Toolbar reopens, no duplicate or shifted writes | Fill in | Untested |
| Browser / rich text | Surrounding content and styles preserved | Fill in | Untested |
| AI, if tested | User-triggered result, no folder prompt | Fill in | Untested |

Report [a bug](https://github.com/shian493719730-art/snapper-assist/issues/new?template=bug_report.yml) with the shortest steps, expected/actual result and app versions. Use only test text in screenshots. Never attach credentials or private drafts.
