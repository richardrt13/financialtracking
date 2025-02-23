import streamlit as st
from auth_manager import AuthManager

def login_page():
    """Render login page"""
    st.title("🔐 Login")
    
    # Initialize auth manager
    auth_manager = AuthManager(st.secrets["mongo_uri"])
    
    # Check if already logged in
    current_user = auth_manager.get_current_user()
    if current_user:
        st.success(f"Você já está logado como {current_user['name']}!")
        if st.button("Sair"):
            auth_manager.logout_user()
            st.rerun()
        return True
