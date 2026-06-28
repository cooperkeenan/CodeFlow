from pydantic import BaseModel


class ZonePlan(BaseModel):
    name: str
    description: str = ""
    directories: list[str] = []


class ModulePlan(BaseModel):
    name: str
    description: str = ""
    root_path: str
    style: str = ""
    zones: list[ZonePlan] = []


class RepoBlueprint(BaseModel):
    architecture_type: str
    language: str
    framework: str
    patterns: list[str] = []
    modules: list[ModulePlan] = []
