import sqlite3
import shutil
import os
import networkx as nx
from config import NODE_COL, LINK_COL, TURN_COL


def database_export(input_path, output_path, G, turn):
    # 원본 DB 복사
    if os.path.exists(output_path):
        os.remove(output_path)
    shutil.copyfile(input_path, output_path)

    # 복사본에 연결
    conn_copied = sqlite3.connect(output_path)
    cursor = conn_copied.cursor()

    # 1. NODE 테이블 정리
    valid_node_nos = set(G.nodes())
    cursor.execute(f"SELECT {','.join(NODE_COL)} FROM NODE")
    all_node_nos = {row[0] for row in cursor.fetchall()}
    to_delete_nodes = all_node_nos - valid_node_nos
    print(
        f"original node num: {len(all_node_nos):>6}, simplfied node num:{len(valid_node_nos):>6}"
    )
    for node_no in to_delete_nodes:
        cursor.execute("DELETE FROM NODE WHERE NO=?", (node_no,))

    # 2. LINK 테이블 정리
    valid_link_nos = {(u, v) for u, v in G.edges()}
    cursor.execute(f"SELECT {','.join(LINK_COL)} FROM LINK")
    all_link_nos = {(row[0], row[1]) for row in cursor.fetchall()}
    to_delete_links = all_link_nos - valid_link_nos
    print(
        f"original link num: {len(all_link_nos):>6}, simplified link num: {len(valid_link_nos):>6}"
    )
    for FROMNODENO, TONODENO in to_delete_links:
        cursor.execute(
            "DELETE FROM LINK WHERE FROMNODENO=? AND TONODENO=?", (FROMNODENO, TONODENO)
        )

    # 3. TURN 테이블 정리
    cursor.execute(f"SELECT {','.join(TURN_COL)} FROM TURN")
    all_turn_triples = {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    to_delete_turns = all_turn_triples - turn
    print(
        f"original turn num: {len(all_turn_triples):>6}, simplfied turn num: {len(turn):>6}"
    )
    for f, v, t in to_delete_turns:
        cursor.execute(
            "DELETE FROM TURN WHERE FROMNODENO=? AND VIANODENO=? AND TONODENO=?",
            (f, v, t),
        )

    conn_copied.commit()
    conn_copied.close()
    print(f"✅ Export DB to {output_path}")
