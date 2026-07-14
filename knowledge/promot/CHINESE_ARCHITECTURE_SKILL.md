---
name: generate-chinese-minecraft-architecture
description: 使用 mcstructure 或类似方块 API 生成中国古代建筑、明京城、宫殿、官署、民居、城墙、城门楼、院落和超大型 MMO 主城时的强约束。重点约束传统都城层级、扇区与水陆交通、建筑签名去重、生活服务链、创新地标、屋顶结构、门洞优先的实体房间、入口交通骨架、接天花隔墙、角色化内饰和视觉验收，避免均匀复制城区、矮墙堵门、入口断路、功能不明家具、假分间和空壳内饰。
---

# 中国古建筑 Minecraft 生成约束

本技能用于中国古代建筑生成，尤其是明清京师、宫城、皇城、官署、民居、坊市、园林和 MMORPG 主城。

核心判断：古建不像古建，通常不是因为方块不够多，而是因为没有中国木构建筑的语法。生成器必须先解决屋顶、柱网、台基、院落和轴线，再谈规模。

## 样板引用门槛

开始编码前必须先读 [`../reference/chinese_prototype_catalog.md`](../reference/chinese_prototype_catalog.md)，并按目录打开任务涉及的具体源函数。大型首都必须同时读取：

- [`../reference/chinese_roof_prototype_gallery.py`](../reference/chinese_roof_prototype_gallery.py)：以 `*_refined` 函数为五类屋顶的最高优先级来源。
- [`../reference/chinese_ancient_prototypes.py`](../reference/chinese_ancient_prototypes.py)：用于台基、柱网、墙门窗、额枋、院墙和完整单体装配。
- [`../reference/chinese_prefab_gallery.py`](../reference/chinese_prefab_gallery.py)：用于居民、市场、客栈、官署、宫殿、园林、桥、城防和 MMO 功能布局。
- [`../reference/chinese_roof_prototype_lessons.md`](../reference/chinese_roof_prototype_lessons.md)：用于 v33 迭代中已经验证的屋面、梁架和审计经验。
- [`../reference/chinese_enclosure_interior_lighting_rules.md`](../reference/chinese_enclosure_interior_lighting_rules.md)：屋顶侧漏、大型建筑内部规划、家具通行和照明覆盖的硬规则。
- [`../reference/chinese_city_defense_structural_quality_rules.md`](../reference/chinese_city_defense_structural_quality_rules.md)：城台、城门楼、巡道、登城路线、荷载路径和孤立构件审计。
- [`../reference/chinese_detail_placement_quality_rules.md`](../reference/chinese_detail_placement_quality_rules.md)：铁链/吊灯真实锚固、楼梯与旋转方块状态、种植基底和园林构图审计。
- [`../reference/chinese_metropolis_planning_and_variation_rules.md`](../reference/chinese_metropolis_planning_and_variation_rules.md)：1024 格以上都城的扇区、历史层级、水陆网络、建筑签名去重、生活服务链和创新地标。

在 `src/<package>/reference_plan.py` 中记录“源文件 + 具体 symbols → 目标函数 → 真实调用点 → 保留/改造项”。仅提到文件名、复制后不调用、或只登记五类屋顶名称均不算参考。work 最终必须自包含，不得在运行时导入 `knowledge/reference`。

来源冲突时按此优先级处理：v33 `*_refined` 屋顶几何 > ancient prototypes 的完整木构/院落关系 > prefab gallery 的功能和平面。prefab gallery 的通用 `roof()` 和 `hall()` 不能作为正式首都的最终屋顶实现。

## 禁止反模式

