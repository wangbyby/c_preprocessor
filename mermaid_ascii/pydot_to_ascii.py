#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydot Graph to ASCII converter
将 pydot 图形转换为 ASCII 字符图形
"""

from typing import Dict, List, Tuple, Set
import re


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
                char = '-'
            elif dy > dx:
                char = '|'
            else:
                char = '*'
            
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
            self.set_char(x2, y2, '>')
        elif x2 < x1:
            self.set_char(x2, y2, '<')
        elif y2 > y1:
            self.set_char(x2, y2, 'v')
        else:
            self.set_char(x2, y2, '^')
    
    def to_string(self) -> str:
        """转换为字符串"""
        return '\n'.join(''.join(row) for row in self.canvas)


class PydotToASCII:
    """Pydot图形转ASCII转换器"""
    
    def __init__(self):
        self.canvas_width = 80
        self.canvas_height = 40
        self.node_width = 8
        self.node_height = 3
        self.node_spacing_x = 15
        self.node_spacing_y = 8
    
    def parse_graph(self, graph: pydot.Dot) -> Tuple[Dict, List]:
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
    
    def layout_nodes(self, nodes: Dict) -> Dict:
        """计算节点布局位置"""
        positions = {}
        node_names = list(nodes.keys())
        
        # 简单的网格布局
        cols = min(len(node_names), 4)  # 最多4列
        rows = (len(node_names) + cols - 1) // cols
        
        for i, node_name in enumerate(node_names):
            col = i % cols
            row = i // cols
            
            x = 5 + col * self.node_spacing_x
            y = 3 + row * self.node_spacing_y
            
            positions[node_name] = (x, y)
        
        return positions
    
    def convert_to_ascii(self, graph: pydot.Dot) -> str:
        """将pydot图形转换为ASCII"""
        nodes, edges = self.parse_graph(graph)
        
        if not nodes:
            return "没有找到节点"
        
        # 计算布局
        positions = self.layout_nodes(nodes)
        
        # 调整画布大小
        max_x = max(pos[0] for pos in positions.values()) + self.node_width + 5
        max_y = max(pos[1] for pos in positions.values()) + self.node_height + 3
        
        canvas = ASCIIGraphCanvas(max_x, max_y)
        
        # 绘制边
        for src, dst in edges:
            if src in positions and dst in positions:
                src_x, src_y = positions[src]
                dst_x, dst_y = positions[dst]
                
                # 计算连接点（节点中心）
                src_center_x = src_x + self.node_width // 2
                src_center_y = src_y + self.node_height // 2
                dst_center_x = dst_x + self.node_width // 2
                dst_center_y = dst_y + self.node_height // 2
                
                canvas.draw_arrow(src_center_x, src_center_y, dst_center_x, dst_center_y)
        
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
    graph.add_node(pydot.Node('A', label='Start'))
    graph.add_node(pydot.Node('B', label='Process', shape='box'))
    graph.add_node(pydot.Node('C', label='End'))
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