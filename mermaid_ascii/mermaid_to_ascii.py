from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Dict, List, Tuple, Union
import logging
from pydot import Edge, EdgeEndpoint, Graph, Node, Dot, Subgraph, AttributeDict
import pydot

from .parsing import Token


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

        logging.info(f" draw from [{x}, {x+width-1}]")

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
    def __init__(
        self,
        scale=1.0,
        max_width=200,
        max_height=60,
        points_per_char_width=8,
        points_per_char_height=12,
    ):
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

        self.ascii_width = min(
            int(canvas_width_points / self.points_per_char_width), self.max_width
        )
        self.ascii_height = min(
            int(canvas_height_points / self.points_per_char_height), self.max_height
        )

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
        logging.info(f"dot ({dot_x}, {dot_y}) -> ({ascii_x},{ascii_y})")
        return ascii_x, ascii_y

    def dot_size_to_ascii_size(
        self, width_inches: float, height_inches: float
    ) -> Tuple[int, int]:
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

        pos = pos.strip().replace('"', "")
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

    def get_node_shape_type(self, node: Node) -> str:
        """获取节点形状类型"""
        shape = node.get_attributes().get("shape", "box")
        return shape

    def render_all_nodes(self, grid: ASCIIGraphCanvas):
        """渲染所有节点，包含碰撞检测"""
        import sys
        import os

        sys.path.append(os.path.dirname(__file__))
        from collision_resolver import CollisionResolver, Rectangle

        if not self.graph:
            return

        # 收集所有节点的矩形信息
        rectangles = []
        node_info = {}  # 存储节点的详细信息

        for node in self.graph.get_nodes():
            if node.get_name().strip('"') in ["node", "edge", "graph"]:
                continue

            dot_x, dot_y, width_inches, height_inches = self.parse_node_position(node)
            ascii_x, ascii_y = self.dot_to_ascii_position(dot_x, dot_y)
            char_width, char_height = self.dot_size_to_ascii_size(
                width_inches, height_inches
            )

            # 获取标签和形状
            label = node.get_attributes().get("label", node.get_name())
            shape = self.get_node_shape_type(node)

            # 根据label长度调整box宽度
            if label and shape not in ["circle", "doublecircle"]:
                min_width = len(label) + 2
                char_width = max(char_width, min_width)

            # 计算初始位置（居中）
            start_x = max(0, ascii_x - char_width // 2)
            start_y = max(0, ascii_y - char_height // 2)

            # 创建矩形
            rect = Rectangle(start_x, start_y, char_width, char_height, node.get_name())
            rectangles.append(rect)

            # 存储节点信息
            node_info[node.get_name()] = {
                "node": node,
                "label": label,
                "shape": shape,
                "char_width": char_width,
                "char_height": char_height,
            }

        # 解决碰撞
        resolver = CollisionResolver(grid.width, grid.height, min_spacing=2)
        resolved_rectangles = resolver.resolve_collisions(rectangles)

        # 渲染解决碰撞后的节点
        for rect in resolved_rectangles:
            info = node_info[rect.node_id]
            node = info["node"]
            label = info["label"]
            shape = info["shape"]

            logging.debug(
                f"渲染节点 {rect.node_id}: 位置=({rect.x},{rect.y}) 尺寸={rect.width}x{rect.height} 标签='{label}'"
            )

            # 根据形状渲染
            if shape in ["circle", "doublecircle"]:
                radius = min(rect.width, rect.height) // 2
                center_x = rect.x + rect.width // 2
                center_y = rect.y + rect.height // 2
                grid.draw_circle(center_x, center_y, radius, label)
            else:
                # 默认使用矩形
                grid.draw_box(rect.x, rect.y, rect.width, rect.height, label)

    def render_node(self, grid: ASCIIGraphCanvas, node: Node):
        """渲染单个节点（保留原方法以兼容性）"""
        dot_x, dot_y, width_inches, height_inches = self.parse_node_position(node)
        ascii_x, ascii_y = self.dot_to_ascii_position(dot_x, dot_y)
        char_width, char_height = self.dot_size_to_ascii_size(
            width_inches, height_inches
        )

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

        logging.info(
            f"Rendering node {node.get_name()}: pos=({dot_x},{dot_y}) -> ascii=({start_x},{start_y}) size={char_width}x{char_height} label='{label}'"
        )

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
            logging.info(grid.to_string())

        # 渲染所有边
        # self.render_edges(grid)

        return grid.to_string()


if __name__ == "__main__":
    # Enable logging for debugging
    logging.basicConfig(level=logging.INFO)

    test1 = """
    graph TB        
        Sub1[s10000000000000000000000000000000000] & Sub2[s2] --> Merge[merge]
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

            with open("a.tmp", "w", encoding="utf-8") as f:
                f.write(ascii_art)

    else:
        print("No graph found in the input")
