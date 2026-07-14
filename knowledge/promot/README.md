# 大型结构提示词入口

优先从 [`large_structure_workflow/SKILL.md`](large_structure_workflow/SKILL.md) 开始。它规定 AI 与确定性脚本的边界，以及从 `BRIEF.md` 到一次构建通过的完整流程。

按项目需要再读取：

- [`BOSS_STRUCTURE_SKILL.md`](BOSS_STRUCTURE_SKILL.md)：大型 Boss 建筑、路线、空间、叙事和验收质量。
- [`CHINESE_ARCHITECTURE_SKILL.md`](CHINESE_ARCHITECTURE_SKILL.md)：中式屋顶、构架、院落、材料和专项审计。
- [`../reference/chinese_prototype_catalog.md`](../reference/chinese_prototype_catalog.md)：三个中式样板脚本的函数级选型、优先级和采用证据契约。
- [`../reference/chinese_enclosure_interior_lighting_rules.md`](../reference/chinese_enclosure_interior_lighting_rules.md)：中式建筑围护封闭、房间程序、内饰通行与照明覆盖。
- [`../reference/chinese_city_defense_structural_quality_rules.md`](../reference/chinese_city_defense_structural_quality_rules.md)：城台门楼、城墙巡道、荷载路径和浮空细部规则。
- [`../reference/chinese_detail_placement_quality_rules.md`](../reference/chinese_detail_placement_quality_rules.md)：铁链锚固、楼梯/旋转方块状态、植物基底与园林构图规则。
- [`../reference/chinese_metropolis_planning_and_variation_rules.md`](../reference/chinese_metropolis_planning_and_variation_rules.md)：超大型都城扇区规划、建筑签名去重、水陆交通、生活服务链和创新地标规则。
- [`large_structure_workflow/PROMPT_TEMPLATE.md`](large_structure_workflow/PROMPT_TEMPLATE.md)：可以直接交给 AI 的任务模板。

稳定工具不放在提示词中重复生成，统一由 `scripts/structure_work.py` 调用。
