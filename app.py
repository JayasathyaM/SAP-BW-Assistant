"""
SAP BW Process Chain Chatbot - Enhanced Main Application

This is the production-ready entry point for the enhanced Streamlit chatbot application
with intelligent features, smart suggestions, and professional user experience.
Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our enhanced components
from config.settings import AppConfig
from llm.query_processor import QueryProcessor
from database.db_manager_sqlite import DatabaseManager, SAPBWQueries
from ui.visualizations import get_visualizer, create_chart_for_query
from ui.enhancements import get_ui_enhancer, apply_sap_bw_styling, LoadingManager, show_operation_result
from ui.enhanced_chat import (
    create_enhanced_chat_interface, 
    process_enhanced_query,
    SmartSuggestions,
    EnhancedResponseFormatter,
    ChatContext
)

@st.cache_resource
def initialize_enhanced_components():
    """
    Initialize enhanced database and AI components (cached for performance)
    
    Returns:
        Tuple of (db_manager, query_processor, sap_queries) or (None, None, None) if failed
    """
    try:
        # Initialize database manager
        db_manager = DatabaseManager(AppConfig.DATABASE_PATH)
        if not db_manager.initialize_pool():
            st.error("❌ Failed to connect to database")
            return None, None, None
        
        # Initialize SAP BW queries helper
        sap_queries = SAPBWQueries(db_manager)
        
        # Initialize enhanced AI query processor
        with st.spinner("🤖 Loading Enhanced AI model... (this may take a few minutes on first run)"):
            query_processor = QueryProcessor(
                model_name=AppConfig.AI_MODEL_NAME,
                auto_load=False  # We'll load manually to show progress
            )
            
            if not query_processor.initialize():
                st.warning("⚠️ Enhanced AI model failed to load. Using intelligent fallback mode.")
                return db_manager, None, sap_queries
        
        st.success("✅ Enhanced AI model loaded successfully!")
        return db_manager, query_processor, sap_queries
        
    except Exception as e:
        st.error(f"❌ Failed to initialize enhanced components: {e}")
        return None, None, None

def initialize_enhanced_session_state():
    """Initialize enhanced session state for chat with context tracking"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    
    if "chat_context" not in st.session_state:
        st.session_state.chat_context = ChatContext()
    
    if "enhanced_mode" not in st.session_state:
        st.session_state.enhanced_mode = True

def format_enhanced_response(df: pd.DataFrame, query_type: str = "general") -> str:
    """Enhanced response formatting with intelligence"""
    if df.empty:
        return "🔍 No data found. Try adjusting your query or time frame."
    
    count = len(df)
    
    # Smart response based on query type and data
    if query_type == "failed" or "FAILED" in str(df.get("STATUS_OF_PROCESS", "")):
        if count == 0:
            return "🎉 Excellent! No process chains are currently in failed state."
        else:
            return f"⚠️ Found {count} failed process chain(s) requiring attention. Review the details below for immediate action."
    
    elif query_type == "performance":
        return f"📊 Performance analysis complete for {count} process chains. Check success rates and identify optimization opportunities."
    
    elif query_type == "status":
        return f"📋 Current status retrieved for {count} process chains. Monitor running chains and investigate any issues."
    
    else:
        return f"✅ Query successful: {count} records found. Data is displayed below with interactive options."

