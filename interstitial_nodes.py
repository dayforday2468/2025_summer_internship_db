import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString
import pandas as pd
from tqdm import tqdm


def __get_interstitial_nodes(G):
    interstitial_nodes = []

    for node in G.nodes():
        neighbors = list(set(G.successors(node)) | set(G.predecessors(node)))

        if len(neighbors) != 2:
            continue

        u, v = neighbors

        if not (
            G.has_edge(u, node)
            and G.has_edge(node, u)
            and G.has_edge(v, node)
            and G.has_edge(node, v)
        ):
            continue

        interstitial_nodes.append(node)

    return interstitial_nodes


def __delete_link_df(node, u, v, link_df, use_uv, uv_information):

    if not use_uv:
        # 기존 uv_edge 삭제
        u_v_mask = (link_df["FROMNODENO"] == u) & (link_df["TONODENO"] == v)
        v_u_mask = (link_df["FROMNODENO"] == v) & (link_df["TONODENO"] == u)
        drop_mask = u_v_mask | v_u_mask
        link_df = link_df.loc[~drop_mask].copy()

        u_node_mask = (link_df["FROMNODENO"] == u) & (link_df["TONODENO"] == node)
        node_v_mask = (link_df["FROMNODENO"] == node) & (link_df["TONODENO"] == v)
        v_node_mask = (link_df["FROMNODENO"] == v) & (link_df["TONODENO"] == node)
        node_u_mask = (link_df["FROMNODENO"] == node) & (link_df["TONODENO"] == u)

        u_node = link_df.loc[u_node_mask].copy().iloc[0]
        node_v = link_df.loc[node_v_mask].copy().iloc[0]

        total_no = min(u_node["NO"], node_v["NO"])
        total_length = u_node["LENGTH"] + node_v["LENGTH"]
        total_capprt = min(u_node["CAPPRT"], node_v["CAPPRT"])

        # u_v 생성
        uv = u_node.copy()
        uv["NO"] = total_no
        uv["TONODENO"] = v
        uv["LENGTH"] = total_length
        uv["CAPPRT"] = total_capprt

        # v_u 생성
        vu = uv.copy()
        vu["FROMNODENO"], vu["TONODENO"] = uv["TONODENO"], uv["FROMNODENO"]
        vu["UP_DN"] = 1 if uv["UP_DN"] == 0 else 0

        # 기존 u_node_v 엣지 삭제
        drop_mask = u_node_mask | node_v_mask | v_node_mask | node_u_mask
        link_df = link_df.loc[~drop_mask].copy()

        # 새 행 두 개 추가
        link_df = pd.concat([link_df, pd.DataFrame([uv, vu])], ignore_index=True)

    else:
        # 기존 uv_edge 보강
        if "uv" not in uv_information:
            twoside_row = (
                link_df.loc[(link_df["FROMNODENO"] == v) & (link_df["TONODENO"] == u)]
                .iloc[0]
                .copy()
            )
            twoside_row["FROMNODENO"], twoside_row["TONODENO"] = u, v
            twoside_row["UP_DN"] = 1 if twoside_row["UP_DN"] == 0 else 0
        if "vu" not in uv_information:
            twoside_row = (
                link_df.loc[(link_df["FROMNODENO"] == u) & (link_df["TONODENO"] == v)]
                .iloc[0]
                .copy()
            )
            twoside_row["FROMNODENO"], twoside_row["TONODENO"] = v, u
            twoside_row["UP_DN"] = 1 if twoside_row["UP_DN"] == 0 else 0

        u_node_mask = (link_df["FROMNODENO"] == u) & (link_df["TONODENO"] == node)
        node_v_mask = (link_df["FROMNODENO"] == node) & (link_df["TONODENO"] == v)
        v_node_mask = (link_df["FROMNODENO"] == v) & (link_df["TONODENO"] == node)
        node_u_mask = (link_df["FROMNODENO"] == node) & (link_df["TONODENO"] == u)

        # 기존 u_node_v 엣지 삭제
        drop_mask = u_node_mask | node_v_mask | v_node_mask | node_u_mask
        link_df = link_df.loc[~drop_mask].copy()

        if not ("uv" in uv_information and "vu" in uv_information):
            # 기존 uv_edge 보강 추가
            link_df = pd.concat(
                [link_df, pd.DataFrame([twoside_row])], ignore_index=True
            )

    return link_df


