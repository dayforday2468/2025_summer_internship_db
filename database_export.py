import sqlite3
import shutil
import os


def drop_column(cursor, table_name, exclude_col="IS_EXIST"):
    # 1. 전체 컬럼 목록 가져오기
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    all_columns = [col[1] for col in columns_info]

    # 2. 제외할 컬럼 제거
    filtered_columns = [col for col in all_columns if col != exclude_col]

    # 3. 열 이름을 전부 "으로 감싸기
    quoted_columns = [f'"{col}"' for col in filtered_columns]
    columns_str = ", ".join(quoted_columns)

    # 4. 새 테이블 생성
    cursor.execute(
        f"""
        CREATE TABLE {table_name}_NEW AS
        SELECT {columns_str}
        FROM {table_name}
        """
    )

    # 5. 기존 테이블 삭제 후 이름 변경
    cursor.execute(f"DROP TABLE {table_name}")
    cursor.execute(f"ALTER TABLE {table_name}_NEW RENAME TO {table_name}")


def database_export(input_path, output_path):
    # 원본 DB 복사
    if os.path.exists(output_path):
        os.remove(output_path)
    shutil.copyfile(input_path, output_path)

    # 복사본에 연결
    conn_copied = sqlite3.connect(output_path)
    copied_cursor = conn_copied.cursor()

    drop_column(copied_cursor, "NODE")
    drop_column(copied_cursor, "LINK")
    drop_column(copied_cursor, "TURN")

    conn_copied.commit()
    conn_copied.close()
    print(f"✅ Export DB to {output_path}")
