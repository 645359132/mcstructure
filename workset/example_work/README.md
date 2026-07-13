# 标准结构生成项目模板

这个目录把“建筑内容”和“如何放进网易版世界”分开：

- `src/example_project/config.py`：项目名、命名空间、结构尺寸、自定义维度、世界坐标。
- `src/example_project/build.py`：只负责使用 `mcstructure` 建筑。
- `src/example_project/export.py`：通用切片、世界生成 JSON、ModSDK 放置脚本。
- `main.py`：唯一命令行入口。
- `out/`：生成结果，可复制到行为包。

`out/` 已加入 Git 忽略规则，因为所有内容都能由入口命令重新生成。

## 1. 生成

在仓库根目录执行：

```powershell
D:\Python3.12\python.exe workset\example_work\main.py
```

也可以只生成一种资源：

```powershell
D:\Python3.12\python.exe workset\example_work\main.py --mode worldgen
D:\Python3.12\python.exe workset\example_work\main.py --mode modsdk
```

默认示例是一个 `96×48×96` 的大型地标。运行完成后，终端会打印维度 ID、建筑原点和推荐传送命令。

## 2. 开始自己的项目

先修改 `config.py` 中的 `CONFIG`：

- `namespace`：资源标识前缀，只用字母、数字和下划线。
- `structure_name`：结构文件名前缀。
- `structure_size`：完整建筑画布尺寸，必须与 `build_structure()` 返回值相同。
- `world_origin`：建筑西北下角在自定义维度中的绝对坐标；X/Z 必须是 16 的倍数。
- `dimension_id`：模组内唯一的自定义维度整数 ID。
- `dimension_biome`：该维度实际可用的网易生物群系标识。
- `repeat_period`：世界生成锚点的重复距离；默认每 4096 格重复一次。

然后仅修改 `build.py` 中的 `build_structure()`。导出器会自动完成其余工作。

## 3. 大型结构：自定义维度世界生成

大型结构默认切成最大 `16×256×16`、体积不超过 65,536 的片段。每个非空片段会生成：

- `out/structures/example_work_worldgen/*.mcstructure`
- `out/netease_features/*_structure_feature.json`
- `out/netease_feature_rules/*_feature_rule.json`
- `out/netease_dimension/dimension_config.json`
- `out/netease_dimension/dm<维度ID>.json`

将这些目录按同名路径复制到行为包。进入自定义维度后，传送到 `project_manifest.json` 中的 `recommended_teleport`；默认示例命令为：

```mcfunction
/tp @s 1072 66 1012 0 15
```

注意：feature rule 只在新区块生成时执行。若目标坐标区块已经生成，应创建新世界、清除对应区块，或者换到相隔 `repeat_period` 的另一个锚点。

## 4. 小型结构：ModSDK 放置

`out/place_with_modsdk.py` 提供：

```python
place_generated_structure(serverApi, levelId, entity_id)
```

它以玩家脚下为中心放置结构。小型建筑通常只产生一个 `.mcstructure`；较大建筑会自动按 `modsdk_piece_size` 切片，并采用“中心优先、分批延时、重复三遍”的可靠队列，避免同一 tick 调用过多 `PlaceStructure` 导致丢失。

需要复制：

- `out/structures/example_work_modsdk/` 到行为包 `structures/`。
- `place_with_modsdk.py` 的函数到服务端 ModSDK 代码。

## 5. 输出清单

- `project_manifest.json`：尺寸、维度、建筑原点、推荐传送坐标、切片数量。
- `placements.json`：每片文件名、结构标识、相对偏移和尺寸。

每次运行只会清理并重建 `out` 中由模板管理的目录和清单，不会修改项目其他文件。
