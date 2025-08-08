import networkx as nx
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.cm as cm
import osmnx as ox
import sys

sys.setrecursionlimit(10000)


def isolated_nodes(G, turn):
    print("Isolated_nodes")
    print(f"Before(#node,#edge,#turn):{len(G.nodes())}|{len(G.edges())}|{len(turn)}")
    # G에서 isolated nodes 찾기
    nodes_to_remove_G = [node for node in G.nodes() if G.degree(node) == 0]

    # G에서 isolated nodes 삭제
    G.remove_nodes_from(nodes_to_remove_G)

    # 삭제된 노드와 연관된 turn 삭제
    turn = {
        t
        for t in turn
        if not (
            t[0] in nodes_to_remove_G
            or t[1] in nodes_to_remove_G
            or t[2] in nodes_to_remove_G
        )
    }

    print(f"After(#node,#edge,#turn): {len(G.nodes())}|{len(G.edges())}|{len(turn)}")

    return G, turn


def strongly_connected_component(G, turn):
    id = 0
    low = {node: -1 for node in G.nodes()}
    on_stack = {node: False for node in G.nodes()}
    node_stack = []  # (node, how) 형식
    sccs = []

    def DFS(cur, prev=None):
        nonlocal id
        id += 1
        low[cur] = id
        if not prev:
            node_stack.append((cur, []))
        on_stack[cur] = True

        parent = low[cur]

        # 다음 노드 후보 생성
        if prev == None:
            candidates = G.successors(cur)
            use_turn = False
        else:
            candidates = [nxt for nxt in G.successors(cur) if (prev, cur, nxt) in turn]
            use_turn = True

        for nxt in candidates:
            if low[nxt] == -1:
                way = (prev, cur, nxt) if use_turn else (cur, nxt)
                node_stack.append((nxt, [way]))
                parent = min(parent, DFS(nxt, cur))
            elif on_stack[nxt]:
                way = (prev, cur, nxt) if use_turn else (cur, nxt)
                for node, how in node_stack:
                    if node == nxt:
                        how.append(way)
                parent = min(parent, low[nxt])

        if parent == low[cur]:
            nodes = []
            links = []
            turns = []
            while True:
                node, how = node_stack.pop()
                on_stack[node] = False
                nodes.append(node)
                if len(how) != 0:
                    for way in how:
                        if len(way) == 2:
                            links.append(way)
                        elif len(way) == 3:
                            links.append(way[1:])
                            turns.append(way)
                if node == cur:
                    break
            sccs.append({"nodes": nodes, "links": links, "turns": turns})

        return parent

    for node in G.nodes():
        if low[node] == -1:
            DFS(node)

    return sccs


def plot_sccs(sccs, G, max_plots=20):
    sccs = sorted(sccs, key=lambda scc: len(scc["nodes"]), reverse=True)

    num_plots = min(len(sccs), max_plots)

    # 색상 정의 (tab20에서 num_plots개 색 추출)
    cmap = cm.get_cmap("tab20", num_plots)

    # 전체 위치 설정
    pos = {node: (G.nodes[node]["x"], G.nodes[node]["y"]) for node in G.nodes}

    plt.figure(figsize=(10, 8))

    # 모든 edge는 회색으로 그리기
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=False, width=0.5)

    # SCC별 노드 색상만 다르게 그리기
    for i in range(num_plots):
        scc_nodes = sccs[i]["nodes"]
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=scc_nodes,
            node_size=10,
            node_color=[cmap(i)],
            label=f"SCC {i+1}",
        )

    plt.title(f"Top {num_plots} Strongly Connected Components", fontsize=14)
    plt.axis("off")
    plt.legend(loc="upper right", markerscale=2)
    plt.show()


def largest_cc(G, turn, sccs):
    print("largest_cc")
    print(f"Before(#node,#edge,#turn):{len(G.nodes())}|{len(G.edges())}|{len(turn)}")
    scc = max(sccs, key=lambda x: len(x["nodes"]))

    nodes_to_remove = set(G.nodes()) - set(scc["nodes"])
    G.remove_nodes_from(nodes_to_remove)

    turn = turn & set(scc["turns"])
    print(f"After(#node,#edge,#turn): {len(G.nodes())}|{len(G.edges())}|{len(turn)}")

    return G, turn


def database_clean(G, turn):
    # isolated_nodes를 제거
    G, turn = isolated_nodes(G, turn)

    # largest_cc만 남김.
    sccs = strongly_connected_component(G, turn)
    plot_sccs(sccs, G)
    G, turn = largest_cc(G, turn, sccs)

    print(f"✅ Clean data")

    return G, turn
