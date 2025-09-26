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

from dataclasses import dataclass
import logging
from typing import Dict, List
from mermaid_ascii.graph import Graph, Node


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


class Layout:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.levels: Dict[int, List[Node]] = {}

        self._calc_grid()

    def _level_range(self, g: Graph, root: Node):

        l = [root]
        visited = set()
        level = 0

        while len(l) > 0:
            length = len(l)

            for _ in range(length):
                n = l.pop(0)
                if n in visited:
                    continue
                visited.add(n)

                n.y = [level, level + 1, level + 2]

                for next in n.get_neighbors(g):
                    if next not in visited:
                        l.append(next)

            level += 4

    def _calc_grid(self):
        roots = self.graph.get_root_node()

        for root in roots:
            self._level_range(self.graph, root)

        for node in self.graph.get_nodes():
            center = node.y[1]
            l = self.levels.get(center, None)
            if l is None:
                self.levels[center] = [node]
            else:
                self.levels[center].append(node)

        for _, l in self.levels.items():
            x = 0
            for n in l:
                n.x = [x, x + 1, x + 2]
                x += 4

    def calc_ascii_pos(self):
        self.x_mapping: Dict[int, int] = {}
        self.y_mapping: Dict[int, int] = {}

        ascii_y = 0
        ascii_x_max = 0

        for _, nodes in self.levels.items():

            ascii_x = 0

            ascii_y_level = ascii_y

            for n in nodes:
                self.x_mapping[n.x[0]] = ascii_x

                l = len(n.label) // 2

                ascii_x += l + 1

                self.x_mapping[n.x[1]] = ascii_x

                ascii_x += l + 1

                self.x_mapping[n.x[2]] = ascii_x

            for y in nodes[0].y:
                self.y_mapping[y] = ascii_y_level
                ascii_y_level += 1

            ascii_y = ascii_y_level + 2
            ascii_x_max = max(ascii_x_max, ascii_x)

        for node in self.graph.nodes:
            x = [self.x_mapping[i] for i in node.ascii_x]
            y = [self.y_mapping[i] for i in node.ascii_y]

            node.ascii_x = x
            node.ascii_y = y

        return (ascii_x_max, ascii_y)

    def draw(self) -> ASCIIGraphCanvas:
        (w, h) = self.calc_ascii_pos()

        canvas = ASCIIGraphCanvas(w, h)

        for n in self.graph.nodes:

            x = n.ascii_x[0]
            y = n.ascii_y[0]

            w = n.ascii_x[2] - x
            h = n.ascii_y[2] - y

            canvas.draw_box(x, y, w, h, n.label)

        return canvas
