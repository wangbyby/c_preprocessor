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
    def __init__(self, scale=1.0, max_width=200, max_height=60, label_max=20):
        self.scale = scale
        self.max_width = max_width
        self.max_height = max_height
        self.label_max = label_max
        self.graph: Dot | None = None
        self.bb: tuple | None = None
        self.grid = None
        self.node_coords = {}
        self.node_labels = {}

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
        
        logging.info(f"Graph bounding box: {self.bb}")



    def render_ascii(self):
        if self.graph is None or self.bb is None:
            raise ValueError("Graph or bounding box not set")


        xmin, ymin, xmax, ymax = self.bb
        width = int(xmax - xmin)  
        height = int(ymax - ymin)

        grid = ASCIIGraphCanvas(width, height)
        for node in self.graph.get_node_list():
            pos = node.get("pos")
            if pos is None:
                continue
            pos =  pos.strip()
            pos = pos.replace('"','')
            x,y = pos.split(",")
            x = int(x)
            y = int(y)

            w = float(node.get("width")) * 10
            h = float(node.get("height")) * 10

            label :str = node.get_attributes().get("label", "")
            

            grid.draw_box(x,y, int(w), int(h), label  )


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
