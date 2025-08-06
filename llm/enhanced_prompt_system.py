"""
Enhanced Prompt Engineering System for SAP BW SQL Generation

This module provides advanced prompt engineering with few-shot learning,
context awareness, and intelligent query classification for superior SQL generation.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re

class EnhancedQueryType(Enum):
    """Enhanced query classification for better prompt selection"""
    STATUS_CHECK = "status_check"          # "show failed chains", "chain status"
    PERFORMANCE_ANALYSIS = "performance"   # "success rate", "which chains fail most"
    COUNT_AGGREGATE = "count_stats"        # "how many", "total count"  
    TIME_FILTER = "time_based"            # "today", "yesterday", "last week"
    SPECIFIC_CHAIN = "specific_chain"      # "PC_SALES_DAILY status"
    COMPARISON = "comparison"              # "compare chains", "best/worst"
    TROUBLESHOOTING = "troubleshooting"    # "errors", "failed processes"

class FewShotExamples:
    """High-quality few-shot examples for SAP BW SQL generation"""
    
    PERFECT_EXAMPLES = [
        {
            "question": "Show me all failed process chains",
            "sql": "SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1 ORDER BY CURRENT_DATE DESC, TIME DESC;",
            "type": EnhancedQueryType.STATUS_CHECK
        },
        {
            "question": "What is the success rate for each chain?",
            "sql": "SELECT CHAIN_ID, total_runs, successful_runs, failed_runs, success_rate_percent FROM VW_CHAIN_SUMMARY ORDER BY success_rate_percent DESC;",
            "type": EnhancedQueryType.PERFORMANCE_ANALYSIS
        },
        {
            "question": "How many chains are currently running?",
            "sql": "SELECT COUNT(*) as running_count FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'RUNNING' AND rn = 1;",
            "type": EnhancedQueryType.COUNT_AGGREGATE
        },
        {
            "question": "Which chains failed today?",
            "sql": "SELECT CHAIN_ID, TIME, LOG_ID FROM VW_TODAYS_ACTIVITY WHERE STATUS_OF_PROCESS = 'FAILED' ORDER BY TIME DESC;",
            "type": EnhancedQueryType.TIME_FILTER
        },
        {
            "question": "Show me the status of PC_SALES_DAILY",
            "sql": "SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, LOG_ID FROM VW_LATEST_CHAIN_RUNS WHERE CHAIN_ID = 'PC_SALES_DAILY' AND rn = 1;",
            "type": EnhancedQueryType.SPECIFIC_CHAIN
        },
        {
            "question": "Which chain has the lowest success rate?",
            "sql": "SELECT CHAIN_ID, success_rate_percent, total_runs, failed_runs FROM VW_CHAIN_SUMMARY WHERE total_runs >= 3 ORDER BY success_rate_percent ASC LIMIT 1;",
            "type": EnhancedQueryType.COMPARISON
        }
    ]

class EnhancedPromptEngine:
    """Advanced prompt engineering system for SAP BW SQL generation"""
    
    def __init__(self):
        """Initialize the enhanced prompt engine"""
        self.few_shot_examples = FewShotExamples.PERFECT_EXAMPLES
        self.schema_context = self._build_enhanced_schema()
        
    def _build_enhanced_schema(self) -> str:
        """Build enhanced schema context with column details and relationships"""
        return """
=== SAP BW Process Chain Database Schema ===

TABLES:
• RSPCCHAIN (Process chain definitions):
  CHAIN_ID (TEXT) - Primary key, e.g., 'PC_SALES_DAILY', 'PC_INVENTORY_WEEKLY'
  PROCESS_TYPE (TEXT) - 'LOADING', 'DTP', 'CHAIN', 'ATTRIBUTE_CHANGE'
  PROCESS_VARIANT_NAME (TEXT) - Variant name
  VERSION (TEXT) - Version number
  SEQNO (INTEGER) - Sequence number in chain

• RSPCLOGCHAIN (Execution logs):
  CHAIN_ID (TEXT) - Foreign key to RSPCCHAIN
  LOG_ID (TEXT) - Unique execution identifier
  STATUS_OF_PROCESS (TEXT) - 'SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED'
  CURRENT_DATE (TEXT) - Execution date (YYYY-MM-DD)
  TIME (TEXT) - Execution time (HH:MM:SS)
  CREATED_TIMESTAMP (TEXT) - Full timestamp

OPTIMIZED VIEWS (USE THESE FOR QUERIES):
• VW_LATEST_CHAIN_RUNS - Latest execution for each chain:
  CHAIN_ID, PROCESS_TYPE, LOG_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, rn
  
• VW_CHAIN_SUMMARY - Performance statistics:
  CHAIN_ID, total_runs, successful_runs, failed_runs, success_rate_percent, last_run_time
  
• VW_TODAYS_ACTIVITY - Today's activity only:
  CHAIN_ID, LOG_ID, STATUS_OF_PROCESS, TIME

