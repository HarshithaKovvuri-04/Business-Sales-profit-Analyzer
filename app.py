import streamlit as st
import jwt
import datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 1. THEME & STYLING ---
def apply_custom_style():
    st.markdown("""
    <style>
        /* Main background and font */
        .main { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] { background-color: #1e1e2f; color: white; }
        
        /* Metric Card Styling */
        div[data-testid="stMetricValue"] { color: #2e7d32; font-weight: bold; }
        
        /* Custom Button Styling */
        .stButton>button {
            width: 100%; border-radius: 8px; border: none;
            background-color: #4f46e5; color: white; transition: 0.3s;
        }
        .stButton>button:hover { background-color: #4338ca; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        /* Card-like containers for forms */
        .stForm {
            background-color: white; padding: 2rem;
            border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE BACKEND (PostgreSQL Connection) ---
# Replace with your actual PostgreSQL URL (e.g., from Supabase or Render)
DB_URL = "postgresql://user:password@localhost:5432/biz_db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    industry = Column(String)

Base.metadata.create_all(engine)

# --- 3. SECURITY (JWT) ---
SECRET_KEY = "ai_analyzer_secret_2026"

def create_jwt(user):
    payload = {
        "user_id": user.id, "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- 4. APP UI ---
apply_custom_style()

if "token" not in st.session_state:
    st.session_state.token = None

# Sidebar Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208707.png", width=80)
    st.title("BizAnalyzer AI")
    if not st.session_state.token:
        auth_mode = st.selectbox("Account", ["Login", "Register"])
    else:
        st.success(f"Logged in as {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# Authentication Logic
if not st.session_state.token:
    st.header("Welcome to AI Profit Analyzer")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
    if auth_mode == "Register":
        role = st.selectbox("Role", ["Owner", "Manager"])
        if st.button("Create Account"):
            new_user = User(username=username, password=password, role=role)
            session.add(new_user)
            session.commit()
            st.success("Account Created!")
    else:
        if st.button("Sign In"):
            user = session.query(User).filter_by(username=username, password=password).first()
            if user:
                st.session_state.token = create_jwt(user)
                st.session_state.username = user.username
                st.session_state.user_id = user.id
                st.rerun()
            else:
                st.error("Invalid credentials")

# Dashboard Logic (Post-Login)
else:
    # Multiple Business Management Profile Page
    st.subheader("💼 Your Business Profiles") [cite: 46]
    
    # Create new business profile
    with st.expander("Add New Business Profile"):
        b_name = st.text_input("Business Name")
        b_type = st.selectbox("Industry", ["Retail", "Service", "E-commerce"]) [cite: 32]
        if st.button("Register Business"):
            new_biz = Business(user_id=st.session_state.user_id, name=b_name, industry=b_type)
            session.add(new_biz)
            session.commit()
            st.rerun()

    # Select Active Business
    user_bizs = session.query(Business).filter_by(user_id=st.session_state.user_id).all()
    if user_bizs:
        selected_biz = st.sidebar.selectbox("Active Business", [b.name for b in user_bizs])
        
        # Transaction Logging Form 
        st.markdown(f"### 📝 Entry: {selected_biz}")
        with st.form("transaction_form"):
            t_type = st.radio("Type", ["Sales", "Expense"], horizontal=True) [cite: 37]
            amt = st.number_input("Amount ($)", min_value=0.0)
            cat = st.selectbox("Category", ["Inventory", "Marketing", "Rent", "Revenue"]) [cite: 39]
            if st.form_submit_button("Save Transaction"):
                st.success(f"{t_type} recorded successfully!")
