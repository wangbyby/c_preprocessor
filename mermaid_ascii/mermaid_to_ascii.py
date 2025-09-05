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


# @dataclass
# class Line:
#     type: LineType
#     src_arrow: bool  # <---
#     dst_arrow: bool  # -->
#     inline_label: bool  # means label is line --label--> or upper
#     label: str = ""  # --label--> , -->|label|
#     line_len: int = 1  # ---> vs ------>


# @dataclass
# class Node:
#     id: str = ""
#     label: str = ""
#     shape: NodeShape = NodeShape.RECT


# @dataclass
# class Edge:
#     src: Node
#     dst: Node
#     edge: Line
#     label: str = ""


# @dataclass
# class Graph:

#     id: str = ""
#     parent: "Graph" = None
#     children: List["Graph"] = field(default_factory=list)

#     dir = None
#     nodes = []
#     edges = []


@dataclass
class Token:
    content: str


class Lexer:
    def __init__(self):
        self.position = 0
        self.tokens = []

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
            self.tokens.append(Token(text[start:cur]))
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

            if text[cur] in "[](){}":
                self.tokens.append(Token(text[cur]))
                cur += 1
                continue
            if text[cur] in "|&":
                self.tokens.append(Token(text[cur]))
                cur += 1
                continue
            # identifier or label
            start = cur
            while (
                cur < size
                and not text[cur].isspace()
                and text[cur] not in "-.=<>[](){}|&"
            ):
                cur += 1
            if cur > start:
                self.tokens.append(Token(text[start:cur]))


def parse(meriad: str) -> bool:

    lines = meriad.strip().split("\n")

    root = Graph(id="root", parent=None)

    cur = root

    for line in lines:
        line = line.strip()
        if not line or line.startswith("%%"):
            continue

        if line.startswith("graph"):
            if cur.parent is not None:
                raise ValueError("Only top-level graph can define direction")

            dir_match = re.match(r"graph\s+(TD|LR|RL|BT)", line)
            if dir_match:
                cur.dir = Direction(dir_match.group(1))

        if line.startswith("subgraph"):
            subgraph_match = re.match(r"subgraph\s+(\w+)", line)
            if subgraph_match:
                subgraph_id = subgraph_match.group(1)
                subgraph = Graph(id=subgraph_id, parent=cur)
                cur.children.append(subgraph)

                cur = subgraph
            else:
                raise ValueError(f"Invalid subgraph definition: {line}")
        if line == "end":
            if cur.parent is not None:
                cur = cur.parent
                continue
            else:
                raise ValueError(f"No matching subgraph for end in line {line}")

        # parse node def or edge def

        l = Lexer()
        l.run(line)
        tokens = l.tokens

        print(tokens)


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

