from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GameContext: 
    project_name: str
    project_path: Path
    profile: dict = field(default_factory=dict)