def __delete_turn_df(node, u, v, turn_df, use_uv, uv_information):
    # node가 vianode인 turn 제거
    turn_df = turn_df[turn_df["VIANODENO"] != node].copy()

    if use_uv:
        # 기존 node관련 turn 제거
        turn_df = turn_df[
            (turn_df["FROMNODENO"] != node) & (turn_df["TONODENO"] != node)
        ].copy()

        # 보강 기존 uv 엣지 관련 turn 생성
        new_turn = []
        if "uv" not in uv_information:
            xvu_turn = turn_df[
                (turn_df["VIANODENO"] == v) & (turn_df["TONODENO"] == u)
            ].copy()
            uvx_turn = xvu_turn.copy()
            uvx_turn.loc[:, "TONODENO"] = xvu_turn["FROMNODENO"].to_numpy()
            uvx_turn.loc[:, "FROMNODENO"] = u
            new_turn.append(uvx_turn)

            vux_turn = turn_df[
                (turn_df["FROMNODENO"] == v) & (turn_df["VIANODENO"] == u)
            ].copy()
            xuv_turn = vux_turn.copy()
            xuv_turn.loc[:, "TONODENO"] = v
            xuv_turn.loc[:, "FROMNODENO"] = vux_turn["TONODENO"].to_numpy()
            new_turn.append(xuv_turn)

        if "vu" not in uv_information:
            xuv_turn = turn_df[
                (turn_df["VIANODENO"] == u) & (turn_df["TONODENO"] == v)
            ].copy()
            vux_turn = xuv_turn.copy()
            vux_turn.loc[:, "TONODENO"] = xuv_turn["FROMNODENO"].to_numpy()
            vux_turn.loc[:, "FROMNODENO"] = v
            new_turn.append(vux_turn)

            uvx_turn = turn_df[
                (turn_df["FROMNODENO"] == u) & (turn_df["VIANODENO"] == v)
            ].copy()
            xvu_turn = uvx_turn.copy()
            xvu_turn.loc[:, "TONODENO"] = u
            xvu_turn.loc[:, "FROMNODENO"] = uvx_turn["TONODENO"].to_numpy()
            new_turn.append(xvu_turn)

        # 보강 기존 uv 엣지 관련 turn 추가
        turn_df = pd.concat([turn_df] + new_turn, ignore_index=True)

    else:
        # 기존 uv 관련 turn 제거
        if "uv" in uv_information:
            uvx_turn_mask = (turn_df["FROMNODENO"] == u) & (turn_df["VIANODENO"] == v)
            xuv_turn_mask = (turn_df["VIANODENO"] == u) & (turn_df["TONODENO"] == v)
            drop_mask = uvx_turn_mask | xuv_turn_mask
            turn_df = turn_df.loc[~drop_mask].copy()
        if "vu" in uv_information:
            vux_turn_mask = (turn_df["FROMNODENO"] == v) & (turn_df["VIANODENO"] == u)
            xvu_turn_mask = (turn_df["VIANODENO"] == v) & (turn_df["TONODENO"] == u)
            drop_mask = vux_turn_mask | xvu_turn_mask
            turn_df = turn_df.loc[~drop_mask].copy()

        # 기존 node 관련 turn 업데이트
        turn_df.loc[
            (turn_df["VIANODENO"] == u) & (turn_df["TONODENO"] == node), "TONODENO"
        ] = v
        turn_df.loc[
            (turn_df["VIANODENO"] == v) & (turn_df["TONODENO"] == node), "TONODENO"
        ] = u
        turn_df.loc[
            (turn_df["FROMNODENO"] == node) & (turn_df["VIANODENO"] == u), "FROMNODENO"
        ] = v
        turn_df.loc[
            (turn_df["FROMNODENO"] == node) & (turn_df["VIANODENO"] == v), "FROMNODENO"
        ] = u

    return turn_df


