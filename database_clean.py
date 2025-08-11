import networkx as nx
import matplotlib.pyplot as plt
import sys

sys.setrecursionlimit(10000)


def strongly_connected_component(G, turn):
    id = 0
    low = {node: -1 for node in G.nodes()}
    on_stack = {node: False for node in G.nodes()}
    node_stack = []
    sccs = []

    def DFS(cur, prev=None):
        nonlocal id
        id += 1
        low[cur] = id
        if not prev:
            node_stack.append(cur)
        on_stack[cur] = True

        parent = low[cur]

        # 다음 노드 후보 생성
        if prev == None:
            candidates = G.successors(cur)
        else:
            candidates = [nxt for nxt in G.successors(cur) if (prev, cur, nxt) in turn]

        for nxt in candidates:
            if low[nxt] == -1:
                node_stack.append(nxt)
                parent = min(parent, DFS(nxt, cur))
            elif on_stack[nxt]:
                parent = min(parent, low[nxt])

        if parent == low[cur]:
            nodes = []
            links = []
            turns = []
            while True:
                node = node_stack.pop()
                on_stack[node] = False
                nodes.append(node)
                if node == cur:
                    break

            for node1, node2 in G.edges():
                if node1 in nodes and node2 in nodes:
                    links.append((node1, node2))

            for fromnode, vianode, tonode in turn:
                if fromnode in nodes and vianode in nodes and tonode in nodes:
                    turns.append((fromnode, vianode, tonode))

            sccs.append({"nodes": nodes, "links": links, "turns": turns})

        return parent

    for node in G.nodes():
        if low[node] == -1:
            DFS(node)

    return sccs


def plot_sccs(sccs, G):
    # 노드 개수 기준으로 내림차순 정렬
    sccs = sorted(sccs, key=lambda scc: len(scc["nodes"]), reverse=True)

    largest_nodes = set(sccs[0]["nodes"])  # 가장 큰 SCC
    other_nodes = set(G.nodes()) - largest_nodes

    pos = {node: (G.nodes[node]["x"], G.nodes[node]["y"]) for node in G.nodes}

    plt.figure(figsize=(10, 8))

    # 모든 edge는 회색
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=False, width=0.5)

    # 가장 큰 SCC → 검은색
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=largest_nodes,
        node_size=10,
        node_color="black",
        label="Largest SCC",
    )

    # 나머지 → 빨간색
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=other_nodes,
        node_size=10,
        node_color="red",
        label="Other SCCs",
    )

    plt.title("Largest SCC", fontsize=14)
    plt.axis("off")
    plt.show()


def largest_cc(G, turn, sccs):
    print("largest_cc")
    print(
        f"Before(#node,#edge,#turn):{len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn):>6}"
    )
    scc = max(sccs, key=lambda x: len(x["nodes"]))

    nodes_to_remove = set(G.nodes()) - set(scc["nodes"])
    G.remove_nodes_from(nodes_to_remove)

    turn = turn & set(scc["turns"])
    print(
        f"After(#node,#edge,#turn): {len(G.nodes()):>6}|{len(G.edges()):>6}|{len(turn):>6}"
    )

    return G, turn


def database_clean(G, turn):
    # largest_cc만 남김.
    sccs = strongly_connected_component(G, turn)
    plot_sccs(sccs, G)
    G, turn = largest_cc(G, turn, sccs)

    print(f"✅ Clean data")

    return G, turn
