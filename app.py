import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# This function builds the connection and caches it for performance
@st.cache_resource
def init_connection():
    try:
        # Pull the URL from the Secrets we just set up
        db_url = st.secrets["connections"]["postgresql"]["url"]
        engine = create_engine(db_url, pool_pre_ping=True)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to Neon: {e}")
        return None

engine = init_connection()

if engine:
    st.success("✅ Connected to Neon Database!")