IMPORTANT RULES:
- Always use VW_LATEST_CHAIN_RUNS with "rn = 1" for current status
- Use VW_CHAIN_SUMMARY for performance analysis
- Use VW_TODAYS_ACTIVITY for today's data only
- Column name is STATUS_OF_PROCESS (not STATUS)
"""

    def classify_query(self, question: str) -> EnhancedQueryType:
        """Classify the user question to select appropriate prompt strategy"""
        question_lower = question.lower()
        
        # Specific chain query (contains chain ID pattern)
        if re.search(r'pc_\w+', question_lower):
            return EnhancedQueryType.SPECIFIC_CHAIN
        
        # Count/aggregate queries
        if any(word in question_lower for word in ['how many', 'count', 'total', 'number of']):
            return EnhancedQueryType.COUNT_AGGREGATE
        
        # Performance analysis
        if any(word in question_lower for word in ['success rate', 'performance', 'worst', 'best', 'lowest', 'highest']):
            return EnhancedQueryType.PERFORMANCE_ANALYSIS
        
        # Time-based queries
        if any(word in question_lower for word in ['today', 'yesterday', 'last week', 'this month', 'recent']):
            return EnhancedQueryType.TIME_FILTER
        
        # Comparison queries
        if any(word in question_lower for word in ['compare', 'which', 'what', 'most', 'least']):
            return EnhancedQueryType.COMPARISON
        
        # Troubleshooting
        if any(word in question_lower for word in ['error', 'failed', 'problem', 'issue']):
            return EnhancedQueryType.TROUBLESHOOTING
        
        # Default to status check
        return EnhancedQueryType.STATUS_CHECK

    def get_relevant_examples(self, query_type: EnhancedQueryType, count: int = 3) -> List[Dict]:
        """Get relevant few-shot examples for the query type"""
        # Get examples of the same type first
        same_type_examples = [ex for ex in self.few_shot_examples if ex["type"] == query_type]
        
        # If we don't have enough of the same type, add diverse examples
        if len(same_type_examples) < count:
            other_examples = [ex for ex in self.few_shot_examples if ex["type"] != query_type]
            all_examples = same_type_examples + other_examples[:count - len(same_type_examples)]
        else:
            all_examples = same_type_examples[:count]
        
        return all_examples

    def create_enhanced_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Create an enhanced prompt with few-shot learning and context awareness"""
        
        # Classify the query
        query_type = self.classify_query(question)
        
        # Try full prompt first, fallback to compact if too long
        full_prompt = self._create_full_prompt(question, query_type)
        
        # More aggressive token estimation (3 chars ≈ 1 token for safety)
        estimated_tokens = len(full_prompt) // 3
        
        if estimated_tokens > 300:  # Much more conservative limit (was 400)
            compact_prompt = self._create_compact_prompt(question, query_type)
            # Double-check compact prompt size
            compact_tokens = len(compact_prompt) // 3
            if compact_tokens > 400:
                # Ultra-compact if still too long
                return self._create_ultra_compact_prompt(question)
            return compact_prompt
        
        return full_prompt
    
    def _create_full_prompt(self, question: str, query_type: EnhancedQueryType) -> str:
        """Create the full enhanced prompt"""
        
        # Get relevant examples
        examples = self.get_relevant_examples(query_type, count=3)
        
        # Build the prompt with few-shot examples
        prompt_parts = [
            "You are an expert SAP BW SQL generator. Generate ONLY valid SQLite SQL queries.",
            "",
            self.schema_context,
            "",
            "=== EXAMPLES OF PERFECT SQL GENERATION ===",
            ""
        ]
        
        # Add few-shot examples
        for i, example in enumerate(examples, 1):
            prompt_parts.extend([
                f"Example {i}:",
                f"Question: {example['question']}",
                f"SQL: {example['sql']}",
                ""
            ])
        
        # Add the actual query
        prompt_parts.extend([
            "=== YOUR TASK ===",
            f"Question: {question}",
            "",
            "REQUIREMENTS:",
            "- Generate ONLY valid SQLite SQL",
            "- Use the exact column names from schema",
            "- Always include semicolon at the end",
            "- Use appropriate WHERE clauses for filtering",
            "- For latest status, use VW_LATEST_CHAIN_RUNS with rn = 1",
            "",
            "SQL:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _create_compact_prompt(self, question: str, query_type: EnhancedQueryType) -> str:
        """Create a compact prompt when token limit is exceeded"""
        
        # Get only 1 most relevant example
        examples = self.get_relevant_examples(query_type, count=1)
        
        # Simplified schema
        compact_schema = """
SAP BW Tables:
• VW_LATEST_CHAIN_RUNS: CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME (use rn = 1)
• VW_CHAIN_SUMMARY: CHAIN_ID, total_runs, success_rate_percent, failed_runs
• VW_TODAYS_ACTIVITY: CHAIN_ID, STATUS_OF_PROCESS, TIME
Status values: SUCCESS, FAILED, RUNNING, WAITING
"""
        
        prompt_parts = [
            "Generate SQLite SQL for SAP BW process chains.",
            compact_schema,
            "Example:",
            f"Q: {examples[0]['question']}" if examples else "Q: Show failed chains",
            f"SQL: {examples[0]['sql']}" if examples else "SQL: SELECT * FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;",
            "",
            f"Q: {question}",
            "SQL:"
        ]
        
        return "\n".join(prompt_parts)

    def _create_ultra_compact_prompt(self, question: str) -> str:
        """Create an ultra-compact prompt for extreme token limits"""
        
        prompt = f"""SAP BW SQL Generator
Tables: VW_LATEST_CHAIN_RUNS (CHAIN_ID, STATUS_OF_PROCESS, rn=1), VW_CHAIN_SUMMARY (success_rate_percent)
Q: {question}
SQL:"""
        
        return prompt

    def create_conversational_prompt(self, question: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Create a prompt that considers conversation context"""
        
        base_prompt = self.create_enhanced_prompt(question)
        
        if chat_history and len(chat_history) > 0:
            # Add conversation context
            context_parts = [
                "",
                "=== CONVERSATION CONTEXT ===",
                ""
            ]
            
            # Add last few exchanges for context
            for exchange in chat_history[-3:]:  # Last 3 exchanges
                if exchange.get("role") == "user":
                    context_parts.append(f"Previous question: {exchange.get('content', '')}")
                elif exchange.get("role") == "assistant" and exchange.get("sql_query"):
                    context_parts.append(f"Previous SQL: {exchange['sql_query'][:100]}...")
            
            context_parts.append("")
            
            # Insert context before the task section
            base_prompt = base_prompt.replace("=== YOUR TASK ===", 
                                            "\n".join(context_parts) + "\n=== YOUR TASK ===")
        
        return base_prompt

    def validate_generated_sql(self, sql: str, question: str) -> Tuple[bool, str, float]:
        """Validate and score the generated SQL"""
        
        if not sql or len(sql.strip()) < 10:
            return False, "SQL too short or empty", 0.0
        
        sql_clean = sql.strip().upper()
        score = 0.0
        issues = []
        
        # Basic SQL structure validation
        if sql_clean.startswith('SELECT'):
            score += 0.3
        else:
            issues.append("Does not start with SELECT")
        
        # Table/view validation
        required_objects = ['VW_LATEST_CHAIN_RUNS', 'VW_CHAIN_SUMMARY', 'VW_TODAYS_ACTIVITY', 
                          'RSPCCHAIN', 'RSPCLOGCHAIN']
        if any(obj in sql_clean for obj in required_objects):
            score += 0.3
        else:
            issues.append("No valid SAP BW tables/views found")
        
        # Column validation
        sap_columns = ['CHAIN_ID', 'STATUS_OF_PROCESS', 'CURRENT_DATE', 'TIME', 'LOG_ID']
        if any(col in sql_clean for col in sap_columns):
            score += 0.2
        else:
            issues.append("No valid SAP BW columns found")
        
        # Proper WHERE clause for latest data
        if 'VW_LATEST_CHAIN_RUNS' in sql_clean and 'RN = 1' in sql_clean:
            score += 0.1
        
        # Semicolon termination
        if sql.strip().endswith(';'):
            score += 0.1
        else:
            issues.append("Missing semicolon")
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']
        if any(keyword in sql_clean for keyword in dangerous_keywords):
            return False, "Contains dangerous SQL operations", 0.0
        
        # Invalid syntax patterns
        invalid_patterns = [
            r'SELECT\s*:',  # Starts with SELECT :
            r':\s*RS',      # Contains : followed by table names
            r'-\s*RS',      # Contains - followed by table names
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, sql_clean):
                issues.append(f"Contains invalid pattern: {pattern}")
                score = max(0.0, score - 0.5)
        
        is_valid = score >= 0.5 and len(issues) == 0
        issue_summary = "; ".join(issues) if issues else "Valid SQL"
        
        return is_valid, issue_summary, score

def get_enhanced_prompt_engine() -> EnhancedPromptEngine:
    """Get an instance of the enhanced prompt engine"""
    return EnhancedPromptEngine()

# Testing function
def test_enhanced_prompts():
    """Test the enhanced prompt system"""
    engine = EnhancedPromptEngine()
    
    test_questions = [
        "Show me all failed process chains",
        "What is the success rate for each chain?", 
        "How many chains are running?",
        "Which chains failed today?",
        "Show me the status of PC_SALES_DAILY"
    ]
    
    print("🧪 Testing Enhanced Prompt System")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        
        # Classify query
        query_type = engine.classify_query(question)
        print(f"   Classification: {query_type.value}")
        
        # Generate prompt
        prompt = engine.create_enhanced_prompt(question)
        print(f"   Prompt length: {len(prompt)} characters")
        
        # Show examples used
        examples = engine.get_relevant_examples(query_type, 2)
        print(f"   Examples used: {len(examples)}")
        
        print("   Prompt preview:")
        print("   " + "\n   ".join(prompt.split("\n")[:5]) + "...")

if __name__ == "__main__":
    test_enhanced_prompts() 