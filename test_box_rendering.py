#!/usr/bin/env python3
"""
测试box边界渲染
"""

import sys
import os
sys.path.append('mermaid_ascii')

from mermaid_to_ascii import ASCIIGraphCanvas

def test_box_rendering():
    """测试box渲染功能"""
    
    # 创建画布
    canvas = ASCIIGraphCanvas(80, 20)
    
    # 测试不同长度的文本
    test_cases = [
        ("短", 5, 2, 3, 3),
        ("中等长度文本", 15, 2, 8, 3),
        ("这是一个非常长的文本标签用来测试", 5, 6, 10, 3),
        ("子节点100000000000000000000000000000000", 5, 10, 15, 3),
    ]
    
    for text, x, y, width, height in test_cases:
        canvas.draw_box(x, y, width, height, text)
        print(f"绘制文本: '{text}' 在位置 ({x}, {y}) 建议尺寸 {width}x{height}")
    
    # 输出结果
    result = canvas.to_string()
    print("\n渲染结果:")
    print(result)
    
    return result

if __name__ == "__main__":
    test_box_rendering()