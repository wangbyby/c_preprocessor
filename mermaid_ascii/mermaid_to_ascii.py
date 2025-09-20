from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Union
import logging
from pydot import Edge, EdgeEndpoint, Graph, Node, Dot, Subgraph, AttributeDict


class ASCIIGraphCanvas:
    """ASCII图形画布"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.canvas = [[" " for _ in range(width)] for _ in range(height)]

    def set_char(self, x: int, y: int, char: str):
        """在指定位置设置字符"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = char

    def draw_box(self, x: int, y: int, width: int, height: int, text: str = ""):
        """绘制矩形框"""
        # 绘制边框
        for i in range(width):
            self.set_char(x + i, y, "-")  # 上边
            self.set_char(x + i, y + height - 1, "-")  # 下边

        for i in range(height):
            self.set_char(x, y + i, "|")  # 左边
            self.set_char(x + width - 1, y + i, "|")  # 右边

        # 绘制四个角
        self.set_char(x, y, "+")
        self.set_char(x + width - 1, y, "+")
        self.set_char(x, y + height - 1, "+")
        self.set_char(x + width - 1, y + height - 1, "+")

        # 添加文本
        if text:
            text_x = x + (width - len(text)) // 2
            text_y = y + height // 2
            for i, char in enumerate(text):
                if text_x + i < x + width - 1:
                    self.set_char(text_x + i, text_y, char)

    def draw_circle(self, x: int, y: int, radius: int, text: str = ""):
        """绘制圆形"""
        for angle in range(0, 360, 10):
            import math

            rad = math.radians(angle)
            px = int(x + radius * math.cos(rad))
            py = int(y + radius * math.sin(rad))
            self.set_char(px, py, "o")

        # 添加文本
        if text:
            text_x = x - len(text) // 2
            text_y = y
            for i, char in enumerate(text):
                self.set_char(text_x + i, text_y, char)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int):
        """绘制直线"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            # 选择合适的字符
            if dx > dy:
                char = "-"
            elif dy > dx:
                char = "|"
            else:
                char = "*"

            self.set_char(x, y, char)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int):
        """绘制箭头"""
        self.draw_line(x1, y1, x2, y2)

        # 添加箭头头部
        if x2 > x1:
            self.set_char(x2, y2, ">")
        elif x2 < x1:
            self.set_char(x2, y2, "<")
        elif y2 > y1:
            self.set_char(x2, y2, "v")
        else:
            self.set_char(x2, y2, "^")

    def to_string(self) -> str:
        """转换为字符串"""
        return "\n".join("".join(row) for row in self.canvas)


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

    def to_attr_dict(self) -> AttributeDict:
        d = {}
        d["label"] = self.inline_label
        d["label2"] = self.hangoff_label
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
            hangoff_label=l2,
            line_len=line_len,
        )


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

        punctor_num = 0

        while cur < size:
            if text[cur].isspace():
                cur += 1
                continue
            # process --o --x x-- o-- <-- --> <-->
            new_cur = self.parse_line(text, cur)

            if new_cur != cur:
                punctor_num = 0
            cur = new_cur

            punctor = "[](){}|&<>/\\"
            p2 = punctor + "-.="

            if text[cur] in punctor:
                self.tokens.append(Token(text[cur], TokenType(text[cur])))
                cur += 1
                punctor_num = 1
                continue

            # identifier or label
            begin = cur

            if punctor_num > 0:
                punctor_num = 0
                while cur < size and text[cur] not in punctor:
                    cur += 1
            else:
                while (
                    (cur < size) and (not text[cur].isspace()) and (text[cur] not in p2)
                ):
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


class Parser:
    def __init__(self):
        self.graph_roots: List[Graph] = []
        self.graph_stack: List[Graph] = []

    def add_root_graph(self, g: Graph):
        self.graph_roots.append(g)
        self.graph_stack.clear()
        self.graph_stack.append(g)

    def push_sub_graph(self, g: Subgraph):
        if len(self.graph_stack) == 0:
            raise ValueError("No root graph to add sub graph")
        self.graph_stack[-1].add_subgraph(g)
        self.graph_stack.append(g)

    def pop_sub_graph(self):
        if len(self.graph_stack) == 0:
            raise ValueError("No sub graph to pop")
        self.graph_stack.pop()

    def add_node(self, node: Union[Node, List[Node]]):
        if len(self.graph_stack) == 0:
            raise ValueError("No graph to add node")
        last = self.graph_stack[-1]
        if isinstance(node, list):
            for n in node:
                last.add_node(n)
            return
        last.add_node(node)

    def add_edge(self, edge: Union[Edge, List[Edge]]):
        if len(self.graph_stack) == 0:
            raise ValueError("No graph to add edge")
        if isinstance(edge, list):
            for e in edge:
                self.graph_stack[-1].add_edge(e)
            return

        if isinstance(edge, Edge):
            self.graph_stack[-1].add_edge(edge)
            return
        raise TypeError(f"expect Edge|list[Edge] found {type(edge)}")

    # ================================ parsing ================================ #

    def parse_node(self, tokens: List[Token], cur: int) -> Tuple[int, Node | None]:
        token: Token | None = tokens[cur] if cur < len(tokens) else None
        if token is None:
            return cur, None
        if token.type != TokenType.TEXT:
            return cur, None

        node_id = token.content
        shape = NodeShape.RECT

        token = tokens[cur + 1] if (cur + 1) < len(tokens) else None
        if (token is None) or (
            token is not None
            and (token.type == TokenType.LINE or token.type == TokenType.AND)
        ):
            return (cur, Node(node_id, label="", shape=shape))

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
            return (cur, Node(node_id, label=node_label, shape=shape))

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

                return (cur, Node(node_id, label=node_label, shape=shape))
            if token.type == TokenType.RIGHT:  # [>
                shape = NodeShape.AsymmetricShapeRight
                return (cur, Node(node_id, label=node_label, shape=shape))
            if token.type == TokenType.LEFT:  # [<
                shape = NodeShape.AsymmetricShapeLeft
                return (cur, Node(node_id, label=node_label, shape=shape))

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
            return cur, Node(node_id, label=node_label, shape=shape)
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
            return cur, Node(node_id, label=node_label, shape=shape)

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
    def pares_edge(self, tokens: List[Token], cur: int) -> Tuple[int, Line | None]:
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
                    self.add_edge(Edge(src, dst))

            src_list = dst_nodes

    def parse(self, mermaid: str):

        lines = mermaid.strip().split("\n")

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
                root = Dot(graph_type="digraph")

                self.add_root_graph(root)

                cur += 1
                token = tokens[cur] if cur < len(tokens) else None

                if token is None:
                    break

                if (
                    token.type == TokenType.TEXT
                    and token.content in Direction.__members__
                ):
                    pass
                    # root.dir = Direction[token.content]
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
                    f"add sub graph {subgraph_id} to {self.graph_roots[-1].get_name()  }"
                )

                subgraph = Subgraph(subgraph_id)

                self.push_sub_graph(subgraph)

                # drop the rest tokens in this line
                continue

            if token.type == TokenType.END:
                self.pop_sub_graph()
                continue
            self.parse_one_src_line_content(tokens)


@dataclass
class NodePosition:
    x: float
    y: float
    width: float
    height: float
    label: str
    shape: str


@dataclass
class EdgePosition:
    src_id: str
    dst_id: str
    points: List[Tuple[float, float]]
    label: str = ""


class LayOut:
    def __init__(self):
        self.scale_factor = 10  # Scale factor to convert from dot coordinates to ASCII
        self.node_positions: Dict[str, NodePosition] = {}
        self.edge_positions: List[EdgePosition] = []
        self.canvas_width = 0
        self.canvas_height = 0

    def parse_dot_output(self, layout_lines: List[str]):
        """Parse the plain text output from pydot/graphviz"""
        self.node_positions.clear()
        self.edge_positions.clear()

        for line in layout_lines:
            parts = line.strip().split()
            if not parts:
                continue

            if parts[0] == "graph":
                # graph scale width height
                if len(parts) >= 4:
                    self.canvas_width = int(float(parts[2]) * self.scale_factor)
                    self.canvas_height = int(float(parts[3]) * self.scale_factor)

            elif parts[0] == "node":
                # node name x y width height label style shape color fillcolor
                if len(parts) >= 6:
                    node_id = parts[1]
                    x = float(parts[2]) * self.scale_factor
                    y = float(parts[3]) * self.scale_factor
                    width = float(parts[4]) * self.scale_factor
                    height = float(parts[5]) * self.scale_factor
                    label = parts[6] if len(parts) > 6 else node_id
                    shape = parts[8] if len(parts) > 8 else "box"

                    self.node_positions[node_id] = NodePosition(
                        x=x, y=y, width=width, height=height, label=label, shape=shape
                    )

            elif parts[0] == "edge":
                # edge tail head n x1 y1 .. xn yn [label xl yl] style color
                if len(parts) >= 4:
                    src_id = parts[1]
                    dst_id = parts[2]
                    n_points = int(parts[3])

                    points = []
                    for i in range(n_points):
                        if 4 + i * 2 + 1 < len(parts):
                            x = float(parts[4 + i * 2]) * self.scale_factor
                            y = float(parts[4 + i * 2 + 1]) * self.scale_factor
                            points.append((x, y))

                    self.edge_positions.append(
                        EdgePosition(src_id=src_id, dst_id=dst_id, points=points)
                    )

    def layout_calc(self, g: Graph) -> Dict[EdgeEndpoint, Tuple[int, int]]:
        """Calculate layout using pydot and return node positions"""

        # Generate layout
        try:
            l = ""
            if isinstance(g, Dot):
                l = g.create()

            print(l)

            # Convert to simple position dict for compatibility
            positions = {}
            for node_id, pos in self.node_positions.items():
                positions[node_id] = (int(pos.x), int(pos.y))

            return positions

        except Exception as e:
            logging.error(f"Error generating layout: {e}")
            # Fallback to simple grid layout
            return {}

    def _fallback_layout(self, nodes: List[Node]) -> Dict[str, Tuple[int, int]]:
        """Fallback grid layout if pydot fails"""
        positions = {}
        cols = min(len(nodes), 4)
        for i, node in enumerate(nodes):
            col = i % cols
            row = i // cols
            x = 10 + col * 20
            y = 5 + row * 10
            positions[node.get_name()] = (x, y)
        return positions

    def convert_to_ascii(self, graph: Graph) -> str:
        """Convert graph to ASCII using pydot layout"""
        if not graph.get_nodes():
            return ""

        # Get layout positions
        positions = self.layout_calc(graph)

        # Calculate canvas size
        if self.canvas_width == 0 or self.canvas_height == 0:
            max_x = max(pos[0] for pos in positions.values()) + 20
            max_y = max(pos[1] for pos in positions.values()) + 10
        else:
            max_x = max(self.canvas_width, 80)
            max_y = max(self.canvas_height, 40)

        canvas = ASCIIGraphCanvas(max_x, max_y)

        # Draw edges first (so they appear behind nodes)
        self._draw_edges(canvas, graph, positions)

        # Draw nodes
        self._draw_nodes(canvas, graph, positions)

        return canvas.to_string()

    def _draw_edges(
        self,
        canvas: ASCIIGraphCanvas,
        graph: Graph,
        positions: Dict[EdgeEndpoint, Tuple[int, int]],
    ):
        """Draw edges using layout information"""
        for edge in graph.get_edges():
            src_id = edge.get_source()
            dst_id = edge.get_destination()

            if src_id in positions and dst_id in positions:
                src_x, src_y = positions[src_id]
                dst_x, dst_y = positions[dst_id]

                # Use pydot edge positions if available
                edge_pos = next(
                    (
                        ep
                        for ep in self.edge_positions
                        if ep.src_id == src_id and ep.dst_id == dst_id
                    ),
                    None,
                )

                if edge_pos and len(edge_pos.points) >= 2:
                    # Draw polyline using pydot points
                    points = edge_pos.points
                    for i in range(len(points) - 1):
                        x1, y1 = int(points[i][0]), int(points[i][1])
                        x2, y2 = int(points[i + 1][0]), int(points[i + 1][1])
                        self._draw_line_segment(
                            canvas,
                            x1,
                            y1,
                            x2,
                            y2,
                            edge.get_attributes().get("style", LineType.BOLD),
                        )

                    # Draw arrow at the end
                    if len(points) >= 2:
                        x1, y1 = int(points[-2][0]), int(points[-2][1])
                        x2, y2 = int(points[-1][0]), int(points[-1][1])
                        self._draw_arrow_head(canvas, x1, y1, x2, y2)
                else:
                    # Fallback to direct line
                    self._draw_line_segment(
                        canvas,
                        src_x + 4,
                        src_y + 1,
                        dst_x + 4,
                        dst_y + 1,
                        edge.get_attributes().get("style", LineType.BOLD),
                    )
                    self._draw_arrow_head(
                        canvas, src_x + 4, src_y + 1, dst_x + 4, dst_y + 1
                    )

    def _draw_line_segment(
        self, canvas: ASCIIGraphCanvas, x1: int, y1: int, x2: int, y2: int, line: Line
    ):
        """Draw a line segment with appropriate style"""
        if line.type == LineType.DASHED:
            self._draw_dashed_line(canvas, x1, y1, x2, y2)
        elif line.type == LineType.BOLD:
            self._draw_bold_line(canvas, x1, y1, x2, y2)
        else:
            canvas.draw_line(x1, y1, x2, y2)

    def _draw_dashed_line(
        self, canvas: ASCIIGraphCanvas, x1: int, y1: int, x2: int, y2: int
    ):
        """Draw a dashed line"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        step = 0
        while True:
            if step % 3 != 2:  # Draw every 2 out of 3 steps
                if dx > dy:
                    char = "-"
                elif dy > dx:
                    char = "|"
                else:
                    char = "."
                canvas.set_char(x, y, char)

            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            step += 1

    def _draw_bold_line(
        self, canvas: ASCIIGraphCanvas, x1: int, y1: int, x2: int, y2: int
    ):
        """Draw a bold line using double characters"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            if dx > dy:
                char = "="
            elif dy > dx:
                char = "‖"  # Double vertical line
            else:
                char = "#"
            canvas.set_char(x, y, char)

            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def _draw_arrow_head(
        self, canvas: ASCIIGraphCanvas, x1: int, y1: int, x2: int, y2: int
    ):
        """Draw arrow head at the destination"""
        if x2 > x1:
            canvas.set_char(x2, y2, ">")
        elif x2 < x1:
            canvas.set_char(x2, y2, "<")
        elif y2 > y1:
            canvas.set_char(x2, y2, "v")
        else:
            canvas.set_char(x2, y2, "^")

    def _draw_nodes(
        self,
        canvas: ASCIIGraphCanvas,
        graph: Graph,
        positions: Dict[EdgeEndpoint, Tuple[int, int]],
    ):
        """Draw nodes using their shapes"""
        for node in graph.get_nodes():
            if node.get_name() in positions:
                x, y = positions[node.get_name()]
                label = node.get_attributes().get("label", "")
                # Get size from pydot if available
                node_pos = self.node_positions.get(node.get_name())
                if node_pos:
                    width = max(8, int(node_pos.width))
                    height = max(3, int(node_pos.height))
                else:
                    width = max(8, len(label) + 4)
                    height = 3

                self._draw_node_shape(
                    canvas,
                    x,
                    y,
                    width,
                    height,
                    label,
                    node.get_attributes().get("shape", NodeShape.RECT),
                )

    def _draw_node_shape(
        self,
        canvas: ASCIIGraphCanvas,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        shape: NodeShape,
    ):
        """Draw a node with the specified shape"""
        if shape == NodeShape.RECT:
            canvas.draw_box(x, y, width, height, label)
        elif shape == NodeShape.ROUND:
            self._draw_rounded_box(canvas, x, y, width, height, label)
        elif shape in [NodeShape.CIRCLE, NodeShape.DOUBLECIRCLE]:
            radius = min(width, height) // 2
            canvas.draw_circle(x + width // 2, y + height // 2, radius, label)
            if shape == NodeShape.DOUBLECIRCLE:
                canvas.draw_circle(x + width // 2, y + height // 2, radius - 1, "")
        elif shape == NodeShape.DIAMOND:
            self._draw_diamond(canvas, x, y, width, height, label)
        else:
            # Default to rectangle for unsupported shapes
            canvas.draw_box(x, y, width, height, label)

    def _draw_rounded_box(
        self,
        canvas: ASCIIGraphCanvas,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
    ):
        """Draw a rounded rectangle"""
        # Draw horizontal lines
        for i in range(1, width - 1):
            canvas.set_char(x + i, y, "-")
            canvas.set_char(x + i, y + height - 1, "-")

        # Draw vertical lines
        for i in range(1, height - 1):
            canvas.set_char(x, y + i, "|")
            canvas.set_char(x + width - 1, y + i, "|")

        # Draw rounded corners
        canvas.set_char(x, y, ".")
        canvas.set_char(x + width - 1, y, ".")
        canvas.set_char(x, y + height - 1, "'")
        canvas.set_char(x + width - 1, y + height - 1, "'")

        # Add label
        if label:
            text_x = x + (width - len(label)) // 2
            text_y = y + height // 2
            for i, char in enumerate(label):
                if text_x + i < x + width - 1:
                    canvas.set_char(text_x + i, text_y, char)

    def _draw_diamond(
        self,
        canvas: ASCIIGraphCanvas,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
    ):
        """Draw a diamond shape"""
        mid_x = x + width // 2
        mid_y = y + height // 2

        # Draw diamond outline
        for i in range(height // 2 + 1):
            left_x = mid_x - i
            right_x = mid_x + i
            canvas.set_char(left_x, y + i, "/")
            canvas.set_char(right_x, y + i, "\\")
            canvas.set_char(left_x, y + height - 1 - i, "\\")
            canvas.set_char(right_x, y + height - 1 - i, "/")

        # Add label
        if label:
            text_x = x + (width - len(label)) // 2
            text_y = y + height // 2
            for i, char in enumerate(label):
                canvas.set_char(text_x + i, text_y, char)


# class GraphToASCII:
#     def __init__(self):
#         self.canvas_width = 80
#         self.canvas_height = 40
#         self.node_width = 8
#         self.node_height = 3
#         self.node_spacing_x = 15
#         self.node_spacing_y = 8

#     def layout_nodes(self, nodes: List[Node]) -> Dict[str, Tuple[int, int]]:
#         positions = {}
#         node_names = [node.id for node in nodes]

#         # 简单的网格布局
#         cols = min(len(node_names), 4)  # 最多4列
#         rows = (len(node_names) + cols - 1) // cols
#         for i, node_name in enumerate(node_names):
#             col = i % cols
#             row = i // cols

#             x = 5 + col * self.node_spacing_x
#             y = 3 + row * self.node_spacing_y
#             positions[node_name] = (x, y)
#         return positions

#     def convert_to_ascii(self, graph: Graph) -> str:
#         nodes = graph.nodes
#         edges = graph.edges
#         if len(nodes) == 0:
#             return ""

#         positions = self.layout_nodes(nodes)

#         max_x = max(pos[0] for pos in positions.values()) + self.node_width + 5
#         max_y = max(pos[1] for pos in positions.values()) + self.node_height + 3

#         canvas = ASCIIGraphCanvas(max_x, max_y)

#         for e in edges:
#             src = e.src.id
#             dst = e.dst.id
#             if src in positions and dst in positions:
#                 src_x, src_y = positions[src]
#                 dst_x, dst_y = positions[dst]

#                 # 计算连接点（节点中心）
#                 src_center_x = src_x + self.node_width // 2
#                 src_center_y = src_y + self.node_height // 2
#                 dst_center_x = dst_x + self.node_width // 2
#                 dst_center_y = dst_y + self.node_height // 2

#                 canvas.draw_arrow(
#                     src_center_x, src_center_y, dst_center_x, dst_center_y
#                 )
#         for node in nodes:
#             node_name = node.id
#             if node_name in positions:
#                 x, y = positions[node_name]
#                 label = ""
#                 if node.label == "":
#                     label = node.id
#                 else:
#                     label = node.label
#                 shape = node.shape

#                 if shape == NodeShape.RECT:
#                     canvas.draw_box(x, y, self.node_width, self.node_height, label)
#                 else:
#                     # FIXME more shapes
#                     canvas.draw_circle(
#                         x + self.node_width // 2,
#                         y + self.node_height // 2,
#                         self.node_width // 2,
#                         label,
#                     )

#         return canvas.to_string()


if __name__ == "__main__":
    # Enable logging for debugging
    logging.basicConfig(level=logging.INFO)

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
    """

    print("Parsing Mermaid diagram...")
    p = Parser()
    p.parse(test1)

    if p.graph_roots:
        g = p.graph_roots[0]
        print(
            f"Found {len(g.get_node_list())} nodes and {len(g.get_edge_list())} edges"
        )

        print("\nGenerating ASCII diagram using pydot layout...")
        layout = LayOut()
        ascii_result = layout.convert_to_ascii(g)

        print("\nASCII Diagram:")
        print("=" * 60)
        print(ascii_result)
        print("=" * 60)
    else:
        print("No graph found in the input")
