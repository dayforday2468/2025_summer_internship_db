import networkx as nx
import matplotlib.pyplot as plt


def __get_self_loops(G):
    self_loops = []
    for u, v, k in G.edges(keys=True):
        if u == v:
            self_loops.append((u, v, k))

    return self_loops


def run_self_loops(G, turn):
    print("self_loops")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn):>6}"
    )
    self_loops = __get_self_loops(G)
    G.remove_edges_from(self_loops)
    turn = {t for t in turn if not (t[0] == t[1] or t[1] == t[2])}

    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn):>6}"
    )

    return G, turn


def view_self_loops(G):
    self_loops = __get_self_loops(G)

    loops_uv = {(u, v) for u, v, _ in self_loops}

    edge_color = ["red" if (u, v) in loops_uv else "black" for u, v in G.edges()]
    pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}

    plt.figure(figsize=(10, 8))

    nx.draw_networkx_edges(G=G, pos=pos, edge_color=edge_color, width=0.5, arrows=False)
    nx.draw_networkx_nodes(G=G, pos=pos, node_color="black", node_size=10)

    plt.title("self_loops")
    plt.axis("off")
    plt.show()
