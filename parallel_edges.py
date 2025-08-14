import networkx as nx
import matplotlib.pyplot as plt


def __get_parallel_edges(G):
    parallel_edges = []
    for u, v in G.edges():
        if len(G.get_edge_data(u, v)) > 1:
            parallel_edges.append((u, v))

    return parallel_edges


def run_parallel_edges(G, node_df, link_df, turn_df, linkpoly_df):
    print("parallel_edges")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )
    parallel_edges = __get_parallel_edges(G)
    edges_to_remove = []

    for u, v in parallel_edges:
        edge_dict = G.get_edge_data(u, v)
        min_key = min(edge_dict, key=lambda k: edge_dict[k].get("length"))
        for k in edge_dict:
            if k != min_key:
                edges_to_remove.append((u, v, k))

    G.remove_edges_from(edges_to_remove)

    for u, v, _ in edges_to_remove:
        candidates = (link_df["FROMNODENO"] == u) & (link_df["TONODENO"] == v)
        min_index = link_df.loc[candidates, "LENGTH"].idxmin()
        drop_index = link_df.loc[candidates].index.difference([min_index])
        link_df = link_df.drop(index=drop_index)

    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )

    return G, node_df, link_df, turn_df, linkpoly_df


def view_parallel_edges(G):
    parallel_edges = __get_parallel_edges(G)
    edge_color = ["red" if edge in parallel_edges else "gray" for edge in G.edges()]
    pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}

    plt.figure(figsize=(10, 8))

    nx.draw_networkx_edges(G=G, pos=pos, edge_color=edge_color, arrows=False, width=0.5)
    nx.draw_networkx_nodes(G=G, pos=pos, node_color="black", node_size=10)

    plt.title("parallel_edges")
    plt.axis("off")
    plt.show()
