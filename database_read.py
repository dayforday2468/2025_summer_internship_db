import networkx as nx
import sqlite3
from config import NODE_COL, LINK_COL, TURN_COL


def build_node_link_graph(cursor):
    G = nx.MultiDiGraph()

    # 노드 정보
    cursor.execute(f"SELECT {','.join(NODE_COL)} FROM NODE")
    for node_id, x, y, turn_info in cursor.fetchall():
        G.add_node(node_id, x=x, y=y, turn_info=turn_info)

    # 링크 정보
    cursor.execute(f"SELECT {','.join(LINK_COL)} FROM LINK")
    for u, v, length, typeno, capprt in cursor.fetchall():
        G.add_edge(
            u,
            v,
            length=length,
            typeno=typeno,
            capprt=capprt,
        )

    return G


def build_turn_graph(cursor):
    G = nx.DiGraph()

    # 노드 정보 (LINK를 노드로 취급)
    cursor.execute(f"SELECT {','.join(LINK_COL)} FROM LINK")
    for u, v, length, typeno, capprt in cursor.fetchall():
        G.add_node(
            f"{u}_{v}",
            u=u,
            v=v,
            length=length,
            typeno=typeno,
            capprt=capprt,
        )

    # 링크 정보 (TURN을 링크로 취급)
    cursor.execute(f"SELECT {','.join(TURN_COL)} FROM TURN")
    for f, v, t in cursor.fetchall():
        G.add_edge(f"{f}_{v}", f"{v}_{t}", f=f, v=v, t=t)

    return G


def database_read(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    G = build_node_link_graph(cursor)
    G_turn = build_turn_graph(cursor)
    print(f"✅ Builds graphs from {db_path}")

    return G, G_turn
