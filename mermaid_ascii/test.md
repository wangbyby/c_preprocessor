
# 测试编写

## 测试框架

使用pytest

## 测试内容

1. 测试 Parser类型对mermaid的graph和subgraph的parsing逻辑是否正确

2. 测试示例

text="graph....."
p = Parser()
p.run(text)
graph = p.graph_roots
check_graph....


