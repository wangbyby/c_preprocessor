"""
#step 1, calc layout for graph

###support only one graph now


according to direction
1. calc basic mapping info

e.g
graph TD
    A[Start] --> B[Process]
    B --> C{Decision}
    C -->|Yes| D[Result 1]
    C -->|No| E[Result 2]


    A
    |
    B
    |
    C---+
    |   |
    D   E

name  : level
    A : 1
    B : 2
    C : 3
    D : 4
    E : 4

our ascii canvas is like
    
     0 1 2 3
  0  A
  1  |
  2  B
  3  |
  4  C - - +
  5  |     |
  6  D     E
    
also we need to calc label's pos to layout the graph

"""

from typing import Dict, List
from mermaid_ascii.graph import Graph, Node


class Layout:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.levels: Dict[int, List[Node]] = {}

        self._calc_grid()

    def _level_range(self, g: Graph, root: Node):
        l = [root]
        visited = set()
        level = 1

        while len(l) > 0:
            length = len(l)

            for _ in range(length):
                n = l.pop(0)
                if n in visited:
                    continue
                visited.add(n)
                n.grid_y = level

                for next in n.get_neighbors(g):
                    if next not in visited:
                        l.append(next)

            level += 2

    def _calc_grid(self):
        roots = self.graph.get_root_node()

        for root in roots:
            self._level_range(self.graph, root)

        for node in self.graph.get_nodes():
            l = self.levels.get(node.grid_y, None)
            if l is None:
                self.levels[node.grid_y] = [node]
            else:
                self.levels[node.grid_y].append(node)

        for _, l in self.levels.items():
            x = 1
            for n in l:
                n.grid_x = x
                x += 2


    def _calc_ascii_pos(self):
        pass 
      