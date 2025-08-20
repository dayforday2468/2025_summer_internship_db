import sqlite3
import shutil
import os


def database_export(input_path, output_path, node_df, link_df, turn_df, linkpoly_df):
    # 원본 DB 복사
    if os.path.exists(output_path):
        os.remove(output_path)
    shutil.copyfile(input_path, output_path)

    with sqlite3.connect(output_path) as conn:
        # 트랜잭션 시작
        cursor = conn.cursor()

        # 기존 데이터 삭제
        for table in ["NODE", "LINK", "TURN", "LINKPOLY"]:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()

        # DataFrame -> 기존 테이블에 삽입
        node_df.to_sql("NODE", conn, if_exists="append", index=False)
        link_df.to_sql("LINK", conn, if_exists="append", index=False)

        # turn 중복 제거
        keys = ["FROMNODENO", "VIANODENO", "TONODENO"]
        dup_mask = turn_df.duplicated(keys, keep="first")
        turn_df = turn_df.loc[~dup_mask].copy()
        turn_df.to_sql("TURN", conn, if_exists="append", index=False)
        linkpoly_df.to_sql("LINKPOLY", conn, if_exists="append", index=False)

    print(f"✅ Exported into {output_path}")
