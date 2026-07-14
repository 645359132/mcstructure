---
name: build-ai-structure-work
description: Builds a complete AI-authored Minecraft Bedrock structure work whose source can be exported by the repository's deterministic workflow. Use when a user wants to turn a building brief into a workset source package and main.py, then automatically generate mcstructure, NetEase feature rules, dimension files, and ModSDK placement resources.
---

# Build AI Structure Work

将建筑创作与平台工程严格分开：AI 只实现建筑源码和 work 入口，共享脚本拥有全部生成输出。

## 先读取

1. 读取目标 work 的 `BRIEF.md`、`project.json`、`main.py` 和 `src/`。
2. 读取 [WORK_CONTRACT.md](WORK_CONTRACT.md)，确认 builder、画布、坐标和禁止修改范围。
3. 涉及大型地标、Boss 场景或复杂路线时读取 [../BOSS_STRUCTURE_SKILL.md](../BOSS_STRUCTURE_SKILL.md)。
4. 涉及中式建筑时读取 [../CHINESE_ARCHITECTURE_SKILL.md](../CHINESE_ARCHITECTURE_SKILL.md) 和 [../../reference/chinese_prototype_catalog.md](../../reference/chinese_prototype_catalog.md)，按目录把具体样板函数迁移进 work；涉及可进入建筑时再读 [../../reference/chinese_enclosure_interior_lighting_rules.md](../../reference/chinese_enclosure_interior_lighting_rules.md)，涉及城墙/门楼/角楼时再读 [../../reference/chinese_city_defense_structural_quality_rules.md](../../reference/chinese_city_defense_structural_quality_rules.md)，涉及铁链、楼梯方向、旋转方块或园林植物时再读 [../../reference/chinese_detail_placement_quality_rules.md](../../reference/chinese_detail_placement_quality_rules.md)，涉及 1024 格以上超大型都城、全城建筑去重、水系或生活服务链时再读 [../../reference/chinese_metropolis_planning_and_variation_rules.md](../../reference/chinese_metropolis_planning_and_variation_rules.md)。不能只引用文件名、只生成外壳、只统计方块或只抽查路线点。
5. 需要给用户组织需求时使用 [PROMPT_TEMPLATE.md](PROMPT_TEMPLATE.md)；需要示例时读 [EXAMPLES.md](EXAMPLES.md)。

## 工作流程

1. 若 work 不存在，运行：
   `python scripts/structure_work.py new workset/<name> --project-name "<name>" --size X Y Z --origin X Y Z`
2. 把自然语言需求整理进 `BRIEF.md`；尺寸、builder 和维度参数以 `project.json` 为准。
3. 在编码前确定总平面、入口朝向、主路线、垂直层级、区域职责、材料层级和关键视线；若有专项知识库，同时先建立源函数到目标实现与调用点的采用清单。
4. 只编辑目标 work 的 `main.py` 与 `src/`。把材料、几何原语、区域模块和总装函数拆开，避免单文件堆叠坐标。
5. builder 必须是零参数函数，并返回恰好一个尺寸等于 `project.json.structure_size` 的逻辑画布。小型工程返回 `mcstructure.Structure`；预计密集索引达到 256 MiB、任一水平轴不少于 1024 或需要低内存分片生成时返回 `mcstructure.StructurePlan`。两者均使用全局坐标的 `set_block` / `set_blocks`，禁止让建筑模块手工感知或裁剪输出分片。
6. 入口默认朝负 Z；从 `project_manifest.json` 的推荐传送点必须能看见并抵达入口。
7. 每完成一个主要区域就运行完整构建，修复源码中的越界、断路、封门、悬空、错误方块状态、非法种植基底和接缝问题。
8. 最终运行：`python scripts/structure_work.py build workset/<name>`。

## 不要做

- 不手写或修改 `out/`。
- 不在 work 内复制 exporter、feature rule、生物群系/维度 JSON 或 ModSDK 队列代码。
- 不用大量孤立的 `set_block` 替代可命名、可复用的几何函数。
- 不通过缩小需求、删掉内部空间或填死建筑来掩盖构建失败。
- 不用类型名称、注释或未调用的样板函数冒充已采用知识库。
- 不在未验证时声称已完成。

## 完成标准

- `main.py` 可独立执行，仓库级 `build` 命令也可执行。
- 一次构建自动生成 worldgen 与 ModSDK 输出并通过快速审计；独立 `validate` 可复查全部 JSON、引用和结构 NBT 头。
- 建筑具有清晰轮廓、入口、连续路线、可进入内部、照明和区域差异。
- 最终回复列出修改的源码、构建结果、切片数、维度 ID 和推荐传送命令。
