"""
Enhanced Chat Interface for SAP BW Process Chain Assistant

This module provides an intelligent chat interface with conversation context,
smart suggestions, error recovery, and enhanced user experience.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re

class ChatContext:
    """Manages conversation context and user session"""
    
    def __init__(self):
        """Initialize chat context"""
        self.session_start = datetime.now()
        self.query_count = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.user_preferences = {}
        
    def add_query_result(self, success: bool, query_type: str = "general"):
        """Track query results for analytics"""
        self.query_count += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        # Track preferences
        if query_type not in self.user_preferences:
            self.user_preferences[query_type] = 0
        self.user_preferences[query_type] += 1
    
    def get_success_rate(self) -> float:
        """Get current session success rate"""
        if self.query_count == 0:
            return 0.0
        return (self.successful_queries / self.query_count) * 100
    
    def get_session_duration(self) -> int:
        """Get session duration in minutes"""
        return int((datetime.now() - self.session_start).total_seconds() / 60)

class SmartSuggestions:
    """Provides intelligent query suggestions based on context and data"""
    
    def __init__(self, db_manager=None):
        """Initialize with database manager for dynamic suggestions"""
        self.db_manager = db_manager
        
    def get_smart_suggestions(self, user_input: str = "", chat_history: List = None) -> List[str]:
        """Generate smart suggestions based on user input and context"""
        
        suggestions = []
        
        # Base suggestions always available
        base_suggestions = [
            "Show me all failed process chains",
            "What is the success rate for each chain?",
            "Which chains are currently running?",
            "How many chains executed today?",
            "Show me today's process chain activity"
        ]
        
        # Context-aware suggestions based on user input
        if user_input:
            input_lower = user_input.lower()
            
            if "failed" in input_lower or "error" in input_lower:
                suggestions.extend([
                    "Show me all failed process chains from today",
                    "Which process chain fails most often?",
                    "What errors occurred in failed chains?"
                ])
            
            elif "success" in input_lower or "performance" in input_lower:
                suggestions.extend([
                    "Which chain has the highest success rate?",
                    "Show me performance summary for all chains",
                    "Compare success rates between chains"
                ])
            
            elif "running" in input_lower or "status" in input_lower:
                suggestions.extend([
                    "Show current status of all chains",
                    "Which chains are waiting to run?",
                    "List all active process chains"
                ])
            
            elif "today" in input_lower or "time" in input_lower:
                suggestions.extend([
                    "Show me today's process chain activity",
                    "How many chains ran successfully today?",
                    "What chains failed in the last hour?"
                ])
        
        # Add dynamic suggestions based on actual data
        if self.db_manager:
            try:
                # Get real chain names for specific suggestions
                chain_result = self.db_manager.execute_query(
                    "SELECT DISTINCT CHAIN_ID FROM VW_LATEST_CHAIN_RUNS LIMIT 3"
                )
                
                if chain_result:
                    for chain in chain_result:
                        chain_id = chain['CHAIN_ID']
                        suggestions.append(f"Show me the status of {chain_id}")
                
                # Add suggestions based on current failures
                failed_result = self.db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1"
                )
                
                if failed_result and failed_result[0]['count'] > 0:
                    suggestions.append(f"Investigate the {failed_result[0]['count']} failed chains")
                    
            except Exception:
                pass  # Ignore database errors for suggestions
        
        # Combine and deduplicate
        all_suggestions = base_suggestions + suggestions
        seen = set()
        unique_suggestions = []
        
        for suggestion in all_suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:8]  # Return top 8 suggestions
    
    def get_follow_up_suggestions(self, last_query: str, last_result: Any) -> List[str]:
        """Generate follow-up suggestions based on the last query and result"""
        
        follow_ups = []
        
        if not last_query:
            return follow_ups
        
        query_lower = last_query.lower()
        
        # Suggestions based on last query type
        if "failed" in query_lower:
            follow_ups.extend([
                "What caused these failures?",
                "When did these chains last succeed?",
                "Show me the success rate for these chains"
            ])
        
        elif "success rate" in query_lower or "performance" in query_lower:
            follow_ups.extend([
                "Which chain needs attention?",
                "Show me historical performance trends",
                "Compare with last month's performance"
            ])
        
        elif "running" in query_lower or "status" in query_lower:
            follow_ups.extend([
                "How long have they been running?",
                "Show me their typical execution time",
                "Are any chains delayed?"
            ])
        
        # Add data-driven follow-ups
        if hasattr(last_result, '__len__') and len(last_result) > 0:
            follow_ups.append(f"Get more details about these {len(last_result)} results")
            
            if hasattr(last_result, 'columns'):
                if 'CHAIN_ID' in last_result.columns:
                    follow_ups.append("Show execution history for these chains")
                if 'STATUS_OF_PROCESS' in last_result.columns:
                    follow_ups.append("Analyze status patterns for these chains")
        
        return follow_ups[:5]  # Return top 5 follow-ups

class EnhancedResponseFormatter:
    """Formats AI responses with context, insights, and user-friendly explanations"""
    
    def __init__(self):
        """Initialize the response formatter"""
        self.insights_cache = {}
    
    def format_intelligent_response(self, 
                                  query: str, 
                                  sql: str, 
                                  result: pd.DataFrame, 
                                  execution_time: float = 0.0) -> Dict[str, Any]:
        """Create an intelligent, context-aware response"""
        
        response = {
            "summary": "",
            "insights": [],
            "data_highlights": [],
            "recommendations": [],
            "technical_details": {
                "query": query,
                "sql": sql,
                "execution_time": execution_time,
                "result_count": len(result) if not result.empty else 0
            }
        }
        
        # Generate summary based on query type and results
        response["summary"] = self._generate_summary(query, result)
        
        # Add insights based on data analysis
        response["insights"] = self._generate_insights(query, result)
        
        # Highlight important data points
        response["data_highlights"] = self._generate_highlights(result)
        
        # Provide actionable recommendations
        response["recommendations"] = self._generate_recommendations(query, result)
        
        return response
    
    def _generate_summary(self, query: str, result: pd.DataFrame) -> str:
        """Generate a natural language summary of the results"""
        
        if result.empty:
            return "No data found matching your query. The process chains might all be in a different state, or there might be no recent activity."
        
        count = len(result)
        query_lower = query.lower()
        
        # Context-aware summaries
        if "failed" in query_lower:
            if count == 0:
                return "Great news! No process chains are currently in a failed state."
            elif count == 1:
                return f"Found 1 failed process chain that needs attention."
            else:
                return f"Found {count} failed process chains that require investigation."
        
        elif "success rate" in query_lower or "performance" in query_lower:
            if 'success_rate_percent' in result.columns:
                avg_success = result['success_rate_percent'].mean()
                return f"Analyzed performance for {count} process chains. Average success rate: {avg_success:.1f}%"
            else:
                return f"Retrieved performance data for {count} process chains."
        
        elif "running" in query_lower:
            if count == 0:
                return "No process chains are currently running."
            else:
                return f"Found {count} process chains currently in execution."
        
        elif "status" in query_lower:
            return f"Retrieved current status for {count} process chains."
        
        else:
            return f"Found {count} records matching your query."
    
    def _generate_insights(self, query: str, result: pd.DataFrame) -> List[str]:
        """Generate data-driven insights"""
        
        insights = []
        
        if result.empty:
            return insights
        
        # Status distribution insights
        if 'STATUS_OF_PROCESS' in result.columns:
            status_counts = result['STATUS_OF_PROCESS'].value_counts()
            
            if 'FAILED' in status_counts and status_counts['FAILED'] > 0:
                insights.append(f"⚠️ {status_counts['FAILED']} chains have failed status")
            
            if 'SUCCESS' in status_counts:
                insights.append(f"✅ {status_counts['SUCCESS']} chains completed successfully")
            
            if 'RUNNING' in status_counts and status_counts['RUNNING'] > 0:
                insights.append(f"🔄 {status_counts['RUNNING']} chains are currently executing")
        
        # Performance insights
        if 'success_rate_percent' in result.columns:
            low_performers = result[result['success_rate_percent'] < 80]
            if not low_performers.empty:
                insights.append(f"📉 {len(low_performers)} chains have success rates below 80%")
            
            high_performers = result[result['success_rate_percent'] >= 95]
            if not high_performers.empty:
                insights.append(f"🌟 {len(high_performers)} chains have excellent success rates (95%+)")
        
        # Time-based insights
        if 'CURRENT_DATE' in result.columns:
            today = datetime.now().strftime('%Y-%m-%d')
            today_records = result[result['CURRENT_DATE'] == today]
            if not today_records.empty:
                insights.append(f"📅 {len(today_records)} of these are from today")
        
        return insights
    
    def _generate_highlights(self, result: pd.DataFrame) -> List[str]:
        """Generate key data highlights"""
        
        highlights = []
        
        if result.empty:
            return highlights
        
        # Highlight critical issues
        if 'STATUS_OF_PROCESS' in result.columns:
            failed_chains = result[result['STATUS_OF_PROCESS'] == 'FAILED']
            if not failed_chains.empty and 'CHAIN_ID' in failed_chains.columns:
                top_failed = failed_chains['CHAIN_ID'].head(3).tolist()
                highlights.append(f"🚨 Critical: {', '.join(top_failed)} need immediate attention")
        
        # Highlight performance extremes
        if 'success_rate_percent' in result.columns and len(result) > 1:
            best_chain = result.loc[result['success_rate_percent'].idxmax()]
            worst_chain = result.loc[result['success_rate_percent'].idxmin()]
            
            highlights.append(f"🥇 Best performer: {best_chain.get('CHAIN_ID', 'Unknown')} ({best_chain['success_rate_percent']:.1f}%)")
            highlights.append(f"📉 Needs improvement: {worst_chain.get('CHAIN_ID', 'Unknown')} ({worst_chain['success_rate_percent']:.1f}%)")
        
        return highlights
    
    def _generate_recommendations(self, query: str, result: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if result.empty:
            recommendations.append("💡 Try broadening your search criteria or check different time periods")
            return recommendations
        
        query_lower = query.lower()
        
        # Failure-related recommendations
        if "failed" in query_lower and not result.empty:
            recommendations.extend([
                "🔍 Investigate error logs for root cause analysis",
                "📊 Check if failures correlate with specific time periods",
                "🔄 Consider implementing retry mechanisms for unstable chains"
            ])
        
        # Performance recommendations
        elif "success rate" in query_lower or "performance" in query_lower:
            if 'success_rate_percent' in result.columns:
                low_performers = result[result['success_rate_percent'] < 80]
                if not low_performers.empty:
                    recommendations.extend([
                        "⚠️ Focus on optimizing chains with <80% success rate",
                        "📈 Set up monitoring alerts for performance degradation",
                        "🔧 Review and optimize poorly performing process steps"
                    ])
        
        # Status monitoring recommendations
        elif "running" in query_lower:
            recommendations.extend([
                "⏱️ Monitor execution times to detect performance issues",
                "🔔 Set up alerts for long-running chains",
                "📊 Compare current runtime with historical averages"
            ])
        
        # General recommendations
        recommendations.append("📋 Export this data for further analysis and reporting")
        
        return recommendations[:4]  # Limit to top 4 recommendations

def create_enhanced_chat_interface(db_manager, query_processor, sap_queries):
    """Create the enhanced chat interface with all improvements"""
    
    # Initialize enhanced components
    if 'chat_context' not in st.session_state:
        st.session_state.chat_context = ChatContext()
    
    suggestions = SmartSuggestions(db_manager)
    formatter = EnhancedResponseFormatter()
    
    # Chat interface with enhanced features
    st.header("💬 Intelligent SAP BW Assistant")
    
    # Show session stats in a compact format
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Queries", st.session_state.chat_context.query_count)
    with col2:
        success_rate = st.session_state.chat_context.get_success_rate()
        st.metric("Success Rate", f"{success_rate:.0f}%")
    with col3:
        duration = st.session_state.chat_context.get_session_duration()
        st.metric("Session", f"{duration}m")
    
    # Smart suggestions section
    st.subheader("💡 Smart Suggestions")
    
    # Get current suggestions
    current_suggestions = suggestions.get_smart_suggestions(
        chat_history=st.session_state.get('messages', [])
    )
    
    # Display suggestions as clickable buttons
    suggestion_cols = st.columns(2)
    for i, suggestion in enumerate(current_suggestions[:6]):  # Show 6 suggestions
        col = suggestion_cols[i % 2]
        if col.button(f"💭 {suggestion}", key=f"suggestion_{i}"):
            # Simulate user input with the suggestion
            st.session_state.suggested_query = suggestion
            st.rerun()
    
    # Process suggested query if any
    if hasattr(st.session_state, 'suggested_query'):
        suggested_query = st.session_state.suggested_query
        del st.session_state.suggested_query
        
        # Add to chat history and process
        st.session_state.messages.append({
            "role": "user",
            "content": suggested_query,
            "timestamp": datetime.now(),
            "source": "suggestion"
        })
        
        # Process the suggested query
        process_enhanced_query(suggested_query, db_manager, query_processor, 
                             sap_queries, formatter, st.session_state.chat_context)
    
    return suggestions, formatter

def process_enhanced_query(user_input: str, db_manager, query_processor, 
                         sap_queries, formatter, chat_context):
    """Process user query with enhanced intelligence and error handling"""
    
    start_time = datetime.now()
    
    try:
        # Try AI-generated SQL first
        ai_success = False
        sql_query = None
        df_result = pd.DataFrame()
        
        if query_processor and query_processor.is_ready:
            with st.spinner("🤖 AI is analyzing your question..."):
                ai_result = query_processor.process_question(user_input)
                
                if ai_result and ai_result.get("success"):
                    sql_query = ai_result["sql"]
                    
                    # Execute AI-generated SQL
                    try:
                        # Check if it's an error SQL first
                        if sql_query.startswith("SELECT 'Failed to parse") or sql_query.startswith("SELECT 'Error:") or sql_query.startswith("SELECT 'No valid") or sql_query.startswith("SELECT 'Invalid") or sql_query.startswith("SELECT 'Dangerous"):
                            st.warning(f"⚠️ AI generated error SQL: {sql_query}")
                            ai_success = False
                        else:
                            df_result = db_manager.execute_query_to_dataframe(sql_query)
                            
                            # Additional check: if the result has an 'error' column, it's likely an error response
                            if not df_result.empty and 'error' in df_result.columns:
                                st.warning(f"⚠️ AI generated error result: {df_result.iloc[0]['error'] if len(df_result) > 0 else 'Unknown error'}")
                                ai_success = False
                            else:
                                ai_success = True
                                st.success("✅ AI successfully generated and executed query")
                    except Exception as sql_error:
                        st.warning(f"⚠️ AI-generated SQL failed: {str(sql_error)[:100]}")
                        ai_success = False
        
        # Fallback to predefined queries if AI failed
        if not ai_success or df_result.empty:
            with st.spinner("🔄 Using intelligent fallback..."):
                fallback_result = get_intelligent_fallback(user_input, sap_queries)
                if fallback_result is not None:
                    df_result = fallback_result if isinstance(fallback_result, pd.DataFrame) else pd.DataFrame(fallback_result)
                    sql_query = "-- Intelligent fallback query used"
                    st.info("🎯 Used intelligent fallback for reliable results")
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Generate enhanced response
        if not df_result.empty or ai_success:
            enhanced_response = formatter.format_intelligent_response(
                user_input, sql_query or "N/A", df_result, execution_time
            )
            
            # Display enhanced response
            display_enhanced_response(enhanced_response, df_result, sql_query)
            
            # Update context
            chat_context.add_query_result(True, classify_query_type(user_input))
            
            # Add to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": enhanced_response["summary"],
                "sql_result": df_result,
                "sql_query": sql_query,
                "timestamp": datetime.now(),
                "enhanced_response": enhanced_response
            })
            
        else:
            # Handle complete failure
            error_response = handle_query_failure(user_input, formatter)
            st.error(error_response["message"])
            
            # Update context
            chat_context.add_query_result(False, classify_query_type(user_input))
            
            # Add error to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_response["message"],
                "timestamp": datetime.now(),
                "error": True
            })
    
    except Exception as e:
        st.error(f"🚨 Unexpected error: {str(e)}")
        chat_context.add_query_result(False, "error")

def get_intelligent_fallback(user_input: str, sap_queries) -> Optional[pd.DataFrame]:
    """Provide intelligent fallback based on query analysis"""
    
    input_lower = user_input.lower()
    
    try:
        # Pattern matching for common queries
        if any(word in input_lower for word in ['failed', 'failure', 'error', 'problem']):
            return sap_queries.get_failed_chains_today()
        
        elif any(word in input_lower for word in ['success rate', 'performance', 'worst', 'best', 'statistics', 'stats']):
            perf_data = sap_queries.get_chain_success_rates(20)
            return perf_data
        
        elif any(word in input_lower for word in ['running', 'active', 'executing', 'in progress']):
            status_data = sap_queries.get_latest_chain_status()
            if not status_data.empty:
                return status_data[status_data['STATUS_OF_PROCESS'] == 'RUNNING']
        
        elif any(word in input_lower for word in ['today', 'recent', 'current', 'now']):
            return sap_queries.get_todays_activity()
        
        elif any(word in input_lower for word in ['waiting', 'queued', 'scheduled']):
            status_data = sap_queries.get_latest_chain_status()
            if not status_data.empty:
                return status_data[status_data['STATUS_OF_PROCESS'] == 'WAITING']
        
        elif any(word in input_lower for word in ['successful', 'completed', 'finished']):
            status_data = sap_queries.get_latest_chain_status()
            if not status_data.empty:
                return status_data[status_data['STATUS_OF_PROCESS'] == 'SUCCESS']
        
        elif any(word in input_lower for word in ['status', 'state', 'overview', 'summary']):
            return sap_queries.get_latest_chain_status()
        
        elif any(word in input_lower for word in ['variant', 'most']):
            # For variant-related queries, get performance data
            return sap_queries.get_chain_success_rates(20)
        
        else:
            # Default to latest status
            return sap_queries.get_latest_chain_status()
            
    except Exception as e:
        # Log the error and return a basic fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fallback query failed: {e}")
        
        # Try the most basic query possible
        try:
            return sap_queries.get_latest_chain_status()
        except:
            return None

def display_enhanced_response(enhanced_response: Dict, df_result: pd.DataFrame, sql_query: str):
    """Display the enhanced response with insights and recommendations"""
    
    # Main summary
    st.markdown(f"**📋 Summary:** {enhanced_response['summary']}")
    
    # Insights section
    if enhanced_response["insights"]:
        st.markdown("**💡 Key Insights:**")
        for insight in enhanced_response["insights"]:
            st.markdown(f"• {insight}")
    
    # Data highlights
    if enhanced_response["data_highlights"]:
        st.markdown("**🎯 Data Highlights:**")
        for highlight in enhanced_response["data_highlights"]:
            st.markdown(f"• {highlight}")
    
    # Show data
    if not df_result.empty:
        st.markdown("**📊 Detailed Results:**")
        st.dataframe(df_result, use_container_width=True)
        
        # Add download button
        csv = df_result.to_csv(index=False)
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name=f"sap_bw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=f"download_chat_csv_{unique_id}"
        )
    
    # Recommendations
    if enhanced_response["recommendations"]:
        st.markdown("**🎯 Recommendations:**")
        for rec in enhanced_response["recommendations"]:
            st.markdown(f"• {rec}")
    
    # Technical details in expander
    with st.expander("🔧 Technical Details"):
        st.code(sql_query, language="sql")
        st.json(enhanced_response["technical_details"])

def handle_query_failure(user_input: str, formatter) -> Dict[str, str]:
    """Handle query failures with helpful guidance"""
    
    return {
        "message": f"""
🚨 I couldn't process your query: "{user_input}"

💡 **Suggestions to try:**
• Use more specific terms like 'failed chains', 'success rate', or 'running status'
• Try asking about specific process chains by name (e.g., 'PC_SALES_DAILY status')
• Use time references like 'today', 'yesterday', or 'this week'

🔍 **Example queries that work well:**
• "Show me all failed process chains"
• "What is the success rate for each chain?"
• "Which chains are currently running?"
""",
        "type": "guidance"
    }

def classify_query_type(query: str) -> str:
    """Classify query type for analytics"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['failed', 'error', 'failure']):
        return "troubleshooting"
    elif any(word in query_lower for word in ['success', 'performance', 'rate']):
        return "performance"
    elif any(word in query_lower for word in ['running', 'status', 'current']):
        return "status"
    elif any(word in query_lower for word in ['count', 'how many', 'total']):
        return "analytics"
    else:
        return "general" 