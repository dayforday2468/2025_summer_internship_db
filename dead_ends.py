import networkx as nx
import matplotlib.pyplot as plt


def __get_dead_ends(G):
    dead_end_nodes = []

    for node in G.nodes():
        # 전/후방향 이웃 합집합
        neighbors = set(G.successors(node)) | set(G.predecessors(node))

        # 진짜 말단: 이웃이 1개뿐
        if len(neighbors) != 1:
            continue

        nbr = next(iter(neighbors))
        lengths = []

        def collect_lengths(u, v):
            if not G.has_edge(u, v):
                return
            data = G.get_edge_data(u, v, default={})
            for attrs in data.values():
                lengths.append(attrs.get("length", 0))

        # 양방향 모두 확인
        collect_lengths(node, nbr)
        collect_lengths(nbr, node)

        max_len = max(lengths) if lengths else 0
        if max_len < 500:  # < 500m
            dead_end_nodes.append(node)

    return dead_end_nodes


def run_dead_ends(G, turn):
    dead_end_nodes = __get_dead_ends(G)
    G.remove_nodes_from(dead_end_nodes)
    turn = {
        t
        for t in turn
        if t[0] in dead_end_nodes or t[1] in dead_end_nodes or t[2] in dead_end_nodes
    }

    return G, turn


def view_dead_ends(G, turn):
    dead_end_nodes = __get_dead_ends(G)

    plt.figure(figsize=(10, 8))

    node_color = ["red" if node in dead_end_nodes else "black" for node in G.nodes()]

    pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}

    nx.draw(
        G=G,
        pos=pos,
        node_size=10,
        node_color=node_color,
        edge_color="gray",
        width=0.5,
        arrows=False,
    )
    plt.title("dead_ends")
    plt.axis("off")
    plt.show()
