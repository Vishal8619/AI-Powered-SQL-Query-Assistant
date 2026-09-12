import sqlite3
import os
import tempfile
import pandas as pd


def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    schema = ""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        schema += f"{table_name}({', '.join(column_names)})\n"
    conn.close()
    return schema


def run_query(sql, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()
        return {"columns": column_names, "rows": results, "error": None}
    except Exception as e:
        return {"columns": [], "rows": [], "error": str(e)}


def load_sql_file(sql_file_path):
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "uploaded.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    return db_path


def load_csv_file(csv_file_path):
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "uploaded.db")
    df = pd.read_csv(csv_file_path)
    df.columns = [col.strip().replace(" ", "_").replace("-", "_").lower() for col in df.columns]
    conn = sqlite3.connect(db_path)
    table_name = os.path.basename(csv_file_path).replace(".csv", "").replace(" ", "_").lower()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    return db_path


def load_excel_file(excel_file_path):
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "uploaded.db")
    conn = sqlite3.connect(db_path)
    sheets = pd.read_excel(excel_file_path, sheet_name=None)
    for sheet_name, df in sheets.items():
        df.columns = [col.strip().replace(" ", "_").replace("-", "_").lower() for col in df.columns]
        table_name = sheet_name.strip().replace(" ", "_").replace("-", "_").lower()
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    return db_path