import pandas as pd
import sqlite3


def analyze_database(db_path):
    """Analyzes the database and returns a full summary"""
    conn = sqlite3.connect(db_path)

    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    table_names = tables["name"].tolist()

    report = {}

    for table in table_names:
        df = pd.read_sql(f"SELECT * FROM '{table}'", conn)

        total_rows = len(df)
        total_cols = len(df.columns)

        missing = df.isnull().sum()
        missing_info = {col: int(val) for col, val in missing.items() if val > 0}

        duplicate_count = int(df.duplicated().sum())

        col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        numeric_stats = {}
        for col in numeric_cols:
            numeric_stats[col] = {
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
                "mean": round(float(df[col].mean()), 2),
                "median": round(float(df[col].median()), 2)
            }

        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        categorical_stats = {}
        for col in categorical_cols:
            top_values = df[col].value_counts().head(5).to_dict()
            categorical_stats[col] = {str(k): int(v) for k, v in top_values.items()}

        report[table] = {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "columns": col_types,
            "missing_values": missing_info,
            "duplicate_rows": duplicate_count,
            "numeric_stats": numeric_stats,
            "categorical_stats": categorical_stats
        }

    conn.close()
    return report


def generate_ai_insights(report, client):
    """Ask AI to generate insights from the data summary"""
    import json

    prompt = f"""
You are a data analyst. Based on the following database analysis report, provide:
1. A brief overview of the data (2-3 sentences)
2. Key observations (3-5 bullet points)
3. Data quality issues found (missing values, duplicates)
4. Suggested questions the user can ask about this data

Keep it friendly, clear and insightful.

REPORT:
{json.dumps(report, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return "Could not generate AI insights at this time."