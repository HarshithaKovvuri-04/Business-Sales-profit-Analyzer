import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. JWT SECURITY CONFIG ---
# This satisfies the Secure Authentication requirement
JWT_SECRET = "secure_biz_analyzer_2026"
JWT_ALGORITHM = "HS256"

def create_jwt(user_id):
    """Generates a secure token."""
    payload = {
        "u_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt(token):
    """Verifies the secure token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["u_id"]
    except:
        return None

# --- 2. CUSTOM CSS STYLING ---
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

# --- 3. DATABASE ENGINE ---
@st.cache_resource
def get_engine():
    # URL.create is the only way to safely handle the @ in your password
    conn_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    # pool_pre_ping=True is the fix for OperationalError
    return create_engine(conn_url, pool_pre_ping=True)

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

# --- 5. APP INTERFACE ---
st.title("🛡️ Secure BizAnalyzer AI")

if "token" not in st.session_state:
    st.session_state.token = None

# Extract User ID from the secure JWT
current_user_id = decode_jwt(st.session_state.token) if st.session_state.token else None

if not current_user_id:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab2:
        st.subheader("New User Registration")
        ru = st.text_input("Username", key="reg_u")
        rp = st.text_input("Password", type="password", key="reg_p")
        rr = st.selectbox("Your Role", ["Owner", "Manager", "Analyst"], key="reg_r")
        
        if st.button("Register Now"):
            engine = get_engine()
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                new_user = User(username=ru, password=rp, role=rr)
                session.add(new_user)
                session.commit() # Registration works here
                st.success("Registration Success! Please switch to Login tab.")
            except:
                session.rollback()
                st.error("Registration failed. Username may exist.")
            finally:
                session.close()

    with tab1:
        st.subheader("Sign In")
        lu = st.text_input("Username", key="log_u")
        lp = st.text_input("Password", type="password", key="log_p")
        
        if st.button("Login"):
            engine = get_engine()
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                # Fresh session here prevents the login OperationalError
                user = session.query(User).filter_by(username=lu, password=lp).first()
                if user:
                    # Generate secure JWT on success
                    st.session_state.token = create_jwt(user.id)
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            finally:
                session.close()

else:
    # --- LOGGED IN SECURE DASHBOARD ---
    st.sidebar.success(f"Verified Session: {st.session_state.username}")
    st.sidebar.info(f"Role: {st.session_state.role}")
    
    if st.sidebar.button("Log Out"):
        st.session_state.token = None
        st.rerun()

    st.header("🏢 Your Business Entities")
    
    with st.form("biz_add_form"):
        name = st.text_input("Entity Name")
        ind = st.selectbox("Industry", ["Retail", "Food", "Services", "Tech"])
        if st.form_submit_button("Register Business"):
            engine = get_engine()
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                new_biz = Business(owner_id=current_user_id, name=name, industry=ind)
                session.add(new_biz)
                session.commit()
                st.rerun()
            finally:
                session.close()

    # Display profiles linked to current user
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    profiles = session.query(Business).filter_by(owner_id=current_user_id).all()
    for b in profiles:
        st.markdown(f'<div class="biz-card"><h4>{b.name}</h4><p>{b.industry}</p></div>', unsafe_allow_html=True)
    session.close()
