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

        types = [edata.get("type", "residential") for _, _, edata in incident_edges]

        if max(lengths) >= 300:
            continue

        if not all(t == "residential" for t in types):
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


def run_gridiron(G, node_df, link_df, turn_df, linkpoly_df):
    modified = False

    print("gridiron")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )
    gridiron = __get_gridiron(G)
    if len(gridiron) != 0:
        modified = True
    G.remove_nodes_from(gridiron)

    gridiron = set(gridiron)

    node_mask = node_df["NO"].isin(gridiron)
    node_df = node_df[~node_mask]

    link_mask = link_df["FROMNODENO"].isin(gridiron) | link_df["TONODENO"].isin(
        gridiron
    )
    link_df = link_df[~link_mask]

    turn_mask = (
        turn_df["FROMNODENO"].isin(gridiron)
        | turn_df["VIANODENO"].isin(gridiron)
        | turn_df["TONODENO"].isin(gridiron)
    )
    turn_df = turn_df[~turn_mask]

    linkpoly_mask = linkpoly_df["FROMNODENO"].isin(gridiron) | linkpoly_df[
        "TONODENO"
    ].isin(gridiron)
    linkpoly_df = linkpoly_df[~linkpoly_mask]

    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )

    return G, node_df, link_df, turn_df, linkpoly_df, modified


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
