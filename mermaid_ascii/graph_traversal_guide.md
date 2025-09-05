# Pydot Graph to ASCII Conversion Guide

## 概述

将 pydot 图形转换为 ASCII 文本图形需要以下步骤：

1. **解析图形结构** - 提取节点和边信息
2. **计算布局** - 确定节点在ASCII画布上的位置
3. **绘制图形** - 使用ASCII字符绘制节点和连接线

## 核心组件

### 1. 图形解析 (Graph Parsing)

```python
def parse_graph(self, graph: pydot.Dot):
    nodes = {}
    edges = []
    
    # 提取节点
    for node in graph.get_nodes():
        node_name = node.get_name().strip('"')
        if node_name not in ['node', 'edge', 'graph']:  # 跳过默认属性
            label = node.get('label', node_name).strip('"')
            shape = node.get('shape', 'ellipse').strip('"')
            nodes[node_name] = {'label': label, 'shape': shape}
    
    # 提取边
    for edge in graph.get_edges():
        src = edge.get_source().strip('"')
        dst = edge.get_destination().strip('"')
        edges.append((src, dst))
    
    return nodes, edges
```

### 2. 布局算法 (Layout Algorithm)

```python
def layout_nodes(self, nodes: Dict):
    positions = {}
    node_names = list(nodes.keys())
    
    # 网格布局
    cols = min(len(node_names), 4)  # 最多4列
    rows = (len(node_names) + cols - 1) // cols
    
    for i, node_name in enumerate(node_names):
        col = i % cols
        row = i // cols
        x = 5 + col * self.node_spacing_x
        y = 3 + row * self.node_spacing_y
        positions[node_name] = (x, y)
    
    return positions
```

### 3. ASCII绘制 (ASCII Rendering)

#### 节点绘制
```python
# 矩形节点
def draw_box(self, x, y, width, height, text):
    # 绘制边框
    for i in range(width):
        self.set_char(x + i, y, '-')  # 上下边
        self.set_char(x + i, y + height - 1, '-')
    
    for i in range(height):
        self.set_char(x, y + i, '|')  # 左右边
        self.set_char(x + width - 1, y + i, '|')
    
    # 四个角
    self.set_char(x, y, '+')
    self.set_char(x + width - 1, y, '+')
    self.set_char(x, y + height - 1, '+')
    self.set_char(x + width - 1, y + height - 1, '+')

# 圆形节点
def draw_circle(self, x, y, radius, text):
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        px = int(x + radius * math.cos(rad))
        py = int(y + radius * math.sin(rad))
        self.set_char(px, py, 'o')
```

#### 连接线绘制
```python
def draw_arrow(self, x1, y1, x2, y2):
    # 绘制线条
    self.draw_line(x1, y1, x2, y2)
    
    # 添加箭头
    if x2 > x1:
        self.set_char(x2, y2, '>')
    elif x2 < x1:
        self.set_char(x2, y2, '<')
    elif y2 > y1:
        self.set_char(x2, y2, 'v')
    else:
        self.set_char(x2, y2, '^')
```

## 使用示例

### 基本用法

```python
import pydot
from pydot_to_ascii import PydotToASCII

# 创建图形
graph = pydot.Dot(graph_type='digraph')

# 添加节点
graph.add_node(pydot.Node('A', label='Start'))
graph.add_node(pydot.Node('B', label='Process', shape='box'))
graph.add_node(pydot.Node('C', label='End'))

# 添加边
graph.add_edge(pydot.Edge('A', 'B'))
graph.add_edge(pydot.Edge('B', 'C'))

# 转换为ASCII
converter = PydotToASCII()
ascii_graph = converter.convert_to_ascii(graph)
print(ascii_graph)
```

### 预期输出

```
     ooooo           +-------+           ooooo
    o Start o  --->  |Process|  --->   o End o
     ooooo           +-------+           ooooo
```

## 高级功能

### 1. 自定义节点样式

```python
# 支持的节点形状
shapes = {
    'box': 'draw_box',      # 矩形
    'ellipse': 'draw_circle', # 椭圆
    'circle': 'draw_circle',  # 圆形
    'diamond': 'draw_diamond' # 菱形
}
```

### 2. 布局算法选择

```python
# 可选布局算法
layouts = {
    'grid': 'grid_layout',        # 网格布局
    'hierarchical': 'tree_layout', # 层次布局
    'circular': 'circle_layout'    # 环形布局
}
```

### 3. 自定义画布大小

```python
converter = PydotToASCII()
converter.canvas_width = 100   # 画布宽度
converter.canvas_height = 50   # 画布高度
converter.node_spacing_x = 20  # 节点水平间距
converter.node_spacing_y = 10  # 节点垂直间距
```

## 图形遍历方法

### 深度优先遍历 (DFS)

```python
def dfs_traverse(graph, start_node):
    visited = set()
    result = []
    
    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        result.append(node)
        
        # 遍历所有出边
        for edge in graph.get_edges():
            if edge.get_source().strip('"') == node:
                dst = edge.get_destination().strip('"')
                dfs(dst)
    
    dfs(start_node)
    return result
```

### 广度优先遍历 (BFS)

```python
def bfs_traverse(graph, start_node):
    from collections import deque
    
    visited = set()
    queue = deque([start_node])
    result = []
    
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        
        visited.add(node)
        result.append(node)
        
        # 添加所有邻接节点
        for edge in graph.get_edges():
            if edge.get_source().strip('"') == node:
                dst = edge.get_destination().strip('"')
                if dst not in visited:
                    queue.append(dst)
    
    return result
```

### 拓扑排序

```python
def topological_sort(graph):
    # 计算入度
    in_degree = {}
    nodes = [n.get_name().strip('"') for n in graph.get_nodes() 
             if n.get_name().strip('"') not in ['node', 'edge', 'graph']]
    
    for node in nodes:
        in_degree[node] = 0
    
    for edge in graph.get_edges():
        dst = edge.get_destination().strip('"')
        if dst in in_degree:
            in_degree[dst] += 1
    
    # 拓扑排序
    from collections import deque
    queue = deque([node for node, degree in in_degree.items() if degree == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for edge in graph.get_edges():
            if edge.get_source().strip('"') == node:
                dst = edge.get_destination().strip('"')
                if dst in in_degree:
                    in_degree[dst] -= 1
                    if in_degree[dst] == 0:
                        queue.append(dst)
    
    return result
```

## 扩展功能

### 1. 支持子图 (Subgraphs)

```python
def handle_subgraphs(graph):
    subgraphs = graph.get_subgraphs()
    for subgraph in subgraphs:
        # 递归处理子图
        sub_ascii = convert_to_ascii(subgraph)
        # 合并到主图中
```

### 2. 边标签支持

```python
def draw_edge_label(self, x, y, label):
    for i, char in enumerate(label):
        self.set_char(x + i, y, char)
```

### 3. 多种连接线样式

```python
line_styles = {
    'solid': '-',
    'dashed': '.',
    'dotted': ':',
    'bold': '='
}
```

## 性能优化

1. **缓存布局结果** - 避免重复计算
2. **按需绘制** - 只绘制可见区域
3. **内存管理** - 使用稀疏矩阵存储大画布
4. **并行处理** - 多线程处理大型图形

## 故障排除

### 常见问题

1. **节点重叠** - 增加节点间距
2. **连接线交叉** - 使用更好的布局算法
3. **文本截断** - 调整节点大小
4. **画布太小** - 自动调整画布大小

### 调试技巧

```python
# 启用调试模式
converter.debug = True
converter.show_coordinates = True
converter.highlight_connections = True
```