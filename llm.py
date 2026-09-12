from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an intelligent data analyst assistant. You help users explore and understand their database by answering questions in plain English.

YOU HAVE MEMORY:
- You remember the last SQL query that was executed
- If the user asks a follow-up question like "now filter by X" or "sort by Y" or "show only Z", modify the last SQL query accordingly
- If the user asks a completely new question, generate a fresh SQL query

YOUR BEHAVIOR:
1. If the user greets you → greet back warmly and explain what you can do
2. If the user asks what you can do → explain your capabilities clearly
3. If the user asks a data question → generate SQL and explain what you're doing
4. If the user asks a follow-up → ALWAYS check chat history first and modify previous query
5. If the user says "I just asked you" or "as I said" → look back at chat history immediately
6. If the user asks something unclear → look at chat history before asking for clarification
7. NEVER forget what was discussed earlier in the conversation
8. Always be friendly, clear and professional

MEMORY RULES:
- Always read the full conversation history before responding
- If user refers to something previous ("that", "it", "same", "as before") → find it in history
- If user says "summarize", "analyze", "explain" without specifying → check what data was last discussed
- Never ask the user to repeat something that is already in the chat history

RESPONSE FORMAT:
You must always respond in this exact JSON format:
{
  "type": "greeting" | "sql" | "clarification" | "general" | "error",
  "message": "your friendly message to the user",
  "sql": "SELECT ... (only if type is sql, otherwise null)"
}

RULES FOR SQL:
- Generate valid SQLite SQL only
- Use only tables and columns from the schema
- Always return the sql field as null if type is not sql
"""


def chat_with_ai(user_message, schema, chat_history, last_sql=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if schema:
        messages.append({
            "role": "system",
            "content": f"DATABASE SCHEMA:\n{schema}"
        })

    if last_sql:
        messages.append({
            "role": "system",
            "content": f"LAST EXECUTED SQL QUERY (use this for follow-up questions):\n{last_sql}"
        })

    # Add chat history (last 10 messages for better memory)
    for msg in chat_history[-10:]:
        # Skip messages with dataframes to save tokens
        content = msg["content"]
        role = msg["role"]

        # Add SQL context if available
        if "sql" in msg and msg["sql"]:
            content = f"{content}\n[SQL used: {msg['sql']}]"

        messages.append({
            "role": role,
            "content": content
        })

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return {
            "type": parsed.get("type", "general"),
            "message": parsed.get("message", "I couldn't understand that."),
            "sql": parsed.get("sql", None),
            "error": None
        }
    except Exception as e:
        return {
            "type": "error",
            "message": "Sorry, I had trouble processing that. Could you rephrase your question?",
            "sql": None,
            "error": str(e)
        }


def explain_error(sql, error, question):
    prompt = f"""
A user asked: "{question}"
I generated this SQL: {sql}
But it gave this error: {error}

Please explain in simple, friendly language:
1. Why this error occurred
2. What the user can do to fix it or rephrase their question

Keep it short, clear and helpful. No technical jargon.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "There was an error running your query. Please try rephrasing your question."


def fix_and_retry_sql(sql, error, schema):
    prompt = f"""
You are an expert SQLite SQL debugger.
The following SQL query failed with an error. Fix it and return the corrected SQL.

SCHEMA:
{schema}

BROKEN SQL:
{sql}

ERROR:
{error}

RULES:
- Return ONLY the fixed SQL query, nothing else
- No explanations, no markdown, no code blocks
- Make sure column names match exactly with the schema
- Use double quotes for column names with special characters
- Fix any syntax errors, wrong column names, or type mismatches
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        fixed_sql = response.choices[0].message.content.strip()
        fixed_sql = fixed_sql.replace("```sql", "").replace("```", "").strip()
        return fixed_sql
    except Exception:
        return None


def decide_chart(question, columns, rows):
    sample_data = str(rows[:3]) if rows else "No data"
    prompt = f"""
You are a data visualization expert.
Based on the user's question and the data returned, decide the best chart type.

USER QUESTION: {question}
COLUMNS: {columns}
SAMPLE DATA (first 3 rows): {sample_data}

CHART TYPES AVAILABLE:
- "bar" → comparing categories
- "line" → trends over time
- "pie" → proportions/percentages
- "scatter" → relationship between two numbers
- "none" → data doesn't suit a chart

Respond ONLY in this exact JSON format:
{{
  "chart_type": "bar" | "line" | "pie" | "scatter" | "none",
  "x_column": "column name for x axis",
  "y_column": "column name for y axis",
  "title": "chart title"
}}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return {"chart_type": "none"}