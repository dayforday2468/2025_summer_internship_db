import os
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

from database_read import database_read
from database_clean import database_clean
from database_export import database_export


from dead_ends import run_dead_ends, view_dead_ends
from self_loops import run_self_loops, view_self_loops
from gridiron import run_gridiron, view_gridiron
from interstitial_nodes import run_interstitial_nodes, view_interstitial_nodes


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
    G, node_df, link_df, turn_df, linkpoly_df = database_read(db_path)

    # 데이터 베이스 클리닝
    G, node_df, link_df, turn_df, linkpoly_df, _ = database_clean(
        G, node_df, link_df, turn_df, linkpoly_df
    )

    # self-loops
    view_self_loops(G)
    G, node_df, link_df, turn_df, linkpoly_df, _ = run_self_loops(
        G, node_df, link_df, turn_df, linkpoly_df
    )

    # gridiron
    view_gridiron(G)
    G, node_df, link_df, turn_df, linkpoly_df, _ = run_gridiron(
        G, node_df, link_df, turn_df, linkpoly_df
    )

    modified = True
    while modified:
        while modified:
            modified = False
            # dead_ends
            view_dead_ends(G)
            G, node_df, link_df, turn_df, linkpoly_df, modified = run_dead_ends(
                G, node_df, link_df, turn_df, linkpoly_df
            )

        # interstitial nodes
        view_interstitial_nodes(G)
        G, node_df, link_df, turn_df, linkpoly_df, modified = run_interstitial_nodes(
            G, node_df, link_df, turn_df, linkpoly_df
        )

    print("✅ Pipeline Complete!")

    # 데이터 베이스 클리닝
    G, node_df, link_df, turn_df, linkpoly_df, _ = database_clean(
        G, node_df, link_df, turn_df, linkpoly_df
    )

    # 데이터 베이스 저장
    database_export(db_path, export_path, node_df, link_df, turn_df, linkpoly_df)


if __name__ == "__main__":
    initialization()
    run_pipeline()