def __delete_linkpoly_df(node, u, v, node_df, linkpoly_df, use_uv, uv_information):

    u_node_mask = (linkpoly_df["FROMNODENO"] == u) & (linkpoly_df["TONODENO"] == node)
    node_v_mask = (linkpoly_df["FROMNODENO"] == node) & (linkpoly_df["TONODENO"] == v)
    v_node_mask = (linkpoly_df["FROMNODENO"] == v) & (linkpoly_df["TONODENO"] == node)
    node_u_mask = (linkpoly_df["FROMNODENO"] == node) & (linkpoly_df["TONODENO"] == u)

    u_node = linkpoly_df.loc[u_node_mask].copy()
    node_v = linkpoly_df.loc[node_v_mask].copy()
    v_node = linkpoly_df.loc[v_node_mask].copy()
    node_u = linkpoly_df.loc[node_u_mask].copy()

    if not use_uv:
        # 기존 uv 엣지 삭제
        u_v_mask = (linkpoly_df["FROMNODENO"] == u) & (linkpoly_df["TONODENO"] == v)
        v_u_mask = (linkpoly_df["FROMNODENO"] == v) & (linkpoly_df["TONODENO"] == u)
        drop_mask = u_v_mask | v_u_mask
        linkpoly_df = linkpoly_df.loc[~drop_mask].copy()
        # node 위치정보
        locrow = node_df.loc[
            node_df["NO"] == node, ["XCOORD", "YCOORD", "ZCOORD"]
        ].iloc[0]
        x, y, z = locrow["XCOORD"], locrow["YCOORD"], locrow["ZCOORD"]

        # case 1: u->node + node->v  ->  u->v
        if len(u_node) > 0 or len(node_v) > 0:
            last_index = int(u_node["INDEX"].max()) if len(u_node) > 0 else 0

            if len(u_node) > 0:
                u_node.loc[:, "TONODENO"] = v
            if len(node_v) > 0:
                node_v.loc[:, "FROMNODENO"] = u
                node_v.loc[:, "INDEX"] = node_v["INDEX"] + last_index + 1

            node_row = pd.DataFrame(
                {
                    "FROMNODENO": [u],
                    "TONODENO": [v],
                    "INDEX": [last_index + 1],
                    "XCOORD": [x],
                    "YCOORD": [y],
                    "ZCOORD": [z],
                }
            )

            u_v = pd.concat([u_node, node_row, node_v], ignore_index=True)
            linkpoly_df = linkpoly_df.loc[~(u_node_mask | node_v_mask)].copy()
            linkpoly_df = pd.concat([linkpoly_df, u_v], ignore_index=True)

        # case 2: v->node + node->u  ->  v->u
        elif len(v_node) > 0 or len(node_u) > 0:
            last_index = int(v_node["INDEX"].max()) if len(v_node) > 0 else 0

            if len(v_node) > 0:
                v_node.loc[:, "TONODENO"] = u
            if len(node_u) > 0:
                node_u.loc[:, "FROMNODENO"] = v
                node_u.loc[:, "INDEX"] = node_u["INDEX"] + last_index + 1

            node_row = pd.DataFrame(
                {
                    "FROMNODENO": [v],
                    "TONODENO": [u],
                    "INDEX": [last_index + 1],
                    "XCOORD": [x],
                    "YCOORD": [y],
                    "ZCOORD": [z],
                }
            )

            v_u = pd.concat([v_node, node_row, node_u], ignore_index=True)
            linkpoly_df = linkpoly_df.loc[~(v_node_mask | node_u_mask)].copy()
            linkpoly_df = pd.concat([linkpoly_df, v_u], ignore_index=True)
    else:
        # 기존 node 관련 엣지 삭제
        if len(u_node) > 0 or len(node_v) > 0:
            linkpoly_df = linkpoly_df.loc[~(u_node_mask | node_v_mask)].copy()
        elif len(v_node) > 0 or len(node_u) > 0:
            linkpoly_df = linkpoly_df.loc[~(v_node_mask | node_u_mask)].copy()

    return linkpoly_df


