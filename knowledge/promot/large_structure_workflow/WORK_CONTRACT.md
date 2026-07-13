# Work 工程契约

## 目录所有权

标准目录：

```text
workset/<work>/
├── BRIEF.md               # 用户需求；先由人或 AI 整理
├── project.json           # scaffold 生成的稳定工程参数
├── main.py                # AI 可维护，但只调用共享工作流
├── .gitignore             # 忽略 out/
├── src/<package>/         # AI 的建筑实现
│   ├── __init__.py
│   ├── build.py
│   └── ...                # palette/geometry/regions/audit 等
└── out/                   # 共享工具生成，禁止手工编辑
```

AI 的写入范围是 `main.py` 与 `src/`。若需求与 `project.json` 冲突，应报告冲突；不要静默改尺寸、维度或世界坐标。

## Builder 接口

`project.json.builder` 使用 `module.path:function` 格式，例如：

```json
"builder": "example_project:build_structure"
```

对应包必须导出零参数函数：

```python
from mcstructure import Structure

def build_structure() -> Structure:
    ...
```

返回值代表完整建筑的局部画布，而不是某个切片。返回尺寸必须严格等于 `structure_size`；切片、跳过全空气片、命名和偏移均由共享 exporter 处理。

## `project.json` 字段

- `schema_version`：当前固定为 `1`。
- `project_name`：展示名称。
- `namespace` / `structure_name`：只允许小写字母、数字、下划线。
- `builder`：源码入口。
- `structure_size`：完整局部画布 `[X, Y, Z]`。
- `world_origin`：世界中的西北下角；X/Z 必须对齐 16 格。
- `dimension_id` / `dimension_mod_id` / `dimension_biome`：网易自定义维度参数；生物群系标识同时作为 feature rule 使用的 tag。
- `biome_inherits`：生成的自定义生物群系所继承的原版群系，默认 `plains`；例如林地府邸可设为 `roofed_forest`。
- `repeat_period`：worldgen 锚点重复距离，必须是 16 的正整数倍。
- `worldgen_piece_size`：默认 `[16, 256, 16]`。
- `modsdk_piece_size`：默认 `[32, 64, 32]`。
- `modsdk_batch_*` / `modsdk_pass*`：ModSDK 分批、多遍放置策略。

每片体积都必须不超过 65,536。worldgen 的 X/Z 不能超过 16、Y 不能超过 256；ModSDK 单轴上限为 64×384×64。

## 坐标约定

- 局部原点 `(0, 0, 0)` 是建筑画布的西北下角。
- X 向东，Y 向上，Z 向南。
- 默认正面和入口朝负 Z。
- `world_origin + placement.offset` 得到 worldgen 片段的世界放置点。
- ModSDK 输出以玩家脚下为结构水平中心，保留局部 Y 偏移。

## 一键构建产物

`python scripts/structure_work.py build workset/<work>` 自动生成并校验：

- `structures/<namespace>_worldgen/*.mcstructure`
- `netease_features/*.json`
- `netease_feature_rules/*.json`
- `netease_biomes/dm<dimension_id>/<dimension_biome>.json`
- `netease_dimension/*.json`
- `structures/<namespace>_modsdk/*.mcstructure`
- `place_with_modsdk.py`
- `placements.json` 与 `project_manifest.json`

校验覆盖源码语法、规格字段、builder 类型和尺寸、所有 JSON、切片边界/体积、结构文件回读、清单计数及必要引用文件。
