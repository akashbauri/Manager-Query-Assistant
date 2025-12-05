# streamlit_app.py

import streamlit as st
import pandas as pd
import time

from modules.database import DatabaseManager
from modules.ai_engine import AIEngine
from modules.rag_engine import RAGEngine
from modules.stt_engine import STTEngine
from modules.image_engine import ImageEngine
from modules.utils import df_plot_bytes

st.set_page_config(page_title="Manager Query Assistant", layout="wide")

st.title("Manager Query Assistant")
st.write("Ask natural language questions about your dataset using SQL + RAG + AI.")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
USE_LOCAL = st.sidebar.checkbox("Use Local MySQL (Testing Mode)", value=True)

db = DatabaseManager(use_local=USE_LOCAL)
engine = db.get_engine()

ai = AIEngine()
rag = RAGEngine()
stt = STTEngine()
img = ImageEngine()

# ---------------------------------------------------------
# Dataset Import
# ---------------------------------------------------------
with st.sidebar.expander("Upload & Push Data to DB"):
    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if file:
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        st.write(df.head())
        if st.button("Push to DB"):
            db.push_dataframe(df, table_name="clothing_inventory")
            st.success("Pushed to MySQL successfully!")

# ---------------------------------------------------------
# CHAT INTERFACE
# ---------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Ask a Question")

    mode = st.radio("Input Type:", ["Text", "Voice"])

    if mode == "Text":
        user_input = st.text_input("Ask anything about your inventory…")
        send = st.button("Send")
    else:
        audio = st.file_uploader("Upload Audio File", type=["wav", "mp3", "m4a"])
        send = st.button("Send Voice Input")

    allow_sql_edit = st.checkbox("Show & Edit SQL", value=True)

    if send:
        query = ""

        if mode == "Text":
            query = user_input
        else:
            if audio is None:
                st.warning("Upload an audio file first.")
                st.stop()
            query = stt.save_temp_audio_and_transcribe(audio)
            st.info(f"Transcribed: {query}")

        sql_keywords = ["how many", "count", "sum", "average", "where", "list", "show"]
        is_sql = any(k in query.lower() for k in sql_keywords)

        executed_sql = None
        bot_reply = None
        plot_img = None

        if is_sql:
            schema = db.get_table_schema("clothing_inventory")
            sql = ai.nl_to_sql(query, schema)

            if allow_sql_edit:
                edited_sql = st.text_area("Generated SQL:", sql, height=120)
                if st.button("Execute SQL"):
                    df_res = db.execute_sql(edited_sql)
                    executed_sql = edited_sql
                    bot_reply = f"Returned {len(df_res)} rows."
                    plot_img = df_plot_bytes(df_res)
            else:
                df_res = db.execute_sql(sql)
                executed_sql = sql
                bot_reply = f"Returned {len(df_res)} rows."
                plot_img = df_plot_bytes(df_res)

        else:
            rag_output = rag.answer(query)
            if rag_output.startswith("NOT_IN_DATASET"):
                bot_reply = ai.web_search(query)
            else:
                bot_reply = rag_output

        st.session_state.history.append({
            "user": query,
            "bot": bot_reply,
            "sql": executed_sql,
            "time": time.time()
        })

        st.write("### Bot Response")
        st.write(bot_reply)
        if plot_img:
            st.image(plot_img)

with col2:
    st.subheader("Table Preview")
    try:
        st.dataframe(db.preview_table("clothing_inventory"))
    except:
        st.info("No table loaded.")

# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------
st.subheader("Conversation History")
for msg in reversed(st.session_state.history[-20:]):
    st.markdown(f"**You:** {msg['user']}")
    st.markdown(f"**Bot:** {msg['bot']}")
    if msg["sql"]:
        st.code(msg["sql"])
