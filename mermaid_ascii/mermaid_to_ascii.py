from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Set, Generic, TypeVar, Union
from collections import defaultdict
import logging


class Direction(Enum):
    TB = "TB"  # Top to Bottom
    TD = "TD"  # same as TB
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
    hangoff_label: str = ""  #  -->|label|
    line_len: int = 1  # ---> vs ------>

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
            hangoff_label=l2,
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
    edge: Line

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Edge):
            return False
        return self.src == value.src and self.dst == value.dst

    def __hash__(self) -> int:
        return hash((self.src, self.dst))


@dataclass
class Graph:

    id: str = ""
    parent: "Graph" = None
    children: List["Graph"] = field(default_factory=list)

    dir = None

    nodes: List["Node"] = field(default_factory=list)
    node_set = set()

    edges: List["Edge"] = field(default_factory=list)
    edge_set = set()

    def add_sub_graph(self, g: Union["Graph", List["Graph"]]):
        if isinstance(g, list):
            for sub in g:
                self.children.append(sub)
                sub.parent = self
        else:
            self.children.append(g)
            g.parent = self

    def add_node(self, node: Union[Node, List[Node]]):
        if isinstance(node, list):  # 如果是列表，逐个添加节点
            for n in node:
                if n not in self.node_set:
                    self.node_set.add(n)
                    self.nodes.append(n)

        else:  # 如果是单个节点，直接添加
            if node not in self.node_set:
                self.nodes.append(node)
                self.node_set.add(node)

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


class TokenType(Enum):
    TEXT = "TEXT"
    LINE = "LINE"

    GRAPH = "graph"
    SUBGRAPH = "subgraph"
    END = "end"

    L_PAREN = "("
    R_PAREN = ")"
    L_BRACKET = "["
    R_BRACKET = "]"
    L_CURLY = "{"
    R_CURLY = "}"
    LABEL = "|"
    AND = "&"

    LEFT = "<"
    RIGHT = ">"
    SLASH = "/"
    BACKSLASH = "\\"

    @staticmethod
    def from_keyword(s: str):
        mapping = {
            "graph": TokenType.GRAPH,
            "subgraph": TokenType.SUBGRAPH,
            "end": TokenType.END,
        }
        return mapping.get(s, None)


@dataclass
class Token:
    content: str
    type: TokenType


class Lexer:
    def __init__(self):
        self.position = 0
        self.tokens: list[Token] = []

    def parse_line(self, text: str, cur: int) -> int:
        size = len(text)
        while cur < size and text[cur].isspace():
            cur += 1
        if cur >= size:
            return cur

        # ox<>  ---/===/-.-- ox<>

        start = cur
        if text[cur] in "ox<>":
            if cur + 1 < size and text[cur + 1] in "-.=":
                cur += 1

        if text[cur] in "-.=":
            while cur < size and text[cur] in "-.=":
                cur += 1

        if cur < size and text[cur] in "ox<>":
            cur += 1

        if cur > start:
            self.tokens.append(Token(text[start:cur], TokenType.LINE))
        return cur

    def run(self, text: str):
        cur = 0
        size = len(text)
        while cur < size:
            if text[cur].isspace():
                cur += 1
                continue
            # process --o --x x-- o-- <-- --> <-->
            cur = self.parse_line(text, cur)

            punctor = "[](){}|&<>/\\"
            p2 = punctor + "-.="

            if text[cur] in punctor:
                self.tokens.append(Token(text[cur], TokenType(text[cur])))
                cur += 1
                continue

            # identifier or label
            begin = cur

            while (cur < size) and (not text[cur].isspace()) and (text[cur] not in p2):
                cur += 1

            if begin == cur:
                cur = begin
                continue

            sub = text[begin:cur]

            k = TokenType.from_keyword(sub)
            if k is not None:
                self.tokens.append(Token(sub, k))
            else:
                self.tokens.append(Token(sub, TokenType.TEXT))


