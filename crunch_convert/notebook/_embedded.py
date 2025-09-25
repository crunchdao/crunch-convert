from dataclasses import dataclass


@dataclass(kw_only=True)
class EmbeddedFile:
    path: str
    normalized_path: str
    content: str
