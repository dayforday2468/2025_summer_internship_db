import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import math
import sys
from pyproj import Transformer, Geod

sys.setrecursionlimit(100000)


def load_path_links_csv(path):
    df = pd.read_csv(path)

    # LINKNO, FROMNODENO, TONODENO 컬럼들을 한 칸 위로 올림
    shift_up_column = ["INDEX", "LINKNO", "FROMNODENO", "TONODENO"]
    df[shift_up_column] = df[shift_up_column].shift(-1)

    # 빈 행 제거
    empty_mask = df.isna().all(axis=1)
    df = df.loc[~empty_mask].copy()

    # ORIGZONENO, DESTZONENO, PATHINDEX 컬럼들을 위의 값으로 채움.
    ffill_column = ["ORIGZONENO", "DESTZONENO", "PATHINDEX"]
    df[ffill_column] = df[ffill_column].ffill()

    # PATHINDEX 컬럼 제거
    df.drop(columns=["PATHINDEX"], inplace=True)

    # int 형변환
    df = df.astype("int64")

    return df


def make_trajectory(path_link_df, db_path):
    # 1) 좌표 테이블 로드
    with sqlite3.connect(db_path) as conn:
        node_pos = pd.read_sql("SELECT NO, XCOORD, YCOORD FROM NODE", conn)
        linkpoly = pd.read_sql(
            "SELECT FROMNODENO, TONODENO, [INDEX] AS IDX, XCOORD, YCOORD FROM LINKPOLY",
            conn,
        )

    # 2) 노드번호 -> (x,y) 매핑
    pos_map = node_pos.set_index("NO")[["XCOORD", "YCOORD"]].to_dict("index")

    # 3) (FROM,TO) -> [(x,y), ...] 매핑 (INDEX로 정렬)
    linkpoly = linkpoly.sort_values(["FROMNODENO", "TONODENO", "IDX"])
    poly_map = {
        (fn, tn): list(
            zip(
                g["XCOORD"],
                g["YCOORD"],
            )
        )
        for (fn, tn), g in linkpoly.groupby(["FROMNODENO", "TONODENO"], sort=False)
    }

    def get_poly_sequence(f, t):
        pts = poly_map.get((f, t))
        if pts:  # 올바른 방향이 있으면 그대로
            return pts
        pts_rev = poly_map.get((t, f))
        if pts_rev:  # 반대방향 있으면 뒤집어서 사용
            return list(reversed(pts_rev))
        return []

    traj = {}

    # 4) OD별로 링크 순서(INDEX)대로 좌표 궤적 구성
    for (oz, dz), g in path_link_df.groupby(["ORIGZONENO", "DESTZONENO"], sort=False):
        g = g.sort_values("INDEX")

        coords = []

        # 시작점: 첫 링크의 FROM 노드 좌표
        f0 = int(g.iloc[0]["FROMNODENO"])
        pf = pos_map.get(f0)
        coords.append((pf["XCOORD"], pf["YCOORD"]))

        # 각 링크마다: LINKPOLY 점들 + TO 노드 좌표
        for f, t in zip(g["FROMNODENO"].to_numpy(), g["TONODENO"].to_numpy()):
            # LINKPOLY 중간점들
            for pt in get_poly_sequence(f, t):
                coords.append(pt)

            # 링크 끝점(TO 노드)
            pt_to = pos_map.get(t)
            coords.append((pt_to["XCOORD"], pt_to["YCOORD"]))

        traj[(int(oz), int(dz))] = coords

    return traj


def plot_trajectories(original_traj, simplified_traj, key):
    def _plot(coords, label):
        xs, ys = zip(*coords)
        xs = np.asarray(xs, dtype=float)
        ys = np.asarray(ys, dtype=float)
        plt.plot(xs, ys, ls="-", lw=2, label=label)
        plt.scatter([xs[0]], [ys[0]], s=30, marker="o", color="black")  # 시작점
        if len(xs) > 2:
            plt.scatter(xs[1:-1], ys[1:-1], s=15, color="gray")  # 중간점
        plt.scatter([xs[-1]], [ys[-1]], s=30, marker="s", color="red")  # 도착점

    plt.figure(figsize=(8, 7))

    original_coords = original_traj[key]
    simplified_coords = simplified_traj[key]
    _plot(original_coords, "origianl")
    _plot(simplified_coords, "simplified")

    plt.legend()
    plt.title(f"trajectory comparison: {key}")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()


