"""
SAP BW Response Formatter

This module provides intelligent formatting for different types of query results
from SAP BW process chains, making data readable and actionable for users.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, date, time
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseType(Enum):
    """Types of responses for different query patterns"""
    STATUS = "status"              # Chain status queries
    ANALYTICAL = "analytical"      # Analysis and statistics
    HISTORICAL = "historical"      # Time-based data
    COUNT = "count"               # Count and aggregation queries
    LIST = "list"                 # Simple list results
    ERROR = "error"               # Error responses
    EMPTY = "empty"               # No data found

class FormatStyle(Enum):
    """Output format styles"""
    CONVERSATIONAL = "conversational"  # Natural language
    STRUCTURED = "structured"          # Structured text
    TABLE = "table"                    # Table format
    SUMMARY = "summary"                # Summary format

class ResponseFormatter:
    """
    Intelligent response formatter for SAP BW process chain queries
    """
    
    def __init__(self, default_style: FormatStyle = FormatStyle.CONVERSATIONAL):
        """
        Initialize the response formatter
        
        Args:
            default_style: Default formatting style
        """
        self.default_style = default_style
        self.max_rows_display = 20
        self.date_format = "%Y-%m-%d"
        self.time_format = "%H:%M:%S"
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        
        logger.info(f"ResponseFormatter initialized with style: {default_style.value}")
    
    def format_response(self, 
                       data: Union[pd.DataFrame, List[Dict], Dict, str], 
                       query_type: ResponseType,
                       question: str = "",
                       style: Optional[FormatStyle] = None) -> str:
        """
        Format query results based on data type and query pattern
        
        Args:
            data: Query results (DataFrame, list, dict, or string)
            query_type: Type of query/response
            question: Original user question for context
            style: Formatting style to use
            
        Returns:
            Formatted response string
        """
        if style is None:
            style = self.default_style
        
        try:
            # Handle different data types
            if isinstance(data, str):
                return self._format_string_response(data, query_type, style)
            elif isinstance(data, pd.DataFrame):
                return self._format_dataframe_response(data, query_type, question, style)
            elif isinstance(data, (list, dict)):
                return self._format_structured_response(data, query_type, question, style)
            else:
                return self._format_error_response(f"Unsupported data type: {type(data)}")
                
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return self._format_error_response(f"Error formatting response: {e}")
    
    def _format_dataframe_response(self, 
                                 df: pd.DataFrame, 
                                 query_type: ResponseType,
                                 question: str,
                                 style: FormatStyle) -> str:
        """Format pandas DataFrame responses"""
        
        if df.empty:
            return self._format_empty_response(question, style)
        
        # Route to specific formatters based on query type
        if query_type == ResponseType.STATUS:
            return self._format_status_response(df, question, style)
        elif query_type == ResponseType.ANALYTICAL:
            return self._format_analytical_response(df, question, style)
        elif query_type == ResponseType.HISTORICAL:
            return self._format_historical_response(df, question, style)
        elif query_type == ResponseType.COUNT:
            return self._format_count_response(df, question, style)
        elif query_type == ResponseType.LIST:
            return self._format_list_response(df, question, style)
        else:
            return self._format_generic_response(df, question, style)
    
    def _format_status_response(self, df: pd.DataFrame, question: str, style: FormatStyle) -> str:
        """Format process chain status responses"""
        
        if style == FormatStyle.CONVERSATIONAL:
            if len(df) == 1:
                # Single chain status
                row = df.iloc[0]
                chain_id = row.get('chain_id', 'Unknown')
                status = row.get('status_of_process', 'Unknown')
                date_col = row.get('current_date', row.get('time', ''))
                
                status_emoji = self._get_status_emoji(status)
                
                response = f"🔍 **Status of {chain_id}**\n\n"
                response += f"{status_emoji} **{status.upper()}**"
                
                if date_col:
                    response += f" (as of {self._format_datetime(date_col)})"
                
                response += "\n\n"
                
                # Add context based on status
                if status.upper() == 'FAILED':
                    response += "❗ This process chain has failed. You may want to check the logs for details."
                elif status.upper() == 'SUCCESS':
                    response += "✅ This process chain completed successfully."
                elif status.upper() == 'RUNNING':
                    response += "⏳ This process chain is currently running."
                else:
                    response += f"ℹ️ Current status: {status}"
                
                return response
            
            else:
                # Multiple chain status
                response = f"📊 **Process Chain Status Summary** ({len(df)} chains)\n\n"
                
                status_counts = df['status_of_process'].value_counts() if 'status_of_process' in df.columns else {}
                
                for status, count in status_counts.items():
                    emoji = self._get_status_emoji(status)
                    response += f"{emoji} **{status.upper()}**: {count} chains\n"
                
                response += "\n**Details:**\n"
                
                for _, row in df.head(self.max_rows_display).iterrows():
                    chain_id = row.get('chain_id', 'Unknown')
                    status = row.get('status_of_process', 'Unknown')
                    emoji = self._get_status_emoji(status)
                    response += f"{emoji} {chain_id}: {status.upper()}\n"
                
                if len(df) > self.max_rows_display:
                    response += f"\n... and {len(df) - self.max_rows_display} more chains"
                
                return response
        
        else:
            return self._format_table_response(df, "Process Chain Status")
    
    def _format_analytical_response(self, df: pd.DataFrame, question: str, style: FormatStyle) -> str:
        """Format analytical/statistical responses"""
        
        if style == FormatStyle.CONVERSATIONAL:
            response = "📈 **Analysis Results**\n\n"
            
            # Check for common analytical columns
            if 'success_rate_percent' in df.columns:
                response += "**Success Rate Analysis:**\n"
                for _, row in df.head(10).iterrows():
                    chain_id = row.get('chain_id', 'Unknown')
                    success_rate = row.get('success_rate_percent', 0)
                    total_runs = row.get('total_runs', 0)
                    
                    rate_emoji = "🟢" if success_rate >= 90 else "🟡" if success_rate >= 75 else "🔴"
                    response += f"{rate_emoji} **{chain_id}**: {success_rate:.1f}% ({total_runs} runs)\n"
            
            elif any(col in df.columns for col in ['count', 'total', 'sum']):
                # Count/aggregation results
                if len(df) == 1 and len(df.columns) == 1:
                    value = df.iloc[0, 0]
                    response += f"📊 **Result**: {value:,}"
                    
                    # Add context based on the question
                    if 'failed' in question.lower():
                        response += " failed process chains"
                    elif 'success' in question.lower():
                        response += " successful process chains"
                    elif 'total' in question.lower():
                        response += " total process chains"
                else:
                    response += self._format_table_response(df, "Analytical Results")
            
            else:
                response += self._format_table_response(df, "Analysis")
            
            return response
        
        else:
            return self._format_table_response(df, "Analytical Results")
    
    def _format_historical_response(self, df: pd.DataFrame, question: str, style: FormatStyle) -> str:
        """Format historical/time-based responses"""
        
        if style == FormatStyle.CONVERSATIONAL:
            response = "📅 **Historical Data**\n\n"
            
            # Sort by date/time if available
            date_cols = ['current_date', 'created_timestamp', 'time']
            sort_col = None
            for col in date_cols:
                if col in df.columns:
                    sort_col = col
                    break
            
            if sort_col:
                df_sorted = df.sort_values(sort_col, ascending=False)
            else:
                df_sorted = df
            
            if 'last run' in question.lower() and len(df_sorted) > 0:
                # Latest run information
                latest = df_sorted.iloc[0]
                chain_id = latest.get('chain_id', 'Unknown')
                status = latest.get('status_of_process', 'Unknown')
                date_val = latest.get('current_date', latest.get('created_timestamp', ''))
                
                response += f"**Latest run of {chain_id}:**\n"
                response += f"🕐 **When**: {self._format_datetime(date_val)}\n"
                response += f"{self._get_status_emoji(status)} **Status**: {status.upper()}\n"
            
            else:
                # General historical data
                response += f"Showing {len(df_sorted)} records:\n\n"
                
                for _, row in df_sorted.head(self.max_rows_display).iterrows():
                    chain_id = row.get('chain_id', 'Unknown')
                    status = row.get('status_of_process', 'Unknown')
                    date_val = row.get('current_date', row.get('created_timestamp', ''))
                    
                    emoji = self._get_status_emoji(status)
                    date_str = self._format_datetime(date_val)
                    
                    response += f"{emoji} **{chain_id}** - {status.upper()} ({date_str})\n"
                
                if len(df_sorted) > self.max_rows_display:
                    response += f"\n... and {len(df_sorted) - self.max_rows_display} more records"
            
            return response
        
        else:
            return self._format_table_response(df, "Historical Data")
    
    def _format_count_response(self, df: pd.DataFrame, question: str, style: FormatStyle) -> str:
        """Format count/aggregation responses"""
        
        if len(df) == 1 and len(df.columns) == 1:
            # Single count value
            count = df.iloc[0, 0]
            
            if style == FormatStyle.CONVERSATIONAL:
                response = f"📊 **Count Result**: {count:,}"
                
                # Add context based on question
                if 'failed' in question.lower():
                    response += " failed process chains"
                    if count > 0:
                        response += "\n\n⚠️ You may want to investigate these failures."
                elif 'success' in question.lower():
                    response += " successful process chains"
                elif 'today' in question.lower():
                    response += " process chains ran today"
                elif 'total' in question.lower():
                    response += " total process chains"
                
                return response
            else:
                return f"Count: {count:,}"
        
        else:
            return self._format_table_response(df, "Count Results")
    
    def _format_list_response(self, df: pd.DataFrame, question: str, style: FormatStyle) -> str:
        """Format simple list responses"""
        
        if style == FormatStyle.CONVERSATIONAL:
            response = f"📋 **List Results** ({len(df)} items)\n\n"
            
            for i, row in df.head(self.max_rows_display).iterrows():
                if 'chain_id' in row:
                    chain_id = row['chain_id']
                    status = row.get('status_of_process', '')
                    if status:
                        emoji = self._get_status_emoji(status)
                        response += f"{emoji} {chain_id} - {status.upper()}\n"
                    else:
                        response += f"• {chain_id}\n"
                else:
                    # Generic list item
                    response += f"• {', '.join(str(val) for val in row.values)}\n"
            
            if len(df) > self.max_rows_display:
                response += f"\n... and {len(df) - self.max_rows_display} more items"
            
            return response
        
        else:
            return self._format_table_response(df, "List Results")
    
    def _format_generic_response(self, df: pd.DataFrame, question: str, style: FormatStyle) -> str:
        """Format generic responses when type is unclear"""
        
        if style == FormatStyle.CONVERSATIONAL:
            response = f"📄 **Query Results** ({len(df)} rows, {len(df.columns)} columns)\n\n"
            response += self._format_table_response(df, "Results")
            return response
        else:
            return self._format_table_response(df, "Query Results")
    
    def _format_table_response(self, df: pd.DataFrame, title: str) -> str:
        """Format data as a readable table"""
        
        response = f"**{title}**\n\n"
        
        if len(df) == 0:
            return response + "No data found."
        
        # Limit rows for display
        display_df = df.head(self.max_rows_display)
        
        # Format columns
        formatted_columns = []
        for col in display_df.columns:
            formatted_col = col.replace('_', ' ').title()
            formatted_columns.append(formatted_col)
        
        # Create table string
        table_str = display_df.to_string(
            index=False,
            columns=display_df.columns,
            max_rows=self.max_rows_display,
            formatters=self._get_column_formatters(display_df)
        )
        
        # Replace column names with formatted versions
        lines = table_str.split('\n')
        if lines:
            # Replace header
            lines[0] = '  '.join(formatted_columns)
            table_str = '\n'.join(lines)
        
        response += f"```\n{table_str}\n```"
        
        if len(df) > self.max_rows_display:
            response += f"\n\n*Showing first {self.max_rows_display} of {len(df)} rows*"
        
        return response
    
    def _format_empty_response(self, question: str, style: FormatStyle) -> str:
        """Format response when no data is found"""
        
        if style == FormatStyle.CONVERSATIONAL:
            response = "🔍 **No Results Found**\n\n"
            response += "I couldn't find any data matching your query.\n\n"
            
            # Provide helpful suggestions based on the question
            if 'pc_' in question.lower():
                response += "💡 **Suggestions:**\n"
                response += "• Check if the process chain ID is correct\n"
                response += "• Try searching without the 'PC_' prefix\n"
                response += "• Use 'show all process chains' to see available chains\n"
            else:
                response += "💡 **Suggestions:**\n"
                response += "• Try a broader search\n"
                response += "• Check the date range\n"
                response += "• Use 'show all process chains' to see what's available\n"
            
            return response
        else:
            return "No data found for your query."
    
    def _format_string_response(self, data: str, query_type: ResponseType, style: FormatStyle) -> str:
        """Format string responses (usually errors)"""
        
        if query_type == ResponseType.ERROR:
            return self._format_error_response(data)
        else:
            return data
    
    def _format_structured_response(self, data: Union[List, Dict], query_type: ResponseType, question: str, style: FormatStyle) -> str:
        """Format list/dict responses"""
        
        if isinstance(data, dict):
            if style == FormatStyle.CONVERSATIONAL:
                response = "📊 **Results**\n\n"
                for key, value in data.items():
                    formatted_key = key.replace('_', ' ').title()
                    response += f"**{formatted_key}**: {value}\n"
                return response
            else:
                return json.dumps(data, indent=2)
        
        elif isinstance(data, list):
            if style == FormatStyle.CONVERSATIONAL:
                response = f"📋 **List Results** ({len(data)} items)\n\n"
                for i, item in enumerate(data[:self.max_rows_display], 1):
                    response += f"{i}. {item}\n"
                
                if len(data) > self.max_rows_display:
                    response += f"\n... and {len(data) - self.max_rows_display} more items"
                
                return response
            else:
                return '\n'.join(str(item) for item in data[:self.max_rows_display])
    
    def _format_error_response(self, error_message: str) -> str:
        """Format error responses"""
        
        response = "❌ **Error**\n\n"
        response += f"{error_message}\n\n"
        response += "💡 **What you can try:**\n"
        response += "• Rephrase your question\n"
        response += "• Ask for 'help' to see example questions\n"
        response += "• Check if you're asking about valid process chains\n"
        
        return response
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for process chain status"""
        
        status_upper = status.upper() if status else 'UNKNOWN'
        
        emoji_map = {
            'SUCCESS': '✅',
            'FAILED': '❌',
            'RUNNING': '⏳',
            'WAITING': '⏸️',
            'CANCELLED': '🚫',
            'UNKNOWN': '❓'
        }
        
        return emoji_map.get(status_upper, '❓')
    
    def _format_datetime(self, dt_value: Any) -> str:
        """Format datetime values consistently"""
        
        if pd.isna(dt_value) or dt_value is None:
            return "Unknown"
        
        try:
            if isinstance(dt_value, str):
                # Try to parse string datetime
                try:
                    dt = pd.to_datetime(dt_value)
                    return dt.strftime(self.datetime_format)
                except:
                    return str(dt_value)
            
            elif isinstance(dt_value, (datetime, pd.Timestamp)):
                return dt_value.strftime(self.datetime_format)
            
            elif isinstance(dt_value, date):
                return dt_value.strftime(self.date_format)
            
            elif isinstance(dt_value, time):
                return dt_value.strftime(self.time_format)
            
            else:
                return str(dt_value)
                
        except Exception:
            return str(dt_value)
    
    def _get_column_formatters(self, df: pd.DataFrame) -> Dict[str, callable]:
        """Get formatters for different column types"""
        
        formatters = {}
        
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                formatters[col] = lambda x: self._format_datetime(x)
            elif 'percent' in col.lower() or 'rate' in col.lower():
                formatters[col] = lambda x: f"{x:.1f}%" if pd.notnull(x) else ""
            elif df[col].dtype in ['int64', 'float64']:
                formatters[col] = lambda x: f"{x:,}" if pd.notnull(x) else ""
        
        return formatters

