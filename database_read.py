import networkx as nx
import sqlite3

NODE_COL = ["NO", "XCOORD", "YCOORD"]
LINK_COL = ["NO", "FROMNODENO", "TONODENO", "LENGTH", "TYPENO", "CAPPRT"]
TURN_COL = ["FROMNODENO", "VIANODENO", "TONODENO"]


def build_node_link_graph(cursor):
    G = nx.MultiDiGraph()

    # 노드 정보
    cursor.execute(f"SELECT {','.join(NODE_COL)} FROM NODE")
    for node_id, x, y in cursor.fetchall():
        G.add_node(str(node_id), x=x, y=y)

    # 링크 정보
    cursor.execute(f"SELECT {','.join(LINK_COL)} FROM LINK")
    for link_id, u, v, length, typeno, capprt in cursor.fetchall():
        G.add_edge(
            str(u),
            str(v),
            link_id=str(link_id),
            length=length,
            typeno=typeno,
            capprt=capprt,
        )

    return G


def build_turn_graph(cursor):
    G = nx.DiGraph()

    # 노드 정보 (LINK를 노드로 취급)
    cursor.execute(f"SELECT {','.join(LINK_COL)} FROM LINK")
    for link_id, u, v, length, typeno, capprt in cursor.fetchall():
        G.add_node(
            str(link_id),
            u=u,
            v=v,
            length=length,
            typeno=typeno,
            capprt=capprt,
        )

    # 링크 정보 (TURN을 링크로 취급)
    cursor.execute(f"SELECT {','.join(TURN_COL)} FROM TURN")
    for f, v, t in cursor.fetchall():
        G.add_edge(f"{f}_{v}", f"{v}_{t}")

    return G


def database_read(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    G = build_node_link_graph(cursor)
    G_turn = build_turn_graph(cursor)
    print(f"✅ Builds graphs from {db_path}")

    return G, G_turn
