from dataclasses import dataclass


@dataclass()
class EmbeddedFile:
    path: str
    normalized_path: str
    content: str
