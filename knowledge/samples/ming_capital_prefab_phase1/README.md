# 明代主城第一阶段 prefab 验收

本目录不是完整主城。请先单独检查五个角色化 prefab，确认建筑水准没有低于冻结的 v33 屋顶基线。

## 检查顺序

1. 台基、柱网、墙体、檐下承托是否落地并连续。
2. 屋顶类型是否一眼可辨，排水坡面、屋脊和飞檐是否自然。
3. 大门与中轴路线是否可直接通行。
4. 建筑功能是否能从立面和内部布置读出。
5. 不接受悬空构件、门洞阻塞、随机木板和同模板换皮。

## 原型

- `01_hutong_courtyard_residence`：胡同院落正房，硬山，roof=1939，passed=True
- `02_street_shop`：沿街商铺，悬山，roof=1505，passed=True
- `03_yamen_gatehall`：衙门门厅，歇山，roof=4435，passed=True
- `04_palace_corridor`：宫城连廊，悬山，roof=2677，passed=True
- `05_palace_gate`：宫门，庑殿，roof=4043，passed=True

## 放置

把结构复制到行为包后执行 `place_with_modsdk.py` 中的代码。玩家位置是整排图库的中心。
