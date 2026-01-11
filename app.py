import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base


from sqlalchemy.engine import URL

# 1. Break your connection string into clear parts
# Use your REAL password here, exactly as it appears in Neon (with the @)
try:
    # We build the URL object properly so SQLAlchemy doesn't get confused
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", # Use the RAW password
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    
    engine = create_engine(connection_url, pool_pre_ping=True)
    # ... rest of your session setup ...
except Exception as e:
    st.error(f"Connection Error: {e}")

# --- 1. THEME & STYLING ---
def apply_custom_style():
    st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        [data-testid="stSidebar"] { background-color: #1e1e2f; color: white; }
        .stButton>button {
            width: 100%; border-radius: 8px; border: none;
            background-color: #4f46e5; color: white;
        }
        .stForm {
            background-color: white; padding: 2rem;
            border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
try:
    # This pulls your URL (with the %40 fix) from Streamlit Secrets
    DB_URL = st.secrets["connections"]["postgresql"]["url"]
    engine = create_engine(
        DB_URL, 
        connect_args={"sslmode": "require"},
        pool_pre_ping=True
    )
    Session = sessionmaker(bind=engine)
    db = Session()
    Base = declarative_base()
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- 3. DATABASE MODELS ---
# These match the tables you created in the Neon SQL Editor
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    role = Column(String)

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    industry = Column(String)

# --- 4. SECURITY LOGIC ---
SECRET_KEY = "your_ai_project_secret"

def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- 5. APP UI ---
apply_custom_style()

if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# AUTHENTICATION HUB
if not st.session_state.token:
    st.title("🚀 BizAnalyzer AI")
    auth_choice = st.sidebar.selectbox("Access", ["Login", "Register"])
    
    if auth_choice == "Register":
        st.subheader("Create Account")
        with st.form("reg_form"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                user = User(username=new_user, password=new_pass, role="Owner")
                db.add(user)
                db.commit()
                st.success("Account created! Switch to Login.")
                
    else:
        st.subheader("Welcome Back")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user = db.query(User).filter_by(username=username, password=password).first()
                if user:
                    st.session_state.token = create_token(user.id)
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.rerun()
                else:
                    st.error("Invalid credentials")

# POST-LOGIN: DASHBOARD
else:
    st.sidebar.title(f"Hi, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()

    st.title("🏢 Business Management")
    
    # Milestone 1: Multi-Business Profiles
    with st.expander("➕ Register a New Business"):
        with st.form("biz_reg"):
            b_name = st.text_input("Business Name")
            b_type = st.selectbox("Type", ["Retail", "Food", "Online Shop", "Services"])
            if st.form_submit_button("Create Profile"):
                new_biz = Business(owner_id=st.session_state.user_id, name=b_name, industry=b_type)
                db.add(new_biz)
                db.commit()
                st.success(f"Registered {b_name}!")
                st.rerun()

    # Select Active Business for Milestone 2 Transactions
    user_businesses = db.query(Business).filter_by(owner_id=st.session_state.user_id).all()
    if user_businesses:
        st.subheader("Your Registered Businesses")
        for b in user_businesses:
            st.info(f"**{b.name}** | Industry: {b.industry}")
    else:
        st.warning("No businesses found. Create one above!")

