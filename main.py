import os
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

from database_read import database_read
from database_clean import database_clean
from database_export import database_export


from dead_ends import run_dead_ends, view_dead_ends
from parallel_edges import run_parallel_edges, view_parallel_edges
from self_loops import run_self_loops, view_self_loops


def plot_graph(G, title=None):
    plt.figure(figsize=(8, 6))

    # 노드의 위치 추출 (dict 형태: {node: (x, y)})
    pos = {
        node: (data["x"], data["y"])
        for node, data in G.nodes(data=True)
        if "x" in data and "y" in data
    }
    # 노드와 엣지만 시각화
    nx.draw(G, pos, node_size=10, node_color="black", width=1, arrows=False)

    if title:
        plt.title(title)

    plt.axis("off")
    plt.show()


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
    G, turn = database_read(db_path)

    # 데이터 베이스 클리닝
    G, turn = database_clean(G, turn)

    # parallel_edges
    view_parallel_edges(G)
    G = run_parallel_edges(G, turn)

    # self_loops
    view_self_loops(G)
    G, turn = run_self_loops(G, turn)

    # dead_ends
    view_dead_ends(G)
    G, turn = run_dead_ends(G, turn)
    print("✅ Pipeline Complete!")

    # 데이터 베이스 저장
    database_export(db_path, export_path, G, turn)


if __name__ == "__main__":
    initialization()
    run_pipeline()
