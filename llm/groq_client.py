"""
Groq API Client for SAP BW Natural Language to SQL Conversion

This module provides the Groq API interface for converting natural language
questions into SQL queries for SAP BW process chains using Llama3 models.
"""

import os
import logging
import re
from typing import Optional, Dict, Any
from groq import Groq
import time

# Configure logging
logger = logging.getLogger(__name__)

class GroqClient:
    """
    Groq API client for SAP BW natural language to SQL conversion using Llama3
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "llama3-8b-8192",
                 max_tokens: int = 8192,
                 temperature: float = 0.1):
        """
        Initialize the Groq client
        
        Args:
            api_key: Groq API key (if None, will use environment variable)
            model: Groq model name to use
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation (0.0-1.0)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        logger.info(f"Initializing GroqClient with model: {model}")
        
        # Initialize Groq client
        self.client = None
        self.is_ready = False
        self.initialization_error = None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def initialize(self) -> bool:
        """
        Initialize the Groq client and test connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.api_key:
                raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")
            
            # Initialize Groq client
            self.client = Groq(api_key=self.api_key)
            
            # Test connection with a simple request
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10,
                temperature=0.1
            )
            
            if test_response:
                self.is_ready = True
                logger.info("Groq client initialized successfully")
                return True
            else:
                self.initialization_error = "Failed to get test response from Groq API"
                return False
                
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Failed to initialize Groq client: {e}")
            return False
    
    def generate_sql(self, question: str, context: Optional[str] = None) -> str:
        """
        Generate SQL query from natural language question using Groq/Llama3
        
        Args:
            question: Natural language question
            context: Optional context about the database schema
            
        Returns:
            Generated SQL query string
        """
        try:
            if not self.is_ready or not self.client:
                raise RuntimeError("Groq client not initialized. Call initialize() first.")
            
            # Rate limiting
            self._apply_rate_limit()
            
            # Create optimized prompt for Llama3
            prompt = self._create_llama3_prompt(question, context)
            
            # Generate SQL using Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert SQL generator for SAP BW process chains. Generate only valid SQLite SQL queries."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=512,  # Limit output length
                temperature=self.temperature,
                stop=["```", "---", "Note:", "Explanation:"]  # Stop at common endings
            )
            
            # Extract generated SQL
            generated_sql = response.choices[0].message.content
            
            # Clean up the generated SQL
            cleaned_sql = self._extract_sql_from_response(generated_sql)
            
            logger.info(f"Generated SQL for question: '{question[:50]}...'")
            logger.debug(f"Raw response: '{generated_sql[:200]}...'")
            logger.debug(f"Cleaned SQL: '{cleaned_sql}'")
            
            return cleaned_sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return "SELECT 'Error: Unable to generate SQL with Groq API' as error_message;"
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _create_llama3_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Create an optimized prompt for Llama3 instruction-following
        
        Args:
            question: User's natural language question
            context: Optional database schema context
            
        Returns:
            Formatted prompt string optimized for Llama3
        """
        
        # SAP BW schema information
        schema_info = """
DATABASE SCHEMA - SAP BW Process Chains:

Tables and Views:
1. VW_LATEST_CHAIN_RUNS - Latest execution for each chain
   Columns: CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, LOG_ID, rn
   Important: Always use "rn = 1" for latest data

2. VW_CHAIN_SUMMARY - Performance statistics
   Columns: CHAIN_ID, total_runs, successful_runs, failed_runs, success_rate_percent, last_run_time

3. VW_TODAYS_ACTIVITY - Today's executions only
   Columns: CHAIN_ID, LOG_ID, STATUS_OF_PROCESS, TIME

Status Values: 'SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED'
"""

        # Few-shot examples for Llama3
        examples = """
EXAMPLES:

Question: "Show all failed chains today"
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;

Question: "What are the success rates for all chains?"
SQL: SELECT CHAIN_ID, success_rate_percent, total_runs FROM VW_CHAIN_SUMMARY ORDER BY success_rate_percent DESC;

Question: "List all chain names"
SQL: SELECT DISTINCT CHAIN_ID FROM VW_LATEST_CHAIN_RUNS WHERE rn = 1;
"""

        # Construct the final prompt
        prompt = f"""
{schema_info}

{examples}

TASK: Generate a SQLite SQL query to answer the following question about SAP BW process chains.

REQUIREMENTS:
- Generate ONLY the SQL query, no explanations
- Use exact column names from the schema
- Always include semicolon at the end
- For latest status, use VW_LATEST_CHAIN_RUNS with "rn = 1"
- For performance analysis, use VW_CHAIN_SUMMARY

Question: {question}

SQL:"""
        
        return prompt.strip()
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract and clean SQL from Llama3 response
        
        Args:
            response: Raw response from Llama3
            
        Returns:
            Cleaned and validated SQL query
        """
        if not response:
            return "SELECT 'No response from Groq API' as error;"
        
        # Log raw response for debugging
        logger.debug(f"Extracting SQL from response: '{response[:500]}...'")
        
        # Clean the response
        sql = response.strip()
        
        # Remove common Llama3 artifacts
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'```\s*$', '', sql)
        sql = re.sub(r'^SQL:\s*', '', sql, flags=re.IGNORECASE)
        
        # Extract just the SQL query
        lines = sql.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            # Stop at explanatory text
            if any(stop_word in line.lower() for stop_word in ['note:', 'explanation:', 'this query', 'the above']):
                break
            # Keep SQL lines
            if line and (line.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')) or 
                        'SELECT' in line.upper() or
                        any(keyword in line.upper() for keyword in ['FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'HAVING'])):
                sql_lines.append(line)
        
        sql = ' '.join(sql_lines).strip()
        
        # Ensure it starts with SELECT
        if not sql.upper().startswith(('SELECT', 'WITH')):
            if 'SELECT' in sql.upper():
                # Find the SELECT and start from there
                select_idx = sql.upper().find('SELECT')
                sql = sql[select_idx:]
            else:
                return "SELECT 'No valid SQL found in Groq response' as error;"
        
        # Clean up whitespace
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        # Basic validation
        if len(sql.strip()) < 15 or 'SELECT' not in sql.upper():
            return "SELECT 'Invalid SQL structure from Groq' as error;"
        
        # Check for valid SAP BW tables
        valid_tables = ['VW_LATEST_CHAIN_RUNS', 'VW_CHAIN_SUMMARY', 'VW_TODAYS_ACTIVITY', 'RSPCCHAIN', 'RSPCLOGCHAIN']
        if not any(table in sql.upper() for table in valid_tables):
            return "SELECT 'No valid SAP BW tables found in Groq response' as error;"
        
        # Security check - no dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper and not (keyword == 'DELETE' and 'SELECT' in sql_upper):
                return f"SELECT 'Dangerous operation {keyword} not allowed' as error;"
        
        return sql
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Groq API connection and return status
        
        Returns:
            Dictionary with connection test results
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "Client not initialized",
                    "api_key_set": bool(self.api_key)
                }
            
            # Test with a simple request
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            end_time = time.time()
            
            return {
                "success": True,
                "model": self.model,
                "response_time": round(end_time - start_time, 2),
                "api_key_set": bool(self.api_key),
                "test_response": response.choices[0].message.content if response.choices else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "api_key_set": bool(self.api_key)
            } 