- 禁止用一个通用坡屋顶函数生成全部建筑。
- 禁止没有正脊、垂脊、戗脊、檐口的屋顶。
- 禁止飞檐做成随机尖刺、悬浮块或长距离无支撑挑出。
- 禁止大面积红墙、灰墙、白墙连续超过 8 格没有柱、窗、格栅、额枋或灯。
- 禁止重要建筑没有台基、没有踏道、没有正面轴线。
- 禁止宫殿只是一个巨型房子；宫殿必须是多进院落。
- 禁止主路后补。主路、城门、宫门、正殿、后寝、园林轴线必须先规划。
- 禁止先生成整座城再解释“哪里像”。必须先做可验收的屋顶和单体原型。
- 禁止只验证屋面俯视投影，不检查山墙、侧坡与墙顶接缝。
- 禁止大型建筑只有外壳、单一大厅或象征性两三件家具。
- 禁止每栋建筑只放一盏灯，或直接放光源却不登记照明覆盖。
- 禁止把城门楼直接放在普通薄城墙上；必须先生成覆盖屋身足迹的城台。
- 禁止用四五个可站立采样点证明整圈巡道可走；必须对全部巡道格做 BFS。
- 禁止女墙/垛口横穿巡道，禁止只旋转侧城门屋顶而不旋转屋身与入口。
- 禁止以 `RoomPlan` 名称和家具密度代替实际隔断、组合家具和空间层次。
- 禁止铁链顶端接空气、悬挂灯状态与支撑关系不符，或在灯笼下方无意义续链。
- 禁止旋转/镜像建筑时只变坐标不变楼梯、门、梯子和活板门状态；可行走楼梯必须按实际上下平台推导朝向。
- 禁止花草直接长在石砖、木板、楼梯或空气上，禁止随机散点、棋盘格和无语义等距花阵。
- 禁止只检查楼梯朝向或踏步正上方一格；必须验证玩家头部沿整跑楼梯、转向平台和楼板洞口扫过的体积。
- 禁止用多个 `RoomPlan` 名称表示同一片无隔断空气，禁止用地毯、书架、工作台和木桶冒充墙、屏风、门洞及角色化内饰。
- 禁止先生成实心隔墙再用零散 `clear()` 猜门洞；门洞、门内外缓冲和入口 RoutePlan 必须先冻结，墙段围绕开口生成。
- 禁止 enclosed 隔墙统一只做两格高或停在门高；必须逐列接到天花、梁底或坡屋面下表面，并封门检查墙顶/墙端绕漏。
- 禁止入口后撞墙、侧挤窄缝或被家具截断；从室外入口前点到公共房间、楼梯和出口必须基于最终方块 BFS 连通。
- 禁止只用 role 名称解释内饰；主锚点、两个辅助证据、活动区和使用侧必须共同形成从门口可辨认的功能场景。
- 禁止在皇城/兵营豁免组团之外复制完全相同的建筑；换颜色、旋转 prefab、移动一棵树或替换一盏灯不算结构变体。
- 禁止把超大型城市做成均匀棋盘、64 个互不相干的扇区或沿路无限重复同一种民居；全局礼仪轴、市井网与水运网必须跨扇区连续。
- 禁止用随机杂物冒充生活气息；住宅、商业、作坊、军防、码头和公共建筑必须接入可解释的食物、水、货运、住宿、生产或文化服务链。

## 强制流程

1. 先完成 `reference_plan.py`，每条采用关系必须落到具体源函数和调用建筑。
2. 先迁移并验证五类 v33 精细屋顶，不直接从简化屋顶扩展整城。
3. 每个 prefab 必须声明 `roof_type`：`硬山`、`悬山`、`歇山`、`庑殿`、`攒尖` 之一。
4. 大型建筑先声明楼层、实体房间、PortalPlan、入口 RoutePlan、门/路线/楼梯保护体积、角色家具证据和光源点，再生成外壳。
5. 单体建筑按 `建筑计划 -> 台基/楼板 -> 柱网 -> 墙门窗/楼梯 -> 斗拱/檐下层 -> 屋顶围护 -> 内部分区/家具 -> 照明 -> 院落收边` 生成。
6. 城市按 `城门/宫门轴线 -> 主路 -> 皇城/宫城边界 -> 院落组团 -> 单体建筑 -> 市井填充 -> 灯光与路缘` 生成。
7. 自动审计必须验证真实几何、内外 flood fill、房间连通、照明覆盖与调用关系，不能只验证登记名称是否出现。
8. 自动审计通过后仍需要玩家高度、俯瞰、四向侧视、屋内仰视、屋顶俯视、室内路线和夜间目视验收。
9. 涉及城防时先生成“直城墙 + 城台门楼 + 左右侧门 + 登城路线 + 转角角楼”样段；样段通过后再扩展整圈。
10. 涉及吊灯、方向方块或园林时先生成“梁架悬灯 + 四向楼梯 + 小型花境”样段，校准 Bedrock 状态与种植基底后再批量生成。
11. 大型建筑在铺设家具前临时封闭登记门洞，对室内空气做 flood fill；实际分区不足时先修隔墙/屏风/门洞，不用家具填充掩盖。
12. 从室外入口前点对最终方块做 BFS，并逐列审计 enclosed 墙顶；门口或路线被覆盖、墙未接上部结构时先修墙段生成顺序。
13. 1024 格以上城市先生成 CityPlan、256 格扇区、全局道路/水系保护带和全城 BuildingSignature 清单；核心样区通过后再扩展其余扇区。

## 围护、内部与照明门槛

