from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class Direction(Enum):
    TD = "TD"  # top to down
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


@dataclass
class Line:
    type: LineType
    src_arrow: bool  # <---
    dst_arrow: bool  # -->
    inline_label: bool  # means label is line --label--> or upper
    label: str = ""  # --label--> , -->|label|
    line_len: int = 1  # ---> vs ------>


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
    parent: "Graph" = None
    children: List["Graph"] = field(default_factory=list)

    dir = None
    nodes = []
    edges = []


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
            start = cur
            while cur < size and not text[cur].isspace() and text[cur] not in p2:
                cur += 1
            if cur > start:
                self.tokens.append(Token(text[start:cur], TokenType.TEXT))


class Parser:
    def __init__(self):
        self.graph_roots: List[Graph] = []

    def parse_node(self, tokens: List[Token], cur: int) -> Tuple[int, Node]:
        token =  tokens[cur] if cur < len(tokens) else None
        if token is None:
            return cur, None
        if token.type != TokenType.TEXT:
            return cur, None

        node_id = token.content
        shape = NodeShape.RECT

        cur += 1
    
        token: Token = tokens[cur] if cur < len(tokens) else None
         
        if token is None:
            return Node(id=node_id, label="", shape=shape)

        if token.type == TokenType.L_PAREN:

            count = 1
            tmp_it =  cur
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
            return Node(id=node_id, label=node_label, shape=shape)

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

                return Node(id=node_id, label=node_label, shape=shape)
            if token.type == TokenType.RIGHT:  # [>
                shape = NodeShape.AsymmetricShapeRight
                return Node(id=node_id, label=node_label, shape=shape)
            if token.type == TokenType.LEFT:  # [<
                shape = NodeShape.AsymmetricShapeLeft
                return Node(id=node_id, label=node_label, shape=shape)

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
            return Node(id=node_id, label=node_label, shape=shape)

    def parse_node_list(self, tokens: List[Token], cur:int):
        nodes = []
        while True:
            cur, node = self.parse_node(tokens, cur)
            if node is None:
                break
            nodes.append(node)

            cur +=1
            token = tokens[cur] if cur < len(tokens) else None
            
            if token is None or token.type != TokenType.AND:
                pass

    def parse_graph_content(self, it):
        while True:
            line = next(it, None)
            if line is None:
                break
            line = line.strip()
            if line.startswith("%%"):
                continue

            l = Lexer()
            l.run(line)
            tokens = l.tokens
            if len(tokens) == 0:
                continue
            token_it = iter(tokens)
            # parse nodes and edges

    def parse(meriad: str) -> bool:

        lines = meriad.strip().split("\n")

        graph_roots = []

        line_it = iter(lines)

        while True:
            line = next(line_it, None)
            if line is None:
                break
            line = line.strip()
            if line.startswith("%%"):
                continue

            l = Lexer()
            l.run(line)
            tokens = l.tokens

            if len(tokens) == 0:
                continue

            it = iter(tokens)

            if next(it).type == TokenType.GRAPH:
                root = Graph(id="root", parent=None)
                graph_roots.append(root)

                dir_token = next(it)
                if (
                    dir_token.type == TokenType.TEXT
                    and dir_token.content in Direction.__members__
                ):
                    root.dir = Direction[dir_token.content]
                else:
                    raise ValueError(f"Invalid graph direction: {dir_token.content}")

                # drop the rest tokens if this line

                continue

            if next(it).type == TokenType.SUBGRAPH:
                subgraph_token = next(it)
                if subgraph_token.type == TokenType.TEXT:
                    subgraph_id = subgraph_token.content
                    subgraph = Graph(id=subgraph_id, parent=graph_roots[-1])
                    graph_roots[-1].children.append(subgraph)
                else:
                    raise ValueError(f"Invalid subgraph id: {subgraph_token.content}")

                # drop the rest tokens in this line

                # parse graph content

                continue


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

parse(test1)

