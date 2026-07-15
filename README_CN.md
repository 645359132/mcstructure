<p align="center">
	<img
		src="https://raw.githubusercontent.com/phoenixr-codes/mcstructure/main/logo.png"
		width="120px"
		align="center" alt="mcstructure logo"
	/>
	<h1 align="center">mcstructure</h1>
	<p align="center">
		《我的世界》<code>.mcstructure</code> 文件的读写操作库
	</p>
</p>


🌍 此介绍文件亦可见于以下语种：

* [🇬🇧 英文](./README.md)
* [🇩🇪 德文](./README_DE.md) *(未及时更新)*

<!-- Not really accessible ♿️ but we get a prettier line
than the default "<hr/>" or "---" --> 
<h2></h2>

[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/mcstructure/badge/?style=for-the-badge&version=latest)](https://mcstructure.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/mcstructure?style=for-the-badge)](https://pypi.org/project/mcstructure)

_在整个项目中（且更官方地是在“大一统更新”("Better Together Update")之后，名词《我的世界》("Minecraft")所指代的均为基岩版("Bedrock Edition")。_

_此库中的所有特性也是仅仅针对基岩版的。_

> [!WARNING]
> **请注意**
> 此项目目前仍属于 **BETA** 版本，因此部分特性可能并未启用或在未经示警的情况下频繁更改。

<!-- start elevator-pitch -->

此库可以让您以代码实现对 *《我的世界》* 结构文件的创建与编辑。
您能够凭此而将您自己的结构存储为 `.mcstructure` 文件，因而可以使之用于行为包中，或者发展出更厉害的用途。

当然，通过此库您也可以通过此库来读取(read)这些在游戏中通过*结构方块*保存的结构文件，从而获取(identify)其中存储之方块与实体之类。

<!-- end elevator-pitch -->

下载安装
------------

```console
pip install mcstructure
```

### Rust 原生读取加速

`Structure.load()` 会自动使用可选的 Rust NBT 解码器。对于无实体、无方块实体/计划刻等位置元数据的常见结构，它直接把方块索引解码为紧凑字节并交给 NumPy，避免为每个索引创建 Python 标签对象；复杂结构自动回退到完整 Python 解码器，调用方式不变。

可以检查当前安装是否包含原生解码器：

```python
from mcstructure import NATIVE_DECODER_AVAILABLE

print(NATIVE_DECODER_AVAILABLE)
```

从源码安装时需要 Rust 工具链和 `setuptools-rust`；Rust 扩展被声明为可选构建，无法编译时仍可安装纯 Python 回退版本。发布时应为支持的平台构建带原生扩展的 wheel，避免最终用户本地编译。


基本用法
-----------

1.	写入结构文件

	```python
	# 导入库
	from mcstructure import Block, Structure

	# 实例化对象 Structure
	struct = Structure(
		(7, 7, 7),  # 声明结构大小
		Block("minecraft:wool", color = "red")	# 预填充方块
	)

	# 设定方块
	(struct
		.set_block((1, 1, 1), Block("minecraft:grass"))
		.set_block((2, 2, 2), Block("minecraft:grass"))
		.set_block((3, 3, 3), Block("minecraft:grass"))
		.set_block((4, 4, 4), Block("minecraft:grass"))
		.set_block((5, 5, 5), Block("minecraft:grass"))
		.set_block((6, 6, 6), Block("minecraft:grass"))
	)

	# 写入文件
	with open("house.mcstructure", "wb") as f:
		struct.dump(f)

	```

2.	读取结构文件

	```python
	with open("house.mcstructure", "rb") as f:
		struct = Structure.load(f)

	```

AI 协作大型建筑开发
-------------------

本仓库提供了一套适合与 AI 协作的大型建筑开发方式。核心原则是：**AI 只负责建筑设计与源码，稳定工具负责切片、网易配置、放置脚本和输出校验。** 这样可以持续修改建筑，而不需要让 AI 每次重新编写 `netease_feature_rules`、自定义生物群系/维度 JSON 或 ModSDK 放置队列。

> [!NOTE]
> 下面的命令用于克隆后的项目仓库，不属于 PyPI 包的公共 API。

标准 work 目录如下：

```text
workset/<work>/
├── BRIEF.md           # 建筑需求、路线和验收条件
├── project.json       # 画布尺寸、builder、维度和切片参数
├── main.py            # 该 work 的一键入口
├── src/<package>/     # AI 编写的建筑生成器
└── out/               # 自动生成，不手工修改或提交
```

其中 `project.json` 声明的 builder 必须是零参数函数，并返回尺寸严格等于 `structure_size` 的完整逻辑画布。小型工程使用密集 `mcstructure.Structure`；预计密集索引达到 256 MiB 的工程由 scaffold 自动使用低内存 `mcstructure.StructurePlan`。两者具有相同的全局坐标建造接口，AI 不需要感知 `.mcstructure` 分片。AI 应只修改目标 work 的 `main.py` 与 `src/`；切片、feature、feature rule、维度文件、ModSDK 队列和输出清单统一由共享工具生成。

创建一个新 work：

```console
python scripts/structure_work.py new workset/my_palace --project-name "My Palace" --size 192 80 192 --origin 2048 56 2048
```

接着填写生成的 `BRIEF.md`，并将 [`knowledge/promot/large_structure_workflow/PROMPT_TEMPLATE.md`](knowledge/promot/large_structure_workflow/PROMPT_TEMPLATE.md) 交给 AI。完整执行协议见 [`SKILL.md`](knowledge/promot/large_structure_workflow/SKILL.md)，工程字段和坐标约定见 [`WORK_CONTRACT.md`](knowledge/promot/large_structure_workflow/WORK_CONTRACT.md)。

一次构建、导出并校验所有内容：

```console
python scripts/structure_work.py build workset/my_palace
```

也可以直接运行 work 自己的入口：

```console
python workset/my_palace/main.py
```

构建命令会自动完成：

* 将密集逻辑画布切片，或把记录式逻辑画布逐片渲染成体积不超过 65,536 方块的 `.mcstructure`。
* 生成大型建筑所需的 `netease_features`、`netease_feature_rules`、`netease_biomes` 和自定义维度 JSON；继承的原版群系由 `project.json` 中的 `biome_inherits` 指定。
* 生成适合小型建筑或手动触发的 ModSDK 分批放置脚本。
* 构建时检查内存中的 JSON/尺寸、文件存在性、边界、清单计数和必要引用，不立即重开数千个刚写出的文件。

已有输出可以单独复查：

```console
python scripts/structure_work.py validate workset/my_palace
```

独立 `validate` 会以最多 16 个受限并发 worker 重新解析全部 JSON 并读取每个结构的 NBT 头，但仍不会完整解码每片数万个方块索引。可用 `--workers N` 调整并发；日常快速迭代可运行 `python scripts/structure_work.py validate workset/my_palace --fast`，只检查清单、计数、引用和文件库存。发布前仍应执行默认深度校验。完整 NBT 编解码由小型 round-trip 测试覆盖。

可运行的最小基准位于 [`workset/example_work`](workset/example_work/README.md)。建议先构建该示例，以区分共享工具链问题与新建筑源码问题。

妙用链接
------------

* 📖 [此项目之文档](https://mcstructure.readthedocs.io/en/latest/)
* 📁 [此项目之源码](https://github.com/phoenixr-codes/mcstructure)
* 🐍 [PyPI](https://pypi.org/project/mcstructure/)

### 其他资源

* 👋 [结构方块的简介](https://learn.microsoft.com/en-us/minecraft/creator/documents/introductiontostructureblocks)
* 📖 [基岩版维基](https://wiki.bedrock.dev/nbt/mcstructure.html#file-format)
_译注：文件结构文档已经被我翻译了，详见[我的译本](https://gitee.com/TriM-Organization/mcstructure/blob/main/docs/mcstructure%E6%96%87%E4%BB%B6%E7%BB%93%E6%9E%84.md)_
--------------------------------------------

NOT AN OFFICIAL MINECRAFT PRODUCT.
NOT APPROVED BY OR ASSOCIATED WITH MOJANG.

此项目并非一个官方 《我的世界》（*Minecraft*）项目

此项目不隶属或关联于 Mojang Studios
