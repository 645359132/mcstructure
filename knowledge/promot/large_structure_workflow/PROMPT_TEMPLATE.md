# 大型建筑协作提示词模板

将尖括号内容替换后交给 AI。第一次使用先通过 scaffold 创建 work。

```text
请按照 knowledge/promot/large_structure_workflow/SKILL.md 完成
workset/<work_name> 中的大型建筑。

需求：
<建筑主题、世界观、用途、规模感>

必须出现：
- <地标 1>
- <区域 2>
- <玩法或叙事空间 3>

玩家体验：
- 玩家从负 Z 的推荐传送点接近。
- 主路线为：<入口 → 前厅 → ... → 核心/Boss 区>。
- 必须可进入的内部：<房间列表>。
- 希望第一眼看到：<轮廓与视觉焦点>。

风格与材料：
- <建筑风格>
- <主材、次材、强调材>
- 禁止：<不想出现的材料或形态>

工程边界：
- 先读取 BRIEF.md 和 project.json。
- 只修改该 work 的 main.py 与 src/；不要手写 out/ 或网易配置。
- builder 返回 project.json 指定尺寸的一个完整 Structure。
- 最后必须运行 python scripts/structure_work.py build workset/<work_name>。
- 构建失败就继续修复源码，直到一次构建与审计通过。

完成时报告：源码模块、已实现区域、worldgen/ModSDK 切片数、维度 ID、推荐传送命令和仍需进游戏目测的项目。
```

如果尺寸、维度或世界坐标尚未确定，先运行：

```powershell
python scripts/structure_work.py new workset/<work_name> `
  --project-name "<display name>" `
  --size <X> <Y> <Z> `
  --origin <X> <Y> <Z>
```
