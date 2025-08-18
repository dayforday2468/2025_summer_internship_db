import networkx as nx
import sqlite3
import pandas as pd

residential_type = [9, 10, 13, 14, 17, 18, 21, 22, 25, 26, 29, 30]


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
                type="residential" if typeno in residential_type else "Non-residential",
            )

    return G


def build_table(db_path):
    with sqlite3.connect(db_path) as conn:
        node_df = pd.read_sql("SELECT * FROM NODE", conn)

        # CAPPRT=0인 링크는 거름.
        link_df = pd.read_sql("SELECT * FROM LINK WHERE CAPPRT!=0", conn)
        turn_df = pd.read_sql("SELECT * FROM TURN", conn)
        linkpoly_df = pd.read_sql("SELECT * FROM LINKPOLY", conn)

        # speed up을 위한 index 재설정
        link_df = link_df.set_index(
            ["FROMNODENO", "TONODENO"], drop=False, verify_integrity=True
        ).sort_index()
        linkpoly_df = linkpoly_df.set_index(
            ["FROMNODENO", "TONODENO"], drop=False
        ).sort_index()

    return node_df, link_df, turn_df, linkpoly_df


def database_read(db_path):

    node_df, link_df, turn_df, linkpoly_df = build_table(db_path)

    G = build_graph(node_df, link_df)
    print(f"✅ Builds from {db_path}")

    return G, node_df, link_df, turn_df, linkpoly_df
