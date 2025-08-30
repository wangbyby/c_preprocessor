#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exclidraw to ASCII converter
将 exclidraw.json 中的图形转换为 ASCII 字符图形
"""

import json
import sys
import math
from typing import List, Dict, Any, Tuple


class ASCIICanvas:
    """ASCII画布类"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]
    
    def set_char(self, x: int, y: int, char: str):
        """在指定位置设置字符"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = char
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, char: str = '*'):
        """使用Bresenham算法绘制直线"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
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
    
    def draw_rectangle(self, x: int, y: int, width: int, height: int):
        """绘制矩形"""
        # 绘制四条边
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
    
    def draw_ellipse(self, cx: int, cy: int, rx: int, ry: int):
        """绘制椭圆/圆形"""
        for angle in range(0, 360, 5):  # 每5度绘制一个点
            rad = math.radians(angle)
            x = int(cx + rx * math.cos(rad))
            y = int(cy + ry * math.sin(rad))
            self.set_char(x, y, 'o')
    
    def draw_diamond(self, cx: int, cy: int, width: int, height: int):
        """绘制菱形"""
        half_w = width // 2
        half_h = height // 2
        
        # 绘制四条边
        self.draw_line(cx, cy - half_h, cx + half_w, cy, '*')  # 右上
        self.draw_line(cx + half_w, cy, cx, cy + half_h, '*')  # 右下
        self.draw_line(cx, cy + half_h, cx - half_w, cy, '*')  # 左下
        self.draw_line(cx - half_w, cy, cx, cy - half_h, '*')  # 左上
    
    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int):
        """绘制有向线段（箭头）"""
        # 绘制主线
        self.draw_line(x1, y1, x2, y2, '-')
        
        # 计算箭头方向
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # 标准化方向向量
            dx /= length
            dy /= length
            
            # 箭头长度
            arrow_len = 3
            
            # 箭头角度（30度）
            cos30 = math.cos(math.radians(30))
            sin30 = math.sin(math.radians(30))
            
            # 计算箭头两个分支的终点
            ax1 = x2 - arrow_len * (dx * cos30 - dy * sin30)
            ay1 = y2 - arrow_len * (dx * sin30 + dy * cos30)
            ax2 = x2 - arrow_len * (dx * cos30 + dy * sin30)
            ay2 = y2 - arrow_len * (dy * cos30 - dx * sin30)
            
            # 绘制箭头
            self.draw_line(x2, y2, int(ax1), int(ay1), '>')
            self.draw_line(x2, y2, int(ax2), int(ay2), '>')
            
        # 箭头头部
        self.set_char(x2, y2, '>')
    
    def to_string(self) -> str:
        """将画布转换为字符串"""
        return '\n'.join(''.join(row) for row in self.canvas)


