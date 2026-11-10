# Domain preferences / 分领域偏好

Snapper can use different editing methods for different kinds of request. A preference for Socratic dialogue in academic discussion does not imply that study plans, email drafts or bug fixes should become a question-and-answer exercise.

This optional data layer works with the installed 0.7.1 app's live recipe loader; rebuilding, re-signing, restarting and renewed Accessibility permission are not required. It is currently managed by the collaboration agent or the commands below, **not a new in-app settings screen**. Automatic feedback collection from Replace/Undo buttons is not connected.

## What is remembered

- **Explicit preference:** a user statement or a deliberately confirmed candidate can select a method for a named domain.
- **Candidate:** manual accept/reject/undo feedback stores counts only. Three accept signals can suggest a candidate; they cannot confirm or activate it. This is a product heuristic, not proof of preference or quality.
- **Current request wins:** direct-answer/no-question/no-Socratic instructions override the stored preference in the prepared editing guidance.
- **Separate domains:** changing academic discussion does not change argument review or other tasks. Removing a preference removes only its generated recipe.

Personal state lives in `~/.codex/agent-learning-loop/domain-preferences.json`, with private file permissions. It contains domain/method IDs, explicit-vs-confirmed provenance, timestamps and optional feedback counts. It does not contain selected text or chat logs. The public repository ships a method library, not the developer's confirmed preferences.

No app history or private folders are scanned. Referencing a method or skill is not authorization to install or run its code. Only the applicable prepared editing instructions accompany a deliberate AI request.

## Optional setup

Run from a source checkout. These example commands are an explicit choice, not a universal default:

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

Local domain selection currently uses the existing keyword router. Ambiguous or unrecognized requests can fall back to the general recipe. The 0.7.1 native English-only local scaffold remains generic; **this iteration validates Chinese preference instructions, not full English preference behavior**. There is no background model call to infer a domain. New AI outputs, conversational quality and user preference gains still require deliberate user testing.

## 中文说明

目前可分别为“学术讨论”和“观点推敲”保存苏格拉底式提问或论证梳理偏好。只保存明确表达或确认的选择；重复接受只能形成候选，撤回一次不代表长期不喜欢。其他领域继续使用原有配方，不推测用户也喜欢某种方法。

苏格拉底式提问以“准确理解 → 澄清概念/前提/证据 → 反例与边界 → 根据回答继续”为方向，每次只问一个关键问题。它是后续对话的交互要求，助手本身仍只完善选文。若本次要求“直接给结论”“不要提问”或“不用苏格拉底法”，以本次要求为先。

本轮通过既有热加载接口更新本机方法数据，没有重建应用或改变授权。匹配是关键词初筛，中文提示词构建已做本地检查；反馈按钮、跨软件自动学习、全量聊天分析、任意 Skill 自动执行均未实现，也不会声称已经实现。收费模型的实际输出继续由用户点击验收。