- `roof_projection_coverage` 不能替代侧面封闭审计；硬山/悬山/歇山检查山墙，庑殿检查四坡接缝，攒尖检查宝顶周围。
- 大型建筑必须有共享的 `BuildingPlan` / `RoomPlan` 数据，外壳、家具、照明和审计从同一份计划取坐标。
- 面积不少于 160、宽深达到 20×12、两层以上或属于宫殿/城楼/客栈/衙署/寺观的建筑均按大型建筑处理。
- 每个房间必须有用途、入口、通行采样和至少一个识别锚点；两层外观必须对应真实楼板和楼梯。
- 每跑楼梯先登记低/高平台、逐级踏步、上升方向和保留净空；最终结构中玩家扫掠体积、平台和楼板洞口均不得有阻挡。
- 大型民居、客栈、衙署等每层至少形成两个真实空气分区；除有意大厅外，单一无隔断空间不超过该层可用面积的 60%。
- 每个房间至少有多方块主锚点和辅助家具组；家具模板随面积达到 3/5/7 种，书架、工作台和木桶不得作为所有房间的默认填充物。
- 门洞和入口路线在隔墙前冻结；隔墙由带开口墙段 helper 生成，门内外保留 3×3 缓冲，入口 BFS 到达各公共房间和楼梯。
- enclosed 墙逐列连接天花/梁底/坡屋面下表面；矮墙仅属于 screened/open_zone，不能计入封闭房边界。
- 每个房间从门内 viewpoint 可见或可达主锚点，并有至少两个辅助证据、活动区和家具使用侧；隐藏 role 名称后仍应大致可辨用途。
- 所有光源通过统一 helper 放置并登记。每个封闭房间至少一盏灯，室内照明按面积和最远覆盖距离增加，不能只满足方块计数。
- 详细阈值和房间程序遵循 `chinese_enclosure_interior_lighting_rules.md`。

## 五类屋顶硬规则

### 硬山

用于普通民居、仓库、低等级铺面。

- 必须有一条连续正脊。
- 两面坡，山墙包住屋面。
- 山墙应高出屋面边缘 1 格左右，形成封火墙或墀头感。
- 出檐少，不能用于皇宫正殿。

### 悬山

用于厢房、廊屋、普通厅堂、民居。

- 必须有一条连续正脊。
- 两面坡，屋面越过山墙外侧。
- 山墙外侧必须有挑出檐口、搏风板或木构边框。

### 歇山

用于官署正堂、宫门、重要厅堂。

- 必须有正脊、垂脊、戗脊。
- 两侧必须有山花或山面，且山面不能是空白三角墙。
- 山面应有木框、搏风板、悬鱼状垂饰或深色边线。
- 视觉上必须读出“上半庑殿 + 下半悬山”的层次。

### 庑殿

用于宫殿正殿、重要城楼、最高等级建筑。

- 必须有一条正脊和四条垂脊。
- 四面坡，无山墙三角面。
- 出檐可宽，但角部只允许最后 2-4 格抬升，最多抬 2 格。
- 檐下必须有柱网、额枋、斗拱或托木。

### 攒尖

用于亭、角楼、碑亭、园林节点。

- 多个坡面必须汇向中心。
- 屋脊从角部汇向宝顶，不能只是方锥。
- 顶部必须有宝顶或尖顶。

## 屋面材料等级

- 普通民居、胡同院落、商铺、作坊和低等级附属房优先使用深板岩瓦、深板岩瓦楼梯等深灰石瓦体系；不可整片使用橡木屋面，否则会与宫殿等级混淆。
- 官署、寺观可继续使用灰瓦体系，但允许增加更完整的正脊、垂脊和檐下木构。
- 皇城、宫殿和最高等级门楼可使用橡木楼梯、橡木木板近似琉璃瓦；这是受原版方块颜色限制的视觉替代，不代表民居也应使用同材质。
- 屋面材料变化只改变瓦面和屋脊表达，檩、梁、椽、额枋仍使用有明确受力关系的木构材料。
- 同一城区必须通过屋面颜色和屋顶等级让玩家一眼分辨民居、官署与宫殿。

## 屋顶验收

每个屋顶原型必须满足：

- 一眼能看出屋顶类型。
- 正脊连续，长度不小于主体长边的 60%。
- 歇山/庑殿有可读的垂脊或戗脊。
- 檐口连续，不是点状悬浮块。
- 飞檐不尖刺化，角部抬升幅度克制。
- 檐下有托木、斗拱、柱头或墙体支撑。
- 屋面有瓦垄或色带，不是一片纯色平板。

## 立面验收

- 正面开间数优先为 3、5、7、9。
- 中央开间为门，左右为窗、格扇或墙心装饰。
- 柱必须贯通到檐下。
- 檐下必须有至少两层横向构件，例如额枋、普拍枋、斗拱、椽。
- 重要建筑台基至少比屋身四周宽 4 格；普通建筑至少宽 1-2 格。
- 入口必须有踏道，不能让门悬在台基上。

## 院落与城市布局

