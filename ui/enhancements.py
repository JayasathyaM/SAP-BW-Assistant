"""
SAP BW Process Chain UI Enhancements

This module provides UI improvements including loading states, error notifications,
styling enhancements, and user experience optimizations.
"""

import streamlit as st
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import pandas as pd

class UIEnhancer:
    """
    UI enhancement utilities for better user experience
    """
    
    def __init__(self):
        """Initialize UI enhancer with custom styling"""
        self.custom_css = """
        <style>
        /* Custom CSS for SAP BW Assistant */
        
        .main > div {
            padding-top: 2rem;
        }
        
        /* Chat message styling */
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .chat-message.user {
            background-color: #e3f2fd;
            border-left: 4px solid #1976d2;
        }
        
        .chat-message.assistant {
            background-color: #f1f8e9;
            border-left: 4px solid #388e3c;
        }
        
        /* Status indicators */
        .status-success {
            color: #4caf50;
            font-weight: bold;
        }
        
        .status-failed {
            color: #f44336;
            font-weight: bold;
        }
        
        .status-running {
            color: #ff9800;
            font-weight: bold;
        }
        
        .status-waiting {
            color: #2196f3;
            font-weight: bold;
        }
        
        /* Loading animation */
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #1976d2;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Enhanced metrics */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 0.5rem;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        /* Dashboard cards */
        .dashboard-card {
            background: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        
        /* Success/Error alerts */
        .alert {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }
        
        .alert-success {
            background-color: #d4edda;
            border-color: #28a745;
            color: #155724;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            border-color: #17a2b8;
            color: #0c5460;
        }
        
        /* Improved buttons */
        .stButton > button {
            border-radius: 0.5rem;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(90deg, #1976d2, #388e3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        
        /* Sidebar enhancements */
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        /* Chart containers */
        .chart-container {
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            color: #6c757d;
            border-top: 1px solid #e0e0e0;
            margin-top: 2rem;
        }
        </style>
        """
    
    def apply_custom_styling(self):
        """Apply custom CSS styling"""
        st.markdown(self.custom_css, unsafe_allow_html=True)
    
    def show_loading_spinner(self, message: str = "Processing..."):
        """
        Display a loading spinner with message
        
        Args:
            message: Loading message to display
        """
        return st.empty().markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div class="loading-spinner"></div>
            <p style="margin-top: 1rem; color: #666;">{message}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def show_success_alert(self, message: str, details: Optional[str] = None):
        """Show success alert"""
        alert_html = f"""
        <div class="alert alert-success">
            <strong>✅ Success!</strong> {message}
            {f'<br><small>{details}</small>' if details else ''}
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)
    
    def show_error_alert(self, message: str, details: Optional[str] = None):
        """Show error alert"""
        alert_html = f"""
        <div class="alert alert-error">
            <strong>❌ Error!</strong> {message}
            {f'<br><small>{details}</small>' if details else ''}
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)
    
    def show_warning_alert(self, message: str, details: Optional[str] = None):
        """Show warning alert"""
        alert_html = f"""
        <div class="alert alert-warning">
            <strong>⚠️ Warning!</strong> {message}
            {f'<br><small>{details}</small>' if details else ''}
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)
    
    def show_info_alert(self, message: str, details: Optional[str] = None):
        """Show info alert"""
        alert_html = f"""
        <div class="alert alert-info">
            <strong>ℹ️ Info:</strong> {message}
            {f'<br><small>{details}</small>' if details else ''}
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)
    
    def create_metric_card(self, title: str, value: str, delta: Optional[str] = None):
        """
        Create an enhanced metric card
        
        Args:
            title: Metric title
            value: Metric value
            delta: Change indicator (optional)
        """
        delta_html = f'<div style="font-size: 0.8rem; margin-top: 0.5rem;">{delta}</div>' if delta else ''
        
        card_html = f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{title}</div>
            {delta_html}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    def create_status_badge(self, status: str) -> str:
        """
        Create a status badge with appropriate styling
        
        Args:
            status: Process chain status
            
        Returns:
            HTML string for status badge
        """
        status_configs = {
            'SUCCESS': {'emoji': '✅', 'class': 'status-success', 'text': 'Success'},
            'FAILED': {'emoji': '❌', 'class': 'status-failed', 'text': 'Failed'},
            'RUNNING': {'emoji': '🔄', 'class': 'status-running', 'text': 'Running'},
            'WAITING': {'emoji': '⏳', 'class': 'status-waiting', 'text': 'Waiting'},
            'CANCELLED': {'emoji': '🚫', 'class': 'status-cancelled', 'text': 'Cancelled'}
        }
        
        config = status_configs.get(status, {'emoji': '❓', 'class': '', 'text': status})
        
        return f'<span class="{config["class"]}">{config["emoji"]} {config["text"]}</span>'
    
    def show_processing_steps(self, steps: list, current_step: int = 0):
        """
        Show processing steps with progress indicator
        
        Args:
            steps: List of step descriptions
            current_step: Current step index (0-based)
        """
        progress_html = "<div style='margin: 1rem 0;'>"
        
        for i, step in enumerate(steps):
            if i < current_step:
                icon = "✅"
                style = "color: #28a745; font-weight: bold;"
            elif i == current_step:
                icon = "🔄"
                style = "color: #ffc107; font-weight: bold;"
            else:
                icon = "⏳"
                style = "color: #6c757d;"
            
            progress_html += f"<div style='{style} margin: 0.5rem 0;'>{icon} {step}</div>"
        
        progress_html += "</div>"
        st.markdown(progress_html, unsafe_allow_html=True)
    
    def create_enhanced_dataframe(self, df: pd.DataFrame, title: str = "Data Results"):
        """
        Create an enhanced dataframe display with title and styling
        
        Args:
            df: DataFrame to display
            title: Title for the dataframe
        """
        if df.empty:
            self.show_warning_alert("No data available", "The query returned no results.")
            return
        
        st.markdown(f"### 📊 {title}")
        st.markdown(f"*Showing {len(df)} records*")
        
        # Add download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.dataframe(df, use_container_width=True)
    
    def create_compact_progress_bar(self, progress: float, label: str = ""):
        """
        Create a compact progress bar
        
        Args:
            progress: Progress value (0.0 to 1.0)
            label: Optional label
        """
        percentage = int(progress * 100)
        color = "#28a745" if progress >= 0.8 else "#ffc107" if progress >= 0.5 else "#dc3545"
        
        progress_html = f"""
        <div style="margin: 0.5rem 0;">
            {f'<small>{label}</small><br>' if label else ''}
            <div style="background: #e9ecef; border-radius: 0.25rem; height: 0.5rem;">
                <div style="background: {color}; width: {percentage}%; height: 100%; border-radius: 0.25rem; transition: width 0.3s ease;"></div>
            </div>
            <small style="color: #6c757d;">{percentage}%</small>
        </div>
        """
        st.markdown(progress_html, unsafe_allow_html=True)

