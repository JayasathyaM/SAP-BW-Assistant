"""
Modern Login UI - Version 1: Glassmorphism Design
Sleek, modern interface with glass-like effects and smooth animations
"""

import streamlit as st

def show_modern_login_v1():
    # Custom CSS for glassmorphism effect
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    .main-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
    }
    
    .login-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        max-width: 400px;
        width: 100%;
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .login-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        font-weight: 400;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        color: white;
        padding: 15px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.5);
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.6);
    }
    
    .login-button {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        border: none;
        border-radius: 12px;
        color: white;
        padding: 15px 30px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
        margin-top: 20px;
    }
    
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
    }
    
    .forgot-password {
        text-align: center;
        margin-top: 20px;
    }
    
    .forgot-password a {
        color: rgba(255, 255, 255, 0.8);
        text-decoration: none;
        font-size: 14px;
        transition: color 0.3s ease;
    }
    
    .forgot-password a:hover {
        color: white;
    }
    
    .social-login {
        margin-top: 30px;
        text-align: center;
    }
    
    .social-button {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        color: white;
        padding: 12px 20px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
        width: 45%;
    }
    
    .social-button:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main content
    st.markdown("""
    <div class="main-container">
        <div class="login-card">
            <div class="login-header">
                <div class="login-title">🤖 SAP BW</div>
                <div class="login-subtitle">Process Chain Intelligence</div>
            </div>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("", placeholder="Username", key="username")
        password = st.text_input("", placeholder="Password", type="password", key="password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            remember_me = st.checkbox("Remember me")
        with col2:
            st.markdown('<div style="text-align: right; margin-top: 5px;"><a href="#" style="color: rgba(255,255,255,0.8); text-decoration: none; font-size: 14px;">Forgot?</a></div>', unsafe_allow_html=True)
        
        login_clicked = st.form_submit_button("Sign In", use_container_width=True)
    
    # Social login options
    st.markdown("""
        <div class="social-login">
            <div style="color: rgba(255,255,255,0.6); margin-bottom: 15px; font-size: 14px;">Or continue with</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 SSO", use_container_width=True):
            st.info("SSO login would go here")
    with col2:
        if st.button("🏢 LDAP", use_container_width=True):
            st.info("LDAP login would go here")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    return login_clicked, username, password, remember_me

if __name__ == "__main__":
    st.set_page_config(page_title="Modern Login", layout="wide")
    show_modern_login_v1() 