#!/usr/bin/env python3
"""
碰撞检测和位置调整系统
"""

from dataclasses import dataclass
from typing import List, Tuple
import logging


@dataclass
class Rectangle:
    """矩形区域"""
    x: int
    y: int
    width: int
    height: int
    node_id: str = ""
    
    def right(self) -> int:
        return self.x + self.width
    
    def bottom(self) -> int:
        return self.y + self.height
    
    def center_x(self) -> int:
        return self.x + self.width // 2
    
    def center_y(self) -> int:
        return self.y + self.height // 2
    
    def overlaps_with(self, other: 'Rectangle') -> bool:
        """检查是否与另一个矩形重叠"""
        return not (self.right() <= other.x or 
                   other.right() <= self.x or 
                   self.bottom() <= other.y or 
                   other.bottom() <= self.y)
    
    def distance_to(self, other: 'Rectangle') -> float:
        """计算到另一个矩形中心的距离"""
        dx = self.center_x() - other.center_x()
        dy = self.center_y() - other.center_y()
        return (dx * dx + dy * dy) ** 0.5


class CollisionResolver:
    """碰撞检测和解决器"""
    
    def __init__(self, canvas_width: int, canvas_height: int, min_spacing: int = 1):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.min_spacing = min_spacing  # 节点之间的最小间距
        
    def resolve_collisions(self, rectangles: List[Rectangle]) -> List[Rectangle]:
        """解决矩形之间的碰撞"""
        if len(rectangles) <= 1:
            return rectangles
        
        # 创建副本以避免修改原始数据
        resolved_rects = [Rectangle(r.x, r.y, r.width, r.height, r.node_id) for r in rectangles]
        
        # 多次迭代直到没有碰撞
        max_iterations = 50
        for iteration in range(max_iterations):
            collisions_found = False
            
            for i in range(len(resolved_rects)):
                for j in range(i + 1, len(resolved_rects)):
                    rect1 = resolved_rects[i]
                    rect2 = resolved_rects[j]
                    
                    if self._rectangles_too_close(rect1, rect2):
                        collisions_found = True
                        self._separate_rectangles(rect1, rect2)
                        
                        # 确保矩形在画布范围内
                        self._clamp_to_canvas(rect1)
                        self._clamp_to_canvas(rect2)
            
            if not collisions_found:
                logging.debug(f"碰撞解决完成，迭代次数: {iteration + 1}")
                break
        
        return resolved_rects
    
    def _rectangles_too_close(self, rect1: Rectangle, rect2: Rectangle) -> bool:
        """检查两个矩形是否太接近（包括重叠和间距不足）"""
        # 检查是否重叠
        if rect1.overlaps_with(rect2):
            return True
        
        # 计算两个矩形之间的最小距离
        dx = max(0, max(rect1.x - rect2.right(), rect2.x - rect1.right()))
        dy = max(0, max(rect1.y - rect2.bottom(), rect2.y - rect1.bottom()))
        
        # 如果距离小于最小间距，则认为太接近
        return dx < self.min_spacing and dy < self.min_spacing
    
    def _separate_rectangles(self, rect1: Rectangle, rect2: Rectangle):
        """分离两个矩形"""
        # 计算重叠区域
        overlap_x = min(rect1.right(), rect2.right()) - max(rect1.x, rect2.x)
        overlap_y = min(rect1.bottom(), rect2.bottom()) - max(rect1.y, rect2.y)
        
        # 添加最小间距
        overlap_x += self.min_spacing
        overlap_y += self.min_spacing
        
        # 选择分离方向（优先选择重叠较小的方向）
        if overlap_x <= overlap_y:
            # 水平分离
            if rect1.center_x() < rect2.center_x():
                # rect1在左，rect2在右
                move_distance = overlap_x // 2
                rect1.x -= move_distance
                rect2.x += move_distance
            else:
                # rect1在右，rect2在左
                move_distance = overlap_x // 2
                rect1.x += move_distance
                rect2.x -= move_distance
        else:
            # 垂直分离
            if rect1.center_y() < rect2.center_y():
                # rect1在上，rect2在下
                move_distance = overlap_y // 2
                rect1.y -= move_distance
                rect2.y += move_distance
            else:
                # rect1在下，rect2在上
                move_distance = overlap_y // 2
                rect1.y += move_distance
                rect2.y -= move_distance
    
    def _clamp_to_canvas(self, rect: Rectangle):
        """确保矩形在画布范围内"""
        # 确保不超出左边界
        if rect.x < 0:
            rect.x = 0
        
        # 确保不超出上边界
        if rect.y < 0:
            rect.y = 0
        
        # 确保不超出右边界
        if rect.right() > self.canvas_width:
            rect.x = max(0, self.canvas_width - rect.width)
        
        # 确保不超出下边界
        if rect.bottom() > self.canvas_height:
            rect.y = max(0, self.canvas_height - rect.height)
    
    def arrange_in_grid(self, rectangles: List[Rectangle]) -> List[Rectangle]:
        """将矩形按网格排列（备用方案）"""
        if not rectangles:
            return rectangles
        
        # 计算网格尺寸
        num_rects = len(rectangles)
        cols = int(num_rects ** 0.5) + 1
        rows = (num_rects + cols - 1) // cols
        
        # 计算每个网格单元的尺寸
        cell_width = self.canvas_width // cols
        cell_height = self.canvas_height // rows
        
        arranged_rects = []
        for i, rect in enumerate(rectangles):
            row = i // cols
            col = i % cols
            
            # 计算新位置（居中在网格单元内）
            new_x = col * cell_width + (cell_width - rect.width) // 2
            new_y = row * cell_height + (cell_height - rect.height) // 2
            
            # 确保在画布范围内
            new_x = max(0, min(new_x, self.canvas_width - rect.width))
            new_y = max(0, min(new_y, self.canvas_height - rect.height))
            
            arranged_rect = Rectangle(new_x, new_y, rect.width, rect.height, rect.node_id)
            arranged_rects.append(arranged_rect)
        
        return arranged_rects


def test_collision_resolver():
    """测试碰撞解决器"""
    # 创建一些重叠的矩形
    rectangles = [
        Rectangle(10, 10, 20, 5, "A"),
        Rectangle(15, 12, 25, 5, "B"),  # 与A重叠
        Rectangle(12, 8, 15, 5, "C"),   # 与A重叠
    ]
    
    resolver = CollisionResolver(100, 50, min_spacing=2)
    
    print("原始矩形:")
    for rect in rectangles:
        print(f"  {rect.node_id}: ({rect.x}, {rect.y}) {rect.width}x{rect.height}")
    
    resolved = resolver.resolve_collisions(rectangles)
    
    print("\n解决碰撞后:")
    for rect in resolved:
        print(f"  {rect.node_id}: ({rect.x}, {rect.y}) {rect.width}x{rect.height}")
    
    # 检查是否还有重叠
    print("\n碰撞检查:")
    for i in range(len(resolved)):
        for j in range(i + 1, len(resolved)):
            if resolved[i].overlaps_with(resolved[j]):
                print(f"  警告: {resolved[i].node_id} 和 {resolved[j].node_id} 仍然重叠")
            else:
                print(f"  ✓ {resolved[i].node_id} 和 {resolved[j].node_id} 已分离")


if __name__ == "__main__":
    test_collision_resolver()