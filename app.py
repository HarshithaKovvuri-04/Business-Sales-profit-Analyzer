import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. PROFESSIONAL CSS & STYLING ---
def apply_ui_style():
    st.markdown("""
    <style>
        .main { background-color: #f4f7f6; }
        .stButton>button {
            width: 100%; border-radius: 5px; height: 3em;
            background-color: #007bff; color: white; border: none;
        }
        .stTextInput>div>div>input { border-radius: 5px; }
        .business-card {
            background-color: white; padding: 20px;
            border-radius: 10px; border-left: 5px solid #007bff;
            margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION (FIXED FOR STABILITY) ---
@st.cache_resource
def get_db_engine():
    # We use URL.create to prevent the 'int()' parsing error permanently
    conn_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    return create_engine(
        conn_url, 
        pool_pre_ping=True,  # This fixes the 'commit()' error by checking the link first
        pool_recycle=300     # Refreshes the connection every 5 minutes
    )

engine = get_db_engine()
Session = sessionmaker(bind=engine)
db = Session()
Base = declarative_base()

# --- 3. MODELS ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    industry = Column(String)

# --- 4. AUTH HELPERS ---
def create_token(user_id):
    payload = {"u_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)}
    return jwt.encode(payload, "secret_key_123", algorithm="HS256")

# --- 5. MAIN APP INTERFACE ---
apply_ui_style()
st.title("📊 Small Business Sales & Profit Analyzer")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab2:
        with st.form("reg"):
            u = st.text_input("Choose Username")
            p = st.text_input("Choose Password", type="password")
            if st.form_submit_button("Register"):
                try:
                    new_user = User(username=u, password=p)
                    db.add(new_user)
                    db.commit() # The fixed engine makes this safe now
                    st.success("Account created! Go to Login tab.")
                except Exception as e:
                    db.rollback()
                    st.error(f"Error: {e}")

    with tab1:
        with st.form("log"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                user = db.query(User).filter_by(username=u, password=p).first()
                if user:
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

else:
    # LOGGED IN VIEW
    st.sidebar.markdown(f"### Welcome, **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()

    st.header("🏢 Your Business Profiles")
    
    with st.expander("➕ Add a New Business"):
        with st.form("add_biz"):
            b_name = st.text_input("Business Name")
            b_ind = st.selectbox("Industry", ["Retail", "Food", "Tech", "Services"])
            if st.form_submit_button("Save Business"):
                new_biz = Business(owner_id=st.session_state.user_id, name=b_name, industry=b_ind)
                db.add(new_biz)
                db.commit()
                st.success(f"{b_name} registered!")
                st.rerun()

    # Show existing businesses in styled cards
    my_biz = db.query(Business).filter_by(owner_id=st.session_state.user_id).all()
    for b in my_biz:
        st.markdown(f"""
        <div class="business-card">
            <h4>{b.name}</h4>
            <p>Industry: {b.industry}</p>
        </div>
        """, unsafe_allow_html=True)
