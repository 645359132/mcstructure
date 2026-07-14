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

对应包必须导出零参数函数。小型结构可返回密集画布，超大型结构返回记录式画布：

```python
from mcstructure import Structure, StructurePlan

def build_structure() -> Structure | StructurePlan:
    ...
```

返回值代表完整建筑的逻辑局部画布，而不是某个切片。返回尺寸必须严格等于 `structure_size`；切片、跳过全空气片、命名和偏移均由共享 exporter 处理。

- `Structure` 是密集 NumPy Adapter，适合小型结构和需要直接数组审计的工程。
- `StructurePlan` 是记录式 Adapter，使用相同的全局坐标 `set_block()` / `set_blocks()` 接口，只保存有序填充操作并在导出时逐片渲染。后写入仍覆盖先写入，AI 不得自行裁剪跨片建筑。
- scaffold 在预计密集索引达到 256 MiB 时自动选择 `StructurePlan`。AI 也可为更小但操作稀疏的工程主动选择它。
- `StructurePlan` 没有完整 `.structure` 数组；使用 `get_block()` 查询单点，使用 `render_region(offset, size)` 生成局部预览或体素审计。全城审计优先使用规划、包围盒、路线图和局部窗口。

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

`build` 根据刚生成的内存数据校验规格、builder、尺寸、切片边界/体积、文件存在性、清单计数和引用，不立即重开数千个新文件。独立 `validate` 还会重新解析所有 JSON 并读取每片结构的固定 NBT 头，但不完整解码方块数组；完整 NBT 编解码正确性由小型 round-trip 测试覆盖。
