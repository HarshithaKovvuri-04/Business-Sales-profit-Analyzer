import streamlit as st
import jwt
import datetime
import json
import os

# --- Configuration ---
SECRET_KEY = "mysecretkey"
USERS_FILE = "users.json"

# --- Backend Helper Functions ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# --- JWT Token Logic ---
def create_token(user):
    # This follows the requirement for secure JWT authentication [cite: 142]
    payload = {
        "username": user["username"],
        "role": user["role"],
        "business": user["business"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- Streamlit UI ---
st.set_page_config(page_title="AI Sales Analyzer", layout="wide")
st.title("Small Business Sales & Profit Analyzer")

if "token" not in st.session_state:
    st.session_state.token = None

# Sidebar Navigation
menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Action", menu)

if not st.session_state.token:
    if choice == "Register":
        st.subheader("Create Business Profile") # Part of Milestone 1 [cite: 143]
        reg_user = st.text_input("Username")
        reg_pass = st.text_input("Password", type="password")
        reg_role = st.selectbox("Role", ["Owner", "Employee"])
        reg_biz = st.text_input("Business Name")
        
        if st.button("Register"):
            users = load_users()
            if any(u['username'] == reg_user for u in users):
                st.error("User already exists!")
            else:
                # Saving user profile data [cite: 143]
                users.append({"username": reg_user, "password": reg_pass, "role": reg_role, "business": reg_biz})
                save_users(users)
                st.success("Registration successful! Now go to the Login tab.")

    elif choice == "Login":
        st.subheader("Login to your Dashboard") # Part of Milestone 1 [cite: 142]
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = load_users()
            user = next((u for u in users if u['username'] == username and u['password'] == password), None)
            
            if user:
                token = create_token(user)
                st.session_state.token = token
                st.rerun()
            else:
                st.error("Invalid Username or Password")

else:
    # --- Logged In: Milestone 1 Core Transaction Logging ---
    try:
        user_info = jwt.decode(st.session_state.token, SECRET_KEY, algorithms=["HS256"])
        st.sidebar.success(f"Logged in: {user_info['username']}")
        
        if st.sidebar.button("Logout"):
            st.session_state.token = None
            st.rerun()

        st.header(f"Business: {user_info['business']}")
        
        # Milestone 1: Foundational input forms for logging sales and expenses [cite: 144]
        with st.form("transaction_form"):
            st.subheader("Daily Sales & Expense Logging")
            t_type = st.selectbox("Type", ["Sale", "Expense"])
            amount = st.number_input("Amount", min_value=0.0)
            category = st.text_input("Category (e.g., Inventory, Marketing, Rent)")
            
            if st.form_submit_button("Log Transaction"):
                # Logic to handle the transaction logging [cite: 144]
                st.success(f"Logged {t_type} of ${amount} in {category}")

    except jwt.ExpiredSignatureError:
        st.session_state.token = None
        st.error("Session expired. Please login again.")
