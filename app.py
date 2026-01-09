import streamlit as st
import jwt
import datetime
import json
import os

# --- Configuration ---
SECRET_KEY = "super_secret_business_key"
DB_FILE = "users_db.json"

# --- Database Logic ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# --- Security Logic ---
def create_token(username):
    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- UI Setup ---
st.set_page_config(page_title="BizAnalyzer", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- AUTHENTICATION SECTION ---
if not st.session_state.token:
    st.title("🚀 Small Business Sales & Profit Analyzer")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab2:
        st.header("Create Account")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        role = st.selectbox("Your Primary Role", ["Owner", "Admin", "Manager"]) # cite: 164
        
        if st.button("Register"):
            db = load_db()
            if new_user in db:
                st.error("Username already exists.")
            else:
                # Initialize user with an empty list of businesses
                db[new_user] = {
                    "password": new_pass,
                    "role": role,
                    "businesses": [] # cite: 163
                }
                save_db(db)
                st.success("Account created! Please login.")

    with tab1:
        st.header("Login")
        username = st.text_input("Username", key="log_user")
        password = st.text_input("Password", type="password", key="log_pass")
        
        if st.button("Login"):
            db = load_db()
            if username in db and db[username]["password"] == password:
                st.session_state.token = create_token(username)
                st.session_state.current_user = username
                st.rerun()
            else:
                st.error("Invalid credentials.")

# --- POST-LOGIN: PROFILE & BUSINESS MANAGEMENT ---
else:
    try:
        # Verify Security with JWT 
        decoded = jwt.decode(st.session_state.token, SECRET_KEY, algorithms=["HS256"])
        user = st.session_state.current_user
        db = load_db()
        
        st.sidebar.title(f"Welcome, {user}")
        st.sidebar.info(f"Role: {db[user]['role']}")
        
        if st.sidebar.button("Logout"):
            st.session_state.token = None
            st.rerun()

        # Profile Page: Multi-Business Management [cite: 176]
        st.title("💼 User Profile & Businesses")
        
        # 1. Register a New Business
        with st.expander("➕ Register a New Business"):
            biz_name = st.text_input("Business Name")
            biz_type = st.selectbox("Industry", ["Retail", "Service", "Online Shop", "Food/Beverage"])
            if st.button("Create Business Profile"):
                if biz_name:
                    db[user]["businesses"].append({"name": biz_name, "type": biz_type})
                    save_db(db)
                    st.success(f"Registered {biz_name}!")
                    st.rerun()

        # 2. Display Existing Businesses
        st.subheader("Your Managed Businesses")
        if not db[user]["businesses"]:
            st.warning("No businesses registered yet.")
        else:
            cols = st.columns(3)
            for idx, biz in enumerate(db[user]["businesses"]):
                with cols[idx % 3]:
                    st.info(f"**{biz['name']}**\n\nType: {biz['type']}")
                    if st.button(f"Manage {biz['name']}", key=f"btn_{idx}"):
                        st.session_state.active_business = biz['name']
        
        # 3. Milestone 1: Transaction Logging Form 
        if "active_business" in st.session_state:
            st.divider()
            st.header(f"📝 Logging for: {st.session_state.active_business}")
            with st.form("log_entry"):
                t_type = st.selectbox("Transaction Type", ["Sales", "Expense"])
                cat = st.text_input("Category (e.g. Marketing, Rent)")
                amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Submit Entry"):
                    st.success(f"Recorded ${amt} for {st.session_state.active_business}")

    except jwt.ExpiredSignatureError:
        st.session_state.token = None
        st.error("Session expired. Please login again.")
