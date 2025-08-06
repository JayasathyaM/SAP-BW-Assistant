"""
Groq/Llama3 Optimized Prompts for SAP BW SQL Generation

This module contains prompt templates specifically optimized for Llama3's
instruction-following capabilities via the Groq API.
"""

from typing import Dict, List, Optional
from enum import Enum

class QueryType(Enum):
    """Types of SAP BW queries for prompt optimization"""
    STATUS_CHECK = "status_check"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    FAILURE_INVESTIGATION = "failure_investigation"
    CHAIN_LISTING = "chain_listing"
    HISTORICAL_ANALYSIS = "historical_analysis"

class GroqPromptEngine:
    """
    Optimized prompt engine for Groq/Llama3 SAP BW SQL generation
    """
    
    # SAP BW Schema optimized for Llama3
    SCHEMA_CONTEXT = """
# SAP BW Process Chain Database Schema

## Main Tables/Views:

### 1. VW_LATEST_CHAIN_RUNS (Latest Status)
- **Purpose**: Current status of all process chains
- **Key Columns**: 
  - CHAIN_ID (TEXT): Process chain identifier
  - STATUS_OF_PROCESS (TEXT): 'SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED'
  - CURRENT_DATE (TEXT): Execution date (YYYY-MM-DD)
  - TIME (TEXT): Execution time (HH:MM:SS)
  - LOG_ID (TEXT): Unique execution log ID
  - rn (INTEGER): Row number (always use WHERE rn = 1 for latest)

### 2. VW_CHAIN_SUMMARY (Performance Statistics)
- **Purpose**: Aggregated performance metrics
- **Key Columns**:
  - CHAIN_ID (TEXT): Process chain identifier
  - total_runs (INTEGER): Total execution count
  - successful_runs (INTEGER): Successful execution count
  - failed_runs (INTEGER): Failed execution count
  - success_rate_percent (REAL): Success percentage
  - last_run_time (TEXT): Most recent execution time

### 3. VW_TODAYS_ACTIVITY (Today's Activity)
- **Purpose**: All executions from current day
- **Key Columns**:
  - CHAIN_ID (TEXT): Process chain identifier
  - LOG_ID (TEXT): Execution log ID
  - STATUS_OF_PROCESS (TEXT): Current status
  - TIME (TEXT): Execution time
"""

    # Few-shot examples optimized for Llama3
    LLAMA3_EXAMPLES = [
        {
            "question": "Show all failed process chains",
            "sql": "SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;",
            "explanation": "Gets current failed chains using latest status view"
        },
        {
            "question": "What are the success rates for all chains?",
            "sql": "SELECT CHAIN_ID, success_rate_percent, total_runs, failed_runs FROM VW_CHAIN_SUMMARY ORDER BY success_rate_percent ASC;",
            "explanation": "Gets performance statistics ordered by success rate"
        },
        {
            "question": "List all process chain names",
            "sql": "SELECT DISTINCT CHAIN_ID FROM VW_LATEST_CHAIN_RUNS WHERE rn = 1 ORDER BY CHAIN_ID;",
            "explanation": "Gets unique chain identifiers from latest status"
        },
        {
            "question": "Which chains are currently running?",
            "sql": "SELECT CHAIN_ID, CURRENT_DATE, TIME FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'RUNNING' AND rn = 1;",
            "explanation": "Filters for chains with RUNNING status"
        },
        {
            "question": "Show chains with worst performance",
            "sql": "SELECT CHAIN_ID, success_rate_percent, failed_runs, total_runs FROM VW_CHAIN_SUMMARY WHERE total_runs >= 5 ORDER BY success_rate_percent ASC LIMIT 10;",
            "explanation": "Gets chains with lowest success rates (minimum 5 runs)"
        }
    ]

    @classmethod
    def classify_question(cls, question: str) -> QueryType:
        """
        Classify question type for prompt optimization
        
        Args:
            question: User's natural language question
            
        Returns:
            QueryType enum for the detected question type
        """
        question_lower = question.lower()
        
        # Status-related questions
        if any(keyword in question_lower for keyword in ['status', 'running', 'failed', 'success', 'current', 'now']):
            if 'failed' in question_lower or 'error' in question_lower:
                return QueryType.FAILURE_INVESTIGATION
            return QueryType.STATUS_CHECK
        
        # Performance analysis
        elif any(keyword in question_lower for keyword in ['performance', 'success rate', 'worst', 'best', 'statistics', 'analysis']):
            return QueryType.PERFORMANCE_ANALYSIS
        
        # Chain listing
        elif any(keyword in question_lower for keyword in ['list', 'show all', 'names', 'chains']):
            return QueryType.CHAIN_LISTING
        
        # Historical analysis
        elif any(keyword in question_lower for keyword in ['history', 'past', 'yesterday', 'last week', 'trend']):
            return QueryType.HISTORICAL_ANALYSIS
        
        # Default to status check
        return QueryType.STATUS_CHECK

    @classmethod
    def create_optimized_prompt(cls, question: str, query_type: Optional[QueryType] = None) -> str:
        """
        Create a prompt optimized for Llama3's instruction-following capabilities
        
        Args:
            question: User's natural language question
            query_type: Optional query type (will be auto-detected if None)
            
        Returns:
            Optimized prompt string for Llama3
        """
        if query_type is None:
            query_type = cls.classify_question(question)
        
        # Get relevant examples based on query type
        relevant_examples = cls._get_relevant_examples(query_type)
        
        # Build the instruction-following prompt
        prompt = f"""You are an expert SQL generator for SAP BW process chain analysis. Your task is to convert natural language questions into precise SQLite queries.

{cls.SCHEMA_CONTEXT}

## Query Examples:

{cls._format_examples(relevant_examples)}

## Instructions:
1. Generate ONLY the SQL query - no explanations or additional text
2. Use exact column names from the schema above
3. Always end queries with a semicolon
4. For latest data, use VW_LATEST_CHAIN_RUNS with "WHERE rn = 1"
5. For performance analysis, use VW_CHAIN_SUMMARY
6. Use appropriate WHERE clauses for filtering

## Question to Convert:
{question}

## SQL Query:"""

        return prompt

    @classmethod
    def _get_relevant_examples(cls, query_type: QueryType) -> List[Dict]:
        """Get examples relevant to the query type"""
        
        if query_type == QueryType.FAILURE_INVESTIGATION:
            return [ex for ex in cls.LLAMA3_EXAMPLES if 'failed' in ex['question'].lower()][:2]
        
        elif query_type == QueryType.PERFORMANCE_ANALYSIS:
            return [ex for ex in cls.LLAMA3_EXAMPLES if any(word in ex['question'].lower() 
                   for word in ['success', 'performance', 'worst'])][:2]
        
        elif query_type == QueryType.CHAIN_LISTING:
            return [ex for ex in cls.LLAMA3_EXAMPLES if any(word in ex['question'].lower() 
                   for word in ['list', 'names', 'all'])][:2]
        
        elif query_type == QueryType.STATUS_CHECK:
            return [ex for ex in cls.LLAMA3_EXAMPLES if 'running' in ex['question'].lower()][:2]
        
        else:
            # Return first 2 examples for other types
            return cls.LLAMA3_EXAMPLES[:2]

    @classmethod
    def _format_examples(cls, examples: List[Dict]) -> str:
        """Format examples for the prompt"""
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"""
Example {i}:
Question: "{example['question']}"
SQL: {example['sql']}""")
        
        return "\n".join(formatted)

    @classmethod
    def create_system_message(cls) -> str:
        """Create the system message for Groq chat completion"""
        return """You are an expert SQL generator for SAP BW (Business Warehouse) process chain analysis. You specialize in converting natural language questions into precise SQLite SQL queries.

Key responsibilities:
- Generate only valid SQLite SQL syntax
- Focus on SAP BW process chain tables and views
- Ensure queries are safe (no DDL operations)
- Return precise, executable SQL queries
- Handle status checks, performance analysis, and chain management queries

Always respond with just the SQL query, no additional explanations unless specifically requested."""

    @classmethod
    def create_conversation_prompt(cls, question: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        Create a conversational prompt that includes chat history context
        
        Args:
            question: Current user question
            chat_history: Previous conversation messages
            
        Returns:
            Conversational prompt with context
        """
        base_prompt = cls.create_optimized_prompt(question)
        
        if chat_history and len(chat_history) > 0:
            context_section = "\n## Previous Context:\n"
            
            # Include last 2-3 exchanges for context
            recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
            
            for msg in recent_history:
                if msg.get("role") == "user":
                    context_section += f"Previous Question: {msg.get('content', '')}\n"
                elif msg.get("role") == "assistant":
                    # Include SQL if available
                    sql = msg.get("sql_query", msg.get("content", ""))
                    if "SELECT" in sql.upper():
                        context_section += f"Previous SQL: {sql}\n"
            
            # Insert context before the current question
            base_prompt = base_prompt.replace("## Question to Convert:", 
                                            f"{context_section}\n## Current Question to Convert:")
        
        return base_prompt 