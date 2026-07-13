<p align="center">
  <img
    src="https://raw.githubusercontent.com/phoenixr-codes/mcstructure/main/logo.png"
    width="120px"
    align="center" alt="mcstructure logo"
  />
  <h1 align="center">mcstructure</h1>
  <p align="center">
    Read and write Minecraft <code>.mcstructure</code> files.
  </p>
</p>

🌍 This README is also available in the following
languages:

* 🇨🇳 [Chinese](./README_CN.md)
* 🇩🇪 [German](./README_DE.md)


<!-- Not really accessible ♿️ but we get a prettier line
than the default "<hr/>" or "---" --> 
<h2></h2>

[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/mcstructure/badge/?style=for-the-badge&version=latest)](https://mcstructure.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/mcstructure?style=for-the-badge)](https://pypi.org/project/mcstructure)

_In the entire project ([and officially since 
the "Better Together Update"](https://www.minecraft.net/de-de/article/all-news-e3)) the term
"Minecraft" refers to the edition of Minecraft
that is also known as the "Bedrock Edition"._

_Features that this library provides are only
useful for the above named edition of Minecraft._

> [!WARNING]
> This project is currently in the **BETA** version. Some
> features may not work as expected and might change without backwards compability or deprecation warnings.

<!-- start elevator-pitch -->

This library lets you programmatically create
and edit Minecraft structures. You are able to
save these as ``.mcstructure`` files and for
example use them in behavior packs.

You may as well read them to identify blocks and
and entities that were saved with a Structure
Block in-game.

<!-- end elevator-pitch -->

Installation
------------

```console
pip install mcstructure
```


Basic Usage
-----------

```python
from mcstructure import Block, Structure

struct = Structure(
    (7, 7, 7),
    Block("minecraft:wool", color = "red")
)

(struct
    .set_block((1, 1, 1), Block("minecraft:grass"))
    .set_block((2, 2, 2), Block("minecraft:grass"))
    .set_block((3, 3, 3), Block("minecraft:grass"))
    .set_block((4, 4, 4), Block("minecraft:grass"))
    .set_block((5, 5, 5), Block("minecraft:grass"))
    .set_block((6, 6, 6), Block("minecraft:grass"))
)

with open("house.mcstructure", "wb") as f:
    struct.dump(f)
```

```python
with open("house.mcstructure", "rb") as f:
    struct = Structure.load(f)
```

AI-Assisted Large-Structure Workflow
------------------------------------

This repository includes a workflow for building large structures with an AI collaborator. Its central rule is: **AI authors the building design and source code; deterministic tooling owns slicing, NetEase configuration, placement scripts, and output validation.** This keeps generated platform files out of prompts and makes architectural iterations reproducible.

> [!NOTE]
> These commands are repository-local development tools, not part of the public PyPI API.

A standard work directory contains:

```text
workset/<work>/
├── BRIEF.md           # Building requirements, route, and acceptance criteria
├── project.json       # Canvas, builder, dimension, and slicing contract
├── main.py            # One-command entry point for this work
├── src/<package>/     # AI-authored building generator
└── out/               # Generated output; do not edit or commit
```

The builder declared in `project.json` must be a zero-argument function returning one complete `mcstructure.Structure` whose size exactly matches `structure_size`. The AI should edit only the target work's `main.py` and `src/`; the shared workflow generates `.mcstructure` pieces, features, feature rules, dimension files, the ModSDK queue, and manifests.

Create a work shell:

```console
python scripts/structure_work.py new workset/my_palace --project-name "My Palace" --size 192 80 192 --origin 2048 56 2048
```

Fill in the generated `BRIEF.md`, then give the AI the repository's [prompt template](knowledge/promot/large_structure_workflow/PROMPT_TEMPLATE.md). See the complete [AI workflow](knowledge/promot/large_structure_workflow/SKILL.md) and [work contract](knowledge/promot/large_structure_workflow/WORK_CONTRACT.md) for the implementation rules.

Build, export, and validate everything in one pass:

```console
python scripts/structure_work.py build workset/my_palace
```

The generated `main.py` is also a valid entry point:

```console
python workset/my_palace/main.py
```

The build automatically:

* Splits the logical canvas into `.mcstructure` pieces of at most 65,536 blocks.
* Generates NetEase features, feature rules, and custom-dimension JSON for large world-generated structures.
* Generates a batched ModSDK placement helper for smaller or manually triggered structures.
* Loads the structures back and validates JSON, dimensions, bounds, manifest counts, and required references.

Audit an existing output without rewriting it:

```console
python scripts/structure_work.py validate workset/my_palace
```

The runnable [`workset/example_work`](workset/example_work/README.md) project is the minimal reference implementation. Build it first when you need to distinguish a shared-tooling problem from a new generator problem.


References
----------

* 📖 [Documentation](https://mcstructure.readthedocs.io/en/latest/)
* 📁 [Source Code](https://github.com/phoenixr-codes/mcstructure)
* 🐍 [PyPI](https://pypi.org/project/mcstructure/)

### External Resources

* 👋 [Introduction to Structure Blocks](https://learn.microsoft.com/en-us/minecraft/creator/documents/introductiontostructureblocks)
* 📖 [Bedrock Wiki](https://wiki.bedrock.dev/nbt/mcstructure.html#file-format)


--------------------------------------------

NOT AN OFFICIAL MINECRAFT PRODUCT.
NOT APPROVED BY OR ASSOCIATED WITH MOJANG.
