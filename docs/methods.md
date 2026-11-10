# Methods, not magic prompts

The helper selects relevant rules and small task recipes, keeps original facts/constraints and labels inferred requirements as unconfirmed. It does not execute source text as instructions. Ordinary prose should not inherit an engineering checklist; a study request should not gain irrelevant budget or GitHub boilerplate.

| Source | Bounded idea used |
| --- | --- |
| [Lauren Tan / pstack](https://github.com/cursor/plugins/tree/main/pstack) | Make outcomes observable; verify real user journeys. |
| [Ethan Mollick](https://www.oneusefulthing.org/p/a-guide-to-prompting-ai-for-what) | Relevant context, constraints and iterative clarification. |
| [Addy Osmani](https://addyosmani.com/blog/ai-coding-workflow/) | Small, checkable work units for engineering tasks. |
| [Simon Willison](https://simonwillison.net/guides/agentic-engineering-patterns/agentic-manual-testing/) | Exercise the delivered behavior and disclose test coverage. |
| [OpenAI prompting guidance](https://developers.openai.com/api/docs/guides/prompt-engineering) | Explicit tasks, context and evaluation. |

The broader source list and checked dates are in `desktop/knowledge.json`; task recipes are in `skills/agent-learning-loop/references/prompt-recipes.json`. This beta ships snapshots. It does not install the developer's weekly source-research task on testers' Macs.

Separately, the product's problem-solving preference is to reuse relevant evidence and existing implementations, question inherited assumptions, and compare testable alternatives. Coding requests may include evaluating suitable GitHub projects; explicit offline/no-open-source constraints take precedence. These preferences are not attributed to an external author, and the text editor does not claim to have searched anything.

Local checks establish behavior and constraints, not broad gains in model quality, latency or novelty. Independent comparisons remain unperformed.
