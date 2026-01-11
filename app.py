import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. PROFESSIONAL UI STYLING ---
def apply_ui_style():
    st.markdown("""
    <style>
        .main { background-color: #f4f7f6; }
        .stButton>button {
            width: 100%; border-radius: 8px; height: 3.5em;
            background-color: #4f46e5; color: white; font-weight: bold; border: none;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #e5e7eb; border-radius: 5px 5px 0 0; padding: 10px 20px;
        }
        .biz-card {
            background-color: white; padding: 20px; margin: 10px 0;
            border-radius: 12px; border-left: 6px solid #4f46e5;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ROBUST DATABASE CONNECTION ---
@st.cache_resource
def get_db_engine():
    conn_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    return create_engine(conn_url, pool_pre_ping=True, pool_recycle=300)

engine = get_db_engine()
Session = sessionmaker(bind=engine)
db = Session()
Base = declarative_base()

# --- 3. DATABASE MODELS ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="Owner") # Added Role Field

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    industry = Column(String)

# --- 4. MAIN APP INTERFACE ---
apply_ui_style()
st.title("📊 BizAnalyzer AI")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["**Login**", "**Register**"])
    
    with tab2:
        st.subheader("Create Your Profile")
        with st.form("registration_form"):
            new_u = st.text_input("Username")
            new_p = st.text_input("Password", type="password")
            # --- ROLE SELECTION ADDED ---
            new_r = st.selectbox("Select Your Role", ["Owner", "Manager", "Analyst"])
            
            if st.form_submit_button("Create Account"):
                try:
                    user = User(username=new_u, password=new_p, role=new_r)
                    db.add(user)
                    db.commit()
                    st.success(f"Account for {new_u} ({new_r}) created! Switch to Login.")
                except Exception as e:
                    db.rollback()
                    st.error("Username already exists or connection timed out.")

    with tab1:
        st.subheader("Welcome Back")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                user = db.query(User).filter_by(username=u, password=p).first()
                if user:
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

else:
    # --- LOGGED IN DASHBOARD ---
    st.sidebar.markdown(f"### 👋 Hello, {st.session_state.username}")
    st.sidebar.info(f"**Role:** {st.session_state.role}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()

    st.header("🏢 Business Profile Management")
    
    with st.expander("Register a New Business Entity"):
        with st.form("biz_add"):
            name = st.text_input("Business Name")
            ind = st.selectbox("Industry", ["Retail", "Food & Beverage", "Tech", "Manufacturing"])
            if st.form_submit_button("Save Profile"):
                new_biz = Business(owner_id=st.session_state.user_id, name=name, industry=ind)
                db.add(new_biz)
                db.commit()
                st.success(f"Registered {name}!")
                st.rerun()

    # Display Existing Profiles
    my_biz = db.query(Business).filter_by(owner_id=st.session_state.user_id).all()
    if my_biz:
        for b in my_biz:
            st.markdown(f"""
            <div class="biz-card">
                <h4 style='margin:0;'>{b.name}</h4>
                <p style='margin:0; color:#666;'>Industry: {b.industry}</p>
            </div>
            """, unsafe_allow_html=True)
