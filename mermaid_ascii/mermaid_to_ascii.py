from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Dict, List, Tuple, Union
import logging
from pydot import Edge, EdgeEndpoint, Graph, Node, Dot, Subgraph, AttributeDict
import pydot


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
        # 如果有文本，确保box宽度至少能容纳文本加上边框
        if text:
            min_width = len(text) + 2  # 文本长度 + 左右边框
            if width < min_width:
                width = min_width
        
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

        # 添加文本 - 不截断，完整显示
        if text:
            text_x = x + (width - len(text)) // 2
            text_y = y + height // 2
            for i, char in enumerate(text):
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
                self._add_single_node(last, n)
            return
        self._add_single_node(last, node)
    
    def _add_single_node(self, graph, node):
        """添加单个节点，避免重复"""
        node_name = node.get_name()
        
        # 检查是否已经存在同名节点
        existing_nodes = graph.get_nodes()
        for existing_node in existing_nodes:
            if existing_node.get_name() == node_name:
                # 如果新节点有标签而现有节点没有，更新标签
                new_label = node.get_attributes().get("label", "")
                existing_label = existing_node.get_attributes().get("label", "")
                if new_label and not existing_label:
                    existing_node.set("label", new_label)
                return  # 节点已存在，不重复添加
        
        # 节点不存在，添加新节点
        graph.add_node(node)

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
            return (cur, Node(node_id, label="", shape=shape.to_pydot_shape()))

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
            return (cur, Node(node_id, label=node_label, shape=shape.to_pydot_shape()))

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

                return (
                    cur,
                    Node(node_id, label=node_label, shape=shape.to_pydot_shape()),
                )
            if token.type == TokenType.RIGHT:  # [>
                shape = NodeShape.AsymmetricShapeRight
                return (
                    cur,
                    Node(node_id, label=node_label, shape=shape.to_pydot_shape()),
                )
            if token.type == TokenType.LEFT:  # [<
                shape = NodeShape.AsymmetricShapeLeft
                return (
                    cur,
                    Node(node_id, label=node_label, shape=shape.to_pydot_shape()),
                )

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
            return cur, Node(node_id, label=node_label, shape=shape.to_pydot_shape())
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
            return cur, Node(node_id, label=node_label, shape=shape.to_pydot_shape())

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
        pass

    def layout_calc(self, g: Graph) -> List[Dot]:
        """Calculate layout using pydot and return node positions"""

        # Generate layout
        try:
            l = ""
            output_format = "dot"
            if isinstance(g, Dot):
                l = g.create(prog="dot", format=output_format)

            if isinstance(l, bytes):
                try:
                    l = l.decode("utf-8")
                except Exception:
                    logging.info(f"decode {output_format} with utf-8 failed, try gbk")
                    try:
                        
                        l = l.decode("gbk")  

                        logging.info("using gbk ")
                        
                    except Exception:
                        logging.error(f"decode {output_format} with gbk failed")
            logging.info(f"pydot layout output with format {output_format} is: {l}")

            if l is None or len(l) == 0:
                return []

            out_graph = pydot.graph_from_dot_data(l)
            if out_graph is None:
                return []
            return out_graph

        except Exception as e:
            logging.error(f"Error generating layout: {e}")
            # Fallback to simple grid layout
            return []


