#!/usr/bin/env python3
"""
测试复杂布局的碰撞检测
"""

import sys
import os
sys.path.append('mermaid_ascii')

from mermaid_to_ascii import Parser, LayOut, DotToASCII
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_complex_collision():
    """测试复杂布局的碰撞检测"""
    
    mermaid_text = """
graph LR
    A[开始] --> B[步骤1]
    A --> C[步骤2]
    B --> D[长标签步骤3]
    C --> D
    D --> E[结束]
    B --> F[分支步骤]
    F --> E
    """
    
    print("原始Mermaid代码:")
    print(mermaid_text)
    
    # 解析mermaid
    parser = Parser()
    parser.parse(mermaid_text)
    
    if not parser.graph_roots:
        print("解析失败，没有找到图形")
        return
    
    # 布局计算
    layout = LayOut()
    graphs = layout.layout_calc(parser.graph_roots[0])
    
    if not graphs:
        print("布局计算失败")
        return
    
    # 转换为ASCII
    converter = DotToASCII(max_width=150, max_height=30)
    converter.load_dot(graphs[0])
    
    # 计算所需的最小画布宽度
    min_canvas_width = converter.ascii_width
    for node in graphs[0].get_nodes():
        if node.get_name().strip('"') not in ['node', 'edge', 'graph']:
            label = node.get_attributes().get("label", node.get_name())
            if label:
                min_width = len(label) + 2
                min_canvas_width = max(min_canvas_width, min_width + 10)
    
    # 创建画布
    from mermaid_to_ascii import ASCIIGraphCanvas
    canvas = ASCIIGraphCanvas(min_canvas_width, converter.ascii_height)
    
    # 渲染所有节点（包含碰撞检测）
    converter.render_all_nodes(canvas)
    
    # 输出结果
    result = canvas.to_string()
    print("\nASCII渲染结果:")
    print(result)
    
    return result

if __name__ == "__main__":
    test_complex_collision()