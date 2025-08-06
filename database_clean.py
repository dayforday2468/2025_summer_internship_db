import networkx as nx
import matplotlib as plt
import osmnx as ox


def plot_graph(G, figsize=(8, 6), title=None):
    plt.figure(figsize=figsize)

    # 노드의 위치 추출 (dict 형태: {node: (x, y)})
    pos = {
        node: (data["x"], data["y"])
        for node, data in G.nodes(data=True)
        if "x" in data and "y" in data
    }
    # 노드와 엣지만 시각화
    nx.draw(G, pos, node_size=10, node_color="skyblue", width=1)

    if title:
        plt.title(title)

    plt.axis("off")
    plt.show()


def database_clean(G, G_turn):
    # turn graph의 largest_cc
    largest_cc = max(nx.strongly_connected_components(G_turn), key=len)

    # turn graph의 largest_cc에 포함되지 않은 turn graph의 노드 추출
    links_to_remove = set(G_turn.nodes()) - largest_cc

    # turn graph에서 노드 제거
    G_turn.remove_nodes_from(links_to_remove)

    # turn graph의 largest_cc에 포함되지 않은 node-link graph의 노드 추출
    nodes_to_remove = set()
    for link in links_to_remove:
        node1, node2 = map(int, link.split("_"))
        nodes_to_remove.update([node1, node2])

    # node-link graph에서 노드 제거
    G.remove_nodes_from(nodes_to_remove)

    return G, G_turn
