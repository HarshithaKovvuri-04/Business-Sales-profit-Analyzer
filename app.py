import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# --- 1. SECURE DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        # We define each part separately so the computer doesn't have to "guess"
        conn_url = URL.create(
            drivername="postgresql+psycopg2",
            username="neondb_owner",
            # Enter your password exactly as it appears in Neon (with the @)
            password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
            host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
            database="neondb",
            query={"sslmode": "require"},
        )
        
        # pool_pre_ping=True prevents the "OperationalError" we saw earlier
        engine = create_engine(conn_url, pool_pre_ping=True)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to Neon: {e}")
        return None

engine = init_connection()

if engine:
    st.success("✅ Connected to Neon Database!")
