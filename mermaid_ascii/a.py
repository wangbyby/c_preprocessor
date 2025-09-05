import pydot
from pydot_to_ascii import PydotToASCII

# 创建图形
graph = pydot.Dot(graph_type='digraph', rankdir='LR')

# 添加节点和边
graph.add_node(pydot.Node('A', label='Start'))
graph.add_node(pydot.Node('B', label='Process', shape='box'))
graph.add_node(pydot.Node('C', label='End'))
graph.add_node(pydot.Node('D', label='Error', shape='box'))

graph.add_edge(pydot.Edge('A', 'B'))
graph.add_edge(pydot.Edge('B', 'C'))
graph.add_edge(pydot.Edge('B', 'D'))

print("Original pydot graph:")
print(graph)
print("\n" + "="*50 + "\n")

# 使用新的ASCII转换器
converter = PydotToASCII()
ascii_graph = converter.convert_to_ascii(graph)

print("ASCII Graph:")
print(ascii_graph)