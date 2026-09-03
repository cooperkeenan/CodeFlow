from collections.abc import Mapping

from tracer.services.analysis.graph_ops import Containered, is_descendant


class ContainerRepointer:
    def repoint(self, nodes: Mapping[str, Containered], keep: str, other: str) -> None:
        for node_id in sorted(nodes):
            if node_id == other:
                continue
            node = nodes[node_id]
            if other in node.containers:
                node.containers.remove(other)
                if (
                    keep != node_id
                    and keep not in node.containers
                    and not is_descendant(nodes, keep, node_id)
                ):
                    node.containers.append(keep)
                node.containers.sort()
