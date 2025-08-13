"""
Modern Login UI - Version 2: Minimalist Dark Theme
Clean, professional interface with subtle animations and dark aesthetics
"""

import streamlit as st

def show_modern_login_v2():
    # Custom CSS for minimalist dark theme
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: #0f1419;
        font-family: 'Poppins', sans-serif;
    }
    
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
    }
    
    .login-box {
        background: #1a1f2e;
        border-radius: 16px;
        padding: 50px 40px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        border: 1px solid #2d3748;
        max-width: 420px;
        width: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .login-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        animation: gradientShift 3s ease-in-out infinite;
    }
    
    @keyframes gradientShift {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .brand-section {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .brand-icon {
        font-size: 3rem;
        margin-bottom: 15px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .brand-title {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    .brand-subtitle {
        color: #8892b0;
        font-size: 0.9rem;
        font-weight: 400;
    }
    
    .input-group {
        margin-bottom: 25px;
        position: relative;
    }
    
    .stTextInput > div > div > input {
        background: #2d3748;
        border: 2px solid #4a5568;
        border-radius: 12px;
        color: #ffffff;
        padding: 16px 20px;
        font-size: 15px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        background: #374151;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #8892b0;
    }
    
    .options-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        font-size: 14px;
    }
    
    .forgot-link {
        color: #667eea;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    .forgot-link:hover {
        color: #764ba2;
    }
    
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 12px;
        color: white;
        padding: 16px 24px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .primary-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .primary-button:hover::before {
        left: 100%;
    }
    
    .primary-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    .divider {
        text-align: center;
        margin: 30px 0;
        position: relative;
        color: #8892b0;
        font-size: 14px;
    }
    
    .divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #4a5568;
        z-index: 1;
    }
    
    .divider span {
        background: #1a1f2e;
        padding: 0 20px;
        position: relative;
        z-index: 2;
    }
    
    .secondary-buttons {
        display: flex;
        gap: 15px;
    }
    
    .secondary-button {
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 10px;
        color: #ffffff;
        padding: 12px 20px;
        font-size: 14px;
        cursor: pointer;
        flex: 1;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .secondary-button:hover {
        background: #374151;
        border-color: #667eea;
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main content
    st.markdown("""
    <div class="login-container">
        <div class="login-box">
            <div class="brand-section">
                <div class="brand-icon">🚀</div>
                <div class="brand-title">SAP BW Portal</div>
                <div class="brand-subtitle">Enterprise Process Intelligence</div>
            </div>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("dark_login_form"):
        st.markdown('<div class="input-group">', unsafe_allow_html=True)
        username = st.text_input("", placeholder="Enter your username", key="dark_username")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="input-group">', unsafe_allow_html=True)
        password = st.text_input("", placeholder="Enter your password", type="password", key="dark_password")
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            remember = st.checkbox("Keep me signed in", key="dark_remember")
        with col2:
            st.markdown('<div style="text-align: right; margin-top: 8px;"><a href="#" class="forgot-link">Forgot password?</a></div>', unsafe_allow_html=True)
        
        login_clicked = st.form_submit_button("Sign In", use_container_width=True)
    
    # Alternative login options
    st.markdown("""
        <div class="divider">
            <span>or continue with</span>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        sso_clicked = st.button("🔐 SSO Login", use_container_width=True, key="dark_sso")
    with col2:
        ldap_clicked = st.button("🏢 Active Directory", use_container_width=True, key="dark_ldap")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    return login_clicked, username, password, remember, sso_clicked, ldap_clicked

if __name__ == "__main__":
    st.set_page_config(page_title="Dark Login", layout="wide")
    show_modern_login_v2() 