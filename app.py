import streamlit as st
import pandas as pd
import os
import tempfile
from llm import chat_with_ai, explain_error, fix_and_retry_sql, decide_chart, client
from db import get_schema, run_query, load_sql_file, load_csv_file, load_excel_file
from charts import generate_chart
from analyzer import analyze_database, generate_ai_insights
from history import (init_history_db, create_session, save_message,
                     get_all_sessions, get_session_messages, delete_session)

# Initialize history database
init_history_db()

# Page config
st.set_page_config(
    page_title="AI Data Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .title { text-align: center; color: #1a1a2e; }
    .subtitle { text-align: center; color: #666; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='title'>🤖 AI Data Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Upload your data and chat with it like talking to a real analyst!</p>", unsafe_allow_html=True)
st.markdown("---")

# Load past session if requested
if "load_session_id" in st.session_state:
    session_id = st.session_state.load_session_id
    past_messages = get_session_messages(session_id)
    st.session_state.messages = []
    for role, content, sql_query, timestamp in past_messages:
        msg = {"role": role, "content": content}
        if sql_query:
            msg["sql"] = sql_query
        st.session_state.messages.append(msg)
    st.session_state.session_id = session_id
    del st.session_state.load_session_id

# ─── Sidebar ───
with st.sidebar:
    st.header("📂 Upload File")
    st.markdown("Supported: `.db` `.sqlite` `.sql` `.csv` `.xlsx` `.xls`")
    uploaded_file = st.file_uploader(
        "Upload your file",
        type=["db", "sqlite", "sqlite3", "sql", "csv", "xlsx", "xls"]
    )

    if uploaded_file:
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, uploaded_file.name)

        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Processing file..."):
            if uploaded_file.name.endswith(".sql"):
                db_path = load_sql_file(tmp_path)
            elif uploaded_file.name.endswith(".csv"):
                db_path = load_csv_file(tmp_path)
            elif uploaded_file.name.endswith((".xlsx", ".xls")):
                db_path = load_excel_file(tmp_path)
            else:
                db_path = tmp_path

        st.session_state.db_path = db_path
        st.session_state.db_engine = None
        st.session_state.messages = []
        st.session_state.last_sql = None
        st.session_state.analysis = None

        # Create new session
        session_id = create_session(uploaded_file.name)
        st.session_state.session_id = session_id

        st.success(f"✅ {uploaded_file.name} loaded!")

        st.markdown("---")
        st.header("📋 Database Schema")
        schema = get_schema(db_path)
        st.code(schema)

        st.markdown("---")
        st.header("🔍 Data Analysis")
        with st.spinner("Analyzing your data..."):
            analysis = analyze_database(db_path)
            st.session_state.analysis = analysis

        for table_name, info in analysis.items():
            st.markdown(f"### 📊 `{table_name}`")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", info["total_rows"])
            with col2:
                st.metric("Columns", info["total_columns"])
            with col3:
                st.metric("Duplicates", info["duplicate_rows"])

            if info["missing_values"]:
                st.warning("⚠️ Missing Values:")
                for col, count in info["missing_values"].items():
                    st.markdown(f"- `{col}`: **{count}**")
            else:
                st.success("✅ No missing values!")

            if info["numeric_stats"]:
                with st.expander("📈 Numeric Stats"):
                    stats_df = pd.DataFrame(info["numeric_stats"]).T
                    st.dataframe(stats_df, use_container_width=True)

            if info["categorical_stats"]:
                with st.expander("📝 Top Values"):
                    for col, values in info["categorical_stats"].items():
                        st.markdown(f"**{col}:**")
                        for val, count in values.items():
                            st.markdown(f"  - {val}: {count}")

        st.markdown("---")
        st.header("🤖 AI Insights")
        with st.spinner("Generating insights..."):
            insights = generate_ai_insights(analysis, client)
        st.markdown(insights)

    st.markdown("---")
    st.header("💡 Try asking:")
    st.markdown("- Hi, what can you do?")
    st.markdown("- How many rows are there?")
    st.markdown("- Show me the top 5 records")
    st.markdown("- Show me a bar chart of customers by city")
    st.markdown("- Plot sales by product")

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_sql = None
        st.rerun()

    # Past chats
    st.markdown("---")
    st.header("🕐 Past Chats")
    sessions = get_all_sessions()

    if not sessions:
        st.info("No past chats yet!")
    else:
        for session in sessions:
            session_id, session_name, file_name, created_at, msg_count = session
            with st.expander(f"💬 {session_name}"):
                st.markdown(f"📁 `{file_name}`")
                st.markdown(f"🕐 {created_at}")
                st.markdown(f"💬 {msg_count} messages")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📂 Load", key=f"load_{session_id}"):
                        st.session_state.load_session_id = session_id
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{session_id}"):
                        delete_session(session_id)
                        st.rerun()


def make_unique_columns(columns):
    seen = {}
    unique_columns = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            unique_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            unique_columns.append(col)
    return unique_columns


CHART_KEYWORDS = [
    "chart", "graph", "plot", "visualize", "visualise",
    "bar", "pie", "line", "scatter", "diagram",
    "show me a chart", "draw", "display chart", "visual"
]


def user_wants_chart(question):
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in CHART_KEYWORDS)


