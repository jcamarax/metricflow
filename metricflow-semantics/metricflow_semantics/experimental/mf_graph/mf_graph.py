"""Base classes for modeling a graph.

The graph object in `networkx` was evaluated, but it was not found to be well-typed.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import cached_property
from typing import ClassVar, Generic, Optional, TypeVar

from typing_extensions import Self, override

from metricflow_semantics.collection_helpers.mf_type_aliases import Pair
from metricflow_semantics.experimental.mf_graph.comparable import Comparable
from metricflow_semantics.experimental.mf_graph.formatting.dot_attributes import (
    DotEdgeAttributeSet,
    DotGraphAttributeSet,
    DotNodeAttributeSet,
)
from metricflow_semantics.experimental.mf_graph.formatting.graph_formatter import MetricflowGraphFormatter
from metricflow_semantics.experimental.mf_graph.formatting.pretty_graph_formatter import PrettyFormatGraphFormatter
from metricflow_semantics.experimental.mf_graph.graph_element import (
    MetricflowGraphElement,
)
from metricflow_semantics.experimental.mf_graph.graph_id import MetricflowGraphId
from metricflow_semantics.experimental.mf_graph.graph_labeling import MetricflowGraphLabel
from metricflow_semantics.experimental.mf_graph.node_descriptor import MetricflowGraphNodeDescriptor
from metricflow_semantics.experimental.ordered_set import FrozenOrderedSet, MutableOrderedSet, OrderedSet
from metricflow_semantics.experimental.singleton_decorator import singleton_dataclass
from metricflow_semantics.mf_logging.pretty_formattable import MetricFlowPrettyFormattable
from metricflow_semantics.mf_logging.pretty_formatter import (
    MetricFlowPrettyFormatter,
    PrettyFormatContext,
    PrettyFormatOption,
)

logger = logging.getLogger(__name__)


NodeT = TypeVar("NodeT", bound="MetricflowGraphNode", covariant=True)


class MetricflowGraphNode(MetricflowGraphElement, MetricFlowPrettyFormattable, Comparable, ABC):
    """Base class for nodes in a directed graph."""

    _DEFAULT_NODE_LABELS: ClassVar[OrderedSet[MetricflowGraphLabel]] = FrozenOrderedSet()

    def as_dot_node(self, include_graphical_attributes: bool) -> DotNodeAttributeSet:
        """Return this as attributes for a DOT node.

        Args:
            include_graphical_attributes: If set, include attributes for a graphical representation.

        Returns: An attribute set that can be used to create the DOT node.
        """
        return DotNodeAttributeSet.create(
            name=self.node_descriptor.node_name,
        )

    @property
    @abstractmethod
    def node_descriptor(self) -> MetricflowGraphNodeDescriptor:  # noqa: D102
        raise NotImplementedError

    @property
    def labels(self) -> OrderedSet[MetricflowGraphLabel]:
        """Return the labels that can be used for lookups to get this node."""
        return MetricflowGraphNode._DEFAULT_NODE_LABELS

    @override
    def pretty_format(self, format_context: PrettyFormatContext) -> Optional[str]:
        formatter = MetricFlowPrettyFormatter(
            format_option=format_context.formatter.format_option.merge(
                PrettyFormatOption(include_object_field_names=False)
            )
        )
        return formatter.pretty_format_object_by_parts(
            class_name=self.__class__.__name__,
            field_mapping={
                "node": self.node_descriptor.node_name,
            },
        )


@singleton_dataclass(order=False)
class MetricflowGraphEdge(MetricflowGraphElement, MetricFlowPrettyFormattable, Comparable, Generic[NodeT], ABC):
    """Base class for edges in a directed graph.

    An edge can be visualized as an arrow that points from the tail node to the head node.
    """

    _DEFAULT_EDGE_LABELS: ClassVar[OrderedSet[MetricflowGraphLabel]] = FrozenOrderedSet()

    # TODO: Check if these can be renamed / remove property accessors.
    _tail_node: NodeT
    _head_node: NodeT

    @property
    def tail_node(self) -> NodeT:  # noqa: D102
        return self._tail_node

    @property
    def head_node(self) -> NodeT:  # noqa: D102
        return self._head_node

    @property
    def node_pair(self) -> Pair[NodeT, NodeT]:
        """Return a tuple of the head node and the tail node."""
        return (self._tail_node, self._head_node)

    @property
    @abstractmethod
    def inverse(self) -> Self:
        """Return the inverse edge."""
        raise NotImplementedError()

    def as_dot_edge(self, include_graphical_attributes: bool) -> DotEdgeAttributeSet:
        """Return this as attributes for a DOT edge.

        Args:
            include_graphical_attributes: If set, include attributes for a graphical representation.

        Returns: An attribute set that can be used to create the DOT edge.
        """
        return DotEdgeAttributeSet.create(
            tail_name=self.tail_node.node_descriptor.node_name,
            head_name=self.head_node.node_descriptor.node_name,
        )

    @property
    def labels(self) -> OrderedSet[MetricflowGraphLabel]:
        """Return the labels that can be used for lookups to get this edge."""
        return MetricflowGraphEdge._DEFAULT_EDGE_LABELS

    @override
    def pretty_format(self, format_context: PrettyFormatContext) -> Optional[str]:
        formatter = MetricFlowPrettyFormatter(
            format_option=format_context.formatter.format_option.merge(
                PrettyFormatOption(include_object_field_names=False)
            )
        )
        return formatter.pretty_format_object_by_parts(
            class_name=self.__class__.__name__,
            field_mapping={
                "edge_str": f"{self._tail_node.node_descriptor.node_name} -> {self._head_node.node_descriptor.node_name}",
            },
        )

    @cached_property
    def labels_for_path_addition(self) -> OrderedSet[MetricflowGraphLabel]:
        """Return the labels for this edge and the head node.

        This is useful for collecting labels while building a path by adding an edge.
        """
        return self.labels.union(self._head_node.labels)


EdgeT = TypeVar("EdgeT", bound="MetricflowGraphEdge", covariant=True)


class MetricflowGraph(MetricFlowPrettyFormattable, Generic[NodeT, EdgeT], ABC):
    """Base class for a directed graph."""

    @property
    @abstractmethod
    def nodes(self) -> OrderedSet[NodeT]:
        """Return the set of nodes in the graph."""
        raise NotImplementedError()

    @abstractmethod
    def nodes_with_label(self, graph_label: MetricflowGraphLabel) -> OrderedSet[NodeT]:
        """Return nodes in the graph with the given label."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def edges(self) -> OrderedSet[EdgeT]:
        """Return the set of edges in a graph."""
        raise NotImplementedError()

    @abstractmethod
    def edges_with_tail_node(self, tail_node: MetricflowGraphNode) -> OrderedSet[EdgeT]:
        """Returns edges with the given tail node."""
        raise NotImplementedError()

    @abstractmethod
    def edges_with_head_node(self, tail_node: MetricflowGraphNode) -> OrderedSet[EdgeT]:
        """Returns edges with the given head node."""
        raise NotImplementedError()

    @abstractmethod
    def edges_with_label(self, label: MetricflowGraphLabel) -> OrderedSet[EdgeT]:
        """Return the set of edges in a graph that have the given label."""
        raise NotImplementedError()

    def format(self, formatter: MetricflowGraphFormatter = PrettyFormatGraphFormatter()) -> str:
        """Return a representation of this graph using the given formatter."""
        return formatter.format_graph(self)

    @abstractmethod
    def successors(self, node: MetricflowGraphNode) -> OrderedSet[NodeT]:
        """Returns successors of the given node.

        Raises `UnknownNodeException` if the node does not exist in the graph.
        """
        return FrozenOrderedSet(edge.head_node for edge in self.edges_with_tail_node(node))

    @abstractmethod
    def predecessors(self, node: MetricflowGraphNode) -> OrderedSet[NodeT]:
        """Returns predecessors of the given node.

        Raises `UnknownNodeException` if the node does not exist in the graph.
        """
        return FrozenOrderedSet(edge.tail_node for edge in self.edges_with_head_node(node))

    @override
    def pretty_format(self, format_context: PrettyFormatContext) -> str:
        return format_context.formatter.pretty_format_object_by_parts(
            class_name=self.__class__.__name__,
            field_mapping={"nodes": self.nodes, "edges": self.edges},
        )

    @abstractmethod
    def as_sorted(self) -> Self:
        """Return a copy of this graph with the nodes and edges sorted."""
        raise NotImplementedError

    def _intersect_edges(self, other: MetricflowGraph[NodeT, EdgeT]) -> OrderedSet[EdgeT]:
        return self.edges.intersection(other.edges)

    @abstractmethod
    def intersection(self, other: MetricflowGraph[NodeT, EdgeT]) -> Self:  # noqa: D102
        raise NotImplementedError()

    @abstractmethod
    def inverse(self) -> Self:  # noqa: D102
        raise NotImplementedError()

    def adjacent_edges(self, selected_nodes: OrderedSet[NodeT]) -> OrderedSet[EdgeT]:
        """Return the edges that have an end point in the selected nodes."""
        subgraph_edges = MutableOrderedSet[EdgeT]()
        for node in selected_nodes:
            for edge in self.edges_with_tail_node(node):
                if edge.head_node in selected_nodes:
                    subgraph_edges.add(edge)
            for edge in self.edges_with_head_node(node):
                if edge.tail_node in selected_nodes:
                    subgraph_edges.add(edge)
        return subgraph_edges

    def as_dot_graph(self, include_graphical_attributes: bool) -> DotGraphAttributeSet:
        """Return the attributes that should be used when creating a representation of this graph in DOT.

        Note that this does not contain the nodes and edges.
        """
        return DotGraphAttributeSet.create(
            name=self.__class__.__name__,
        )

    @property
    @abstractmethod
    def graph_id(self) -> MetricflowGraphId:
        """Return a graph ID.

        This ID will be used for caching cases.
        """
        raise NotImplementedError()