- 单体建筑必须服务于院落，不得孤立散放。
- 院落至少包含门、主屋、厢房或廊、围墙、庭院元素。
- 宫殿必须多进院落，沿中轴从城门、广场、宫门、正殿、后寝、御花园递进。
- 京城主路必须宽阔、平直、材料清晰，支路与主路不能同等级。
- 主路沿线要有连续边界：墙、廊、灯、树阵、牌坊、河道或建筑正立面。
- 超大型都城同时维护礼仪轴线、市井道路网和水运网；护城河、运河、桥、码头和跨扇区接缝先于建筑。
- 除皇城和兵营登记的秩序性组团外，每栋建筑维护唯一 `BuildingSignature`，至少从体量/院落、构造/屋顶、立面/入口、内部/生活四类中改变两类。
- 城区必须覆盖皇城、官署、军营、豪华院落、商业、居民、手工业、仓储漕运、文化宗教、滨水娱乐和城外服务，并以生活服务链互相支持。
- 高大酒楼、画舫、水上会馆/戏台、桥市和临河仓楼先作为独立原型验证，再成为全城唯一地标。

## 自动审计建议

至少实现这些字段：

- `roof_type_declared`
- `main_ridge_blocks >= min(width, depth) * 0.6`
- `hip_or_xieshan_ridge_blocks > 0`，用于庑殿和歇山
- `eave_support_ratio >= 0.5`
- `blank_wall_run <= 8`
- `floating_mass_count == 0`
- `bay_count in {3, 5, 7, 9}`
- `platform_margin >= 1`，宫殿 `>= 4`
- `courtyard_components >= 4`
- `roof_projection_holes == 0`
- `roof_symmetry_mismatches == 0`，对称建筑适用
- `solid_roof_layer_ratio` 不得表现为逐层实心收缩矩形
- `reference_sources_covered == 3`
- `reference_targets_called == true`
- `roof_shell_holes == 0`
- `gable_shell_holes == 0`
- `eave_joint_gaps == 0`
- `rain_exposed_interior_columns == 0`
- `exterior_air_leaks == []`
- `unplanned_large_buildings == []`
- `unreachable_rooms == []`
- `blocked_circulation_samples == []`
- `rooms_without_lights == []`
- `dark_walkable_samples == []`
- `unregistered_light_blocks == []`
- `visible_technical_lights == []`
- `gatehouse_body_overhang_cells == []`
- `unsupported_floor_cells == []`
- `load_path_failures == []`
- `wall_walk_components == 1`
- `wall_walk_reachable_ratio >= 0.98`
- `transverse_battlement_obstructions == []`
- `unreachable_gatehouses == []`
- `floating_detail_components == []`
- `metadata_only_rooms == []`
- 大型建筑 `distinct_furniture_templates >= 3`
- `stair_swept_volume_blockers == []`
- `stair_landing_blockers == []`
- `stair_shaft_intrusions == []`
- `physical_compartment_shortfall == []`
- `unmaterialized_partitions == []`
- `oversized_undivided_interiors == []`
- `rooms_without_role_anchors == []`
- `generic_furniture_only_rooms == []`
- `furniture_template_shortfall == []`
- `duplicate_large_interior_layouts == []`
- `portal_volume_blockers == []`
- `partition_overwrites_portals == []`
- `door_approach_blockers == []`
- `entrance_route_breaks == []`
- `rooms_disconnected_from_entrance == []`
- `protected_route_intrusions == []`
- `partition_ceiling_gaps == []`
- `short_enclosed_partitions == []`
- `partition_side_leaks == []`
- `functionally_ambiguous_rooms == []`
- `role_anchor_mismatches == []`
- `unusable_furniture_groups == []`
- `planned_sector_count == built_sector_count`
- `sector_seam_errors == []`
- `moat_continuity_breaks == []`
- `canal_continuity_breaks == []`
- `missing_required_districts == []`
- `unreachable_districts == []`
- `duplicate_building_signatures == []`
- `color_only_variants == []`
- `residences_without_life_evidence == []`
- `broken_service_chains == []`
- `innovation_landmarks_without_prototypes == []`
- `floating_boats == []`
- `unreachable_boat_gangways == []`
- `unanchored_chain_tops == []`
- `broken_chain_columns == []`
- `unsupported_hanging_fixtures == []`
- `hanging_state_mismatches == []`
- `misoriented_stairs == []`
- `stair_route_breaks == []`
- `stair_headroom_failures == []`
- `unrotated_directional_states == []`
- `invalid_plant_substrates == []`
- `orphan_double_plants == []`
- `plants_outside_planting_zones == []`
- `landscape_clearance_blockers == []`
- `building_landscape_intersections == []`
- `mechanical_plant_repetitions == []`

## 推荐下一步

任何新的中国古代主城生成任务，应先从 v33 `chinese_roof_prototype_gallery.py` 迁移并测试五类精细屋顶。只有硬山、悬山、歇山、庑殿、攒尖五个原型在游戏里合格，且 `reference_plan.py` 能追踪到真实调用建筑后，才允许扩展成民居、商铺、官署、宫殿和整座城市。
