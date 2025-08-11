import networkx as nx
import sqlite3
from config import NODE_COL, LINK_COL, TURN_COL


residental_type = [9, 10, 13, 14, 17, 18, 21, 22, 25, 26, 29, 30]


def build_graph(cursor):
    G = nx.MultiDiGraph()

    # 노드 정보
    cursor.execute(f"SELECT {','.join(NODE_COL)} FROM NODE")
    for node_id, x, y in cursor.fetchall():
        G.add_node(node_id, x=x, y=y)

    # 링크 정보
    cursor.execute(f"SELECT {','.join(LINK_COL)} FROM LINK")
    for u, v, length, typeno, capprt in cursor.fetchall():
        # capprt=0로 한 방향도로 인식
        if capprt != 0:
            G.add_edge(
                u,
                v,
                length=length * 1000,  # Km->m
                type="residental" if typeno in residental_type else "Non-residental",
            )

    return G


def build_turn(cursor):
    turn = set()

    # turn 쿼리
    cursor.execute(f"SELECT {','.join(TURN_COL)} FROM TURN")

    turn.update((f, v, t) for f, v, t in cursor.fetchall())

    return turn


def database_read(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    G = build_graph(cursor)
    turn = build_turn(cursor)
    print(f"✅ Builds from {db_path}")

    return G, turn
