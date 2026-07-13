type NativeBlock = tuple[
    str,
    list[tuple[str, int]],
    list[tuple[str, str]],
    bool,
]
type NativeStructure = tuple[
    tuple[int, int, int],
    bytes,
    list[NativeBlock],
]

def load_simple_structure(data: bytes) -> NativeStructure | None: ...
