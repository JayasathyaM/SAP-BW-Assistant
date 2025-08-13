#!/usr/bin/env python3
"""
SAP BW Process Chain Chatbot with Authentication
Main application entry point
"""

import sys
import streamlit as st
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from ui.login_page import show_login_page, check_authentication, get_current_user, logout

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="SAP BW Process Chain Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Check authentication
    if not check_authentication():
        # Show login page
        show_login_page()
        return
    
    # User is authenticated - show main application
    show_main_application()

def show_main_application():
    """Show main chatbot application for authenticated users"""
    
    user = get_current_user()
    
    if not user:
        st.error("❌ Authentication error. Please login again.")
        logout()
        st.rerun()
        return
    
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("🤖 SAP BW Process Chain Chatbot")
        st.caption("Your intelligent assistant for SAP BW process chains")
    
    with col2:
        st.markdown(f"**👤 Welcome, {user['username']}**")
        st.caption(f"Role: {user['role']}")
    
    with col3:
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout()
            st.success("✅ Logged out successfully!")
            st.rerun()
    
    st.markdown("---")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        
        page = st.radio(
            "Select Page:",
            ["💬 Chat", "📊 Dashboard", "⚙️ Settings"],
            index=0
        )
        
        # User info section
        st.markdown("---")
        st.markdown("### 👤 User Info")
        st.info(f"""
        **Username:** {user['username']}  
        **Role:** {user['role']}  
        **Email:** {user['email']}
        """)
        
        # Quick actions
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Session", use_container_width=True):
            st.success("Session refreshed!")
        
        if user['role'] == 'admin':
            if st.button("👥 Manage Users", use_container_width=True):
                st.session_state.show_user_management = True
    
    # Main content area
    if page == "💬 Chat":
        show_chat_page(user)
    elif page == "📊 Dashboard":
        show_dashboard_page(user)
    elif page == "⚙️ Settings":
        show_settings_page(user)
    
    # Show user management if admin requested it
    if user['role'] == 'admin' and getattr(st.session_state, 'show_user_management', False):
        show_user_management_page()

def show_chat_page(user):
    """Show the main chat interface"""
    
    st.header("💬 SAP BW Process Chain Chat")
    st.markdown("Ask me anything about your SAP BW process chains!")
    
    # Placeholder chat interface
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Hello {user['username']}! I'm your SAP BW assistant. I can help you with:\n"
                          "• Process chain status checks\n"
                          "• Error analysis and troubleshooting\n"
                          "• Performance monitoring\n"
                          "• Execution history\n\n"
                          "What would you like to know?"
            }
        ]
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your SAP BW process chains..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simulated bot response (replace with actual SAP BW integration later)
        with st.chat_message("assistant"):
            if "status" in prompt.lower():
                response = "🔍 I would check the process chain status in SAP BW for you. Currently, this is a demo version. The actual integration with SAP BW will be implemented in the next phase."
            elif "error" in prompt.lower():
                response = "🚨 I would analyze errors in your process chains. In the full version, I'll connect to SAP BW tables to provide detailed error analysis."
            elif "help" in prompt.lower():
                response = "💡 I can help you with:\n• Process chain monitoring\n• Error troubleshooting\n• Performance analysis\n• Historical data review"
            else:
                response = f"Thank you for your question: '{prompt}'. I'm currently in demo mode. The full SAP BW integration will be available soon!"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def show_dashboard_page(user):
    """Show dashboard with process chain overview"""
    
    st.header("📊 Process Chain Dashboard")
    
    # Sample dashboard content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏃 Running", "5", "2")
    
    with col2:
        st.metric("✅ Completed", "12", "3")
    
    with col3:
        st.metric("❌ Failed", "2", "-1")
    
    with col4:
        st.metric("⏸️ Pending", "3", "1")
    
    st.markdown("---")
    
    # Sample process chain list
    st.subheader("📋 Recent Process Chains")
    
    import pandas as pd
    
    sample_data = {
        "Process Chain": ["ZBW_SALES_LOAD", "ZBW_INVENTORY", "ZBW_FINANCE", "ZBW_CUSTOMER"],
        "Status": ["✅ Completed", "🏃 Running", "❌ Failed", "⏸️ Pending"],
        "Last Run": ["2024-01-19 10:30", "2024-01-19 11:15", "2024-01-19 09:45", "2024-01-19 12:00"],
        "Duration": ["15 min", "Running...", "5 min", "Waiting..."]
    }
    
    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True)
    
    # Note about demo data
    st.info("📝 **Note:** This is sample data for demonstration. Real data will be retrieved from your SAP BW system.")

def show_settings_page(user):
    """Show user settings page"""
    
    st.header("⚙️ Settings")
    
    tab1, tab2 = st.tabs(["👤 Profile", "🔔 Notifications"])
    
    with tab1:
        st.subheader("Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Username", value=user['username'], disabled=True)
            st.text_input("Email", value=user['email'])
        
        with col2:
            st.text_input("Role", value=user['role'], disabled=True)
            st.selectbox("Theme", ["Light", "Dark", "Auto"])
        
        if st.button("💾 Save Changes"):
            st.success("✅ Settings saved!")
    
    with tab2:
        st.subheader("Notification Preferences")
        
        st.checkbox("📧 Email notifications for failed process chains")
        st.checkbox("🔔 Browser notifications")
        st.checkbox("📱 SMS alerts for critical errors")
        
        if st.button("💾 Save Notifications"):
            st.success("✅ Notification settings saved!")

def show_user_management_page():
    """Show user management page (admin only)"""
    
    st.markdown("---")
    st.header("👥 User Management (Admin)")
    
    # Get auth manager from session
    auth_manager = st.session_state.auth_manager
    users = auth_manager.get_users()
    
    # Display users table
    import pandas as pd
    df = pd.DataFrame(users)
    st.dataframe(df, use_container_width=True)
    
    # Close button
    if st.button("❌ Close User Management"):
        st.session_state.show_user_management = False
        st.rerun()

if __name__ == "__main__":
    main() 