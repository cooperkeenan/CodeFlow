from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupForest
from shared.flow_endpoints.group_meta import GroupMeta
from shared.flow_endpoints.slice_assembler import ENDPOINT_LANE_ID, SliceAssembler
from shared.flow_endpoints.slice_graph import SliceGraph
from shared.flow_endpoints.terminal_closer import LINK_PREFIX
from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode

_PREVIEW_PATHS = 3


class GroupOverview:
    def __init__(self, assembler: SliceAssembler, meta: GroupMeta) -> None:
        self._assembler = assembler
        self._meta = meta

    def slice(self, graph: FlowGraph, forest: GroupForest, group_id: str) -> FlowGraph | None:
        group = forest.find(group_id)
        if group is None or group.is_leaf:
            return None
        entry = next((n for n in graph.nodes if n.id == group.entry_id), None)
        if entry is None:
            return None
        title = self._meta.title(group)
        root = entry.model_copy(
            deep=True,
            update={
                "label": title,
                "llm_label": title,
                "lane": ENDPOINT_LANE_ID,
                "level": 0,
                "members": [],
                "hidden_children": [],
                "containers": [],
                "body_head": "",
                "body_tails": [],
            },
        )
        children = [self._child(c) for c in forest.children(group_id)]
        edges = [FlowEdge(source=root.id, target=c.id, kind="sequence") for c in children]
        working = SliceGraph({n.id: n for n in [root, *children]}, edges, root.id)
        meta = {
            "entry_id": root.id,
            "entry_label": title,
            "group": self._meta.of(group),
            "paths": [],
        }
        return self._assembler.finish(graph, working, root, meta)

    def _child(self, child: EndpointGroup) -> FlowNode:
        paths = sorted({route.path for route in child.routes})[:_PREVIEW_PATHS]
        return FlowNode(
            id=f"{LINK_PREFIX}{child.id}",
            kind="step",
            lane=ENDPOINT_LANE_ID,
            label=self._meta.title(child),
            one_liner=", ".join(paths),
        )
