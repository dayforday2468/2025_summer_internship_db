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

        forward = G.has_edge(u, node) and G.has_edge(node, v)
        backward = G.has_edge(v, node) and G.has_edge(node, u)
        if not (forward or backward):
            continue

        interstitial_nodes.append(node)

    return interstitial_nodes


def __delete_link_df(
    node,
    u,
    v,
    link_df,
    node_information,
    uv_information,
    shortest_mode,
    total_length,
):

    to_add = []

    if shortest_mode == "node":
        # 기존 u<->v 삭제
        drop_list = []
        if "forward" in uv_information:
            drop_list.append((u, v))
        if "backward" in uv_information:
            drop_list.append((v, u))
        link_df = link_df.drop(drop_list, errors="ignore")

        # u->node, node->v로 u->v 생성
        if "forward" in node_information:
            u_node = link_df.loc[(u, node)].copy()
            node_v = link_df.loc[(node, v)].copy()

            total_no = min(u_node["NO"], node_v["NO"])
            total_capprt = min(u_node["CAPPRT"], node_v["CAPPRT"])

            uv = u_node.copy()
            uv["NO"] = total_no
            uv["TONODENO"] = v
            uv["LENGTH"] = total_length / 1000
            uv["CAPPRT"] = total_capprt

            to_add.append(uv)

        # v->node, node->u로 v->u 생성
        if "backward" in node_information:
            v_node = link_df.loc[(v, node)].copy()
            node_u = link_df.loc[(node, u)].copy()

            total_no = min(v_node["NO"], node_u["NO"])
            total_capprt = min(v_node["CAPPRT"], node_u["CAPPRT"])

            vu = v_node.copy()
            vu["NO"] = total_no
            vu["TONODENO"] = u
            vu["LENGTH"] = total_length / 1000
            vu["CAPPRT"] = total_capprt

            to_add.append(vu)

        # v->node, node->u로 u->v 생성 (반대 방향 생성)
        if "forward" in uv_information and "forward" not in node_information:
            v_node = link_df.loc[(v, node)].copy()
            node_u = link_df.loc[(node, u)].copy()

            total_no = min(v_node["NO"], node_u["NO"])
            total_capprt = min(v_node["CAPPRT"], node_u["CAPPRT"])

            uv = v_node.copy()
            uv["NO"] = total_no
            uv["FROMNODENO"], uv["TONODENO"] = u, v
            uv["LENGTH"] = total_length / 1000
            uv["CAPPRT"] = total_capprt
            uv["UP_DN"] = 1 if uv["UP_DN"] == 0 else 0

            to_add.append(uv)

        # u->node, node->v로 v->u 생성 (반대 방향 생성)
        if "backward" in uv_information and "backward" not in node_information:
            u_node = link_df.loc[(u, node)].copy()
            node_v = link_df.loc[(node, v)].copy()

            total_no = min(u_node["NO"], node_v["NO"])
            total_capprt = min(u_node["CAPPRT"], node_v["CAPPRT"])

            vu = u_node.copy()
            vu["NO"] = total_no
            vu["FROMNODENO"], vu["TONODENO"] = v, u
            vu["LENGTH"] = total_length / 1000
            vu["CAPPRT"] = total_capprt
            vu["UP_DN"] = 1 if vu["UP_DN"] == 0 else 0

            to_add.append(vu)

    elif shortest_mode == "uv":

        # u->node, node->v 있다면 u->v 보강 (v->u를 복사하여)
        if "forward" in node_information and "forward" not in uv_information:
            uv = link_df.loc[(v, u)].copy()
            uv["FROMNODENO"], uv["TONODENO"] = u, v
            uv["UP_DN"] = 1 if uv["UP_DN"] == 0 else 0

            to_add.append(uv)

        # v->node, node->u 있다면 v->u 보강 (u->v를 복사하여)
        if "backward" in node_information and "backward" not in uv_information:
            vu = link_df.loc[(u, v)].copy()
            vu["FROMNODENO"], vu["TONODENO"] = v, u
            vu["UP_DN"] = 1 if vu["UP_DN"] == 0 else 0

            to_add.append(vu)

    # 기존 u<->node<->v 삭제
    link_df = link_df.drop(
        [(u, node), (node, v), (v, node), (node, u)], errors="ignore"
    )

    # 새 엣지 추가
    if to_add:
        to_add = pd.DataFrame(to_add).set_index(["FROMNODENO", "TONODENO"], drop=False)
        link_df = pd.concat([link_df, to_add])

    return link_df


