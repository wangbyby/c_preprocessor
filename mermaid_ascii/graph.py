from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union


class Direction(Enum):
    TB = "TB"  # Top to Bottom
    TD = "TB"  # Top to Down
    LR = "LR"  # left to right
    RL = "RL"  # right to left
    BT = "BT"  # bottom to top


class NodeShape(Enum):
    RECT = "RECT"  # [] rectangle
    ROUND = "ROUND"  # ()  rounded rectangle
    CIRCLE = "CIRCLE"  # (()) circle
    DOUBLECIRCLE = "DOUBLECIRCLE"  # ((()))  double circle
    DIAMOND = "DIAMOND"  # {} diamond
    AsymmetricShapeRight = "AsymmetricShapeRight"  # >]
    AsymmetricShapeLeft = "AsymmetricShapeLeft"  # [<
    HEXAGON = "HEXAGON"  # {{}} 六边形
    LEFT_RECT = "LEFT_RECT"  # [/ /]
    RIGHT_RECT = "RIGHT_RECT"  # [\ \]
    TRAPEZOID_A = "TRAPEZOID"  # [/ \]
    TRAPEZOID_B = "TRAPEZOID_B"  # [\ /]

    def to_pydot_shape(self) -> str:
        mapping = {
            NodeShape.RECT: "box",
            NodeShape.ROUND: "oval",
            NodeShape.CIRCLE: "circle",
            NodeShape.DOUBLECIRCLE: "doublecircle",
            NodeShape.DIAMOND: "diamond",
            NodeShape.AsymmetricShapeRight: "trapezium",
            NodeShape.AsymmetricShapeLeft: "trapezium",
            NodeShape.HEXAGON: "hexagon",
            NodeShape.LEFT_RECT: "parallelogram",
            NodeShape.RIGHT_RECT: "parallelogram",
            NodeShape.TRAPEZOID_A: "trapezium",
            NodeShape.TRAPEZOID_B: "trapezium",
        }
        return mapping.get(self, "box")


class LineType(Enum):
    SOLID = "SOLID"  #  ---, -->
    DASHED = "DASHED"  # -.--, -.->
    BOLD = "BOLD"  # ===, ==>

    @staticmethod
    def from_str(s: str) -> "LineType":
        if "=" in s:
            return LineType.BOLD
        if "." in s:
            return LineType.DASHED
        return LineType.SOLID


@dataclass
class Line:
    type: LineType
    src_arrow: bool  # <---
    dst_arrow: bool  # -->
    inline_label: str = ""  # means label is line --label--> or upper
    outline_label: str = ""  #  -->|label|
    line_len: int = 1  # ---> vs ------>

    def to_attr_dict(self) -> dict:
        d = {}
        d["label"] = self.inline_label
        d["label2"] = self.outline_label
        d["style"] = self.type

        return d

    @staticmethod
    def from_style(style: str, l1: str = "", l2: str = "") -> "Line":
        line_type = LineType.from_str(style)
        src_arrow = style.startswith("<")
        dst_arrow = style.endswith(">")
        line_len = len(style) - (1 if src_arrow else 0) - (1 if dst_arrow else 0)
        return Line(
            type=line_type,
            src_arrow=src_arrow,
            dst_arrow=dst_arrow,
            inline_label=l1,
            outline_label=l2,
            line_len=line_len,
        )


@dataclass
class Node:
    id: str = ""
    label: str = ""
    shape: NodeShape = NodeShape.RECT

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Node):
            return False
        return id == value.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Edge:
    src: Node
    dst: Node
    line: Line

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Edge):
            return False
        return self.src == value.src and self.dst == value.dst

    def __hash__(self) -> int:
        return hash((self.src, self.dst))


@dataclass
class Graph:

    id: str = ""
    parent: "Graph | None" = None
    children: List["Graph"] = field(default_factory=list)

    direction: Direction = Direction.TB

    nodes: List["Node"] = field(default_factory=list)
    node_set: dict = field(default_factory=dict)

    edges: List["Edge"] = field(default_factory=list)
    edge_set = set()

    def add_sub_graph(self, g: Union["Graph", List["Graph"]]):
        if isinstance(g, list):
            for sub in g:
                self.children.append(sub)
                sub.parent = self
        elif isinstance(g, Graph):
            self.children.append(g)
            g.parent = self
        else:
            raise ValueError(f"Invalid type for add_sub_graph: {type(g)}")

    def add_node(self, node: Union[Node, List[Node]]):
        if isinstance(node, list):  # 如果是列表，逐个添加节点
            for n in node:
                if n.id not in self.node_set:
                    self.node_set[n.id] = n
                    self.nodes.append(n)

        else:  # 如果是单个节点，直接添加
            if node.id not in self.node_set:
                self.nodes.append(node)
                self.node_set[node.id] = node

    def contains_node(self, node_id: str) -> bool:
        return node_id in self.node_set

    def get_node(self, node_id: str) -> Node | None:
        return self.node_set.get(node_id, None)

    def add_edge(self, edge: Union[Edge, List[Edge]]):
        if isinstance(edge, list):
            for e in edge:
                if e not in self.edge_set:
                    self.edge_set.add(e)
                    self.edges.append(e)
        else:
            if edge not in self.edge_set:
                self.edges.append(edge)
                self.edge_set.add(edge)

    def get_nodes(self) -> List[Node]:
        return self.nodes

    def get_edges(self) -> List[Edge]:
        return self.edges
