from dataclasses import dataclass, field


@dataclass
class DirGroup:
    path: str
    file_count: int
    sample_files: list[str] = field(default_factory=list)


@dataclass
class ModuleSkeleton:
    name: str
    root_path: str
    directories: list[DirGroup] = field(default_factory=list)


@dataclass
class RepoSkeleton:
    modules: list[ModuleSkeleton] = field(default_factory=list)
