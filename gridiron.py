import networkx as nx
import matplotlib.pyplot as plt


def __get_gridiron(G):
    gridiron = []
    candidate = []
    for node in G.nodes():
        neighbors = list(set(G.successors(node)) | set(G.predecessors(node)))
        if len(neighbors) != 4:
            continue

        incident_edges = list(G.in_edges(node, data=True)) + list(
            G.out_edges(node, data=True)
        )
        lengths = [edata.get("length", 0) for _, _, edata in incident_edges]

        types = [edata.get("type", "residental") for _, _, edata in incident_edges]

        if max(lengths) >= 300:
            continue

        if not all(t == "residental" for t in types):
            continue

        candidate.append(node)

    for node in candidate:
        count = sum(
            1
            for nbr in list(set(G.successors(node)) | set(G.predecessors(node)))
            if nbr in candidate
        )
        if count >= 2:
            gridiron.append(node)

    return gridiron


def run_gridiron(G, turn):
    print("gridiron")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn):>6}"
    )
    gridiron = __get_gridiron(G)
    G.remove_nodes_from(gridiron)
    turn = {
        t
        for t in turn
        if not (t[0] in gridiron or t[1] in gridiron or t[2] in gridiron)
    }

    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn):>6}"
    )

    return G, turn


def view_gridiron(G):
    gridiron = __get_gridiron(G)

    node_color = ["red" if node in gridiron else "black" for node in G.nodes()]
    edge_color = [
        "red" if u in gridiron or v in gridiron else "black" for u, v in G.edges()
    ]

    pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}

    plt.figure(figsize=(10, 8))

    nx.draw_networkx_nodes(G=G, pos=pos, node_color=node_color, node_size=10)
    nx.draw_networkx_edges(G=G, pos=pos, edge_color=edge_color, width=0.5, arrows=False)

    plt.title("gridiron")
    plt.axis("off")
    plt.show()
