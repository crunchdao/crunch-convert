from typing import Any, Literal


def cell(
    id: str,
    type: Literal["markdown", "code"],
    source: list[str],
) -> dict[str, Any]:
    return {
        "metadata": {
            "id": id,
        },
        "cell_type": type,
        "source": source,
    }
