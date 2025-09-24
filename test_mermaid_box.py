#!/usr/bin/env python3
"""
测试mermaid转ASCII的box渲染
"""

import sys
import os
sys.path.append('mermaid_ascii')

from mermaid_to_ascii import Parser, LayOut, DotToASCII
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_mermaid_with_long_labels():
    """测试包含长标签的mermaid图"""
    
    mermaid_text = """
graph TD
    A[开始] --> B[这是一个很长的处理步骤标签]
    B --> C[子节点100000000000000000000000000000000]
    C --> D[结束]
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
    converter = DotToASCII(max_width=200, max_height=40)
    converter.load_dot(graphs[0])
    
    # 计算所需的最小画布宽度
    min_canvas_width = converter.ascii_width
    for node in graphs[0].get_nodes():
        if node.get_name().strip('"') not in ['node', 'edge', 'graph']:
            label = node.get_attributes().get("label", node.get_name())
            if label:
                min_width = len(label) + 2
                min_canvas_width = max(min_canvas_width, min_width + 10)  # 额外空间
    
    # 创建画布
    from mermaid_to_ascii import ASCIIGraphCanvas
    canvas = ASCIIGraphCanvas(min_canvas_width, converter.ascii_height)
    
    # 渲染节点
    for node in graphs[0].get_nodes():
        if node.get_name().strip('"') not in ['node', 'edge', 'graph']:
            converter.render_node(canvas, node)
    
    # 输出结果
    result = canvas.to_string()
    print("\nASCII渲染结果:")
    print(result)
    
    return result

if __name__ == "__main__":
    test_mermaid_with_long_labels()