def __delete_interstitial_node(
    G, node, neighbors, node_df, link_df, turn_df, linkpoly_df
):

    if len(neighbors) != 2:
        return G, node_df, link_df, turn_df, linkpoly_df

    u, v = neighbors

    def extract_coords(a, b):
        edge_attrs = G.get_edge_data(a, b)
        if edge_attrs is None:
            # 엣지가 없으면 노드 좌표로 대체
            return [
                (G.nodes[a]["x"], G.nodes[a]["y"]),
                (G.nodes[b]["x"], G.nodes[b]["y"]),
            ]

        geom = edge_attrs.get("geometry")
        if geom is not None and hasattr(geom, "coords"):
            return list(geom.coords)

        # geometry가 없으면 노드 좌표로 대체
        return [(G.nodes[a]["x"], G.nodes[a]["y"]), (G.nodes[b]["x"], G.nodes[b]["y"])]

    total_length = G[u][node]["length"] + G[node][v]["length"]
    total_type = (
        "residental"
        if G[u][node]["type"] == "residental" and G[node][v]["type"] == "residental"
        else "Non-residental"
    )

    use_uv = False
    uv_information = []
    if G.has_edge(u, v):
        uv_information.append("uv")
        if G[u][v]["length"] < total_length:
            use_uv = True

    if G.has_edge(v, u):
        uv_information.append("vu")
        if G[v][u]["length"] < total_length:
            use_uv = True

    if use_uv:
        if "uv" not in uv_information:
            G.add_edge(u, v, length=G[v][u]["length"], type=G[v][u]["type"])

        if "vu" not in uv_information:
            G.add_edge(v, u, length=G[u][v]["length"], type=G[u][v]["type"])
    else:
        if "uv" in uv_information:
            G.remove_edge(u, v)
        if "vu" in uv_information:
            G.remove_edge(v, u)

        # uv 엣지 추가
        coords1 = extract_coords(u, node)
        coords2 = extract_coords(node, v)
        if coords1 and coords2:
            coords = coords1 + coords2[1:]
            G.add_edge(
                u,
                v,
                geometry=LineString(coords),
                length=total_length,
                type=total_type,
            )

        # vu 엣지 추가
        coords1 = extract_coords(v, node)
        coords2 = extract_coords(node, u)
        if coords1 and coords2:
            coords = coords1 + coords2[1:]
            G.add_edge(
                v,
                u,
                geometry=LineString(coords),
                length=total_length,
                type=total_type,
            )

    # G에서 노드 제거
    G.remove_node(node)

    link_df = __delete_link_df(node, u, v, link_df, use_uv, uv_information)
    turn_df = __delete_turn_df(node, u, v, turn_df, use_uv, uv_information)
    linkpoly_df = __delete_linkpoly_df(
        node, u, v, node_df, linkpoly_df, use_uv, uv_information
    )
    node_df = node_df[node_df["NO"] != node]

    return G, node_df, link_df, turn_df, linkpoly_df


def run_interstitial_nodes(G, node_df, link_df, turn_df, linkpoly_df):
    interstitial_nodes = __get_interstitial_nodes(G)

    cnt = 0
    while True:
        removed_nodes = []
        cnt += 1
        print(f"{cnt} iteration")

        for node in tqdm(interstitial_nodes):
            target = False
            neighbors = list(set(G.successors(node)) | set(G.predecessors(node)))
            for nbr in neighbors:
                if nbr not in interstitial_nodes:
                    target = True
            if target:
                G, node_df, link_df, turn_df, linkpoly_df = __delete_interstitial_node(
                    G,
                    node,
                    neighbors,
                    node_df,
                    link_df,
                    turn_df,
                    linkpoly_df,
                )
                removed_nodes.append(node)

        interstitial_nodes = [n for n in interstitial_nodes if n not in removed_nodes]
        if len(removed_nodes) == 0:
            break

    return G, node_df, link_df, turn_df, linkpoly_df


def view_interstitial_nodes(G):
    interstitial_nodes = __get_interstitial_nodes(G)

    pos = {node: (data["x"], data["y"]) for node, data in G.nodes(data=True)}
    node_color = [
        "red" if node in interstitial_nodes else "black" for node in G.nodes()
    ]

    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G=G, pos=pos, node_color=node_color, node_size=10)
    nx.draw_networkx_edges(G=G, pos=pos, edge_color="gray", width=0.5, arrows=False)

    plt.title("interstitial nodes")
    plt.axis("off")
    plt.show()
