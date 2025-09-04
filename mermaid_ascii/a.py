import pydot

graph = pydot.Dot(graph_type='digraph', rankdir='LR')

# 添加节点和边
graph.add_node(pydot.Node('A', label='Start'))
graph.add_node(pydot.Node('B', shape='box'))
graph.add_edge(pydot.Edge('A', 'B'))
graph.add_edge(pydot.Edge('B', 'C'))
graph.add_edge(pydot.Edge('B', 'D'))


print(graph)

ascii_output = graph.create(format='plain')

# 3. 解码并打印结果（create() 返回的是 bytes）
print(ascii_output.decode('utf-8'))