# T = TypeVar("T")
# class Iterator(Generic[T]):
#     def __init__(self, items: List[T] = []):
#         self.list = items
#         self.index = 0

#     def next(self) -> T:
#         if self.index >= len(self.list):
#             return None
#         item = self.list[self.index]
#         self.index += 1
#         return item


class Parser:
    def __init__(self):
        self.graph_roots: List[Graph] = []
        self.graph_stack: List[Graph] = []

    def add_root_graph(self, g: Graph):
        self.graph_roots.append(g)
        self.graph_stack.clear()
        self.graph_stack.append(g)

    def push_sub_graph(self, g: Graph):
        if len(self.graph_stack) == 0:
            raise ValueError("No root graph to add sub graph")
        self.graph_stack[-1].add_sub_graph(g)
        self.graph_stack.append(g)

    def pop_sub_graph(self):
        if len(self.graph_stack) == 0:
            raise ValueError("No sub graph to pop")
        self.graph_stack.pop()

    def add_node(self, node: Union[Node, List[Node]]):
        if len(self.graph_stack) == 0:
            raise ValueError("No graph to add node")
        self.graph_stack[-1].add_node(node)

    def add_edge(self, edge: Union[Edge, List[Edge]]):
        if len(self.graph_stack) == 0:
            raise ValueError("No graph to add edge")
        self.graph_stack[-1].add_edge(edge)

    # ================================ parsing ================================ #

    def parse_node(self, tokens: List[Token], cur: int) -> Tuple[int, Node]:
        token = tokens[cur] if cur < len(tokens) else None
        if token is None:
            return cur, None
        if token.type != TokenType.TEXT:
            return cur, None

        node_id = token.content
        shape = NodeShape.RECT

        token: Token = tokens[cur + 1] if (cur + 1) < len(tokens) else None
        if (token is None) or (
            token is not None
            and (token.type == TokenType.LINE or token.type == TokenType.AND)
        ):
            return (cur, Node(id=node_id, label="", shape=shape))

        cur += 1

        if token.type == TokenType.L_PAREN:

            count = 1
            tmp_it = cur
            while True:
                tmp_it += 1
                token = tokens[tmp_it] if tmp_it < len(tokens) else None

                if token is None:
                    break
                if token.type == TokenType.L_PAREN:
                    count += 1
                else:
                    break

            if count == 1:
                shape = NodeShape.ROUND
            elif count == 2:
                shape = NodeShape.CIRCLE
            elif count == 3:
                shape = NodeShape.DOUBLECIRCLE
            else:
                raise ValueError(f"Invalid node shape for node {node_id}")

            cur += 1
            token = tokens[cur] if cur < len(tokens) else None

            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")
            if token.type != TokenType.TEXT:
                raise ValueError(f"Invalid node shape for node {node_id}")
            node_label = token.content

            for _ in range(count):
                cur += 1
                token = tokens[cur] if cur < len(tokens) else None

                if token is None or token.type != TokenType.R_PAREN:
                    raise ValueError(f"Invalid node shape for node {node_id}")
            return (cur, Node(id=node_id, label=node_label, shape=shape))

        if token.type == TokenType.L_BRACKET:
            # [ ], [<,  [/ /], [\ \], [/ \], [\ /]
            cur += 1
            token = tokens[cur] if cur < len(tokens) else None
            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")

            left_state = TokenType.L_BRACKET
            right_state = None

            if token.type == TokenType.SLASH or token.type == TokenType.BACKSLASH:
                left_state = token.type

                cur += 1
                token = tokens[cur] if cur < len(tokens) else None

            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")
            if token.type == TokenType.TEXT:
                node_label = token.content

                cur += 1
                token = tokens[cur] if cur < len(tokens) else None

            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")
            if token.type == TokenType.SLASH or token.type == TokenType.BACKSLASH:
                right_state = token.type
                cur += 1
                token = tokens[cur] if cur < len(tokens) else None
            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")

            if token.type == TokenType.R_BRACKET:
                if left_state == TokenType.L_BRACKET and right_state is None:
                    shape = NodeShape.RECT
                elif left_state == TokenType.SLASH and right_state == TokenType.SLASH:
                    shape = NodeShape.LEFT_RECT
                elif (
                    left_state == TokenType.BACKSLASH
                    and right_state == TokenType.BACKSLASH
                ):
                    shape = NodeShape.RIGHT_RECT
                elif (
                    left_state == TokenType.SLASH and right_state == TokenType.BACKSLASH
                ):
                    shape = NodeShape.TRAPEZOID_A
                elif (
                    left_state == TokenType.BACKSLASH and right_state == TokenType.SLASH
                ):
                    shape = NodeShape.TRAPEZOID_B
                else:
                    raise ValueError(f"Invalid node shape for node {node_id}")

                return (cur, Node(id=node_id, label=node_label, shape=shape))
            if token.type == TokenType.RIGHT:  # [>
                shape = NodeShape.AsymmetricShapeRight
                return (cur, Node(id=node_id, label=node_label, shape=shape))
            if token.type == TokenType.LEFT:  # [<
                shape = NodeShape.AsymmetricShapeLeft
                return (cur, Node(id=node_id, label=node_label, shape=shape))

        if token.type == TokenType.LEFT:  # <]
            shape = NodeShape.AsymmetricShapeLeft

            cur += 1
            token = tokens[cur] if cur < len(tokens) else None
            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")

            if token.type == TokenType.TEXT:
                node_label = token.content
                cur += 1
                token = tokens[cur] if cur < len(tokens) else None
            if token is None or token.type != TokenType.R_BRACKET:
                raise ValueError(f"Invalid node shape for node {node_id}")
            return Node(id=node_id, label=node_label, shape=shape)
        if token.type == TokenType.RIGHT:  # >]
            shape = NodeShape.AsymmetricShapeRight
            cur += 1
            token = tokens[cur] if cur < len(tokens) else None
            if token is None:
                raise ValueError(f"Invalid node shape for node {node_id}")
            if token.type == TokenType.TEXT:
                node_label = token.content

                cur += 1
                token = tokens[cur] if cur < len(tokens) else None
            if token is None or token.type != TokenType.R_BRACKET:
                raise ValueError(f"Invalid node shape for node {node_id}")
            return cur, Node(id=node_id, label=node_label, shape=shape)

        return (cur, None)

    def parse_node_list(self, tokens: List[Token], cur: int):
        nodes = []
        while True:
            (cur, node) = self.parse_node(tokens, cur)
            if node is None:
                break
            nodes.append(node)

            cur += 1
            token = tokens[cur] if cur < len(tokens) else None
            if token is not None and token.type == TokenType.AND:
                cur += 1
        return cur, nodes

    # -->|选项1| in Decision -->|选项1| Action1[动作1]
    def pares_edge(self, tokens: List[Token], cur: int) -> Tuple[int, Node]:
        token = tokens[cur] if cur < len(tokens) else None
        if token is None or token.type != TokenType.LINE:
            return cur, None

        line_style = token.content
        line_label_inline = ""
        line_label_hangout = ""

        cur += 1  # eat line
        token = tokens[cur] if cur < len(tokens) else None

        logging.debug(f"pares_edge process {token}")

        if token is not None and token.type == TokenType.TEXT:
            # check is node or inline label?
            tmp_content = token.content

            check_point = cur
            check_point += 1

            token = tokens[check_point] if check_point < len(tokens) else None
            if token is not None and token.type == TokenType.LINE:
                check_point += 1
                token = tokens[check_point] if check_point < len(tokens) else None
                line_label_inline = tmp_content

                cur = check_point
            else:
                # line end
                return cur, Line.from_style(line_style, line_label_inline, "")

        # -->|...|
        if token is not None and token.type == TokenType.LABEL:
            cur += 1
            token = tokens[cur] if cur < len(tokens) else None

            line_label_hangout = (
                token.content
                if token is not None and token.type == TokenType.TEXT
                else ""
            )

            cur += 1
            token = tokens[cur] if cur < len(tokens) else None
            if token is not None and token.type == TokenType.LABEL:
                pass
            else:
                raise ValueError(f"Invalid line label at index {cur}")

        return cur, Line.from_style(line_style, line_label_inline, line_label_hangout)

    def parse_one_src_line_content(self, tokens: List[Token]):

        cur, nodes = self.parse_node_list(tokens, 0)
        if len(nodes) == 0:
            return

        self.add_node(nodes)

        logging.debug(f"the cur state is {cur} : {tokens[cur]}")

        while True:

            src_list = nodes

            cur, line = self.pares_edge(tokens, cur)
            logging.debug(f"the cur token {cur}")
            if line is None:
                break

            cur, dst_nodes = self.parse_node_list(tokens, cur)
            if len(dst_nodes) == 0:
                logging.debug(f"\tdst nodes is {dst_nodes}")
                break

            logging.debug(f"src node:{src_list} , dst nodes:{dst_nodes}")

            self.add_node(dst_nodes)

            for src in src_list:
                for dst in dst_nodes:
                    edge = Edge(src=src, dst=dst, edge=line)
                    self.add_edge(edge)

            src_list = dst_nodes

    def parse(self, meriad: str) -> bool:

        lines = meriad.strip().split("\n")

        for line in lines:
            line = line.strip()
            if len(line) == 0 or line.startswith("%%"):
                continue

            l = Lexer()
            l.run(line)
            tokens = l.tokens

            if len(tokens) == 0:
                continue

            cur = 0
            token = tokens[cur]

            debugging = {"line": line, "tokens": tokens}
            logging.debug(f"Parsing line: {debugging}")

            if token.type == TokenType.GRAPH:
                root = Graph(id="root", parent=None)

                self.add_root_graph(root)

                cur += 1
                token = tokens[cur] if cur < len(tokens) else None

                if token is None:
                    root.dir = Direction.TD
                    break

                if (
                    token.type == TokenType.TEXT
                    and token.content in Direction.__members__
                ):
                    root.dir = Direction[token.content]
                else:
                    raise ValueError(f"Invalid graph direction: {token.content}")

                # drop the rest tokens if this line

                continue

            if token.type == TokenType.SUBGRAPH:
                cur += 1
                token = tokens[cur] if cur < len(tokens) else None
                subgraph_id = ""
                if token is not None and token.type == TokenType.TEXT:
                    subgraph_id = token.content

                logging.debug(
                    f"add sub graph {subgraph_id} to {self.graph_roots[-1].id}"
                )

                subgraph = Graph(id=subgraph_id, parent=self.graph_roots[-1])

                self.push_sub_graph(subgraph)

                # drop the rest tokens in this line
                continue

            if token.type == TokenType.END:
                self.pop_sub_graph()
                continue
            self.parse_one_src_line_content(tokens)


if __name__ == "__main__":
    test1 = """
    graph TB
        Start[开始] --> Process(处理)
        Process --> Decision{判断}
        
        Decision -->|选项1| Action1[动作1]
        Decision -->|选项2| Action2[动作2]
        
        Action1 -.->|虚线| Next[下一步]
        Action2 ==>|粗线| Next
        
        Next --- Final[结束]
        
        Sub1[子节点1] & Sub2[子节点2] --> Merge[合并]
        
        Merge --o Circular[圆形箭头]
        Circular --x Cross[交叉箭头]
        
        Bi1[双向1] <--> Bi2[双向2]
    """
    p = Parser()
    p.parse(test1)
    print(p.graph_roots)
