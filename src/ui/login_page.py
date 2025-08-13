"""
Login page UI for SAP BW Chatbot
"""

import streamlit as st
from typing import Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path to import auth module
sys.path.append(str(Path(__file__).parent.parent))

from auth.auth_manager import AuthManager

def show_login_page() -> Optional[Dict]:
    """Display login page and handle authentication"""
    
    # Initialize auth manager
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    
    auth_manager = st.session_state.auth_manager
    
    # Page styling
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .stForm {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
    }
    
    /* Make text input labels darker and more visible */
    .stTextInput label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    
    /* Make text input text darker */
    .stTextInput > div > div > input {
        color: #1a1a1a !important;
        font-weight: 500 !important;
        border: 2px solid #e0e0e0 !important;
        background-color: #ffffff !important;
    }
    
    /* Make text input focused state darker */
    .stTextInput > div > div > input:focus {
        border-color: #2c3e50 !important;
        box-shadow: 0 0 0 0.2rem rgba(44, 62, 80, 0.25) !important;
    }
    
    /* Make placeholder text darker */
    .stTextInput > div > div > input::placeholder {
        color: #666666 !important;
        opacity: 1 !important;
    }
    
    /* Make form section headers darker */
    .stForm h3 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
    }
    
    /* Make checkbox labels darker */
    .stCheckbox label {
        color: #1a1a1a !important;
        font-weight: 500 !important;
    }
    
    /* Make help text darker */
    .stTextInput .help {
        color: #4a4a4a !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header
        st.markdown("""
        <div class="login-header">
            <h1>🤖 SAP BW Chatbot</h1>
            <h3>Please Login to Continue</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=True):
            st.markdown("### 🔐 Login")
            
            username = st.text_input(
                "👤 Username",
                placeholder="Enter your username",
                help="Default users: admin or user"
            )
            
            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Enter your password",
                help="Default passwords: admin123 or user123"
            )
            
            remember_me = st.checkbox("📌 Remember me")
            
            # Login button
            login_clicked = st.form_submit_button(
                "🚀 Login",
                type="primary",
                use_container_width=True
            )
        
        # Handle login
        if login_clicked:
            if username and password:
                user_data = auth_manager.authenticate(username, password)
                
                if user_data:
                    # Store user data in session state
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    st.session_state.remember_me = remember_me
                    
                    st.success(f"✅ Welcome back, {user_data['username']}!")
                    st.balloons()
                    
                    # Auto redirect after 2 seconds
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
                    st.warning("💡 Try: admin/admin123 or user/user123")
            else:
                st.warning("⚠️ Please enter both username and password")
        
        # Show registration option
        st.markdown("---")
        if st.button("👥 New User? Create Account", use_container_width=True):
            st.session_state.show_registration = True
            st.rerun()
        
        # Show registration form if requested
        if getattr(st.session_state, 'show_registration', False):
            show_registration_form(auth_manager)
        
        # Default credentials info
        with st.expander("ℹ️ Default Login Credentials"):
            st.info("""
            **For testing purposes:**
            
            **🔑 Admin User:**
            - Username: `admin`
            - Password: `admin123`
            - Access: Full system access
            
            **👤 Regular User:**
            - Username: `user`  
            - Password: `user123`
            - Access: Chat functionality
            """)

def show_registration_form(auth_manager: AuthManager) -> None:
    """Show user registration form"""
    
    st.markdown("---")
    st.markdown("### 👥 Create New Account")
    
    with st.form("registration_form"):
        new_username = st.text_input(
            "👤 New Username",
            placeholder="Choose a username"
        )
        new_email = st.text_input(
            "📧 Email Address",
            placeholder="your.email@company.com"
        )
        new_password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Choose a secure password"
        )
        confirm_password = st.text_input(
            "🔒 Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )
        
        col_create, col_cancel = st.columns(2)
        
        with col_create:
            create_clicked = st.form_submit_button(
                "✅ Create Account",
                type="primary",
                use_container_width=True
            )
        
        with col_cancel:
            cancel_clicked = st.form_submit_button(
                "❌ Cancel",
                use_container_width=True
            )
    
    if create_clicked:
        if not all([new_username, new_email, new_password, confirm_password]):
            st.error("❌ Please fill in all fields")
        elif new_password != confirm_password:
            st.error("❌ Passwords do not match")
        elif len(new_password) < 6:
            st.error("❌ Password must be at least 6 characters")
        else:
            if auth_manager.create_user(new_username, new_password, new_email):
                st.success(f"✅ Account created successfully for {new_username}")
                st.info("💡 You can now login with your new credentials")
                st.session_state.show_registration = False
                st.rerun()
            else:
                st.error("❌ Username already exists")
    
    if cancel_clicked:
        st.session_state.show_registration = False
        st.rerun()

def check_authentication() -> bool:
    """Check if user is authenticated"""
    return getattr(st.session_state, 'authenticated', False)

def get_current_user() -> Optional[Dict]:
    """Get current user data"""
    if check_authentication():
        return st.session_state.user
    return None

def logout():
    """Logout user and clear session"""
    for key in ['authenticated', 'user', 'remember_me', 'show_registration']:
        if key in st.session_state:
            del st.session_state[key] 