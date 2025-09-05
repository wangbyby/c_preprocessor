#!/usr/bin/env python3
"""
Converter between custom Graph dataclass and pydot Graph
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import pydot


class NodeShape(Enum):
    RECT = "box"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"


class LineType(Enum):
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


@dataclass
class Line:
    type: LineType = LineType.SOLID
    src_arrow: bool = False  # <---
    dst_arrow: bool = True   # -->
    inline_label: bool = False  # means label is line --label--> or upper
    label: str = ""  # --label--> , -->|label|
    line_len: int = 1  # ---> vs ----->


@dataclass
class Node:
    id: str = ""
    label: str = ""
    shape: NodeShape = NodeShape.RECT


@dataclass
class Edge:
    src: Node
    dst: Node
    edge: Line
    label: str = ""


@dataclass
class Graph:
    id: str = ""
    parent: Optional["Graph"] = None
    children: List["Graph"] = field(default_factory=list)
    dir: str = "TB"  # TB, LR, BT, RL
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)


class GraphConverter:
    """Convert between custom Graph and pydot Graph"""
    
    @staticmethod
    def custom_to_pydot(custom_graph: Graph) -> pydot.Dot:
        """Convert custom Graph to pydot Graph"""
        
        # Create main graph
        pydot_graph = pydot.Dot(
            graph_name=custom_graph.id or 'G',
            graph_type='digraph',
            rankdir=custom_graph.dir or 'TB'
        )
        
        # Add nodes
        for node in custom_graph.nodes:
            pydot_node = pydot.Node(
                node.id,
                label=node.label or node.id,
                shape=node.shape.value
            )
            pydot_graph.add_node(pydot_node)
        
        # Add edges
        for edge in custom_graph.edges:
            # Determine edge attributes
            edge_attrs = {}
            
            if edge.edge.label:
                edge_attrs['label'] = edge.edge.label
            
            if edge.edge.type == LineType.DASHED:
                edge_attrs['style'] = 'dashed'
            elif edge.edge.type == LineType.DOTTED:
                edge_attrs['style'] = 'dotted'
            
            # Handle arrow directions
            if not edge.edge.dst_arrow:
                edge_attrs['arrowhead'] = 'none'
            if edge.edge.src_arrow:
                edge_attrs['dir'] = 'both'
            
            pydot_edge = pydot.Edge(
                edge.src.id,
                edge.dst.id,
                **edge_attrs
            )
            pydot_graph.add_edge(pydot_edge)
        
        # Add subgraphs (children)
        for child in custom_graph.children:
            child_pydot = GraphConverter.custom_to_pydot(child)
            pydot_graph.add_subgraph(child_pydot)
        
        return pydot_graph
    
    @staticmethod
    def pydot_to_custom(pydot_graph: pydot.Dot) -> Graph:
        """Convert pydot Graph to custom Graph"""
        
        # Create custom graph
        custom_graph = Graph(
            id=pydot_graph.get_name() or 'G',
            dir=pydot_graph.get('rankdir') or 'TB'
        )
        
        # Convert nodes
        node_map = {}  # id -> Node mapping
        for pydot_node in pydot_graph.get_nodes():
            node_id = pydot_node.get_name().strip('"')
            
            # Skip default attribute nodes
            if node_id in ['node', 'edge', 'graph']:
                continue
            
            label = pydot_node.get('label')
            if label:
                label = label.strip('"')
            else:
                label = node_id
            
            shape_str = pydot_node.get('shape')
            if shape_str:
                shape_str = shape_str.strip('"')
                # Map pydot shapes to our enum
                shape_map = {
                    'box': NodeShape.RECT,
                    'circle': NodeShape.CIRCLE,
                    'ellipse': NodeShape.ELLIPSE,
                    'diamond': NodeShape.DIAMOND
                }
                shape = shape_map.get(shape_str, NodeShape.RECT)
            else:
                shape = NodeShape.ELLIPSE  # Default
            
            node = Node(id=node_id, label=label, shape=shape)
            custom_graph.nodes.append(node)
            node_map[node_id] = node
        
        # Convert edges
        for pydot_edge in pydot_graph.get_edges():
            src_id = pydot_edge.get_source().strip('"')
            dst_id = pydot_edge.get_destination().strip('"')
            
            if src_id in node_map and dst_id in node_map:
                src_node = node_map[src_id]
                dst_node = node_map[dst_id]
                
                # Parse edge attributes
                label = pydot_edge.get('label')
                if label:
                    label = label.strip('"')
                else:
                    label = ""
                
                style = pydot_edge.get('style')
                if style:
                    style = style.strip('"')
                    line_type = {
                        'dashed': LineType.DASHED,
                        'dotted': LineType.DOTTED
                    }.get(style, LineType.SOLID)
                else:
                    line_type = LineType.SOLID
                
                # Check arrow directions
                arrowhead = pydot_edge.get('arrowhead')
                dst_arrow = arrowhead != 'none' if arrowhead else True
                
                direction = pydot_edge.get('dir')
                src_arrow = direction == 'both' if direction else False
                
                line = Line(
                    type=line_type,
                    src_arrow=src_arrow,
                    dst_arrow=dst_arrow,
                    label=label
                )
                
                edge = Edge(src=src_node, dst=dst_node, edge=line, label=label)
                custom_graph.edges.append(edge)
        
        # Convert subgraphs
        for subgraph in pydot_graph.get_subgraphs():
            child_graph = GraphConverter.pydot_to_custom(subgraph)
            child_graph.parent = custom_graph
            custom_graph.children.append(child_graph)
        
        return custom_graph


def example_usage():
    """Example showing conversion between formats"""
    
    # Create custom graph
    custom_graph = Graph(id="example", dir="LR")
    
    # Add nodes
    start_node = Node(id="start", label="Start", shape=NodeShape.CIRCLE)
    process_node = Node(id="process", label="Process", shape=NodeShape.RECT)
    end_node = Node(id="end", label="End", shape=NodeShape.CIRCLE)
    
    custom_graph.nodes.extend([start_node, process_node, end_node])
    
    # Add edges
    line1 = Line(dst_arrow=True, label="begin")
    edge1 = Edge(src=start_node, dst=process_node, edge=line1)
    
    line2 = Line(dst_arrow=True, label="complete")
    edge2 = Edge(src=process_node, dst=end_node, edge=line2)
    
    custom_graph.edges.extend([edge1, edge2])
    
    print("=== Custom Graph ===")
    print(f"Graph ID: {custom_graph.id}")
    print(f"Direction: {custom_graph.dir}")
    print(f"Nodes: {len(custom_graph.nodes)}")
    print(f"Edges: {len(custom_graph.edges)}")
    
    # Convert to pydot
    pydot_graph = GraphConverter.custom_to_pydot(custom_graph)
    
    print("\n=== Pydot Graph ===")
    print(pydot_graph.to_string())
    
    # Convert back to custom
    converted_back = GraphConverter.pydot_to_custom(pydot_graph)
    
    print("\n=== Converted Back ===")
    print(f"Graph ID: {converted_back.id}")
    print(f"Direction: {converted_back.dir}")
    print(f"Nodes: {len(converted_back.nodes)}")
    print(f"Edges: {len(converted_back.edges)}")


if __name__ == "__main__":
    example_usage()