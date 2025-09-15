#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydot Graph to ASCII converter
将 pydot 图形转换为 ASCII 字符图形
"""

from typing import Dict, List, Tuple, Set
import re
import pydot

class ASCIIGraphCanvas:
    """ASCII图形画布"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]
    
    def set_char(self, x: int, y: int, char: str):
        """在指定位置设置字符"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = char
    
    def draw_box(self, x: int, y: int, width: int, height: int, text: str = ""):
        """绘制矩形框"""
        # 绘制边框
        for i in range(width):
            self.set_char(x + i, y, '-')  # 上边
            self.set_char(x + i, y + height - 1, '-')  # 下边
        
        for i in range(height):
            self.set_char(x, y + i, '|')  # 左边
            self.set_char(x + width - 1, y + i, '|')  # 右边
        
        # 绘制四个角
        self.set_char(x, y, '+')
        self.set_char(x + width - 1, y, '+')
        self.set_char(x, y + height - 1, '+')
        self.set_char(x + width - 1, y + height - 1, '+')
        
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
            self.set_char(px, py, 'o')
        
        # 添加文本
        if text:
            text_x = x - len(text) // 2
            text_y = y
            for i, char in enumerate(text):
                self.set_char(text_x + i, text_y, char)
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, char: str = None):
        """绘制直线，智能选择字符"""
        dx = x2 - x1
        dy = y2 - y1
        
        # 如果没有指定字符，根据方向自动选择
        if char is None:
            if abs(dx) < 2:  # 垂直线
                char = '|'
            elif abs(dy) < 2:  # 水平线
                char = '-'
            elif (dx > 0 and dy > 0) or (dx < 0 and dy < 0):  # 正斜率 (\)
                char = '\\'
            else:  # 负斜率 (/)
                char = '/'
        
        # Bresenham算法绘制线条
        dx = abs(dx)
        dy = abs(dy)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
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
    
    def draw_smart_connection(self, x1: int, y1: int, x2: int, y2: int):
        """绘制智能连接线（L形或直线）"""
        # 如果是直线连接（水平、垂直或对角线）
        if x1 == x2 or y1 == y2 or abs(x2 - x1) == abs(y2 - y1):
            self.draw_line(x1, y1, x2, y2)
        else:
            # L形连接：先垂直再水平
            mid_y = y1 + (y2 - y1) // 2
            
            # 第一段：垂直线
            self.draw_line(x1, y1, x1, mid_y, '|')
            # 第二段：水平线
            self.draw_line(x1, mid_y, x2, mid_y, '-')
            # 第三段：垂直线
            self.draw_line(x2, mid_y, x2, y2, '|')
            
            # 绘制转折点
            if x1 != x2 and y1 != mid_y:
                self.set_char(x1, mid_y, '+')
            if x2 != x1 and mid_y != y2:
                self.set_char(x2, mid_y, '+')
    
    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int):
        """绘制箭头"""
        # 绘制连接线
        self.draw_smart_connection(x1, y1, x2, y2)
        
        # 添加箭头头部
        dx = x2 - x1
        dy = y2 - y1
        
        if abs(dx) > abs(dy):  # 主要是水平方向
            if dx > 0:
                self.set_char(x2, y2, '>')
            else:
                self.set_char(x2, y2, '<')
        else:  # 主要是垂直方向
            if dy > 0:
                self.set_char(x2, y2, 'v')
            else:
                self.set_char(x2, y2, '^')
    
    def to_string(self) -> str:
        """转换为字符串"""
        return '\n'.join(''.join(row) for row in self.canvas)


class PydotToASCII:
    """Pydot图形转ASCII转换器"""
    
    def __init__(self):
        self.node_width = 10
        self.node_height = 3
        self.node_spacing_x = 4  # 节点间水平间距
        self.node_spacing_y = 2  # 层级间垂直间距
        self.margin = 2
    
    def parse_graph(self, graph) -> Tuple[Dict, List]:
        """解析pydot图形，提取节点和边"""
        nodes = {}
        edges = []
        
        # 提取节点
        for node in graph.get_nodes():
            node_name = node.get_name().strip('"')
            if node_name in ['node', 'edge', 'graph']:  # 跳过默认属性节点
                continue
            
            label = node.get('label')
            if label:
                label = label.strip('"')
            else:
                label = node_name
            
            shape = node.get('shape')
            if shape:
                shape = shape.strip('"')
            else:
                shape = 'ellipse'
            
            nodes[node_name] = {
                'label': label,
                'shape': shape
            }
        
        # 提取边
        for edge in graph.get_edges():
            src = edge.get_source().strip('"')
            dst = edge.get_destination().strip('"')
            edges.append((src, dst))
        
        return nodes, edges
    
    def build_adjacency_list(self, nodes: Dict, edges: List) -> Dict:
        """构建邻接表"""
        adj_list = {node: [] for node in nodes.keys()}
        in_degree = {node: 0 for node in nodes.keys()}
        
        for src, dst in edges:
            if src in adj_list and dst in adj_list:
                adj_list[src].append(dst)
                in_degree[dst] += 1
        
        return adj_list, in_degree
    
    def find_root_nodes(self, in_degree: Dict) -> List:
        """找到根节点（入度为0的节点）"""
        return [node for node, degree in in_degree.items() if degree == 0]
    
    def calculate_levels(self, nodes: Dict, edges: List) -> Tuple[Dict, int]:
        """计算每个节点的层级和最大深度"""
        adj_list, in_degree = self.build_adjacency_list(nodes, edges)
        root_nodes = self.find_root_nodes(in_degree)
        
        if not root_nodes:
            # 如果没有根节点（可能有环），选择第一个节点作为根
            root_nodes = [list(nodes.keys())[0]] if nodes else []
        
        levels = {}
        max_depth = 0
        
        # BFS计算层级
        from collections import deque
        queue = deque()
        
        # 初始化根节点
        for root in root_nodes:
            levels[root] = 0
            queue.append((root, 0))
        
        visited = set(root_nodes)
        
        while queue:
            node, level = queue.popleft()
            max_depth = max(max_depth, level)
            
            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    levels[neighbor] = level + 1
                    queue.append((neighbor, level + 1))
                    visited.add(neighbor)
        
        # 处理未访问的节点（可能在环中）
        for node in nodes:
            if node not in levels:
                levels[node] = max_depth + 1
                max_depth += 1
        
        return levels, max_depth
    
    def calculate_level_widths(self, levels: Dict) -> Dict:
        """计算每层的节点数量"""
        level_counts = {}
        for node, level in levels.items():
            level_counts[level] = level_counts.get(level, 0) + 1
        return level_counts
    
    def layout_nodes(self, nodes: Dict, edges: List) -> Tuple[Dict, int, int]:
        """基于图结构计算节点布局位置"""
        levels, max_depth = self.calculate_levels(nodes, edges)
        level_counts = self.calculate_level_widths(levels)
        
        # 计算画布尺寸
        max_width_nodes = max(level_counts.values()) if level_counts else 1
        canvas_width = max_width_nodes * (self.node_width + self.node_spacing_x) + 2 * self.margin
        canvas_height = (max_depth + 1) * (self.node_height + self.node_spacing_y) + 2 * self.margin
        
        # 按层级分组节点
        nodes_by_level = {}
        for node, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)
        
        # 计算每个节点的位置
        positions = {}
        
        for level, level_nodes in nodes_by_level.items():
            level_width = len(level_nodes)
            
            # 计算该层节点的起始x位置（居中对齐）
            total_level_width = level_width * self.node_width + (level_width - 1) * self.node_spacing_x
            start_x = (canvas_width - total_level_width) // 2
            
            # 计算y位置
            y = self.margin + level * (self.node_height + self.node_spacing_y)
            
            # 为该层的每个节点分配位置
            for i, node in enumerate(level_nodes):
                x = start_x + i * (self.node_width + self.node_spacing_x)
                positions[node] = (x, y)
        
        return positions, canvas_width, canvas_height
    
    def get_connection_point(self, node_x: int, node_y: int, target_x: int, target_y: int) -> Tuple[int, int]:
        """计算节点的连接点（边缘而不是中心）"""
        node_center_x = node_x + self.node_width // 2
        node_center_y = node_y + self.node_height // 2
        
        # 计算目标方向
        dx = target_x - node_center_x
        dy = target_y - node_center_y
        
        # 根据方向确定连接点
        if abs(dx) > abs(dy):  # 主要是水平方向
            if dx > 0:  # 目标在右侧，连接右边缘
                return node_x + self.node_width, node_center_y
            else:  # 目标在左侧，连接左边缘
                return node_x, node_center_y
        else:  # 主要是垂直方向
            if dy > 0:  # 目标在下方，连接下边缘
                return node_center_x, node_y + self.node_height
            else:  # 目标在上方，连接上边缘
                return node_center_x, node_y
    
    def convert_to_ascii(self, graph) -> str:
        """将pydot图形转换为ASCII"""
        nodes, edges = self.parse_graph(graph)
        
        if not nodes:
            return "没有找到节点"
        
        # 使用新的布局系统计算位置和画布大小
        positions, canvas_width, canvas_height = self.layout_nodes(nodes, edges)
        
        # 创建画布
        canvas = ASCIIGraphCanvas(canvas_width, canvas_height)
        
        # 绘制边
        for src, dst in edges:
            if src in positions and dst in positions:
                src_x, src_y = positions[src]
                dst_x, dst_y = positions[dst]
                
                # 计算智能连接点（连接到节点边缘而不是中心）
                src_connect_x, src_connect_y = self.get_connection_point(
                    src_x, src_y, dst_x + self.node_width // 2, dst_y + self.node_height // 2
                )
                dst_connect_x, dst_connect_y = self.get_connection_point(
                    dst_x, dst_y, src_x + self.node_width // 2, src_y + self.node_height // 2
                )
                
                canvas.draw_arrow(src_connect_x, src_connect_y, dst_connect_x, dst_connect_y)
        
        # 绘制节点
        for node_name, node_info in nodes.items():
            if node_name in positions:
                x, y = positions[node_name]
                label = node_info['label']
                shape = node_info['shape']
                
                if shape == 'box':
                    canvas.draw_box(x, y, self.node_width, self.node_height, label)
                else:  # 默认为椭圆
                    canvas.draw_circle(x + self.node_width // 2, y + self.node_height // 2, 
                                     self.node_width // 2, label)
        
        return canvas.to_string()


def main():
    """示例用法"""
    # 创建示例图形
    graph = pydot.Dot(graph_type='digraph', rankdir='LR')
    
    # 添加节点
    graph.add_node(pydot.Node('A', label='Start', shape='box'))
    graph.add_node(pydot.Node('B', label='Process', shape='box'))
    graph.add_node(pydot.Node('C', label='End', shape='box'))
    graph.add_node(pydot.Node('D', label='Error', shape='box'))
    
    # 添加边
    graph.add_edge(pydot.Edge('A', 'B'))
    graph.add_edge(pydot.Edge('B', 'C'))
    graph.add_edge(pydot.Edge('B', 'D'))
    
    # 转换为ASCII
    converter = PydotToASCII()
    ascii_graph = converter.convert_to_ascii(graph)
    
    print("Pydot Graph to ASCII:")
    print("=" * 50)
    print(ascii_graph)


if __name__ == "__main__":
    main()