def show_results(result, message, sql, question, key_suffix="new"):
    with st.expander("🔍 View SQL Query"):
        st.code(sql, language="sql")

    if result["rows"]:
        columns = make_unique_columns(result["columns"])
        df = pd.DataFrame(result["rows"], columns=columns)

        if user_wants_chart(question):
            chart_info = decide_chart(question, columns, result["rows"])
            if chart_info.get("chart_type") != "none":
                fig = generate_chart(df, chart_info)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Couldn't generate a chart for this data.")
            else:
                st.info("📊 This data doesn't suit a chart. Showing table instead.")

        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv,
            file_name="results.csv",
            mime="text/csv",
            key=f"download_{key_suffix}"
        )
        final_message = f"{message}\n\n✅ Found **{len(result['rows'])}** result(s)"
    else:
        st.info("✅ Query ran successfully but returned no results.")
        final_message = message

    return final_message


# ─── Main Area ───
if "db_path" not in st.session_state and "db_engine" not in st.session_state:
    st.markdown("## 👋 Welcome!")
    st.markdown("I'm your AI Data Assistant. Upload a file from the sidebar and start chatting with your data!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🗄️ **Database Files**\n\n`.db` `.sqlite` `.sql`")
    with col2:
        st.info("📊 **Spreadsheets**\n\n`.xlsx` `.xls`")
    with col3:
        st.info("📄 **Data Files**\n\n`.csv`")

else:
    db_path = st.session_state.get("db_path", None)
    db_engine = st.session_state.get("db_engine", None)
    schema = get_schema(db_path) if db_path else st.session_state.get("db_schema", "")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sql" not in st.session_state:
        st.session_state.last_sql = None

    # Welcome message on first load
    if len(st.session_state.messages) == 0:
        with st.chat_message("assistant"):
            st.markdown("👋 Hi! I've loaded your database. I can see the following tables:\n\n"
                       f"```\n{schema}\n```\n\n"
                       "Feel free to ask me anything about your data! You can ask in plain English like:\n"
                       "- *'How many records are there?'*\n"
                       "- *'Show me the top 10 rows'*\n"
                       "- *'Show me a bar chart of sales by city'*")

    # ─── Scrollable Chat History ───
    chat_container = st.container(height=500)

    for i, message in enumerate(st.session_state.messages):
        with chat_container:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sql" in message and message["sql"]:
                    with st.expander("🔍 View SQL Query"):
                        st.code(message["sql"], language="sql")
                if "dataframe" in message and message["dataframe"]:
                    columns = make_unique_columns(message["dataframe"]["columns"])
                    df = pd.DataFrame(message["dataframe"]["rows"], columns=columns)
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download as CSV",
                        data=csv,
                        file_name="results.csv",
                        mime="text/csv",
                        key=f"download_history_{i}"
                    )

    # ─── Chat Input ───
    if prompt := st.chat_input("Ask me anything about your data..."):

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        if "session_id" in st.session_state:
            save_message(st.session_state.session_id, "user", prompt)

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):

                    ai_result = chat_with_ai(
                        prompt,
                        schema,
                        st.session_state.messages,
                        st.session_state.last_sql
                    )

                    response_type = ai_result["type"]
                    message = ai_result["message"]
                    sql = ai_result["sql"]
                    memory_note = ai_result.get("memory_note", None)

                    # Show memory note
                    if memory_note:
                        st.caption(f"🧠 Remembering: {memory_note}")

                    if response_type == "sql" and sql:
                        result = run_query(sql, db_path) if db_path else run_query(sql, db_path)

                        if result["error"]:
                            fixed_sql = fix_and_retry_sql(sql, result["error"], schema)

                            if fixed_sql:
                                result2 = run_query(fixed_sql, db_path)

                                if result2["error"]:
                                    explanation = explain_error(fixed_sql, result2["error"], prompt)
                                    st.error("❌ I tried to fix the query but still ran into an issue:")
                                    st.markdown(explanation)
                                    with st.expander("🔍 View SQL Query"):
                                        st.code(fixed_sql, language="sql")
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"❌ {explanation}",
                                        "sql": fixed_sql
                                    })
                                    if "session_id" in st.session_state:
                                        save_message(st.session_state.session_id, "assistant", f"❌ {explanation}", fixed_sql)

                                else:
                                    st.session_state.last_sql = fixed_sql
                                    st.markdown(message)
                                    final_message = show_results(result2, message, fixed_sql, prompt)
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": final_message,
                                        "sql": fixed_sql,
                                        "dataframe": result2 if result2["rows"] else None
                                    })
                                    if "session_id" in st.session_state:
                                        save_message(st.session_state.session_id, "assistant", final_message, fixed_sql)

                            else:
                                explanation = explain_error(sql, result["error"], prompt)
                                st.error("❌ I ran into an issue:")
                                st.markdown(explanation)
                                with st.expander("🔍 View SQL Query"):
                                    st.code(sql, language="sql")
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"❌ {explanation}",
                                    "sql": sql
                                })
                                if "session_id" in st.session_state:
                                    save_message(st.session_state.session_id, "assistant", f"❌ {explanation}", sql)

                        else:
                            st.session_state.last_sql = sql
                            st.markdown(message)
                            final_message = show_results(result, message, sql, prompt)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": final_message,
                                "sql": sql,
                                "dataframe": result if result["rows"] else None
                            })
                            if "session_id" in st.session_state:
                                save_message(st.session_state.session_id, "assistant", final_message, sql)

                    else:
                        st.markdown(message)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": message
                        })
                        if "session_id" in st.session_state:
                            save_message(st.session_state.session_id, "assistant", message)