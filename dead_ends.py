import networkx as nx
import matplotlib.pyplot as plt


def __get_dead_ends_thres(G):
    lengths = [data.get("length", 0) for _, _, data in G.edges(data=True)]
    lengths.sort()
    return lengths[len(lengths) // 2]


def __get_dead_ends(G):
    dead_end_nodes = []
    thres = __get_dead_ends_thres(G)

    for node in G.nodes():
        # 전/후방향 이웃 합집합
        neighbors = set(G.successors(node)) | set(G.predecessors(node))
        if len(neighbors) != 1:
            continue

        nbr = next(iter(neighbors))
        lengths = []

        def collect_length(u, v):
            if G.has_edge(u, v):
                attrs = G.get_edge_data(u, v)  # DiGraph: 바로 속성 dict
                lengths.append(attrs.get("length", 0))

        # 양방향 확인
        collect_length(node, nbr)
        collect_length(nbr, node)

        max_len = max(lengths) if lengths else 0
        if max_len < thres:  # < 500m
            dead_end_nodes.append(node)

    return dead_end_nodes


def run_dead_ends(G, node_df, link_df, turn_df, linkpoly_df):
    modified = False

    print("dead_ends")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )
    dead_end_nodes = __get_dead_ends(G)
    if len(dead_end_nodes) != 0:
        modified = True
    G.remove_nodes_from(dead_end_nodes)

    dead_end_nodes = set(dead_end_nodes)

    node_mask = node_df["NO"].isin(dead_end_nodes)
    node_df = node_df[~node_mask]

    link_mask = link_df["FROMNODENO"].isin(dead_end_nodes) | link_df["TONODENO"].isin(
        dead_end_nodes
    )
    link_df = link_df[~link_mask]

    turn_mask = (
        turn_df["FROMNODENO"].isin(dead_end_nodes)
        | turn_df["VIANODENO"].isin(dead_end_nodes)
        | turn_df["TONODENO"].isin(dead_end_nodes)
    )
    turn_df = turn_df[~turn_mask]

    linkpoly_mask = linkpoly_df["FROMNODENO"].isin(dead_end_nodes) | linkpoly_df[
        "TONODENO"
    ].isin(dead_end_nodes)
    linkpoly_df = linkpoly_df[~linkpoly_mask]

    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )

    return G, node_df, link_df, turn_df, linkpoly_df, modified


def view_dead_ends(G):
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
