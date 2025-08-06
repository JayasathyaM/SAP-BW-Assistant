"""
SAP BW Process Chain Prompt Templates

This module contains optimized prompt templates for converting natural language
questions into SQL queries for SAP BW process chains.
"""

from typing import Dict, List, Optional, Any
from enum import Enum

class QueryType(Enum):
    """Types of queries the chatbot can handle"""
    STATUS = "status"
    ANALYTICAL = "analytical"
    HISTORICAL = "historical"
    COMPARISON = "comparison"
    TROUBLESHOOTING = "troubleshooting"

class PromptTemplates:
    """
    Collection of optimized prompt templates for SAP BW SQL generation
    """
    
    # Base schema information
    SAP_BW_SCHEMA = """
SAP BW Process Chain Database Schema:

CORE TABLES:
• RSPCCHAIN: Process chain definitions
  - CHAIN_ID (VARCHAR): Process chain identifier (e.g., 'PC_SALES_DAILY')
  - PROCESS_TYPE (VARCHAR): Type of process ('LOADING', 'DTP', 'CHAIN', etc.)
  - PROCESS_VARIANT_NAME (VARCHAR): Variant name
  - VERSION (VARCHAR): Version number
  - SEQNO (INTEGER): Sequence number

• RSPCLOGCHAIN: Process chain execution logs
  - CHAIN_ID (VARCHAR): Links to RSPCCHAIN.CHAIN_ID
  - LOG_ID (VARCHAR): Unique log identifier
  - STATUS_OF_PROCESS (VARCHAR): 'SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED'
  - CURRENT_DATE (DATE): Execution date
  - TIME (TIME): Execution time
  - CREATED_TIMESTAMP (TIMESTAMP): Full timestamp

• RSPCPROCESSLOG: Step-level execution details
  - LOG_ID (VARCHAR): Links to RSPCLOGCHAIN.LOG_ID
  - PROCESS_TYPE (VARCHAR): Process step type
  - STATUS_OF_PROCESS (VARCHAR): Step status
  - BACKGROUND_JOB_NAME (VARCHAR): SAP background job name
  - EXECUTION_DURATION (INTEGER): Duration in seconds
  - ERROR_MESSAGE (TEXT): Error details if failed

• RSPCVARIANT: Process variant parameters
  - PROCESS_TYPE (VARCHAR): Links to RSPCCHAIN.PROCESS_TYPE
  - PROCESS_VARIANT_NAME (VARCHAR): Links to RSPCCHAIN.PROCESS_VARIANT_NAME
  - FIELD_NAME (VARCHAR): Parameter field name
  - FROM_VALUE (VARCHAR): Parameter value

OPTIMIZED VIEWS (USE THESE FOR BETTER PERFORMANCE):
• VW_LATEST_CHAIN_RUNS: Shows latest run for each process chain
  - CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, rn (=1 for latest)

• VW_CHAIN_SUMMARY: Success rate statistics per chain
  - CHAIN_ID, total_runs, successful_runs, failed_runs, success_rate_percent, last_run_time

• VW_TODAYS_ACTIVITY: Today's process chain activity
  - CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, CREATED_TIMESTAMP
"""

    # Status query templates
    STATUS_PROMPTS = {
        "single_chain": """
{schema}

TASK: Generate SQL to get the latest status of a specific process chain.

PATTERN: "What's the status of [CHAIN_ID]?" or "Status of [CHAIN_ID]"

EXAMPLES:
Question: "What's the status of PC_SALES_DAILY?"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME 
     FROM VW_LATEST_CHAIN_RUNS 
     WHERE CHAIN_ID = 'PC_SALES_DAILY' AND rn = 1;

Question: "Status of PC_INVENTORY_WEEKLY"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME 
     FROM VW_LATEST_CHAIN_RUNS 
     WHERE CHAIN_ID = 'PC_INVENTORY_WEEKLY' AND rn = 1;

Question: {question}
SQL:""",

        "all_status": """
{schema}

TASK: Generate SQL to show status of all process chains or filter by status.

PATTERN: "Show all [status] chains" or "All process chain status"

EXAMPLES:
Question: "Show all failed process chains"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME 
     FROM VW_LATEST_CHAIN_RUNS 
     WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;

Question: "Show all process chain status"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME 
     FROM VW_LATEST_CHAIN_RUNS 
     WHERE rn = 1 
     ORDER BY CURRENT_DATE DESC, TIME DESC;

Question: {question}
SQL:""",

        "today_activity": """
{schema}

TASK: Generate SQL for today's process chain activity.

PATTERN: "Today's activity" or "Chains that ran today"

EXAMPLES:
Question: "Show me today's failed process chains"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, TIME 
     FROM VW_TODAYS_ACTIVITY 
     WHERE STATUS_OF_PROCESS = 'FAILED' 
     ORDER BY TIME DESC;

Question: "What process chains ran today?"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, TIME 
     FROM VW_TODAYS_ACTIVITY 
     ORDER BY TIME DESC;

Question: {question}
SQL:"""
    }

    # Analytical query templates
    ANALYTICAL_PROMPTS = {
        "success_rates": """
{schema}

TASK: Generate SQL for success rate analysis and chain performance.

PATTERN: "Success rate" or "Which chains fail most" or "Performance analysis"

EXAMPLES:
Question: "Which process chains have the worst success rates?"
SQL: SELECT CHAIN_ID, success_rate_percent, total_runs, failed_runs 
     FROM VW_CHAIN_SUMMARY 
     WHERE total_runs >= 5 
     ORDER BY success_rate_percent ASC 
     LIMIT 10;

Question: "Show me process chain success rates"
SQL: SELECT CHAIN_ID, success_rate_percent, total_runs, successful_runs, failed_runs 
     FROM VW_CHAIN_SUMMARY 
     ORDER BY success_rate_percent DESC;

Question: "Which chains fail most often?"
SQL: SELECT CHAIN_ID, failed_runs, total_runs, success_rate_percent 
     FROM VW_CHAIN_SUMMARY 
     ORDER BY failed_runs DESC 
     LIMIT 10;

Question: {question}
SQL:""",

        "counts_and_stats": """
{schema}

TASK: Generate SQL for counting and statistical queries.

PATTERN: "How many", "Count of", "Total", "Average"

EXAMPLES:
Question: "How many process chains failed today?"
SQL: SELECT COUNT(*) as failed_count 
     FROM VW_TODAYS_ACTIVITY 
     WHERE STATUS_OF_PROCESS = 'FAILED';

Question: "How many total process chains do we have?"
SQL: SELECT COUNT(DISTINCT CHAIN_ID) as total_chains 
     FROM VW_CHAIN_SUMMARY;

Question: "What's the overall success rate?"
SQL: SELECT 
       ROUND(AVG(success_rate_percent), 2) as overall_success_rate,
       SUM(total_runs) as total_executions,
       SUM(successful_runs) as total_successes
     FROM VW_CHAIN_SUMMARY;

Question: {question}
SQL:""",

        "time_based": """
{schema}

TASK: Generate SQL for time-based analysis and trends.

PATTERN: "Last week", "This month", "When did", "Recent"

EXAMPLES:
Question: "When did PC_SALES_DAILY last run?"
SQL: SELECT CHAIN_ID, CURRENT_DATE, TIME, STATUS_OF_PROCESS 
     FROM VW_LATEST_CHAIN_RUNS 
     WHERE CHAIN_ID = 'PC_SALES_DAILY' AND rn = 1;

Question: "Show recent failed process chains"
SQL: SELECT CHAIN_ID, CURRENT_DATE, TIME, STATUS_OF_PROCESS 
     FROM RSPCLOGCHAIN 
     WHERE STATUS_OF_PROCESS = 'FAILED' 
     ORDER BY CREATED_TIMESTAMP DESC 
     LIMIT 20;

Question: "Which chains ran in the last 7 days?"
SQL: SELECT DISTINCT CHAIN_ID, COUNT(*) as run_count 
     FROM RSPCLOGCHAIN 
     WHERE CURRENT_DATE >= CURRENT_DATE - INTERVAL '7 days' 
     GROUP BY CHAIN_ID 
     ORDER BY run_count DESC;

Question: {question}
SQL:"""
    }

    @classmethod
    def classify_question(cls, question: str) -> QueryType:
        """
        Classify the type of question to select appropriate prompt template
        
        Args:
            question: User's natural language question
            
        Returns:
            QueryType enum value
        """
        question_lower = question.lower()
        
        # Status queries
        status_keywords = ['status', 'what is', 'is running', 'current state', 'show me status']
        if any(keyword in question_lower for keyword in status_keywords):
            return QueryType.STATUS
        
        # Analytical queries
        analytical_keywords = ['success rate', 'fail most', 'performance', 'worst', 'best', 'how many', 'count']
        if any(keyword in question_lower for keyword in analytical_keywords):
            return QueryType.ANALYTICAL
        
        # Time-based queries
        time_keywords = ['when', 'last', 'recent', 'today', 'yesterday', 'week', 'month']
        if any(keyword in question_lower for keyword in time_keywords):
            return QueryType.HISTORICAL
        
        # Default to status
        return QueryType.STATUS
    
    @classmethod
    def get_prompt_for_question(cls, question: str, context: Optional[str] = None) -> str:
        """
        Get the most appropriate prompt template for a given question
        
        Args:
            question: User's natural language question
            context: Optional additional context
            
        Returns:
            Formatted prompt string ready for the AI model
        """
        question_type = cls.classify_question(question)
        question_lower = question.lower()
        
        # Build schema context
        schema = cls.SAP_BW_SCHEMA
        if context:
            schema += f"\n\nAdditional Context: {context}"
        
        # Select specific prompt template
        if question_type == QueryType.STATUS:
            if any(chain_pattern in question_lower for chain_pattern in ['pc_', 'chain_', 'specific']):
                prompt_template = cls.STATUS_PROMPTS["single_chain"]
            elif 'today' in question_lower:
                prompt_template = cls.STATUS_PROMPTS["today_activity"]
            else:
                prompt_template = cls.STATUS_PROMPTS["all_status"]
                
        elif question_type == QueryType.ANALYTICAL:
            if any(keyword in question_lower for keyword in ['success', 'fail', 'performance', 'rate']):
                prompt_template = cls.ANALYTICAL_PROMPTS["success_rates"]
            elif any(keyword in question_lower for keyword in ['how many', 'count', 'total', 'average']):
                prompt_template = cls.ANALYTICAL_PROMPTS["counts_and_stats"]
            else:
                prompt_template = cls.ANALYTICAL_PROMPTS["success_rates"]
                
        elif question_type == QueryType.HISTORICAL:
            prompt_template = cls.ANALYTICAL_PROMPTS["time_based"]
            
        else:
            # Default fallback
            prompt_template = cls.STATUS_PROMPTS["single_chain"]
        
        # Format the prompt
        return prompt_template.format(schema=schema, question=question)
    
    @classmethod
    def get_example_questions(cls) -> Dict[str, List[str]]:
        """
        Get example questions for each query type
        
        Returns:
            Dictionary mapping query types to example questions
        """
        return {
            "status": [
                "What's the status of PC_SALES_DAILY?",
                "Show me all failed process chains",
                "Status of PC_INVENTORY_WEEKLY",
                "Which chains are currently running?",
                "Show today's failed process chains"
            ],
            "analytical": [
                "Which process chains have the worst success rates?",
                "How many process chains failed today?",
                "What's the overall success rate?",
                "Which chains fail most often?",
                "Show me process chain performance statistics"
            ],
            "historical": [
                "When did PC_SALES_DAILY last run?",
                "Show recent failed process chains",
                "Which chains ran in the last 7 days?",
                "What happened to PC_FINANCE_MONTHLY last week?",
                "Show me the execution history for PC_CUSTOMER_DAILY"
            ]
        }
    
    @classmethod
    def validate_generated_sql(cls, sql: str, question: str) -> Dict[str, Any]:
        """
        Validate that generated SQL is appropriate for the question
        
        Args:
            sql: Generated SQL query
            question: Original question
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        sql_upper = sql.upper()
        question_lower = question.lower()
        
        # Check for basic SQL structure
        if not sql_upper.startswith('SELECT'):
            validation_result["errors"].append("Query should start with SELECT")
            validation_result["is_valid"] = False
        
        # Check for appropriate table usage
        if 'status' in question_lower:
            if 'VW_LATEST_CHAIN_RUNS' not in sql and 'VW_TODAYS_ACTIVITY' not in sql:
                validation_result["suggestions"].append("Consider using VW_LATEST_CHAIN_RUNS for status queries")
        
        if any(keyword in question_lower for keyword in ['success rate', 'performance', 'statistics']):
            if 'VW_CHAIN_SUMMARY' not in sql:
                validation_result["suggestions"].append("Consider using VW_CHAIN_SUMMARY for analytical queries")
        
        # Check for dangerous operations
        dangerous_keywords = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER', 'CREATE']
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            validation_result["errors"].append("Query contains potentially dangerous operations")
            validation_result["is_valid"] = False
        
        # Check for proper WHERE clauses
        if 'WHERE' not in sql_upper and any(chain_id in question_lower for chain_id in ['pc_', 'chain_']):
            validation_result["warnings"].append("Specific chain mentioned but no WHERE clause found")
        
        return validation_result

# Convenience functions
def get_prompt_for_question(question: str, context: Optional[str] = None) -> str:
    """Convenience function to get prompt for a question"""
    return PromptTemplates.get_prompt_for_question(question, context)

def classify_question(question: str) -> str:
    """Convenience function to classify question type"""
    return PromptTemplates.classify_question(question).value

def get_example_questions() -> Dict[str, List[str]]:
    """Convenience function to get example questions"""
    return PromptTemplates.get_example_questions()

# Test function
def test_prompt_templates():
    """Test the prompt templates with sample questions"""
    test_questions = [
        "What's the status of PC_SALES_DAILY?",
        "Which process chains have the worst success rates?",
        "How many process chains failed today?",
        "When did PC_INVENTORY_WEEKLY last run?",
        "Show me all failed process chains"
    ]
    
    print("Testing Prompt Templates")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        print(f"Type: {classify_question(question)}")
        
        prompt = get_prompt_for_question(question)
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Schema included: {'SAP BW Process Chain Database Schema' in prompt}")
        print("-" * 30)

if __name__ == "__main__":
    test_prompt_templates() 