def __delete_turn_df(
    node, u, v, turn_df, node_information, uv_information, shortest_mode
):
    # node가 vianode인 turn 제거
    turn_df = turn_df[turn_df["VIANODENO"] != node].copy()

    if shortest_mode == "node":
        # 기존 u<->v 엣지 관련 turn 제거
        if "forward" in uv_information:
            uvx_turn_mask = (turn_df["FROMNODENO"] == u) & (turn_df["VIANODENO"] == v)
            xuv_turn_mask = (turn_df["VIANODENO"] == u) & (turn_df["TONODENO"] == v)
            drop_mask = uvx_turn_mask | xuv_turn_mask
            turn_df = turn_df.loc[~drop_mask].copy()

        if "backward" in uv_information:
            vux_turn_mask = (turn_df["FROMNODENO"] == v) & (turn_df["VIANODENO"] == u)
            xvu_turn_mask = (turn_df["VIANODENO"] == v) & (turn_df["TONODENO"] == u)
            drop_mask = vux_turn_mask | xvu_turn_mask
            turn_df = turn_df.loc[~drop_mask].copy()

        # 기존 node 관련 turn 업데이트
        if "forward" in node_information:
            turn_df.loc[
                (turn_df["VIANODENO"] == u) & (turn_df["TONODENO"] == node), "TONODENO"
            ] = v
            turn_df.loc[
                (turn_df["FROMNODENO"] == node) & (turn_df["VIANODENO"] == v),
                "FROMNODENO",
            ] = u

        if "backward" in node_information:
            turn_df.loc[
                (turn_df["VIANODENO"] == v) & (turn_df["TONODENO"] == node), "TONODENO"
            ] = u
            turn_df.loc[
                (turn_df["FROMNODENO"] == node) & (turn_df["VIANODENO"] == u),
                "FROMNODENO",
            ] = v

    elif shortest_mode == "uv":
        # 기존 node관련 turn 제거
        turn_df = turn_df[
            (turn_df["FROMNODENO"] != node) & (turn_df["TONODENO"] != node)
        ].copy()

        # 기존 u<->v 엣지 보강에 따른 turn 추가
        new_turn = []
        if "forward" in node_information and "forward" not in uv_information:
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

        if "backward" in node_information and "backward" not in uv_information:
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

        # 보강 시, 추가
        if new_turn:
            turn_df = pd.concat([turn_df] + new_turn, ignore_index=True)

    return turn_df


