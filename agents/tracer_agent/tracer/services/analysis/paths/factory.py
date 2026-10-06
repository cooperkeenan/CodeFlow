from collections.abc import Iterable

from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite
from tracer.services.analysis.paths.arm_signal_index import ArmSignalIndex
from tracer.services.analysis.paths.candidate_ranker import CandidateRanker
from tracer.services.analysis.paths.failure_oracle import FailureOracle
from tracer.services.analysis.paths.happy_path_tracer import HappyPathTracer
from tracer.services.analysis.paths.happy_path_walker import HappyPathWalker
from tracer.services.analysis.paths.hop_finder import HopFinder
from tracer.services.analysis.paths.path_graph import PathGraph
from tracer.services.analysis.paths.reach_counter import ReachCounter
from tracer.services.analysis.paths.route_owners import RouteOwners
from tracer.services.analysis.resolve.mro_method_finder import MroMethodFinder
from tracer.services.analysis.routes.delegation_resolver import DelegationResolver

from shared.models.flow_graph import FlowGraph


def trace_happy_paths(
    graph: FlowGraph, index: ProjectIndex, dispatch: Iterable[DispatchSite]
) -> FlowGraph:
    path_graph = PathGraph(graph)
    arms = ArmSignalIndex(dispatch)
    oracle = FailureOracle(arms, index, path_graph)
    ranker = CandidateRanker(arms, oracle, ReachCounter(path_graph))
    owners = RouteOwners(DelegationResolver(index, MroMethodFinder(index)))
    walker = HappyPathWalker(path_graph, ranker, HopFinder(path_graph), owners)
    return HappyPathTracer(walker).trace(graph)