class LoadingManager:
    """
    Context manager for handling loading states
    """
    
    def __init__(self, message: str = "Processing...", enhancer: Optional[UIEnhancer] = None):
        """
        Initialize loading manager
        
        Args:
            message: Loading message
            enhancer: UI enhancer instance
        """
        self.message = message
        self.enhancer = enhancer or UIEnhancer()
        self.container = None
        self.start_time = None
    
    def __enter__(self):
        """Start loading state"""
        self.start_time = time.time()
        self.container = self.enhancer.show_loading_spinner(self.message)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End loading state"""
        if self.container:
            self.container.empty()
        
        # Show completion time for long operations
        if self.start_time:
            duration = time.time() - self.start_time
            if duration > 2:  # Show timing for operations > 2 seconds
                st.caption(f"⏱️ Completed in {duration:.1f} seconds")

def with_error_handling(func: Callable, error_message: str = "An error occurred"):
    """
    Decorator function to add error handling to operations
    
    Args:
        func: Function to wrap
        error_message: Custom error message
        
    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        enhancer = UIEnhancer()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            enhancer.show_error_alert(error_message, str(e))
            st.error(f"Technical details: {e}")
            return None
    return wrapper

# Convenience functions
def get_ui_enhancer() -> UIEnhancer:
    """Get a UI enhancer instance"""
    return UIEnhancer()

def apply_sap_bw_styling():
    """Apply SAP BW specific styling"""
    enhancer = get_ui_enhancer()
    enhancer.apply_custom_styling()

def show_operation_result(success: bool, success_msg: str, error_msg: str, details: Optional[str] = None):
    """
    Show operation result with appropriate styling
    
    Args:
        success: Whether operation was successful
        success_msg: Success message
        error_msg: Error message
        details: Optional details
    """
    enhancer = get_ui_enhancer()
    if success:
        enhancer.show_success_alert(success_msg, details)
    else:
        enhancer.show_error_alert(error_msg, details) 