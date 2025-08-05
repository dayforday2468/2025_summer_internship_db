import sqlite3
import shutil
import os


def database_copy(input_path, output_path):
    # 원본 DB 복사
    if os.path.exists(output_path):
        os.remove(output_path)
    shutil.copyfile(input_path, output_path)

    # 복사본에 연결
    conn_copied = sqlite3.connect(output_path)
    copied_cursor = conn_copied.cursor()

    # IS_EXIST 컬럼 추가
    copied_cursor.execute("ALTER TABLE NODE ADD COLUMN IS_EXIST INTEGER DEFAULT 1")
    copied_cursor.execute("ALTER TABLE LINK ADD COLUMN IS_EXIST INTEGER DEFAULT 1")
    copied_cursor.execute("ALTER TABLE TURN ADD COLUMN IS_EXIST INTEGER DEFAULT 1")

    conn_copied.commit()
    conn_copied.close()
    print(f"✅ Copy DB to {output_path}")
