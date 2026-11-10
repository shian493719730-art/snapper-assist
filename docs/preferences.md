# Domain preferences / 分领域偏好

Snapper can use different editing methods for different kinds of request. The expandable [method catalog](method-catalog.md) covers 14 seed directions with source-backed suggestions. A preference for Socratic dialogue in academic discussion does not imply that study plans, email drafts or bug fixes should become a question-and-answer exercise.

**The 0.8 beta includes the methods and an in-app menu.** Fourteen domain recommendations are enabled in the package. Open **menu-bar S → 领域方法**, or **selection toolbar ⋯ → 领域方法**, choose a domain and a method. For academic discussion, choose “苏格拉底式提问”. Choose “跟随内置建议” to remove that personal choice and use the default again. Selections are saved locally and apply to the next refinement; no script, Python installation, model request or restart is needed.

The menu is unavailable while generation, replacement or an applied edit is active, so changing methods does not interrupt a request or disturb an Undo record. Existing local recipe overrides and personal state remain local. The developer's own choices are not bundled. Automatic feedback collection from Replace/Undo is not connected.

The earlier 0.7.1 loader can use compiled method data through the advanced source tools below; its binary does not include this menu. A newly built 0.8 app may require renewing Accessibility permission when replacing an earlier ad-hoc build.

## What is remembered

- **Explicit preference:** a user statement or a deliberately confirmed candidate can select a method for a named domain.
- **Candidate:** manual accept/reject/undo feedback stores counts only. Three accept signals can suggest a candidate; they cannot confirm or activate it. This is a product heuristic, not proof of preference or quality.
- **Current request wins:** direct-answer/no-question/no-Socratic instructions override the stored preference in the prepared editing guidance.
- **Separate domains:** changing academic discussion does not change argument review or other tasks. Removing a preference removes only its generated recipe.

Personal state lives in `~/.codex/agent-learning-loop/domain-preferences.json`, with private file permissions. It contains domain/method IDs, explicit-vs-confirmed provenance, timestamps and optional feedback counts. It does not contain selected text or chat logs. The public repository ships a method library, not the developer's confirmed preferences.

No app history or private folders are scanned. Referencing a method or skill is not authorization to install or run its code. Only the applicable prepared editing instructions accompany a deliberate AI request.

## Optional setup

For advanced automation, run from a source checkout. Most 0.8 users can use the menu above. These example commands are an explicit choice, not a universal default:

```sh
python3 scripts/preferences.py remember --domain academic-dialogue --method socratic-dialogue --origin explicit-user
python3 scripts/preferences.py compile --apply
```

`argument-review` is a separate domain. `argument-map` is available as a direct analysis alternative. `list` shows local state. To remove one domain:

```sh
python3 scripts/preferences.py forget --domain academic-dialogue
python3 scripts/preferences.py compile --apply
```

Compilation preserves unrelated local recipes, validates native limits, writes atomically, and keeps a private last-version backup. The recipe revision is derived from its content, so a method change invalidates the existing in-memory AI cache. Run compile again after deliberately replacing the local recipe catalog with a newer research snapshot.

Optional public suggestions can be enabled with `python3 scripts/preferences.py recommendations on`, then `compile --apply`. They are labeled as suggestions, and never become confirmed preferences. Known native recipe families retain their IDs so coding/evidence rules keep working; changing a customized family requires resolving the actual conflict rather than silently dropping its instructions. The scheduled publisher uses a three-way source refresh and reapplies preferences in a single transaction.

Manual feedback and candidate confirmation are optional:

```sh
python3 scripts/preferences.py feedback --domain argument-review --method socratic-dialogue --signal accept
python3 scripts/preferences.py list
# Only after reviewing a proposed candidate:
python3 scripts/preferences.py remember --domain argument-review --method socratic-dialogue --origin confirmed-candidate
python3 scripts/preferences.py compile --apply
```

## Method and current limits

The Socratic profile helps reconstruct a claim, clarify concepts, examine premises/evidence, and consider counterexamples or boundaries. It asks the later discussion assistant to use one consequential question at a time, wait for an answer, and summarize when useful. It does not make the prompt editor conduct the discussion itself. Avoiding leading questions and honoring a request for a direct answer are product choices.

Sources: [Plato's Meno, translated by Jowett](https://classics.mit.edu/Plato/meno.html), for dialogue about definitions and examples; [University of Antwerp teaching guidance](https://www.uantwerpen.be/en/centres/centre-expertise-higher-education/didactic-information/teaching-tips/activating-students/socratic-method/), for clear questions and room to answer. This is a modern adaptation, not a claim that every practice here was prescribed by Socrates or improves every task.

Local domain selection uses keywords, with an explicit domain label followed by a colon taking priority. Ambiguous or unrecognized requests can fall back to the general recipe. The English-only local scaffold remains generic; **detailed preference construction is validated in Chinese, not full English preference behavior**. There is no background model call to infer a domain. New AI outputs, conversational quality and user preference gains still require deliberate user testing.

## 中文说明

0.8 安装包默认附带 14 类建议、17 种可选方法，不需要另外下载方法数据。通过“菜单栏 S → 领域方法”或“浮条 ⋯ → 领域方法”直接选用；“学术讨论”和“观点推敲”可分别选择苏格拉底式对话或论证梳理。选“跟随内置建议”可恢复默认。没有选择时只显示建议，不冒充个人喜好。生成、替换或待撤回时不能修改偏好，避免打断当前操作。

苏格拉底式提问以“准确理解 → 澄清概念/前提/证据 → 反例与边界 → 根据回答继续”为方向，每次只问一个关键问题。它是后续对话的交互要求，助手本身仍只完善选文。若本次要求“直接给结论”“不要提问”或“不用苏格拉底法”，以本次要求为先。

偏好只在自己的电脑保存；不会带上开发者的个人选择。改变菜单选项不调用模型，下次完善即使用新选择。中文构建已有本地检查；跨软件自动学习、全量聊天分析和任意 Skill 自动执行未实现。收费模型的实际输出继续由使用者点击验收。
