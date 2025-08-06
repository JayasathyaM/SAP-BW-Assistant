"""
SAP BW Process Chain Visualizations

This module provides interactive charts and visualizations for SAP BW process chain data
using Plotly for enhanced analytical capabilities.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class SAPBWVisualizations:
    """
    Advanced visualization generator for SAP BW process chain analytics
    """
    
    def __init__(self):
        """Initialize the visualization generator"""
        # Define consistent color scheme for SAP BW status
        self.status_colors = {
            'SUCCESS': '#28a745',    # Green
            'FAILED': '#dc3545',     # Red
            'RUNNING': '#fd7e14',    # Orange
            'WAITING': '#007bff',    # Blue
            'CANCELLED': '#6c757d'   # Gray
        }
        
        # Define chart theme
        self.chart_theme = {
            'font_family': 'Arial, sans-serif',
            'font_size': 12,
            'title_font_size': 16,
            'background_color': 'rgba(0,0,0,0)',
            'grid_color': 'rgba(128,128,128,0.2)',
            'text_color': '#333333'
        }
    
    def create_status_pie_chart(self, status_data: pd.DataFrame) -> go.Figure:
        """
        Create an interactive pie chart for process chain status distribution
        
        Args:
            status_data: DataFrame with STATUS_OF_PROCESS column
            
        Returns:
            Plotly figure object
        """
        if status_data.empty or 'STATUS_OF_PROCESS' not in status_data.columns:
            return self._create_empty_chart("No status data available")
        
        # Count status occurrences
        status_counts = status_data['STATUS_OF_PROCESS'].value_counts()
        
        # Create colors list matching status order
        colors = [self.status_colors.get(status, '#999999') for status in status_counts.index]
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,  # Donut chart
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textinfo='label+percent+value',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': '🎯 Process Chain Status Distribution',
                'x': 0.5,
                'font': {'size': self.chart_theme['title_font_size']}
            },
            font={'family': self.chart_theme['font_family'], 'size': self.chart_theme['font_size']},
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
            margin=dict(t=60, b=20, l=20, r=120),
            paper_bgcolor=self.chart_theme['background_color'],
            plot_bgcolor=self.chart_theme['background_color']
        )
        
        return fig
    
    def create_success_rate_bar_chart(self, performance_data: pd.DataFrame) -> go.Figure:
        """
        Create a horizontal bar chart for process chain success rates
        
        Args:
            performance_data: DataFrame with CHAIN_ID and success_rate_percent columns
            
        Returns:
            Plotly figure object
        """
        if performance_data.empty or 'success_rate_percent' not in performance_data.columns:
            return self._create_empty_chart("No performance data available")
        
        # Sort by success rate for better visualization
        sorted_data = performance_data.sort_values('success_rate_percent', ascending=True)
        
        # Create color scale based on success rate
        colors = []
        for rate in sorted_data['success_rate_percent']:
            if rate >= 95:
                colors.append('#28a745')  # Green
            elif rate >= 80:
                colors.append('#ffc107')  # Yellow
            elif rate >= 60:
                colors.append('#fd7e14')  # Orange
            else:
                colors.append('#dc3545')  # Red
        
        fig = go.Figure(data=[go.Bar(
            x=sorted_data['success_rate_percent'],
            y=sorted_data['CHAIN_ID'],
            orientation='h',
            marker=dict(color=colors, line=dict(color='#FFFFFF', width=1)),
            text=[f"{rate:.1f}%" for rate in sorted_data['success_rate_percent']],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Success Rate: %{x:.1f}%<br>Total Runs: %{customdata}<extra></extra>',
            customdata=sorted_data.get('total_runs', [0] * len(sorted_data))
        )])
        
        fig.update_layout(
            title={
                'text': '📊 Process Chain Success Rates',
                'x': 0.5,
                'font': {'size': self.chart_theme['title_font_size']}
            },
            xaxis_title='Success Rate (%)',
            yaxis_title='Process Chain',
            font={'family': self.chart_theme['font_family'], 'size': self.chart_theme['font_size']},
            margin=dict(t=60, b=40, l=150, r=40),
            paper_bgcolor=self.chart_theme['background_color'],
            plot_bgcolor=self.chart_theme['background_color'],
            xaxis=dict(gridcolor=self.chart_theme['grid_color'], range=[0, 100]),
            yaxis=dict(gridcolor=self.chart_theme['grid_color'])
        )
        
        return fig
    
    def create_failure_analysis_chart(self, performance_data: pd.DataFrame) -> go.Figure:
        """
        Create a scatter plot for failure analysis (failure rate vs total runs)
        
        Args:
            performance_data: DataFrame with failure analysis data
            
        Returns:
            Plotly figure object
        """
        if performance_data.empty:
            return self._create_empty_chart("No failure data available")
        
        # Calculate failure rate
        performance_data = performance_data.copy()
        performance_data['failure_rate'] = 100 - performance_data.get('success_rate_percent', 0)
        
        # Create size based on total runs (for bubble chart effect)
        sizes = performance_data.get('total_runs', [10] * len(performance_data))
        sizes = [max(10, min(50, size/2)) for size in sizes]  # Scale bubble sizes
        
        fig = go.Figure(data=[go.Scatter(
            x=performance_data.get('total_runs', []),
            y=performance_data['failure_rate'],
            mode='markers+text',
            marker=dict(
                size=sizes,
                color=performance_data['failure_rate'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Failure Rate (%)"),
                line=dict(color='#FFFFFF', width=1)
            ),
            text=performance_data['CHAIN_ID'],
            textposition='middle center',
            textfont=dict(size=8, color='white'),
            hovertemplate='<b>%{text}</b><br>Total Runs: %{x}<br>Failure Rate: %{y:.1f}%<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': '🔍 Failure Analysis: Rate vs Volume',
                'x': 0.5,
                'font': {'size': self.chart_theme['title_font_size']}
            },
            xaxis_title='Total Runs',
            yaxis_title='Failure Rate (%)',
            font={'family': self.chart_theme['font_family'], 'size': self.chart_theme['font_size']},
            margin=dict(t=60, b=40, l=60, r=120),
            paper_bgcolor=self.chart_theme['background_color'],
            plot_bgcolor=self.chart_theme['background_color'],
            xaxis=dict(gridcolor=self.chart_theme['grid_color']),
            yaxis=dict(gridcolor=self.chart_theme['grid_color'])
        )
        
        return fig
    
    def create_activity_timeline(self, activity_data: pd.DataFrame) -> go.Figure:
        """
        Create a timeline chart for recent process chain activity
        
        Args:
            activity_data: DataFrame with CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME
            
        Returns:
            Plotly figure object
        """
        if activity_data.empty:
            return self._create_empty_chart("No activity data available")
        
        # Prepare data for timeline
        activity_data = activity_data.copy()
        
        # Create datetime column for proper sorting
        if 'CURRENT_DATE' in activity_data.columns and 'TIME' in activity_data.columns:
            activity_data['datetime'] = pd.to_datetime(
                activity_data['CURRENT_DATE'].astype(str) + ' ' + activity_data['TIME'].astype(str),
                errors='coerce'
            )
        else:
            activity_data['datetime'] = pd.to_datetime('now')
        
        # Sort by datetime
        activity_data = activity_data.sort_values('datetime')
        
        # Create timeline chart
        fig = go.Figure()
        
        for i, (_, row) in enumerate(activity_data.iterrows()):
            status = row.get('STATUS_OF_PROCESS', 'UNKNOWN')
            color = self.status_colors.get(status, '#999999')
            
            fig.add_trace(go.Scatter(
                x=[row['datetime']],
                y=[row['CHAIN_ID']],
                mode='markers',
                marker=dict(size=12, color=color, line=dict(color='white', width=2)),
                name=status,
                showlegend=i == 0 or status not in [trace.name for trace in fig.data],
                hovertemplate=f'<b>{row["CHAIN_ID"]}</b><br>Status: {status}<br>Time: {row["datetime"]}<extra></extra>'
            ))
        
        fig.update_layout(
            title={
                'text': '⏰ Recent Process Chain Activity',
                'x': 0.5,
                'font': {'size': self.chart_theme['title_font_size']}
            },
            xaxis_title='Execution Time',
            yaxis_title='Process Chain',
            font={'family': self.chart_theme['font_family'], 'size': self.chart_theme['font_size']},
            margin=dict(t=60, b=40, l=150, r=40),
            paper_bgcolor=self.chart_theme['background_color'],
            plot_bgcolor=self.chart_theme['background_color'],
            xaxis=dict(gridcolor=self.chart_theme['grid_color']),
            yaxis=dict(gridcolor=self.chart_theme['grid_color'])
        )
        
        return fig
    
    def create_performance_dashboard(self, status_data: pd.DataFrame, 
                                   performance_data: pd.DataFrame) -> List[go.Figure]:
        """
        Create a comprehensive dashboard with multiple visualizations
        
        Args:
            status_data: Current status data
            performance_data: Performance metrics data
            
        Returns:
            List of Plotly figures for dashboard display
        """
        charts = []
        
        # 1. Status distribution pie chart
        if not status_data.empty:
            charts.append(self.create_status_pie_chart(status_data))
        
        # 2. Success rate bar chart
        if not performance_data.empty:
            charts.append(self.create_success_rate_bar_chart(performance_data))
        
        # 3. Failure analysis scatter plot
        if not performance_data.empty:
            charts.append(self.create_failure_analysis_chart(performance_data))
        
        # 4. Activity timeline
        if not status_data.empty:
            charts.append(self.create_activity_timeline(status_data))
        
        return charts
    
    def create_chat_response_chart(self, data: pd.DataFrame, question: str) -> Optional[go.Figure]:
        """
        Create appropriate chart based on the user's question and data
        
        Args:
            data: Query result data
            question: User's original question
            
        Returns:
            Plotly figure or None if no chart needed
        """
        if data.empty:
            return None
        
        question_lower = question.lower()
        
        # Status-related questions
        if "status" in question_lower and 'STATUS_OF_PROCESS' in data.columns:
            return self.create_status_pie_chart(data)
        
        # Success rate questions
        elif any(word in question_lower for word in ['success', 'performance', 'rate']) and 'success_rate_percent' in data.columns:
            return self.create_success_rate_bar_chart(data)
        
        # Failure analysis questions
        elif "fail" in question_lower and 'failed_runs' in data.columns:
            return self.create_failure_analysis_chart(data)
        
        # Activity/timeline questions
        elif any(word in question_lower for word in ['recent', 'activity', 'when', 'time']) and 'CURRENT_DATE' in data.columns:
            return self.create_activity_timeline(data)
        
        return None
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color=self.chart_theme['text_color'])
        )
        fig.update_layout(
            title={'text': '📊 Visualization', 'x': 0.5},
            xaxis={'visible': False},
            yaxis={'visible': False},
            paper_bgcolor=self.chart_theme['background_color'],
            plot_bgcolor=self.chart_theme['background_color']
        )
        return fig

# Convenience functions
def get_visualizer() -> SAPBWVisualizations:
    """Get a configured visualization instance"""
    return SAPBWVisualizations()

def create_chart_for_query(data: pd.DataFrame, question: str) -> Optional[go.Figure]:
    """
    Quick function to create appropriate chart for a query
    
    Args:
        data: Query result DataFrame
        question: User's question
        
    Returns:
        Plotly figure or None
    """
    visualizer = get_visualizer()
    return visualizer.create_chat_response_chart(data, question) 