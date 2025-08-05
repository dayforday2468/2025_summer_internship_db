import os
import sqlite3
import networkx as nx

from database_read import database_read
from database_copy import database_copy
from database_export import database_export


def init_database_files(base_dir, keep_file="map.sqlite3"):
    for file in os.listdir(base_dir):
        if file.endswith(".sqlite3") and file != keep_file:
            full_path = os.path.join(base_dir, file)
            os.remove(full_path)
            print(f"🗑️ Removed: {full_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "map.sqlite3")
    copy_path = os.path.join(script_dir, "copied_map.sqlite3")
    export_path = os.path.join(script_dir, "simplified_map.sqlite3")

    # 초기화
    init_database_files(script_dir)

    # 데이터 베이스 복사
    database_copy(db_path, copy_path)

    # simplification process
    # 1. 그래프 구축
    G, G_tur = database_read(db_path)
    # 2. to be continue

    # 데이터 베이스 저장
    database_export(copy_path, export_path)
