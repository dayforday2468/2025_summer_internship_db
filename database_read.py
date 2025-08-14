import networkx as nx
import sqlite3
import pandas as pd

residental_type = [9, 10, 13, 14, 17, 18, 21, 22, 25, 26, 29, 30]


def build_graph(node_df, link_df):
    G = nx.DiGraph()

    # 노드 정보
    for node_id, x, y in node_df[["NO", "XCOORD", "YCOORD"]].itertuples(
        index=False, name=None
    ):
        G.add_node(node_id, x=x, y=y)

    # 링크 정보
    for u, v, length, typeno, capprt in link_df[
        ["FROMNODENO", "TONODENO", "LENGTH", "TYPENO", "CAPPRT"]
    ].itertuples(index=False, name=None):
        # capprt=0인 링크는 거름.
        if capprt != 0:
            G.add_edge(
                u,
                v,
                length=length * 1000,  # Km->m
                type="residental" if typeno in residental_type else "Non-residental",
            )

    return G


def build_table(db_path):
    with sqlite3.connect(db_path) as conn:
        node_df = pd.read_sql("SELECT * FROM NODE", conn)

        # CAPPRT=0인 링크는 거름.
        link_df = pd.read_sql("SELECT * FROM LINK WHERE CAPPRT!=0", conn)
        turn_df = pd.read_sql("SELECT * FROM TURN", conn)
        linkpoly_df = pd.read_sql("SELECT * FROM LINKPOLY", conn)

    return node_df, link_df, turn_df, linkpoly_df


def database_read(db_path):

    node_df, link_df, turn_df, linkpoly_df = build_table(db_path)

    G = build_graph(node_df, link_df)
    print(f"✅ Builds from {db_path}")

    return G, node_df, link_df, turn_df, linkpoly_df
