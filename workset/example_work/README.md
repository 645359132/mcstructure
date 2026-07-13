# 标准 AI 大型结构工作目录

这个示例落实了一个明确边界：AI 负责建筑，稳定脚本负责工程输出。

- `BRIEF.md`：玩家需求和建筑验收条件，先写它。
- `project.json`：尺寸、builder、维度、世界坐标和切片参数。
- `src/example_project/`：AI 编写的建筑生成器。
- `main.py`：本 work 的一键入口。
- `out/`：完全可再生的网易资源，不提交版本库。
- `scripts/structure_workflow/`（仓库级）：统一生成 `.mcstructure`、feature、feature rule、生物群系/维度 JSON、ModSDK 队列和清单。

## 一次生成全部内容

在仓库根目录运行任一命令：

```powershell
D:\Python3.12\python.exe workset\example_work\main.py
D:\Python3.12\python.exe scripts\structure_work.py build workset\example_work
```

默认命令会依次完成：读取并校验 `project.json`、导入 builder、生成完整逻辑画布、自动切片、写出两套放置资源、加载回读所有 `.mcstructure` 并审计 JSON/尺寸/引用。

只输出一种放置方式：

```powershell
D:\Python3.12\python.exe workset\example_work\main.py --mode worldgen
D:\Python3.12\python.exe workset\example_work\main.py --mode modsdk
```

再次审计已有结果：

```powershell
D:\Python3.12\python.exe scripts\structure_work.py validate workset\example_work
```

## 创建新 work

```powershell
D:\Python3.12\python.exe scripts\structure_work.py new workset\my_palace `
  --project-name "My Palace" `
  --size 192 80 192 `
  --origin 2048 56 2048
```

命令会生成 `BRIEF.md`、`project.json`、`main.py`、`.gitignore` 和最小 `src/<package>/`。默认维度 ID 由命名空间稳定派生；放入真实模组前仍应确认它未与其他维度冲突。

随后把 `BRIEF.md` 和提示词技能交给 AI。AI 不应手写 `out/`、`netease_features/`、`netease_feature_rules/`、生物群系/维度 JSON 或 ModSDK 放置队列。

## 放入游戏

大型建筑使用 `out/structures/<namespace>_worldgen/`、`out/netease_features/`、`out/netease_feature_rules/`、`out/netease_biomes/` 和 `out/netease_dimension/`。自定义生物群系继承项由 `project.json` 的 `biome_inherits` 控制。feature rule 只在新区块生成时执行；已生成的目标区块需要清除、换新世界或使用另一重复锚点。

小型建筑使用 `out/structures/<namespace>_modsdk/` 与 `out/place_with_modsdk.py`。生成的函数以玩家脚下为中心，按中心优先顺序分批、多遍调用 `PlaceStructure`。

具体维度 ID、原点和推荐传送命令见 `out/project_manifest.json`。