def main():
    """Enhanced main application entry point with intelligent features"""
    
    # Enhanced page configuration
    st.set_page_config(
        page_title="SAP BW Process Chain Assistant - Enhanced",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply enhanced UI styling
    ui_enhancer = get_ui_enhancer()
    ui_enhancer.apply_custom_styling()
    
    # Initialize enhanced session state
    initialize_enhanced_session_state()
    
    # Initialize enhanced components (cached)
    db_manager, query_processor, sap_queries = initialize_enhanced_components()
    
    # Enhanced application header
    st.markdown('<h1 class="main-header">🚀 SAP BW Process Chain Assistant - Enhanced</h1>', unsafe_allow_html=True)
    st.markdown("*Intelligent AI-powered assistant with smart suggestions and advanced insights*")
    st.markdown("---")
    
    # Status indicator with enhanced info
    if db_manager is None:
        ui_enhancer.show_error_alert("Database connection failed", "Please check database configuration")
        return
    
    # Enhanced sidebar with system status and analytics
    with st.sidebar:
        st.header("🎛️ Enhanced System Status")
        
        # Component status with enhanced indicators
        db_status = "🟢 Connected" if db_manager else "🔴 Failed"
        st.markdown(f"**Database:** {db_status}")
        
        ai_status = "🟢 Ready" if query_processor and query_processor.is_ready else "🟡 Fallback Mode"
        st.markdown(f"**Enhanced AI:** {ai_status}")
        
        st.markdown("---")
        
        # Enhanced quick stats with insights
        st.header("📈 Live Analytics")
        
        try:
            # Get enhanced database info
            db_info = db_manager.get_database_info()
            if "tables" in db_info:
                total_records = sum(db_info["tables"].values())
                ui_enhancer.create_metric_card("Total Records", f"{total_records:,}", "📊")
                
                # Get live status distribution
                status_query = """
                SELECT STATUS_OF_PROCESS as status, COUNT(*) as count 
                FROM VW_LATEST_CHAIN_RUNS 
                WHERE rn = 1 
                GROUP BY STATUS_OF_PROCESS
                """
                status_data = db_manager.execute_query(status_query)
                
                if status_data:
                    for status_row in status_data:
                        status = status_row['status']
                        count = status_row['count']
                        
                        if status == 'SUCCESS':
                            st.metric("✅ Successful", count, delta="Active")
                        elif status == 'FAILED':
                            st.metric("❌ Failed", count, delta="Needs Attention")
                        elif status == 'RUNNING':
                            st.metric("🔄 Running", count, delta="In Progress")
                        elif status == 'WAITING':
                            st.metric("⏳ Waiting", count, delta="Queued")
                
                # Session analytics
                if hasattr(st.session_state, 'chat_context'):
                    context = st.session_state.chat_context
                    success_rate = context.get_success_rate()
                    session_duration = context.get_session_duration()
                    
                    st.markdown("---")
                    st.markdown("**🎯 Session Stats**")
                    st.metric("Success Rate", f"{success_rate:.0f}%")
                    st.metric("Session Time", f"{session_duration}min")
                    st.metric("Queries", context.query_count)
        
        except Exception as e:
            st.warning("Unable to load enhanced stats")
        
        # Enhanced help section
        st.markdown("---")
        st.header("💡 Enhanced Features")
        st.markdown("""
        **🎯 Smart Suggestions**
        - Context-aware query recommendations
        - Dynamic suggestions based on data
        
        **🧠 Intelligent Responses**  
        - AI-generated insights and recommendations
        - Professional formatting with highlights
        
        **🔍 Advanced Analytics**
        - Performance analysis and trends
        - Failure pattern recognition
        
        **⚡ Enhanced Experience**
        - Conversation context memory
        - Error recovery and fallbacks
        """)
    
    # Enhanced development notice
    ui_enhancer.show_info_alert(
        "🚀 Enhanced Live Demo", 
        "Production-ready SAP BW Process Chain Assistant with advanced AI capabilities and intelligent user experience!"
    )
    
    # Create enhanced layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Enhanced Chat Interface Section
        st.header("💬 Intelligent Chat Assistant")
        
        # Create enhanced chat interface with all features
        suggestions_engine, response_formatter = create_enhanced_chat_interface(
            db_manager, query_processor, sap_queries
        )
        
        # Enhanced chat history display
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    # Display message content with enhanced formatting
                    if message.get("enhanced_response"):
                        # Show enhanced response
                        enhanced_resp = message["enhanced_response"]
                        st.markdown(f"**📋 {enhanced_resp['summary']}**")
                        
                        # Show insights if available
                        if enhanced_resp.get("insights"):
                            with st.expander("💡 Key Insights"):
                                for insight in enhanced_resp["insights"]:
                                    st.markdown(f"• {insight}")
                        
                        # Show recommendations
                        if enhanced_resp.get("recommendations"):
                            with st.expander("🎯 Recommendations"):
                                for rec in enhanced_resp["recommendations"]:
                                    st.markdown(f"• {rec}")
                    else:
                        # Standard message display
                        st.write(message["content"])
                    
                    # Show data if available
                    if message.get("sql_result") is not None and not message["sql_result"].empty:
                        
                        # Create enhanced dataframe display
                        df = message["sql_result"]
                        ui_enhancer.create_enhanced_dataframe(df, "Query Results")
                        
                        # Add visualization if appropriate
                        try:
                            chart = create_chart_for_query(df, message.get("original_query", ""))
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                        except Exception:
                            pass  # Skip visualization errors
                    
                    # Show SQL in expandable section
                    if message.get("sql_query") and message["sql_query"] != "-- Intelligent fallback query used":
                        with st.expander("🔍 Generated SQL"):
                            st.code(message["sql_query"], language="sql")
        
        # Enhanced chat input with smart processing
        if user_input := st.chat_input("Ask me anything about SAP BW process chains..."):
            
            # Add user message to history
            st.session_state.messages.append({
                "role": "user", 
                "content": user_input,
                "timestamp": datetime.now(),
                "original_query": user_input
            })
            
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
            
            # Process with enhanced intelligence
            with st.chat_message("assistant"):
                
                # Use enhanced query processing
                with LoadingManager("🤖 Processing with enhanced AI intelligence...") as loader:
                    
                    process_enhanced_query(
                        user_input, 
                        db_manager, 
                        query_processor, 
                        sap_queries, 
                        response_formatter,
                        st.session_state.chat_context
                    )
                
                # Force refresh to show new messages
                st.rerun()
    
    with col2:
        # Enhanced Dashboard Section
        st.header("📊 Live Dashboard")
        
        # Get dashboard data
        try:
            visualizer = get_visualizer()
            
            # Enhanced KPI section
            st.subheader("🎯 Key Performance Indicators")
            
            # Get live metrics
            metrics_query = """
            SELECT 
                COUNT(DISTINCT CHAIN_ID) as total_chains,
                AVG(CASE WHEN STATUS_OF_PROCESS = 'SUCCESS' THEN 100.0 ELSE 0.0 END) as avg_success_rate,
                COUNT(CASE WHEN STATUS_OF_PROCESS = 'FAILED' THEN 1 END) as failed_today
            FROM VW_LATEST_CHAIN_RUNS 
            WHERE rn = 1
            """
            
            metrics_result = db_manager.execute_query(metrics_query)
            if metrics_result:
                metrics = metrics_result[0]
                
                # Enhanced metrics display
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    ui_enhancer.create_metric_card(
                        "Total Chains", 
                        str(metrics.get('total_chains', 0)),
                        "📊"
                    )
                
                with col_b:
                    success_rate = metrics.get('avg_success_rate', 0)
                    ui_enhancer.create_metric_card(
                        "Success Rate",
                        f"{success_rate:.1f}%",
                        "🎯"
                    )
                
                with col_c:
                    failed_count = metrics.get('failed_today', 0)
                    ui_enhancer.create_metric_card(
                        "Failed Today",
                        str(failed_count),
                        "⚠️" if failed_count > 0 else "✅"
                    )
            
            # Enhanced visualizations
            st.subheader("📈 Enhanced Analytics")
            
            # Status distribution with enhanced chart
            status_data = db_manager.execute_query_to_dataframe("""
                SELECT STATUS_OF_PROCESS as STATUS, COUNT(*) as count 
                FROM VW_LATEST_CHAIN_RUNS 
                WHERE rn = 1 
                GROUP BY STATUS_OF_PROCESS
            """)
            
            if not status_data.empty:
                status_chart = visualizer.create_status_pie_chart(status_data)
                st.plotly_chart(status_chart, use_container_width=True)
            
            # Performance analysis
            performance_data = db_manager.execute_query_to_dataframe("""
                SELECT CHAIN_ID, success_rate_percent, total_runs, failed_runs
                FROM VW_CHAIN_SUMMARY 
                WHERE total_runs >= 2
                ORDER BY success_rate_percent ASC 
                LIMIT 10
            """)
            
            if not performance_data.empty:
                st.subheader("📉 Chains Needing Attention")
                perf_chart = visualizer.create_success_rate_bar_chart(performance_data)
                st.plotly_chart(perf_chart, use_container_width=True)
            
            # Enhanced data export
            st.subheader("📥 Enhanced Data Export")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                if st.button("📊 Export Status Data"):
                    csv_data = status_data.to_csv(index=False)
                    st.download_button(
                        label="Download Status CSV",
                        data=csv_data,
                        file_name=f"sap_bw_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with export_col2:
                if st.button("📈 Export Performance"):
                    if not performance_data.empty:
                        csv_data = performance_data.to_csv(index=False)
                        st.download_button(
                            label="Download Performance CSV",
                            data=csv_data,
                            file_name=f"sap_bw_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
            
            # Enhanced auto-refresh
            st.subheader("🔄 Enhanced Auto-Refresh")
            auto_refresh = st.checkbox("Enable Smart Refresh (30s)")
            
            if auto_refresh:
                time.sleep(30)
                st.rerun()
        
        except Exception as e:
            ui_enhancer.show_error_alert("Dashboard Error", str(e))
    
    # Enhanced footer
    st.markdown("---")
    st.markdown(
        '<div class="footer">🚀 SAP BW Process Chain Assistant - Enhanced Edition | '
        'Powered by Advanced AI & Intelligent Analytics</div>', 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 