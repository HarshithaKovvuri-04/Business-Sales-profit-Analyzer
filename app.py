import streamlit as st
import jwt
import datetime
import json
import os

# --- CONFIGURATION (From Page 3 of PDF) ---
SECRET_KEY = "mysecretkey" # [cite: 16]
USERS_FILE = "users.json" # [cite: 17]

# --- HELPER FUNCTIONS (From Pages 3 & 4 of PDF) ---
def load_users():
    if not os.path.exists(USERS_FILE): return [] # [cite: 21]
    with open(USERS_FILE, "r") as f:
        return json.load(f) # [cite: 22]

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2) # [cite: 25]

# --- AUTHENTICATION LOGIC (From Pages 5 & 6 of PDF) ---
def create_token(user):
    # JWT Creation Flow: Creates token with username and role [cite: 5, 43]
    payload = {
        "username": user["username"],
        "role": user["role"],
        "business": user["business"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1) # [cite: 44]
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256") # [cite: 41]

# --- STREAMLIT UI ---
st.title("Small Business Sales & Profit Analyzer")

if "token" not in st.session_state:
    st.session_state.token = None

# Sidebar for Login/Register [cite: 74, 142]
menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if not st.session_state.token:
    if choice == "Register":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type='password')
        role = st.selectbox("Role", ["Owner", "Employee"]) # [cite: 52]
        biz = st.text_input("Business Name") # [cite: 27]
        
        if st.button("Register"):
            users = load_users()
            if any(u['username'] == new_user for u in users): # [cite: 28]
                st.error("User already exists") # [cite: 29]
            else:
                users.append({"username": new_user, "password": new_pass, "role": role, "business": biz}) # [cite: 31]
                save_users(users)
                st.success("Registration successful!") # [cite: 32]

    elif choice == "Login":
        st.subheader("Login Section")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        
        if st.button("Login"):
            users = load_users()
            user = next((u for u in users if u['username'] == username and u['password'] == password), None) # [cite: 39]
            
            if user:
                token = create_token(user)
                st.session_state.token = token # Client stores JWT [cite: 102]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials") # [cite: 40]

else:
    # --- LOGGED IN AREA (Milestone 1 Transactions) ---
    decoded_token = jwt.decode(st.session_state.token, SECRET_KEY, algorithms=["HS256"])
    st.sidebar.write(f"Logged in as: {decoded_token['username']} ({decoded_token['role']})")
    
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()

    # Milestone 1: Implement foundational input forms for logging sales and expenses 
    st.header(f"Dashboard: {decoded_token['business']}")
    
    with st.form("transaction_form"):
        st.subheader("Log Daily Sales & Expenses") # [cite: 126]
        t_type = st.selectbox("Type", ["Sale", "Expense"])
        category = st.selectbox("Category", ["Inventory", "Rent", "Marketing", "Sales Revenue"])
        amount = st.number_input("Amount", min_value=0.0)
        
        if st.form_submit_button("Submit Transaction"):
            # This follows the 'Server validates JWT for protected routes' logic [cite: 8, 61]
            if decoded_token['role'] == "Owner": # [cite: 68]
                st.success(f"Successfully logged {t_type} of ${amount}")
            else:
                st.warning("Only Owners can log financial transactions.") # [cite: 63]