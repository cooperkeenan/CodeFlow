from collections import deque
from dataclasses import dataclass

from render.placement.flow_grid_config import FlowGridConfig
from render.placement.flow_reach import longest_path_depths
from render.placement.tree_structure import TreeForest, build_forest, select_root

from shared.models.flow_graph import FlowEdge, FlowNode


@dataclass(frozen=True)
class NodePlacement:
    node: FlowNode
    x: int
    y: int
    column: int
    is_spine: bool


@dataclass(frozen=True)
class LaneBand:
    placements: list[NodePlacement]
    band_top: int
    band_height: int
    center_y: int
    tree_pairs: frozenset[tuple[str, str]]


class TreeLayout:
    def __init__(self, config: FlowGridConfig) -> None:
        self._config = config

    def layout(
        self,
        lane_nodes: list[FlowNode],
        edges: list[FlowEdge],
        spine_nodes: frozenset[str],
        band_top: int,
    ) -> LaneBand:
        cfg = self._config
        center_y = band_top + cfg.lane_header_height + cfg.row_height // 2
        if not lane_nodes:
            return LaneBand(
                [], band_top, cfg.lane_header_height + cfg.lane_padding, center_y, frozenset()
            )
        depths = longest_path_depths(lane_nodes, edges)
        primary_root = select_root(lane_nodes, edges)
        forest = build_forest(lane_nodes, edges, depths, primary_root)
        nodes_by_id = {node.id: node for node in lane_nodes}
        positions = self._layout_forest(forest)
        max_row = max((row for row, _ in positions.values()), default=0)
        placements = [
            self._place(nodes_by_id[node_id], slot, row, center_y, node_id in spine_nodes)
            for node_id, (row, slot) in sorted(positions.items())
        ]
        band_height = cfg.lane_header_height + (max_row + 1) * cfg.row_step + cfg.lane_padding
        pairs = frozenset(
            (parent, child)
            for parent, kids in forest.children.items()
            for child in kids
        )
        return LaneBand(placements, band_top, band_height, center_y, pairs)

    def _place(
        self, node: FlowNode, slot: float, row: int, center_y: int, is_spine: bool
    ) -> NodePlacement:
        cfg = self._config
        x = cfg.lane_header_width + round(slot * cfg.col_step)
        y = center_y + row * cfg.row_step
        return NodePlacement(node, x, y, row, is_spine)

    def _layout_forest(self, forest: TreeForest) -> dict[str, tuple[int, float]]:
        cfg = self._config
        positions: dict[str, tuple[int, float]] = {}
        if not forest.roots:
            return positions
        primary_root, *secondary_roots = forest.roots
        row_cursor = self._place_subtree(primary_root, forest.children, 0, positions)
        row_cursor += cfg.subtree_gap_rows
        leaf_roots = [r for r in secondary_roots if not forest.children.get(r)]
        branch_roots = [r for r in secondary_roots if forest.children.get(r)]
        if leaf_roots:
            for slot, root_id in enumerate(leaf_roots):
                positions[root_id] = (row_cursor, float(slot))
            row_cursor += 1 + cfg.subtree_gap_rows
        for root_id in branch_roots:
            row_cursor = self._place_subtree(root_id, forest.children, row_cursor, positions)
            row_cursor += cfg.subtree_gap_rows
        return positions

    def _place_subtree(
        self,
        root_id: str,
        children: dict[str, list[str]],
        row_offset: int,
        positions: dict[str, tuple[int, float]],
    ) -> int:
        slots: dict[str, float] = {}
        self._assign_slots(root_id, children, slots, 0.0)
        rows = self._assign_rows(root_id, children, row_offset)
        for node_id, slot in slots.items():
            positions[node_id] = (rows[node_id], slot)
        return max(rows.values()) + 1

    def _assign_slots(
        self,
        node_id: str,
        children: dict[str, list[str]],
        slots: dict[str, float],
        cursor: float,
    ) -> float:
        kids = children.get(node_id, [])
        if not kids:
            slots[node_id] = cursor
            return cursor + 1.0
        for child_id in kids:
            cursor = self._assign_slots(child_id, children, slots, cursor)
        child_slots = [slots[child_id] for child_id in kids]
        slots[node_id] = sum(child_slots) / len(child_slots)
        return cursor

    def _assign_rows(
        self, root_id: str, children: dict[str, list[str]], row_offset: int
    ) -> dict[str, int]:
        rows = {root_id: row_offset}
        queue: deque[str] = deque([root_id])
        while queue:
            current = queue.popleft()
            for child_id in children.get(current, []):
                rows[child_id] = rows[current] + 1
                queue.append(child_id)
        return rows
