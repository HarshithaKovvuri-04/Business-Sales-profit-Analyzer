import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# --- 1. PROFESSIONAL UI STYLING ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #4f46e5; color: white; font-weight: bold; border: none;
    }
    .biz-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 6px solid #4f46e5; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .role-badge {
        background-color: #e0e7ff; color: #4338ca;
        padding: 5px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. THE SUCCESSFUL CONNECTION ---
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
    return create_engine(conn_url, pool_pre_ping=True)

engine = get_engine()
Base = declarative_base()

# --- 3. MODELS ---
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

# --- 4. APP INTERFACE ---
st.title("🚀 BizAnalyzer AI")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    tab1, tab2 = st.tabs(["**Login**", "**Register**"])
    
    with tab2:
        st.subheader("Join the Platform")
        with st.form("reg_form"):
            new_u = st.text_input("Username")
            new_p = st.text_input("Password", type="password")
            new_r = st.selectbox("Your Role", ["Owner", "Manager", "Analyst"])
            if st.form_submit_button("Create Account"):
                Session = sessionmaker(bind=engine)
                session = Session()
                try:
                    new_user = User(username=new_u, password=new_p, role=new_r)
                    session.add(new_user)
                    session.commit()
                    st.success(f"Account for {new_u} created! Please log in.")
                except Exception as e:
                    session.rollback()
                    st.error("Registration failed. User might already exist.")
                finally:
                    session.close()
                
    with tab1:
        st.subheader("Welcome Back")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                Session = sessionmaker(bind=engine)
                session = Session()
                user = session.query(User).filter_by(username=u, password=p).first()
                if user:
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    session.close()
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                session.close()

else:
    # --- LOGGED IN DASHBOARD ---
    st.sidebar.markdown(f"### 👋 Hello, {st.session_state.username}")
    st.sidebar.markdown(f"<span class='role-badge'>{st.session_state.role}</span>", unsafe_allow_html=True)
    
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()

    st.header("🏢 Your Business Profiles")
    
    with st.expander("➕ Register a New Business Entity"):
        with st.form("add_biz"):
            b_name = st.text_input("Business Name")
            b_ind = st.selectbox("Industry", ["Retail", "Service", "Food", "Manufacturing"])
            if st.form_submit_button("Save Profile"):
                Session = sessionmaker(bind=engine)
                session = Session()
                new_biz = Business(owner_id=st.session_state.user_id, name=b_name, industry=b_ind)
                session.add(new_biz)
                session.commit()
                session.close()
                st.success(f"Registered {b_name}!")
                st.rerun()

    # Display Profiles
    Session = sessionmaker(bind=engine)
    session = Session()
    my_biz = session.query(Business).filter_by(owner_id=st.session_state.user_id).all()
    for b in my_biz:
        st.markdown(f"""
        <div class="biz-card">
            <h3 style="margin:0;">{b.name}</h3>
            <p style="margin:0; color: #666;">Industry: {b.industry}</p>
        </div>
        """, unsafe_allow_html=True)
    session.close()
