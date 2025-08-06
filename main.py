import os
import sqlite3
import networkx as nx

from database_read import database_read
from database_export import database_export

from parallel_edges import run_parallel_edges
from parallel_edges_view import run_parallel_edges_view


def initialization():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(script_dir):
        if file.endswith(".sqlite3") and file != "map.sqlite3":
            full_path = os.path.join(script_dir, file)
            os.remove(full_path)
            print(f"🗑️ Removed: {full_path}")
    print("✅ Initialization Complete!")


def run_pipeline(max_iter):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "map.sqlite3")
    export_path = os.path.join(script_dir, "simplified_map.sqlite3")

    # 그래프 구축
    G, G_turn = database_read(db_path)

    # # simplification process
    # for i in range(1, max_iter + 1):

    #     # Parallel_edges
    #     run_parallel_edges_view(i, G, G_turn)
    #     G, G_tur = run_parallel_edges(i, G, G_turn)

    # 데이터 베이스 저장
    database_export(db_path, export_path, G, G_turn)


if __name__ == "__main__":
    initialization()
    run_pipeline(1)
