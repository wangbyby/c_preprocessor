import pytest
from mermaid_to_ascii import Parser, Graph


def test_parser_graph_parsing():
    """
    测试 Parser 是否正确解析 mermaid 的 graph 和 subgraph。
    """
    # 示例输入
    text = """
    graph TD
        A[Node A] --> B[Node B]
        subgraph SubGraph1
            C[Node C] --> D[Node D]
        end
    """

    # 初始化 Parser 并运行解析
    p = Parser()
    try:
        p.parse(text)
    except Exception as e:
        print(f"Parsing failed with exception: {e}")

    # 获取解析结果
    graph_roots = p.graph_roots

    print(f"graph is {graph_roots}")

    # 检查解析结果是否符合预期
    assert len(graph_roots) > 0, "解析后的 graph_roots 应包含至少一个根图"
    root_graph = graph_roots[0]

    # 检查根图的节点和边
    assert len(root_graph.nodes) == 4, "根图应包含 4 个节点"
    assert len(root_graph.edges) == 3, "根图应包含 3 条边"

    # 检查子图
    subgraphs = [child for child in root_graph.children if isinstance(child, Graph)]
    assert len(subgraphs) == 1, "根图应包含 1 个子图"
    subgraph = subgraphs[0]
    assert len(subgraph.nodes) == 2, "子图应包含 2 个节点"
    assert len(subgraph.edges) == 1, "子图应包含 1 条边"


def test_parser_empty_input():
    """
    测试 Parser 处理空输入的情况。
    """
    text = ""
    p = Parser()
    p.parse(text)
    assert len(p.graph_roots) == 0, "空输入应返回空的 graph_roots"


def test_parser_invalid_input():
    """
    测试 Parser 处理无效输入的情况。
    """
    text = "invalid text"
    p = Parser()
    with pytest.raises(ValueError, match="Invalid mermaid syntax"):
        p.parse(text)
