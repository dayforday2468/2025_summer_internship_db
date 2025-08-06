import os
import sqlite3
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

from database_read import database_read
from database_clean import database_clean
from database_export import database_export


def initialization():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(script_dir):
        if file.endswith(".sqlite3") and file != "map.sqlite3":
            full_path = os.path.join(script_dir, file)
            os.remove(full_path)
            print(f"🗑️ Removed: {full_path}")
    print("✅ Initialization Complete!")


def run_pipeline():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "map.sqlite3")
    export_path = os.path.join(script_dir, "simplified_map.sqlite3")

    # 그래프 구축
    G, G_turn = database_read(db_path)

    # # 데이터 베이스 클리닝
    # G, G_turn = database_clean(G, G_turn)

    # 데이터 베이스 저장
    database_export(db_path, export_path, G, G_turn)


if __name__ == "__main__":
    initialization()
    run_pipeline()
