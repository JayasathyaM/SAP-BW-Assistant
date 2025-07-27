"""
SAP BW Process Chain Chatbot - Main Application

This is the main entry point for the Streamlit chatbot application.
Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration
from config.settings import AppConfig

def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="SAP BW Process Chain Assistant",
        page_icon="🔗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Application header
    st.title("🔗 SAP BW Process Chain Assistant")
    st.markdown("---")
    
    # Development notice
    st.info("🚧 **Demo Version** - This is a localhost-only demonstration of the SAP BW Process Chain Chatbot")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        st.write("Ask questions about your SAP BW process chains:")
        
        # Placeholder for chat interface
        st.info("Chat interface will be implemented in Phase 4")
        
        # Sample questions
        with st.expander("📝 Sample Questions"):
            st.write("""
            **Status Queries:**
            - What's the status of process chain PC_SALES_DAILY?
            - Show me all failed process chains today
            - When did PC_INVENTORY last run?
            
            **Analytical Queries:**
            - Which process chains fail most often?
            - Show me process chain performance this month
            - What are the longest running chains?
            """)
    
    with col2:
        st.header("📊 Dashboard")
        st.write("Real-time process chain metrics:")
        
        # Placeholder for dashboard
        st.info("Dashboard widgets will be implemented in Phase 4")
        
        # Sample metrics
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        with metrics_col1:
            st.metric("Total Chains", "42", "2")
        with metrics_col2:
            st.metric("Success Rate", "94.2%", "1.2%")
        with metrics_col3:
            st.metric("Failed Today", "3", "-1")
    
    # Footer
    st.markdown("---")
    st.markdown("*SAP BW Process Chain Chatbot POC - Localhost Demo*")

if __name__ == "__main__":
    main() 