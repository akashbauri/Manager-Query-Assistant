import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

class DatabaseManager:

    def __init__(self, use_local=True):
        self.use_local = use_local
        self.local_url = st.secrets.get("LOCAL_SQLALCHEMY")
        self.ps_url = st.secrets.get("PS_SQLALCHEMY")
        self.engine = None

    def get_engine(self):
        if self.engine:
            return self.engine

        url = self.local_url if self.use_local else self.ps_url
        if not url:
            raise ValueError("No SQLAlchemy URL found in secrets.")

        self.engine = create_engine(url)
        return self.engine

    def push_dataframe(self, df, table_name):
        eng = self.get_engine()
        df.to_sql(table_name, eng, if_exists="replace", index=False)

    def execute_sql(self, sql):
        if not sql.lower().startswith("select"):
            raise ValueError("Only SELECT queries allowed!")
        return pd.read_sql(sql, self.get_engine())

    def preview_table(self, table_name):
        return pd.read_sql(f"SELECT * FROM {table_name} LIMIT 20", self.get_engine())

    def get_table_schema(self, table):
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", self.get_engine())
        return df.columns.tolist()
