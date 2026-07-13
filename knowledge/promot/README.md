# 大型结构提示词入口

优先从 [`large_structure_workflow/SKILL.md`](large_structure_workflow/SKILL.md) 开始。它规定 AI 与确定性脚本的边界，以及从 `BRIEF.md` 到一次构建通过的完整流程。

按项目需要再读取：

- [`BOSS_STRUCTURE_SKILL.md`](BOSS_STRUCTURE_SKILL.md)：大型 Boss 建筑、路线、空间、叙事和验收质量。
- [`CHINESE_ARCHITECTURE_SKILL.md`](CHINESE_ARCHITECTURE_SKILL.md)：中式屋顶、构架、院落、材料和专项审计。
- [`large_structure_workflow/PROMPT_TEMPLATE.md`](large_structure_workflow/PROMPT_TEMPLATE.md)：可以直接交给 AI 的任务模板。

稳定工具不放在提示词中重复生成，统一由 `scripts/structure_work.py` 调用。
