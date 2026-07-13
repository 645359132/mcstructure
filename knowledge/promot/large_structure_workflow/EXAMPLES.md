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

## 现成最小基准

`workset/example_work` 是可执行样例：

- `project.json` 声明 `96×48×96` 画布和 `example_project:build_structure`。
- `src/example_project/build.py` 只负责建筑。
- `main.py` 只把 work 交给共享 runner。
- `out/` 可随时删除并由一条命令重建。

先运行该样例可以区分“共享工具链故障”和“新建筑源码故障”。
