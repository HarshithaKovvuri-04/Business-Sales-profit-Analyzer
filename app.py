import streamlit as st
import jwt
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. THEME & CSS STYLING ---
def apply_custom_css():
    st.markdown("""
    <style>
        .main { background-color: #f0f2f6; }
        .stButton>button {
            width: 100%; border-radius: 10px; height: 3em;
            background-color: #4F46E5; color: white; font-weight: bold;
        }
        .biz-card {
            background-color: white; padding: 20px; border-radius: 15px;
            border-left: 8px solid #4F46E5; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        .role-badge {
            background-color: #E0E7FF; color: #4338CA;
            padding: 4px 12px; border-radius: 9999px; font-size: 0.8em;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ROBUST DATABASE SETUP ---
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
    # pool_pre_ping=True is the CRITICAL fix for the OperationalError
    return create_engine(conn_url, pool_pre_ping=True, pool_recycle=300)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()

# --- 3. DATABASE MODELS ---
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

# --- 4. APP LOGIC ---
apply_custom_css()
st.title("📊 BizAnalyzer AI")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["**Login**", "**Register**"])
    
    with tab2:
        st.subheader("Join BizAnalyzer")
        with st.form("register_form"):
            new_u = st.text_input("Username")
            new_p = st.text_input("Password", type="password")
            # ROLE SELECTION
            new_r = st.selectbox("Select Role", ["Owner", "Manager", "Analyst"])
            
            if st.form_submit_button("Create Account"):
                session = get_session()
                try:
                    user = User(username=new_u, password=new_p, role=new_r)
                    session.add(user)
                    session.commit()
                    st.success("Registration successful! Please switch to the Login tab.")
                except:
                    session.rollback()
                    st.error("Username already exists or connection failed.")
                finally:
                    session.close()

    with tab1:
        st.subheader("Welcome Back")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                session = get_session()
                user = session.query(User).filter_by(username=u, password=p).first()
                if user:
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    session.close()
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
                session.close()

else:
    # --- DASHBOARD VIEW ---
    st.sidebar.markdown(f"### 👋 Hello, {st.session_state.username}")
    st.sidebar.markdown(f"<span class='role-badge'>{st.session_state.role}</span>", unsafe_allow_html=True)
    
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()

    st.header("🏢 Your Business Profiles")
    
    with st.expander("➕ Add a New Business Entity"):
        with st.form("add_biz"):
            b_name = st.text_input("Business Name")
            b_ind = st.selectbox("Industry", ["Retail", "Service", "Food", "Manufacturing"])
            if st.form_submit_button("Register Business"):
                session = get_session()
                new_biz = Business(owner_id=st.session_state.user_id, name=b_name, industry=b_ind)
                session.add(new_biz)
                session.commit()
                session.close()
                st.success(f"{b_name} registered successfully!")
                st.rerun()

    # DISPLAY CARDS
    session = get_session()
    my_biz = session.query(Business).filter_by(owner_id=st.session_state.user_id).all()
    for b in my_biz:
        st.markdown(f"""
        <div class="biz-card">
            <h3 style="margin:0;">{b.name}</h3>
            <p style="margin:0; color: #666;">Industry: {b.industry}</p>
        </div>
        """, unsafe_allow_html=True)
    session.close()
