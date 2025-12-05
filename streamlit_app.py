import streamlit as st
# Use AI -> SQL
gen_sql = ai.nl_to_sql(query_text, dbm.get_table_schema('clothing_inventory'))
if sql_preview:
edited_sql = st.text_area('Generated SQL', value=gen_sql, height=140)
if st.button('Execute SQL'):
try:
df_res = dbm.execute_sql(edited_sql)
executed_sql = edited_sql
bot_answer = f"Executed SQL. Returned {len(df_res)} rows."
plot_bytes = df_plot_bytes(df_res)
except Exception as e:
st.error(f'SQL Execution failed: {e}')
else:
try:
df_res = dbm.execute_sql(gen_sql)
executed_sql = gen_sql
bot_answer = f"Executed SQL. Returned {len(df_res)} rows."
plot_bytes = df_plot_bytes(df_res)
except Exception as e:
st.error(f'SQL Execution failed: {e}')
else:
# Use RAG or fallback to AI
if rag is not None:
rag_out = rag.answer(query_text)
if isinstance(rag_out, str) and rag_out.strip().startswith('NOT_IN_DATASET'):
web = ai.web_search(query_text)
bot_answer = 'Not in dataset. Web search result:\n' + web
else:
bot_answer = rag_out
else:
bot_answer = ai.simple_answer(query_text)


# Save history and display
st.session_state.history.append({'time': time.time(), 'user': query_text, 'bot': bot_answer, 'sql': executed_sql})
st.markdown('**Bot:**')
st.write(bot_answer)
if plot_bytes:
st.image(plot_bytes)


with col2:
st.subheader('Dataset & Tools')
try:
df_preview = dbm.preview_table('clothing_inventory')
st.dataframe(df_preview.head(20))
except Exception as e:
st.info('No table preview available yet')


st.markdown('---')
st.subheader('Conversation History')
for item in reversed(st.session_state.history[-50:]):
st.markdown(f"**You:** {item['user']}")
st.markdown(f"**Bot:** {item['bot']}")
if item['sql']:
st.code(item['sql'])


# Footer notes
st.info('Remember to set your API keys and DB credentials in Streamlit Secrets before deploying.')