class ExclidrawConverter:
    """Exclidraw转换器"""
    
    def __init__(self):
        self.target_width = 120  # 目标画布宽度
        self.target_height = 60  # 目标画布高度
        self.min_size = 3  # 最小尺寸
    
    def load_exclidraw(self, filename: str) -> Dict[str, Any]:
        """加载Exclidraw JSON文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 找不到文件 {filename}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"错误: {filename} 不是有效的JSON文件")
            sys.exit(1)
    
    def calculate_bounds(self, elements: List[Dict[str, Any]]) -> Tuple[float, float, float, float]:
        """计算所有元素的边界"""
        if not elements:
            return 0, 0, 100, 50
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element in elements:
            x = element.get('x', 0)
            y = element.get('y', 0)
            width = element.get('width', 0)
            height = element.get('height', 0)
            
            # 处理线条和箭头的特殊情况
            if element.get('type') in ['line', 'arrow']:
                points = element.get('points', [])
                for point in points:
                    px, py = x + point[0], y + point[1]
                    min_x = min(min_x, px)
                    min_y = min(min_y, py)
                    max_x = max(max_x, px)
                    max_y = max(max_y, py)
            else:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + width)
                max_y = max(max_y, y + height)
        
        return min_x, min_y, max_x, max_y
    
    def calculate_scale_factors(self, min_x: float, min_y: float, max_x: float, max_y: float) -> Tuple[float, float]:
        """计算缩放因子"""
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        if content_width == 0 or content_height == 0:
            return 0.1, 0.1
        
        # 计算缩放因子，保持宽高比
        scale_x = (self.target_width - 10) / content_width
        scale_y = (self.target_height - 10) / content_height
        
        # 使用较小的缩放因子以保持宽高比
        scale = min(scale_x, scale_y, 0.2)  # 限制最大缩放因子
        
        return scale, scale
    
    def convert_coordinates(self, x: float, y: float, min_x: float, min_y: float, scale_x: float, scale_y: float) -> Tuple[int, int]:
        """转换坐标系"""
        canvas_x = int((x - min_x) * scale_x) + 2  # 添加边距
        canvas_y = int((y - min_y) * scale_y) + 2  # 添加边距
        return canvas_x, canvas_y
    
    def convert_to_ascii(self, data: Dict[str, Any]) -> str:
        """将Exclidraw数据转换为ASCII"""
        elements = data.get('elements', [])
        
        if not elements:
            return "没有找到可绘制的元素"
        
        # 计算边界
        min_x, min_y, max_x, max_y = self.calculate_bounds(elements)
        
        # 计算缩放因子
        scale_x, scale_y = self.calculate_scale_factors(min_x, min_y, max_x, max_y)
        
        # 计算实际画布大小
        canvas_width = int((max_x - min_x) * scale_x) + 10
        canvas_height = int((max_y - min_y) * scale_y) + 10
        
        # 限制画布大小
        canvas_width = min(canvas_width, self.target_width)
        canvas_height = min(canvas_height, self.target_height)
        
        canvas = ASCIICanvas(canvas_width, canvas_height)
        
        # 绘制每个元素
        for element in elements:
            self.draw_element(canvas, element, min_x, min_y, scale_x, scale_y)
        
        return canvas.to_string()
    
    def draw_element(self, canvas: ASCIICanvas, element: Dict[str, Any], min_x: float, min_y: float, scale_x: float, scale_y: float):
        """绘制单个元素"""
        element_type = element.get('type', '')
        x = element.get('x', 0)
        y = element.get('y', 0)
        width = element.get('width', 0)
        height = element.get('height', 0)
        
        # 转换坐标
        canvas_x, canvas_y = self.convert_coordinates(x, y, min_x, min_y, scale_x, scale_y)
        canvas_width = max(int(width * scale_x), self.min_size)
        canvas_height = max(int(height * scale_y), self.min_size)
        
        if element_type == 'rectangle':
            canvas.draw_rectangle(canvas_x, canvas_y, canvas_width, canvas_height)
        
        elif element_type == 'ellipse':
            rx = max(canvas_width // 2, 2)
            ry = max(canvas_height // 2, 2)
            cx = canvas_x + rx
            cy = canvas_y + ry
            canvas.draw_ellipse(cx, cy, rx, ry)
        
        elif element_type == 'diamond':
            cx = canvas_x + canvas_width // 2
            cy = canvas_y + canvas_height // 2
            canvas.draw_diamond(cx, cy, canvas_width, canvas_height)
        
        elif element_type == 'line':
            points = element.get('points', [])
            if len(points) >= 2:
                start_x, start_y = self.convert_coordinates(x + points[0][0], y + points[0][1], min_x, min_y, scale_x, scale_y)
                end_x, end_y = self.convert_coordinates(x + points[-1][0], y + points[-1][1], min_x, min_y, scale_x, scale_y)
                canvas.draw_line(start_x, start_y, end_x, end_y, '-')
        
        elif element_type == 'arrow':
            points = element.get('points', [])
            if len(points) >= 2:
                start_x, start_y = self.convert_coordinates(x + points[0][0], y + points[0][1], min_x, min_y, scale_x, scale_y)
                end_x, end_y = self.convert_coordinates(x + points[-1][0], y + points[-1][1], min_x, min_y, scale_x, scale_y)
                canvas.draw_arrow(start_x, start_y, end_x, end_y)


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python exclidraw2ascii.py exclidraw.json")
        sys.exit(1)
    
    filename = sys.argv[1]
    converter = ExclidrawConverter()
    
    # 加载并转换
    data = converter.load_exclidraw(filename)
    ascii_art = converter.convert_to_ascii(data)
    
    print(ascii_art)


if __name__ == "__main__":
    main()