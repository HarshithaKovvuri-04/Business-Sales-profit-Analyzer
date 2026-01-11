import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL
from contextlib import contextmanager

# --- 1. MODERN CSS STYLING ---
def apply_ui():
    st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .stButton>button {
            width: 100%; border-radius: 8px; height: 3.5em;
            background-color: #4f46e5; color: white; font-weight: bold; border: none;
        }
        .biz-card {
            background-color: white; padding: 25px; border-radius: 15px;
            border-left: 8px solid #4f46e5; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .role-pill {
            background-color: #e0e7ff; color: #4338ca;
            padding: 5px 15px; border-radius: 50px; font-size: 0.8em; font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SELF-HEALING DATABASE CONNECTION ---
@st.cache_resource
def get_engine():
    conn_url = URL.create(
        drivername="postgresql+psycopg2",
        username="neondb_owner",
        password="npg_ol9NwsE4AvUR@ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech", 
        host="ep-spring-king-ahuzxk0o.c-3.us-east-1.aws.neon.tech",
        database="neondb",
        query={"sslmode": "require"},
    )
    # pool_pre_ping=True prevents the OperationalError by checking the link before queries
    return create_engine(conn_url, pool_pre_ping=True, pool_recycle=300)

@contextmanager
def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

Base = declarative_base()

# --- 3. MODELS ---
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

# --- 4. INTERFACE LOGIC ---
apply_ui()
st.title("📊 BizAnalyzer AI")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["**Login**", "**Register**"])
    
    with tab2:
        with st.form("reg"):
            u = st.text_input("New Username")
            p = st.text_input("New Password", type="password")
            r = st.selectbox("Role", ["Owner", "Manager", "Analyst"])
            if st.form_submit_button("Register"):
                with get_session() as db:
                    new_user = User(username=u, password=p, role=r)
                    db.add(new_user)
                st.success("Account created! Now go to the Login tab.")

    with tab1:
        with st.form("log"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                with get_session() as db:
                    user = db.query(User).filter_by(username=u, password=p).first()
                    if user:
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.session_state.role = user.role
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

else:
    # --- DASHBOARD VIEW ---
    st.sidebar.markdown(f"### 👋 Welcome, {st.session_state.username}")
    st.sidebar.markdown(f"<span class='role-pill'>{st.session_state.role}</span>", unsafe_allow_html=True)
    
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()

    st.header("🏢 Business Profiles")
    
    with st.expander("➕ Register a Business"):
        with st.form("add_biz"):
            b_name = st.text_input("Business Name")
            b_ind = st.selectbox("Industry", ["Retail", "Service", "Food", "Other"])
            if st.form_submit_button("Save"):
                with get_session() as db:
                    new_biz = Business(owner_id=st.session_state.user_id, name=b_name, industry=b_ind)
                    db.add(new_biz)
                st.success(f"Registered {b_name}!")
                st.rerun()

    # Show existing profiles
    with get_session() as db:
        profiles = db.query(Business).filter_by(owner_id=st.session_state.user_id).all()
        for b in profiles:
            st.markdown(f"""
            <div class="biz-card">
                <h3 style="margin:0;">{b.name}</h3>
                <p style="margin:0; color:#666;">Industry: {b.industry}</p>
            </div>
            """, unsafe_allow_html=True)
