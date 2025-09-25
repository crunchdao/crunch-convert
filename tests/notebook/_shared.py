
from typing import Any, Dict, List, Literal


def cell(
    id: str,
    type: Literal["markdown", "code"],
    source: List[str],
) -> Dict[str, Any]:
    return {
        "metadata": {
            "id": id,
        },
        "cell_type": type,
        "source": source,
    }
