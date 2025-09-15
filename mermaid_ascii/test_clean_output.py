#!/usr/bin/env python3
"""
Test the clean line drawing output
"""

# Simple test without importing pydot to show the expected structure
class MockGraph:
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def get_nodes(self):
        return self.nodes
    
    def get_edges(self):
        return self.edges

class MockNode:
    def __init__(self, name, label=None, shape=None):
        self.name = name
        self.label = label
        self.shape = shape
    
    def get_name(self):
        return f'"{self.name}"'
    
    def get(self, attr):
        if attr == 'label':
            return f'"{self.label}"' if self.label else None
        elif attr == 'shape':
            return f'"{self.shape}"' if self.shape else None
        return None

class MockEdge:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
    
    def get_source(self):
        return f'"{self.src}"'
    
    def get_destination(self):
        return f'"{self.dst}"'

# Test the ASCII output structure
def test_clean_output():
    print("Expected Clean ASCII Output Structure:")
    print("=" * 50)
    
    # This is what we want the output to look like:
    expected_output = """
    +--------+
    |  Start |
    +--------+
         |
         v
    +--------+
    |Process |
    +--------+
         |
         +---+
         |   |
         v   v
    +------+ +-------+
    | End  | | Error |
    +------+ +-------+
    """
    
    print(expected_output)
    print("\nKey improvements:")
    print("1. Clean vertical lines using |")
    print("2. Clean horizontal lines using -")
    print("3. Proper junction points using +")
    print("4. Arrow heads: v ^ < >")
    print("5. No overlapping with node boxes")
    print("6. L-shaped connections for branching")

if __name__ == "__main__":
    test_clean_output()
    
    # If pydot is available, test the actual converter
    try:
        import pydot
        from pydot_to_ascii import PydotToASCII
        
        print("\n" + "=" * 50)
        print("Actual Output Test:")
        print("=" * 50)
        
        # Create a simple test graph
        graph = pydot.Dot(graph_type='digraph')
        graph.add_node(pydot.Node('A', label='Start', shape='box'))
        graph.add_node(pydot.Node('B', label='Process', shape='box'))
        graph.add_node(pydot.Node('C', label='End', shape='box'))
        graph.add_node(pydot.Node('D', label='Error', shape='box'))
        
        graph.add_edge(pydot.Edge('A', 'B'))
        graph.add_edge(pydot.Edge('B', 'C'))
        graph.add_edge(pydot.Edge('B', 'D'))
        
        converter = PydotToASCII()
        result = converter.convert_to_ascii(graph)
        print(result)
        
    except ImportError:
        print("\nPydot not available for testing, but the structure should work!")