# Convenience functions
def format_response(data: Union[pd.DataFrame, List, Dict, str], 
                   query_type: ResponseType,
                   question: str = "",
                   style: FormatStyle = FormatStyle.CONVERSATIONAL) -> str:
    """
    Convenience function to format a response
    
    Args:
        data: Query results
        query_type: Type of response
        question: Original question
        style: Formatting style
        
    Returns:
        Formatted response string
    """
    formatter = ResponseFormatter(style)
    return formatter.format_response(data, query_type, question, style)

def format_status_response(df: pd.DataFrame, question: str = "") -> str:
    """Quick format for status responses"""
    return format_response(df, ResponseType.STATUS, question)

def format_analytical_response(df: pd.DataFrame, question: str = "") -> str:
    """Quick format for analytical responses"""
    return format_response(df, ResponseType.ANALYTICAL, question)

def format_error_response(error_message: str) -> str:
    """Quick format for error responses"""
    return format_response(error_message, ResponseType.ERROR)

# Test function
def test_response_formatter():
    """Test the response formatter with sample data"""
    
    # Sample data
    status_data = pd.DataFrame({
        'chain_id': ['PC_SALES_DAILY', 'PC_INVENTORY_WEEKLY'],
        'status_of_process': ['SUCCESS', 'FAILED'],
        'current_date': ['2024-01-15', '2024-01-15'],
        'time': ['08:30:00', '09:15:00']
    })
    
    analytical_data = pd.DataFrame({
        'chain_id': ['PC_SALES_DAILY', 'PC_INVENTORY_WEEKLY'],
        'success_rate_percent': [95.5, 78.2],
        'total_runs': [100, 50],
        'failed_runs': [5, 11]
    })
    
    formatter = ResponseFormatter()
    
    print("Testing Response Formatter")
    print("=" * 50)
    
    # Test status formatting
    print("\n📊 STATUS RESPONSE:")
    print(formatter.format_response(status_data, ResponseType.STATUS, "What's the status of process chains?"))
    
    print("\n📈 ANALYTICAL RESPONSE:")
    print(formatter.format_response(analytical_data, ResponseType.ANALYTICAL, "Which chains have the worst success rates?"))
    
    print("\n❌ ERROR RESPONSE:")
    print(formatter.format_response("Database connection failed", ResponseType.ERROR))
    
    print("\n🔍 EMPTY RESPONSE:")
    empty_df = pd.DataFrame()
    print(formatter.format_response(empty_df, ResponseType.STATUS, "Status of PC_NONEXISTENT"))

if __name__ == "__main__":
    test_response_formatter() 