class DotToASCII:
    def __init__(self, scale=1.0, max_width=200, max_height=60, 
                 points_per_char_width=8, points_per_char_height=12):
        self.scale = scale
        self.max_width = max_width
        self.max_height = max_height
        self.points_per_char_width = points_per_char_width
        self.points_per_char_height = points_per_char_height
        self.graph: Dot | None = None
        self.bb: tuple | None = None
        self.grid = None
        self.node_coords = {}
        self.node_labels = {}
        self.ascii_width = 0
        self.ascii_height = 0

    def load_dot(self, dot: Dot):
        self.graph = dot
        # 解析 bounding box
        parsing_bb = self.graph.get_graph_defaults()
        bb_str = ""

        if isinstance(parsing_bb, list):
            for item in parsing_bb:
                if isinstance(item, dict) and "bb" in item:
                    bb_str = item["bb"]
                    break
        if bb_str:
            self.bb = tuple(map(float, bb_str.strip('"').split(",")))
        else:
            self.bb = (0, 0, 100, 100)
        
        # 计算ASCII画布尺寸
        xmin, ymin, xmax, ymax = self.bb
        canvas_width_points = xmax - xmin
        canvas_height_points = ymax - ymin
        
        self.ascii_width = min(int(canvas_width_points / self.points_per_char_width), self.max_width)
        self.ascii_height = min(int(canvas_height_points / self.points_per_char_height), self.max_height)
        
        logging.info(f"Graph bounding box: {self.bb}")
        logging.info(f"ASCII canvas size: {self.ascii_width} x {self.ascii_height}")

    def dot_to_ascii_position(self, dot_x: float, dot_y: float) -> Tuple[int, int]:
        """将DOT坐标转换为ASCII字符位置"""
        if self.bb is None:
            return 0, 0
            
        xmin, ymin, xmax, ymax = self.bb
        
        # 归一化到0-1范围
        norm_x = (dot_x - xmin) / (xmax - xmin) if (xmax - xmin) > 0 else 0
        norm_y = (dot_y - ymin) / (ymax - ymin) if (ymax - ymin) > 0 else 0
        
        # 转换为ASCII坐标
        ascii_x = int(norm_x * (self.ascii_width - 1))
        ascii_y = int((1 - norm_y) * (self.ascii_height - 1))  # 翻转Y轴
        
        # 确保在画布范围内
        ascii_x = max(0, min(ascii_x, self.ascii_width - 1))
        ascii_y = max(0, min(ascii_y, self.ascii_height - 1))
        
        return ascii_x, ascii_y

    def dot_size_to_ascii_size(self, width_inches: float, height_inches: float) -> Tuple[int, int]:
        """将DOT尺寸（英寸）转换为ASCII字符数"""
        if self.bb is None:
            return 3, 1
            
        xmin, ymin, xmax, ymax = self.bb
        
        # 将英寸转换为点
        width_points = width_inches * 72
        height_points = height_inches * 72
        
        # 计算相对于画布的比例
        canvas_width = xmax - xmin
        canvas_height = ymax - ymin
        
        # 转换为ASCII字符数
        char_width = max(1, int((width_points / canvas_width) * self.ascii_width))
        char_height = max(1, int((height_points / canvas_height) * self.ascii_height))
        
        return char_width, char_height

    def parse_node_position(self, node) -> Tuple[float, float, float, float]:
        """解析节点的位置和尺寸"""
        # 获取位置
        pos = node.get_attributes().get("pos")
        if pos is None:
            return 0, 0, 1, 0.5
            
        pos = pos.strip().replace('"', '')
        try:
            x, y = map(float, pos.split(","))
        except:
            x, y = 0, 0
        
        # 获取尺寸（英寸）
        width_str = node.get_attributes().get("width", "1.0")
        height_str = node.get_attributes().get("height", "0.5")
        
        try:
            width = float(width_str)
            height = float(height_str)
        except:
            width, height = 1.0, 0.5
        
        return x, y, width, height

    def get_node_shape_type(self, node:Node) -> str:
        """获取节点形状类型"""
        shape = node.get_attributes().get("shape", "box")
        return shape

    def render_node(self, grid: ASCIIGraphCanvas, node: Node):
        """渲染单个节点"""
        dot_x, dot_y, width_inches, height_inches = self.parse_node_position(node)
        ascii_x, ascii_y = self.dot_to_ascii_position(dot_x, dot_y)
        char_width, char_height = self.dot_size_to_ascii_size(width_inches, height_inches)
        
        # 获取标签
        label = node.get_attributes().get("label", node.get_name())
        
        # 获取形状
        shape = self.get_node_shape_type(node)
        
        # 根据label长度调整box宽度，确保能完整显示文本
        if label and shape not in ["circle", "doublecircle"]:
            min_width = len(label) + 2  # 文本长度 + 左右边框
            char_width = max(char_width, min_width)
        
        # 调整位置使节点居中
        start_x = max(0, ascii_x - char_width // 2)
        start_y = max(0, ascii_y - char_height // 2)
        
        # 确保不超出画布右边界，如果超出则向左调整
        if start_x + char_width >= self.ascii_width:
            start_x = max(0, self.ascii_width - char_width)
        if start_y + char_height >= self.ascii_height:
            start_y = max(0, self.ascii_height - char_height)
            
        logging.debug(f"Rendering node {node.get_name()}: pos=({dot_x},{dot_y}) -> ascii=({start_x},{start_y}) size={char_width}x{char_height} label='{label}'")
        
        # 根据形状渲染
        if shape in ["circle", "doublecircle"]:
            radius = min(char_width, char_height) // 2
            center_x = start_x + char_width // 2
            center_y = start_y + char_height // 2
            grid.draw_circle(center_x, center_y, radius, label)
        else:
            # 默认使用矩形
            grid.draw_box(start_x, start_y, char_width, char_height, label)

    def render_edges(self, grid: ASCIIGraphCanvas):
        """渲染边"""
        for edge in self.graph.get_edge_list():
            src_name = edge.get_source()
            dst_name = edge.get_destination()
            
            # 找到源节点和目标节点的位置
            src_node = None
            dst_node = None
            
            for node in self.graph.get_node_list():
                if node.get_name() == src_name:
                    src_node = node
                elif node.get_name() == dst_name:
                    dst_node = node
            
            if src_node and dst_node:
                # 获取节点位置
                src_x, src_y, _, _ = self.parse_node_position(src_node)
                dst_x, dst_y, _, _ = self.parse_node_position(dst_node)
                
                # 转换为ASCII坐标
                ascii_src_x, ascii_src_y = self.dot_to_ascii_position(src_x, src_y)
                ascii_dst_x, ascii_dst_y = self.dot_to_ascii_position(dst_x, dst_y)
                
                # 绘制箭头
                grid.draw_arrow(ascii_src_x, ascii_src_y, ascii_dst_x, ascii_dst_y)

    def render_ascii(self):
        """渲染完整的ASCII图形"""
        if self.graph is None or self.bb is None:
            raise ValueError("Graph or bounding box not set")

        # 创建ASCII画布
        grid = ASCIIGraphCanvas(self.ascii_width, self.ascii_height)
        
        # 渲染所有节点
        for node in self.graph.get_node_list():
            self.render_node(grid, node)
        
        # 渲染所有边
        # self.render_edges(grid)

        return grid.to_string()

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
        
        Sub1[子节点10000000000000000000000000000000000] & Sub2[子节点2] --> Merge[合并]
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

        logging.info(f"Graph: {g.to_string()}")

        layout = LayOut()
        dot_graph = layout.layout_calc(g)

        for dg in dot_graph:
            logging.info(f"Dot graph after layout: {dg. get_graph_defaults ()}")
            d = DotToASCII()
            d.load_dot(dg)
            ascii_art = d.render_ascii()
            

            with open("a.tmp",'w', encoding="utf-8") as f:
                f.write(ascii_art)

    else:
        print("No graph found in the input")
