import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. SECURE DATABASE CONNECTION ---
# This specific block solves the "invalid literal for int()" error
try:
    conn_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        # Use your RAW password here (the one with the @)
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    
    engine = create_engine(conn_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()
    Base = declarative_base()
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- 2. DATABASE MODELS ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="Owner")

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    industry = Column(String)

# --- 3. AUTHENTICATION HELPERS ---
SECRET_KEY = "your_project_secret_key"

def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- 4. APP INTERFACE ---
st.set_page_config(page_title="BizAnalyzer AI", layout="centered")
st.title("🚀 Business Sales & Profit Analyzer")

if "token" not in st.session_state:
    st.session_state.token = None

# AUTHENTICATION LOGIC
if not st.session_state.token:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab2:
        st.subheader("Create a New Account")
        reg_user = st.text_input("New Username", key="reg_u")
        reg_pass = st.text_input("New Password", type="password", key="reg_p")
        if st.button("Register"):
            user = User(username=reg_user, password=reg_pass)
            db.add(user)
            db.commit()
            st.success("Registration successful! Please log in.")
            
    with tab1:
        st.subheader("Login")
        log_user = st.text_input("Username", key="log_u")
        log_pass = st.text_input("Password", type="password", key="log_p")
        if st.button("Sign In"):
            user = db.query(User).filter_by(username=log_user, password=log_pass).first()
            if user:
                st.session_state.token = create_token(user.id)
                st.session_state.user_id = user.id
                st.session_state.username = user.username
                st.rerun()
            else:
                st.error("Invalid credentials")

# DASHBOARD LOGIC (After Login)
else:
    st.sidebar.success(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()

    st.header("🏢 Your Business Profiles")
    
    # Form to add a business
    with st.expander("Register a Business Entity"):
        biz_name = st.text_input("Business Name")
        biz_ind = st.selectbox("Industry", ["Retail", "Service", "Food", "Other"])
        if st.button("Add Business"):
            new_biz = Business(owner_id=st.session_state.user_id, name=biz_name, industry=biz_ind)
            db.add(new_biz)
            db.commit()
            st.success(f"Business '{biz_name}' added successfully!")
            st.rerun()

    # List existing businesses
    user_biz = db.query(Business).filter_by(owner_id=st.session_state.user_id).all()
    if user_biz:
        for b in user_biz:
            st.write(f"✅ **{b.name}** ({b.industry})")
    else:
        st.info("No businesses registered yet.")
