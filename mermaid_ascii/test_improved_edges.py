#!/usr/bin/env python3
"""
Test the improved edge drawing system
"""

import pydot
from pydot_to_ascii import PydotToASCII

def test_simple_graph():
    """Test with a simple linear graph"""
    print("=== Simple Linear Graph ===")
    graph = pydot.Dot(graph_type='digraph')
    
    graph.add_node(pydot.Node('A', label='Start', shape='box'))
    graph.add_node(pydot.Node('B', label='Process', shape='box'))
    graph.add_node(pydot.Node('C', label='End', shape='box'))
    
    graph.add_edge(pydot.Edge('A', 'B'))
    graph.add_edge(pydot.Edge('B', 'C'))
    
    converter = PydotToASCII()
    result = converter.convert_to_ascii(graph)
    print(result)
    print()

def test_branching_graph():
    """Test with a branching graph"""
    print("=== Branching Graph ===")
    graph = pydot.Dot(graph_type='digraph')
    
    graph.add_node(pydot.Node('A', label='Start', shape='box'))
    graph.add_node(pydot.Node('B', label='Process', shape='box'))
    graph.add_node(pydot.Node('C', label='Success', shape='box'))
    graph.add_node(pydot.Node('D', label='Error', shape='box'))
    
    graph.add_edge(pydot.Edge('A', 'B'))
    graph.add_edge(pydot.Edge('B', 'C'))
    graph.add_edge(pydot.Edge('B', 'D'))
    
    converter = PydotToASCII()
    result = converter.convert_to_ascii(graph)
    print(result)
    print()

def test_complex_graph():
    """Test with a more complex graph"""
    print("=== Complex Graph ===")
    graph = pydot.Dot(graph_type='digraph')
    
    # Add nodes
    graph.add_node(pydot.Node('A', label='Input'))
    graph.add_node(pydot.Node('B', label='Validate', shape='box'))
    graph.add_node(pydot.Node('C', label='Process', shape='box'))
    graph.add_node(pydot.Node('D', label='Save', shape='box'))
    graph.add_node(pydot.Node('E', label='Output'))
    graph.add_node(pydot.Node('F', label='Error'))
    
    # Add edges
    graph.add_edge(pydot.Edge('A', 'B'))
    graph.add_edge(pydot.Edge('B', 'C'))
    graph.add_edge(pydot.Edge('C', 'D'))
    graph.add_edge(pydot.Edge('D', 'E'))
    graph.add_edge(pydot.Edge('B', 'F'))  # Error path from validation
    graph.add_edge(pydot.Edge('C', 'F'))  # Error path from processing
    
    converter = PydotToASCII()
    result = converter.convert_to_ascii(graph)
    print(result)
    print()

if __name__ == "__main__":
    test_simple_graph()
    test_branching_graph()
    test_complex_graph()