#!/usr/bin/env python3
"""
调试mermaid解析问题
"""

import sys
import os
sys.path.append('mermaid_ascii')

from mermaid_to_ascii import Parser
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

def debug_parsing():
    """调试解析过程"""
    
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
    
    graph = parser.graph_roots[0]
    
    print(f"\n解析结果:")
    print(f"节点数量: {len(graph.get_nodes())}")
    print(f"边数量: {len(graph.get_edge_list())}")
    
    print("\n节点信息:")
    for node in graph.get_nodes():
        name = node.get_name()
        label = node.get_attributes().get("label", "")
        print(f"  节点: {name}, 标签: '{label}'")
    
    print("\n边信息:")
    for edge in graph.get_edge_list():
        src = edge.get_source()
        dst = edge.get_destination()
        print(f"  边: {src} -> {dst}")
    
    # 生成dot格式查看
    dot_string = graph.to_string()
    print(f"\n生成的DOT格式:")
    print(dot_string)

if __name__ == "__main__":
    debug_parsing()