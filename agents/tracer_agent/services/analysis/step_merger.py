from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.label_synthesizer import LabelSynthesizer


class StepMerger:
    def __init__(self, acc: GraphAccumulator, labels: LabelSynthesizer) -> None:
        self._acc = acc
        self._labels = labels

    def merge(self) -> None:
        while self._merge_pass():
            continue

    def _merge_pass(self) -> bool:
        nodes = self._acc.nodes()
        edges = self._acc.edges()
        for source, target, arm_label in sorted(edges):
            if arm_label or edges[(source, target, arm_label)].kind != "sequence":
                continue
            if not self._is_step(source, nodes) or not self._is_step(target, nodes):
                continue
            if self._out_degree(source) != 1 or self._in_degree(target) != 1:
                continue
            self._absorb(source, target)
            return True
        return False

    def _absorb(self, source: str, target: str) -> None:
        nodes = self._acc.nodes()
        edges = self._acc.edges()
        head, tail = nodes[source], nodes[target]
        for fqn in tail.backing:
            if fqn not in head.backing:
                head.backing.append(fqn)
        head.refs.extend(tail.refs)
        head.badges.update(tail.badges)
        head.label = self._labels.step_label(head.backing)
        del edges[(source, target, "")]
        for key in [k for k in edges if k[0] == target]:
            edge = edges.pop(key)
            new_key = (source, key[1], key[2])
            if new_key not in edges and source != key[1]:
                edge.source = source
                edges[new_key] = edge
        self._repoint_containers(nodes, source, target)
        del nodes[target]

    def _repoint_containers(self, nodes: dict, source: str, target: str) -> None:
        for node_id in sorted(nodes):
            if node_id == target:
                continue
            draft = nodes[node_id]
            if target in draft.containers:
                draft.containers.remove(target)
                if (
                    source != node_id
                    and source not in draft.containers
                    and not self._is_descendant(nodes, source, node_id)
                ):
                    draft.containers.append(source)

    def _is_descendant(self, nodes: dict, node_id: str, ancestor: str) -> bool:
        seen = {node_id}
        frontier = list(nodes[node_id].containers) if node_id in nodes else []
        while frontier:
            next_frontier: list[str] = []
            for candidate in frontier:
                if candidate == ancestor:
                    return True
                if candidate in seen or candidate not in nodes:
                    continue
                seen.add(candidate)
                next_frontier.extend(nodes[candidate].containers)
            frontier = next_frontier
        return False

    def _is_step(self, node_id: str, nodes: dict) -> bool:
        node = nodes.get(node_id)
        return node is not None and node.kind == "step"

    def _out_degree(self, source: str) -> int:
        return sum(1 for key in self._acc.edges() if key[0] == source)

    def _in_degree(self, target: str) -> int:
        return sum(1 for key in self._acc.edges() if key[1] == target)
