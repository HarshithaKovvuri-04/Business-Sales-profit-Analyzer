import streamlit as st
import jwt
import datetime
import json
import os

# --- Configuration & Setup ---
SECRET_KEY = "your_super_secret_key_123"
DB_FILE = "users.json"

# --- Backend: Data Management ---
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- Backend: JWT Logic (Milestone 1) ---
def create_token(user_data):
    # Establish secure user authentication using JSON Web Tokens (JWT) 
    payload = {
        "username": user_data["username"],
        "biz_name": user_data["business"],
        "role": user_data["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- UI Layout ---
st.set_page_config(page_title="BizAnalyzer - Milestone 1", layout="wide")
st.title("Small Business Sales & Profit Analyzer")

if "token" not in st.session_state:
    st.session_state.token = None

# Sidebar for Authentication [cite: 195]
st.sidebar.title("User Accounts")
auth_mode = st.sidebar.radio("Select Action", ["Login", "Register"])

if not st.session_state.token:
    if auth_mode == "Register":
        st.subheader("Register Business Profile") # cite: 176
        reg_user = st.text_input("Username")
        reg_pass = st.text_input("Password", type="password")
        reg_biz = st.text_input("Business Name")
        reg_role = st.selectbox("Role", ["Owner", "Employee"]) # cite: 164
        
        if st.button("Create Account"):
            db = load_db()
            if any(u["username"] == reg_user for u in db):
                st.error("Username already taken.")
            else:
                db.append({
                    "username": reg_user, 
                    "password": reg_pass, 
                    "business": reg_biz, 
                    "role": reg_role
                })
                save_db(db)
                st.success("Registration successful! Switch to Login.")

    elif auth_mode == "Login":
        st.subheader("Secure Login") # cite: 174
        user_in = st.text_input("Username")
        pass_in = st.text_input("Password", type="password")
        
        if st.button("Login"):
            db = load_db()
            user = next((u for u in db if u["username"] == user_in and u["password"] == pass_in), None)
            if user:
                st.session_state.token = create_token(user)
                st.rerun()
            else:
                st.error("Invalid credentials.")

else:
    # --- Authenticated Dashboard ---
    try:
        user_info = jwt.decode(st.session_state.token, SECRET_KEY, algorithms=["HS256"])
        st.sidebar.success(f"Logged in: {user_info['username']}")
        st.sidebar.info(f"Business: {user_info['biz_name']}")
        
        if st.sidebar.button("Logout"):
            st.session_state.token = None
            st.rerun()

        # --- Milestone 1: Core Transaction Logging ---
        st.header("Daily Sales & Expense Management") # cite: 168
        
        # Simple interface for adding transactions quickly [cite: 154]
        with st.form("transaction_entry"):
            st.subheader("New Transaction Entry") # cite: 177
            col1, col2 = st.columns(2)
            with col1:
                t_type = st.selectbox("Transaction Type", ["Sales", "Expense"])
                amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
            with col2:
                # Feature for expense categorization [cite: 151]
                category = st.selectbox("Category", ["Inventory", "Rent", "Marketing", "Utility", "Sales Revenue"])
                date = st.date_input("Date")
            
            if st.form_submit_button("Log Transaction"):
                # Role-based access control check [cite: 164]
                if user_info['role'] == "Owner":
                    st.success(f"Successfully logged {t_type} of ${amount} for {user_info['biz_name']}!")
                else:
                    st.warning("Only users with the 'Owner' role can log financial data.")

    except jwt.ExpiredSignatureError:
        st.session_state.token = None
        st.error("Session expired. Please login again.")