def _calculate_dist(coord1, coord2):
    # lazy-init (한 번만 생성)
    if not hasattr(_calculate_dist, "_init"):
        SRC_CRS = "EPSG:5178"  # gcs_korean_datum_1985 https://epsg.io/5178
        _calculate_dist._tf = Transformer.from_crs(SRC_CRS, "EPSG:4326", always_xy=True)
        _calculate_dist._geod = Geod(ellps="WGS84")
        _calculate_dist._init = True

    x1, y1 = coord1
    x2, y2 = coord2
    lon1, lat1 = _calculate_dist._tf.transform(x1, y1)
    lon2, lat2 = _calculate_dist._tf.transform(x2, y2)
    _, _, d_m = _calculate_dist._geod.inv(lon1, lat1, lon2, lat2)
    return d_m / 1000.0  # km


def calculate_DTW(original_traj, simplified_traj, key):
    original_coords = original_traj[key]
    simplified_coords = simplified_traj[key]
    n, m = len(original_coords), len(simplified_coords)

    dist = {}
    for i in range(n):
        for j in range(m):
            dist[(i, j)] = _calculate_dist(original_coords[i], simplified_coords[j])

    DTW_TABLE = {}

    def DTW(i, j):
        if i == n:
            if j == m:
                DTW_TABLE[(i, j)] = 0
                return 0
            else:
                DTW_TABLE[(i, j)] = math.inf
                return math.inf
        elif j == m:
            DTW_TABLE[(i, j)] = math.inf
            return math.inf
        elif (i, j) in DTW_TABLE.keys():
            return DTW_TABLE[(i, j)]

        value = dist[(i, j)] ** 2 + min(DTW(i + 1, j + 1), DTW(i + 1, j), DTW(i, j + 1))
        DTW_TABLE[(i, j)] = value

        return value

    return math.sqrt(DTW(0, 0) / max(n, m))


def calculate_DFD(original_traj, simplified_traj, key):
    original_coords = original_traj[key]
    simplified_coords = simplified_traj[key]
    n, m = len(original_coords), len(simplified_coords)

    dist = {}
    for i in range(n):
        for j in range(m):
            dist[(i, j)] = _calculate_dist(original_coords[i], simplified_coords[j])

    DFD_TABLE = {}

    def DFD(i, j):
        if i == n:
            if j == m:
                DFD_TABLE[(i, j)] = 0
                return 0
            else:
                DFD_TABLE[(i, j)] = math.inf
                return math.inf
        elif j == m:
            DFD_TABLE[(i, j)] = math.inf
            return math.inf
        elif (i, j) in DFD_TABLE.keys():
            return DFD_TABLE[(i, j)]

        value = max(dist[(i, j)], min(DFD(i + 1, j + 1), DFD(i + 1, j), DFD(i, j + 1)))
        DFD_TABLE[(i, j)] = value
        return value

    return DFD(0, 0)


def trajectory_similiarity():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_db = os.path.join(script_dir, "map.sqlite3")
    simplified_db = os.path.join(script_dir, "simplified_map.sqlite3")
    data_dir = os.path.join(script_dir, "pathdata")
    original_path_link = os.path.join(data_dir, "original_path_links.csv")
    simplified_path_link = os.path.join(data_dir, "simplified_path_links.csv")

    # CSV 로드
    original_link_df = load_path_links_csv(original_path_link)
    simplified_link_df = load_path_links_csv(simplified_path_link)

    # trajectory dic 생성
    original_traj = make_trajectory(original_link_df, original_db)
    simplified_traj = make_trajectory(simplified_link_df, simplified_db)

    for key in original_traj.keys():
        print(calculate_DFD(original_traj, simplified_traj, key))
        print(calculate_DTW(original_traj, simplified_traj, key))
        plot_trajectories(original_traj, simplified_traj, key)


if __name__ == "__main__":
    trajectory_similiarity()
