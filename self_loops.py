import networkx as nx
import matplotlib.pyplot as plt


def __get_self_loops(G):
    self_loops = []
    for u, v in G.edges():
        if u == v:
            self_loops.append((u, v))

    return self_loops


def run_self_loops(G, node_df, link_df, turn_df, linkpoly_df):
    modified = False
    print("self_loops")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )
    self_loops = __get_self_loops(G)
    if len(self_loops) != 0:
        modified = True
    G.remove_edges_from(self_loops)

    link_mask = link_df["FROMNODENO"].eq(link_df["TONODENO"])
    turn_mask = turn_df["FROMNODENO"].eq(turn_df["VIANODENO"]) | turn_df[
        "VIANODENO"
    ].eq(turn_df["TONODENO"])
    linkpoly_mask = linkpoly_df["FROMNODENO"].eq(linkpoly_df["TONODENO"])

    link_df = link_df.loc[~link_mask].copy()
    turn_df = turn_df.loc[~turn_mask].copy()
    linkpoly_df = linkpoly_df.loc[~linkpoly_mask].copy()

    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn_df):>6}"
    )

    return G, node_df, link_df, turn_df, linkpoly_df, modified


def view_self_loops(G):
    self_loops = __get_self_loops(G)

    edge_color = ["red" if (u, v) in self_loops else "black" for u, v in G.edges()]
    pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}

    plt.figure(figsize=(10, 8))

    nx.draw_networkx_edges(G=G, pos=pos, edge_color=edge_color, width=0.5, arrows=False)
    nx.draw_networkx_nodes(G=G, pos=pos, node_color="black", node_size=10)

    plt.title("self_loops")
    plt.axis("off")
    plt.show()
