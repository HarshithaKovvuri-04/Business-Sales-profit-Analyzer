import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. SECURE JWT CONFIGURATION ---
# Milestone 1 requires secure authentication
JWT_SECRET = "biz_analyzer_secure_key_2026" 
JWT_ALGORITHM = "HS256"

def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["user_id"]
    except:
        return None

# --- 2. THEME & CSS ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #4f46e5; color: white; font-weight: bold;
    }
    .biz-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 6px solid #4f46e5; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ROBUST CONNECTION ENGINE ---
@st.cache_resource
def get_engine():
    # URL.create prevents the 'int()' parsing error
    conn_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    # pool_pre_ping=True fixes the 'OperationalError' by verifying connection
    return create_engine(conn_url, pool_pre_ping=True)

engine = get_engine()
Base = declarative_base()

# --- 4. MODELS ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    industry = Column(String)

# --- 5. INTERFACE LOGIC ---
st.title("🚀 Secure BizAnalyzer AI")

if "token" not in st.session_state:
    st.session_state.token = None

# Extract User ID from JWT Token
active_user_id = verify_token(st.session_state.token) if st.session_state.token else None

if not active_user_id:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab2:
        st.subheader("Register")
        u_reg = st.text_input("Username", key="ru")
        p_reg = st.text_input("Password", type="password", key="rp")
        r_reg = st.selectbox("Role", ["Owner", "Manager", "Analyst"], key="rr")
        
        if st.button("Register Now"):
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                new_user = User(username=u_reg, password=p_reg, role=r_reg)
                session.add(new_user)
                session.commit()
                st.success("Account created! Please log in.")
            except:
                st.error("Registration failed. Username may be taken.")
            finally:
                session.close()

    with tab1:
        st.subheader("Login")
        u_log = st.text_input("Username", key="lu")
        p_log = st.text_input("Password", type="password", key="lp")
        
        if st.button("Sign In"):
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                user = session.query(User).filter_by(username=u_log, password=p_log).first()
                if user:
                    # SECURE TOKEN GENERATION
                    st.session_state.token = generate_token(user.id)
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            finally:
                session.close()

else:
    # --- DASHBOARD (TOKEN VERIFIED) ---
    st.sidebar.success(f"Verified: {st.session_state.username}")
    st.sidebar.info(f"Role: {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()

    st.header("🏢 Your Business Profiles")
    
    with st.form("biz_form"):
        b_name = st.text_input("Business Name")
        b_ind = st.selectbox("Industry", ["Retail", "Food", "Tech"])
        if st.form_submit_button("Add Business"):
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                new_biz = Business(owner_id=active_user_id, name=b_name, industry=b_ind)
                session.add(new_biz)
                session.commit()
                st.rerun()
            finally:
                session.close()

    # Display results
    Session = sessionmaker(bind=engine)
    session = Session()
    profiles = session.query(Business).filter_by(owner_id=active_user_id).all()
    for b in profiles:
        st.markdown(f'<div class="biz-card"><h4>{b.name}</h4><p>{b.industry}</p></div>', unsafe_allow_html=True)
    session.close()
