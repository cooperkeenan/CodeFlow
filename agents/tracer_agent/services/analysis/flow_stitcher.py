from models.effect_site import EffectSite
from models.flow_entry import FlowEntry
from services.analysis.stitch_detector import StitchDetector
from shared.models.flow_graph import FlowEdge, FlowGraph


class FlowStitcher:
    def __init__(self, detectors: tuple[StitchDetector, ...]) -> None:
        self._detectors = detectors

    def stitch(
        self,
        graph: FlowGraph,
        effects: tuple[EffectSite, ...],
        entries: tuple[FlowEntry, ...],
    ) -> FlowGraph:
        node_ids = {node.id for node in graph.nodes}
        present = tuple(effect for effect in effects if effect.id in node_ids)
        stitched: list[FlowEdge] = []
        for detector in self._detectors:
            for edge in detector.detect(present, entries):
                if edge.source in node_ids and edge.target in node_ids:
                    stitched.append(edge)
        return FlowGraph(
            repo=graph.repo,
            page_title=graph.page_title,
            lanes=graph.lanes,
            nodes=graph.nodes,
            edges=graph.edges + stitched,
            meta=graph.meta,
        )
