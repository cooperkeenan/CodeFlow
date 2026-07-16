from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FlowLabelMaps:
    page_title: str = ""
    lane_titles: dict[str, str] = field(default_factory=dict)
    node_labels: dict[str, str] = field(default_factory=dict)
    node_one_liners: dict[str, str] = field(default_factory=dict)
    arm_labels: dict[str, str] = field(default_factory=dict)