def __delete_linkpoly_df(
    node, u, v, node_df, linkpoly_df, uv_information, shortest_mode
):

    def _safe_slice(df, key):
        return df.loc[[key]].copy() if key in df.index else df.iloc[0:0].copy()

    u_node = _safe_slice(linkpoly_df, (u, node))
    node_v = _safe_slice(linkpoly_df, (node, v))
    v_node = _safe_slice(linkpoly_df, (v, node))
    node_u = _safe_slice(linkpoly_df, (node, u))

    if shortest_mode == "node":
        # 기존 uv 엣지 삭제
        drop_list = []
        if "forward" in uv_information:
            drop_list.append((u, v))
        if "backward" in uv_information:
            drop_list.append((v, u))
        linkpoly_df = linkpoly_df.drop(drop_list, errors="ignore")

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

            u_v = pd.concat([u_node, node_row, node_v]).set_index(
                ["FROMNODENO", "TONODENO"], drop=False
            )
            linkpoly_df = linkpoly_df.drop([(u, node), (node, v)], errors="ignore")
            linkpoly_df = pd.concat([linkpoly_df, u_v])
            linkpoly_df.sort_index(inplace=True)

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

            v_u = pd.concat([v_node, node_row, node_u]).set_index(
                ["FROMNODENO", "TONODENO"], drop=False
            )
            linkpoly_df = linkpoly_df.drop([(v, node), (node, u)], errors="ignore")
            linkpoly_df = pd.concat([linkpoly_df, v_u])
            linkpoly_df.sort_index(inplace=True)

    elif shortest_mode == "uv":
        # 기존 node 관련 엣지 삭제
        if len(u_node) > 0 or len(node_v) > 0:
            linkpoly_df = linkpoly_df.drop([(u, node), (node, v)], errors="ignore")
        elif len(v_node) > 0 or len(node_u) > 0:
            linkpoly_df = linkpoly_df.drop([(v, node), (node, u)], errors="ignore")

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

    node_information = []
    uv_information = []
    lengths = {}
    if G.has_edge(u, node) and G.has_edge(node, v):
        node_information.append("forward")
        lengths["forward_node"] = G[u][node]["length"] + G[node][v]["length"]
    if G.has_edge(v, node) and G.has_edge(node, u):
        node_information.append("backward")
        lengths["backward_node"] = G[v][node]["length"] + G[node][u]["length"]
    if G.has_edge(u, v):
        uv_information.append("forward")
        lengths["forward_uv"] = G[u][v]["length"]
    if G.has_edge(v, u):
        uv_information.append("backward")
        lengths["backward_uv"] = G[v][u]["length"]

    shortest, total_length = min(lengths.items(), key=lambda x: x[1])
    shortest_direction, shortest_mode = shortest.split("_")

    if shortest_mode == "node":
        # 원본 uv 엣지 제거
        if "forward" in uv_information:
            G.remove_edge(u, v)
        if "backward" in uv_information:
            G.remove_edge(v, u)

        if "forward" in node_information:
            # u->node, node->v로 u->v 생성
            coords1 = extract_coords(u, node)
            coords2 = extract_coords(node, v)
            coords = coords1 + coords2[1:]
            total_type = (
                "residential"
                if G[u][node]["type"] == "residential"
                and G[node][v]["type"] == "residential"
                else "Non-residential"
            )
            G.add_edge(
                u,
                v,
                geometry=LineString(coords),
                length=total_length,
                type=total_type,
            )

        if "backward" in node_information:
            # v->node, node->u로 v->u 생성
            coords1 = extract_coords(v, node)
            coords2 = extract_coords(node, u)
            coords = coords1 + coords2[1:]
            total_type = (
                "residential"
                if G[v][node]["type"] == "residential"
                and G[node][u]["type"] == "residential"
                else "Non-residential"
            )
            G.add_edge(
                v,
                u,
                geometry=LineString(coords),
                length=total_length,
                type=total_type,
            )

        if "forward" in uv_information and "forward" not in node_information:
            # v->node, node->u로 u->v 생성 (반대 방향 복사 생성)
            coords1 = extract_coords(v, node)
            coords2 = extract_coords(node, u)
            coords = list(reversed(coords1 + coords2[1:]))
            total_type = (
                "residential"
                if G[v][node]["type"] == "residential"
                and G[node][u]["type"] == "residential"
                else "Non-residential"
            )
            G.add_edge(
                u,
                v,
                geometry=LineString(coords),
                length=total_length,
                type=total_type,
            )

        if "backward" in uv_information and "backward" not in node_information:
            # u->node, node->v로 v->u 생성 (반대 방향 복사 생성)
            coords1 = extract_coords(u, node)
            coords2 = extract_coords(node, v)
            coords = list(reversed(coords1 + coords2[1:]))
            total_type = (
                "residential"
                if G[u][node]["type"] == "residential"
                and G[node][v]["type"] == "residential"
                else "Non-residential"
            )
            G.add_edge(
                v,
                u,
                geometry=LineString(coords),
                length=total_length,
                type=total_type,
            )

    elif shortest_mode == "uv":
        # 원본 node 관련 엣지 제거
        if "forward" in node_information:
            G.remove_edge(u, node)
            G.remove_edge(node, v)
        if "backward" in node_information:
            G.remove_edge(v, node)
            G.remove_edge(node, u)

        if "forward" in node_information and "forward" not in uv_information:
            # uv forward 생성
            G.add_edge(u, v, length=G[v][u]["length"], type=G[v][u]["type"])

        if "backward" in node_information and "backward" not in uv_information:
            # uv backward 생성
            G.add_edge(v, u, length=G[u][v]["length"], type=G[u][v]["type"])

    # G에서 노드 제거
    G.remove_node(node)

    link_df = __delete_link_df(
        node,
        u,
        v,
        link_df,
        node_information,
        uv_information,
        shortest_mode,
        total_length,
    )
    turn_df = __delete_turn_df(
        node,
        u,
        v,
        turn_df,
        node_information,
        uv_information,
        shortest_mode,
    )
    linkpoly_df = __delete_linkpoly_df(
        node,
        u,
        v,
        node_df,
        linkpoly_df,
        uv_information,
        shortest_mode,
    )
    node_df = node_df[node_df["NO"] != node]

    return G, node_df, link_df, turn_df, linkpoly_df


def run_interstitial_nodes(G, node_df, link_df, turn_df, linkpoly_df):
    modified = False
    interstitial_nodes = __get_interstitial_nodes(G)
    if len(interstitial_nodes) != 0:
        modified = True

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

    return G, node_df, link_df, turn_df, linkpoly_df, modified


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
