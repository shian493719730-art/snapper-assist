# 方法目录：从案例和原生分类到适用建议

截至 2026-11-10，种子目录覆盖 **14 个方向、17 个方法条目和 36 条方法来源记录**，包含具体方法正文、仓库 README、示例目录和分类页面。另有 [31 个来源、1,182 项条目的发现库](source-discovery.md)，保留索引、章节审读和正文审读的区别。它们是可扩展的起点，不是对所有 AI 案例的穷举，也不代表这些方法都已运行验证。

| 方向 | 可选方法 | 主要依据 |
| --- | --- | --- |
| 学术讨论 | 苏格拉底式对话、论证梳理 | [Meno](https://classics.mit.edu/Plato/meno.html)、[提问节奏](https://www.uantwerpen.be/en/centres/centre-expertise-higher-education/didactic-information/teaching-tips/activating-students/socratic-method/) |
| 观点推敲 | 主张、依据、反例与边界 | [Fabric claims](https://github.com/danielmiessler/fabric/blob/main/data/patterns/analyze_claims/system.md) 的独立适配 |
| 学习复习 | 提取练习与按需间隔安排 | [Learning Scientists](https://www.learningscientists.org/blog/2016/8/18-1) |
| 研究与证据 | 问题、证据、冲突与缺口 | Fabric；[PRISMA 入口](https://www.prisma-statement.org/prisma-2020-checklist)仅作为正式综述规范线索 |
| 软件排查 | 复现、定位、实现与验证 | [Lauren Tan / pstack](https://github.com/cursor/plugins/tree/main/pstack) |
| 界面交互 | 任务路径与可用性检查 | [Nielsen heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) |
| 写作编辑 | 读者、目的与可理解性 | [Google Technical Writing](https://developers.google.com/tech-writing/one/audience)、[doc-coauthoring](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md) |
| 创意构思 | 有区别的方向与有条件收敛 | [Stanford d.school](https://dschool.stanford.edu/tools/design-thinking-bootleg)资源页作为方法线索；不分发卡片内容 |
| 数据分析 | 探索分布、异常与假设 | [NIST EDA](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm) |
| 决策取舍 | 方案比较与失败预演 | [Gary Klein](https://www.gary-klein.com/premortem) |
| 产品需求 | 结果、用户证据与假设试验 | [Teresa Torres](https://www.producttalk.org/opportunity-solution-trees/) |
| 自动化与 Agent | 根据任务选择流程或路由 | [Anthropic workflows](https://www.anthropic.com/research/building-effective-agents)，保留文章的工具版本提醒 |
| 知识资料 | 围绕用途组织与检索 | [Tiago Forte / PARA](https://fortelabs.com/blog/para/) |
| 沟通协作 | 对象、重点、行动与卡点 | [internal-comms](https://github.com/anthropics/skills/blob/main/skills/internal-comms/SKILL.md)、Google audience |

## 保留来源自己的分类

新增可选方法为“上下文接续”“结果验收”“证据图表”，分别可用于长任务交接、按真实需求比较结果、科学图表规划。默认方法和个人确认的选择保持独立；这些方法需要匹配任务或明确选择，不机械叠加到每条请求中。已有调试、研究和自动化方法也补充了审读来源与适用判断。具体审读范围、未采用的规则和维护问题见 [发现库说明](source-discovery.md)。

统一索引同时记录领域、任务、方法、交付物、交互方式和证据状态。原站的标签、目录名、组织方式另外保存，映射标为可修改的编辑判断。

- [Fabric](https://github.com/danielmiessler/fabric) 主要按任务 pattern 组织；读取了 claims 和 summarize 的具体方法。
- [Anthropic Skills](https://github.com/anthropics/skills) 包含不同用途的 Skill 目录；读取了文档共创和内部沟通正文，其他目录仅作为发现线索。
- [prompts.chat](https://prompts.chat/prompts) 提供类型、类别和标签等入口；用户投稿数量不是效果证据。
- [DAIR.AI](https://www.promptingguide.ai/) 区分技术、应用与提示词案例；[DSPy](https://dspy.ai/current/) 按程序结构和评估优化组织。它们不应被压扁成同一种“角色提示词”。
- [openai/skills](https://github.com/openai/skills) 的 README 已注明弃用并指向 [openai/plugins](https://github.com/openai/plugins)。索引保留迁移记录，而不是按星数继续推荐旧入口。

当前并未复制完整第三方 Prompt、Skill 或代码，也未安装或执行它们。许可证、按项条款和阅读范围保留在 [机器可读目录](../skills/agent-learning-loop/references/domain-methods.json) 中。

## 不照单全收

Fabric claims 的分解方式可供参考；其立场标签、真伪等级和强制推理话术没有采用。固定摘要条数和字数不作为通用约束。PRISMA 本轮只读了规范入口，未逐项审计清单，因此不声称符合正式系统综述标准。d.school 卡片受非商业共享许可约束，本项目只链接资源页并独立表达一般创意建议。

每个方法都记录“适用什么、何时不用、如何检查”。已有框架是可替换的工具，新的证据、用户反馈或更合适的方法可以改变分类和建议。

## 使用与更新

```sh
python3 scripts/method_catalog.py inventory
python3 scripts/method_catalog.py search SQL
python3 scripts/method_catalog.py plan --output /tmp/method-review-plan.json
python3 scripts/preferences.py recommendations on
python3 scripts/preferences.py compile --apply
```

启用后，匹配到的普通推荐标为“建议”，不写成个人已确认偏好；已确认选择优先。关闭可用 `recommendations off` 后重新编译。个人选择仍按 [偏好说明](preferences.md) 单独保存。

当前 0.7.1 使用本地关键词初筛，已验证的是中文提示词构建和既有原生配方适配。模糊、多领域或未识别输入仍可能需要修正。应用只是完善请求，不会执行所引用的方法、自动检索 GitHub、调用其他 Agent 或代发收费请求。新建议的模型输出质量未做独立比较。

每周研究由使用者配置的宿主工作流完成，安装包不附带开发者的自动任务。更新路径应先检查来源与分类，再检查本地构建、个人偏好和冲突，最后原子发布方法数据；不重签原生应用。完整作者扫描与案例目录扫描互相补充，未读或延后项应保留记录，检索计划不等于研究已经执行。
