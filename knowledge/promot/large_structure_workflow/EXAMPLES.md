# 使用示例

## 从零创建

```powershell
python scripts/structure_work.py new workset/frost_citadel `
  --project-name "Frost Citadel" `
  --size 192 96 192 `
  --origin 2048 48 2048
```

填完 `workset/frost_citadel/BRIEF.md` 后，将 [PROMPT_TEMPLATE.md](PROMPT_TEMPLATE.md) 交给 AI。AI 完成源码后运行：

```powershell
python scripts/structure_work.py build workset/frost_citadel
```

## 继续迭代

```text
继续按照 large_structure_workflow/SKILL.md 修改 workset/frost_citadel。
保持 project.json 不变，只修改 main.py 与 src/。
当前问题：北侧塔楼轮廓太平、Boss 房到出口没有可走路线、地下层照明不足。
修复后重新运行完整 build，并报告新的切片数与传送命令。
```

## 按玩家截图返工中式主城

```text
继续按照 knowledge/promot/large_structure_workflow/SKILL.md 和
knowledge/promot/CHINESE_ARCHITECTURE_SKILL.md 修改 workset/chinese_capital。

这不是扩建任务。先把截图中暴露的结构问题做成失败审计，再修复源码：
- 城门楼必须坐在完整城台上，屋身底面不得悬空；屋檐支点要有连续荷载路径。
- 玩家必须能从地面登城，沿整圈巡道进入四座门楼和四座角楼。
- 女墙/垛口不得横穿巡道；用全巡道 BFS，不得只抽查几个点。
- 屋檐、瓦垄、搏风板、脊兽和斗拱不得存在孤立或仅对角接触的方块。
- 大型建筑的 RoomPlan 必须生成实际隔断、门、组合家具和空间层次，不得只分条带并铺散点方块。
- 临时封闭登记门洞后，对室内空气做 flood fill；若多个计划房间仍是一整片连通空气，判定为假分间。
- 先冻结主入口、房门、3×3 门前缓冲和入口到各房间/楼梯的保护路线，再生成带门洞的隔墙；隔墙不得覆盖门口或切断入口 BFS。
- enclosed 隔墙逐列接到天花、梁底或坡屋面下表面，门洞上方有门楣/墙体；随机矮墙和墙顶空气带判失败。
- 室内楼梯按玩家头部扫掠体积检查每一级、转向平台和楼板洞口，不能只检查楼梯朝向或踏步正上方一格。
- 每个房间使用与用途匹配的多方块主锚点和辅助组；书架、工作台、木桶不能成为所有房间的通用填充物。
- 从门内 viewpoint 应能看见或抵达主锚点，主锚点、两个辅助证据和活动空地共同说明用途；隐藏房间名称后仍应可辨认。
- 每列铁链向上追踪到真实梁架锚点，顶端正上方不得是空气；悬挂灯笼状态与支撑关系一致。
- 按楼梯所连接的低/高平台推导上升方向，检查最终 Bedrock 状态；旋转建筑不能只转坐标不转楼梯、门和活板门状态。
- 花草只放在 PlantingPlan 内，脚下是该区允许的草方块/土壤；禁止石砖或木板上直接长花、随机散点和机械棋盘花阵。

保持 project.json 不变，只修改 main.py 与 src/。修复后运行完整 build，报告：
unsupported_floor_cells、load_path_failures、wall_walk_components、
wall_walk_reachable_ratio、unreachable_gatehouses、floating_detail_components、
metadata_only_rooms 和 distinct_furniture_templates。
另外报告 stair_swept_volume_blockers、stair_landing_blockers、
stair_shaft_intrusions、physical_compartment_shortfall、unmaterialized_partitions、
oversized_undivided_interiors、rooms_without_role_anchors 和
generic_furniture_only_rooms、furniture_template_shortfall、
duplicate_large_interior_layouts。
同时报告 portal_volume_blockers、partition_overwrites_portals、
door_approach_blockers、entrance_route_breaks、rooms_disconnected_from_entrance、
partition_ceiling_gaps、short_enclosed_partitions、partition_side_leaks、
functionally_ambiguous_rooms、role_anchor_mismatches 和 unusable_furniture_groups。
另外报告 unanchored_chain_tops、hanging_state_mismatches、misoriented_stairs、
stair_route_breaks、invalid_plant_substrates、plants_outside_planting_zones、
mechanical_plant_repetitions 和 landscape_clearance_blockers。
```

## 超大型项目的低内存写法

AI 不按分片写建筑，只把密集 Adapter 换成记录式 Adapter：

```python
from mcstructure import Block, BlockCanvas, StructurePlan

SIZE = (2048, 128, 2048)
AIR = Block("minecraft:air")
STONE = Block("minecraft:stone")


def foundation(canvas: BlockCanvas) -> None:
    canvas.set_blocks((0, 0, 0), (2047, 3, 2047), STONE)


def build_structure() -> StructurePlan:
    canvas = StructurePlan(SIZE, AIR)
    foundation(canvas)
    return canvas
```

屋顶、房屋、道路和景观 helper 只接受 `BlockCanvas` 并使用完整逻辑画布的全局坐标。共享 exporter 会把跨片填充裁剪到 worldgen 与 ModSDK 分片，保持后写入覆盖先写入。需要体素检查时只渲染局部：

```python
gatehouse = canvas.render_region((960, 0, 64), (128, 96, 128))
```

禁止在建筑模块中循环输出分片或访问不存在的全城 `.structure` 数组。

## 现成最小基准

`workset/example_work` 是可执行样例：

- `project.json` 声明 `96×48×96` 画布和 `example_project:build_structure`。
- `src/example_project/build.py` 只负责建筑。
- `main.py` 只把 work 交给共享 runner。
- `out/` 可随时删除并由一条命令重建。

先运行该样例可以区分“共享工具链故障”和“新建筑源码故障”。
