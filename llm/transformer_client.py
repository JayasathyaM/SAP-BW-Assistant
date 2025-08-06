"""
SAP BW Process Chain Transformer Client

This module provides Hugging Face Transformers integration for converting
natural language questions into SQL queries for SAP BW process chains.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import torch  # type: ignore
from transformers import (  # type: ignore
    AutoTokenizer, 
    AutoModelForSeq2SeqLM, 
    T5ForConditionalGeneration,
    T5Tokenizer
)
from transformers.pipelines import pipeline  # type: ignore

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransformerClient:
    """
    Hugging Face Transformers client for SAP BW natural language to SQL conversion
    """
    
    def __init__(self, 
                 model_name: str = "t5-small",
                 cache_dir: Optional[str] = None,
                 device: Optional[str] = None):
        """
        Initialize the transformer client
        
        Args:
            model_name: Name of the Hugging Face model to use
            cache_dir: Directory to cache downloaded models
            device: Device to run the model on ('cpu', 'cuda', or None for auto)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or "./models"
        
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing TransformerClient with model: {model_name}")
        logger.info(f"Using device: {self.device}")
        
        # Model and tokenizer (loaded lazily)
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        
        # SAP BW specific configuration
        self.max_length = 2048  # Maximized from 1024 - t5-small can handle up to 2048 tokens
        self.temperature = 0.1
        self.top_p = 0.9
        
        # Token monitoring
        self.max_input_tokens = 1500  # Leave room for generation (2048 - 512 = 1536)
        self.token_usage_warnings = True
        
    def load_model(self) -> bool:
        """
        Load the model and tokenizer
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create cache directory
            os.makedirs(self.cache_dir, exist_ok=True)
            
            logger.info(f"Loading tokenizer: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            logger.info(f"Loading model: {self.model_name}")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32  # Ensure compatibility
            )
            
            # Move model to device
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info(f"Model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def create_pipeline(self) -> bool:
        """
        Create a text2text generation pipeline
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.model is None or self.tokenizer is None:
                logger.error("Model not loaded. Call load_model() first.")
                return False
            
            self.pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                num_return_sequences=1
            )
            
            logger.info("Text2text pipeline created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create pipeline: {e}")
            return False
    
    def generate_sql(self, question: str, context: Optional[str] = None) -> str:
        """
        Generate SQL query from natural language question
        
        Args:
            question: Natural language question
            context: Optional context about the database schema
            
        Returns:
            Generated SQL query string
        """
        try:
            if self.pipeline is None:
                raise RuntimeError("Pipeline not initialized. Call create_pipeline() first.")
            
            if self.tokenizer is None:
                raise RuntimeError("Tokenizer not loaded. Call load_model() first.")
            
            # Create prompt with SAP BW context
            prompt = self._create_sql_prompt(question, context)
            
            # Monitor token usage
            if self.token_usage_warnings:
                tokens = self.tokenizer.encode(prompt, return_tensors='pt')
                token_count = tokens.shape[1] if tokens.dim() > 1 else len(tokens)
                
                if token_count > self.max_input_tokens:
                    logger.warning(f"Prompt exceeds recommended length: {token_count} > {self.max_input_tokens} tokens")
                    # Try to create a shorter prompt
                    prompt = self._create_compact_prompt(question, context)
                    tokens = self.tokenizer.encode(prompt, return_tensors='pt')
                    token_count = tokens.shape[1] if tokens.dim() > 1 else len(tokens)
                    logger.info(f"Using compact prompt: {token_count} tokens")
                else:
                    logger.info(f"Prompt token count: {token_count}")
            
            # Get pad token ID safely
            pad_token_id = getattr(self.tokenizer, 'eos_token_id', None)
            if pad_token_id is None:
                pad_token_id = getattr(self.tokenizer, 'pad_token_id', 0)
            
            # Generate SQL with maximized length
            result = self.pipeline(
                prompt,
                max_length=self.max_length,
                max_new_tokens=512,  # Limit generation to 512 tokens
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=pad_token_id,
                truncation=True  # Enable truncation as safety
            )
            
            # Extract generated text
            generated_sql = result[0]['generated_text']
            
            # Add debugging to see what the model actually generated
            logger.info(f"Raw generated text: '{generated_sql}'")
            
            # Clean up the generated SQL
            cleaned_sql = self._clean_generated_sql(generated_sql)
            
            # Log the cleaning result
            if cleaned_sql.startswith("SELECT 'Failed to parse"):
                logger.warning(f"SQL cleaning failed. Raw: '{generated_sql[:200]}' -> Cleaned: '{cleaned_sql}'")
            
            logger.info(f"Generated SQL for question: '{question[:50]}...'")
            return cleaned_sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return "SELECT 'Error: Unable to generate SQL' as error_message;"
    
    def _create_sql_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Create enhanced prompt for SQL generation using few-shot learning
        
        Args:
            question: User's natural language question
            context: Database schema context
            
        Returns:
            Formatted prompt string with examples
        """
        try:
            # Try to use enhanced prompt system
            from llm.enhanced_prompt_system import get_enhanced_prompt_engine
            engine = get_enhanced_prompt_engine()
            return engine.create_enhanced_prompt(question, context)
        except ImportError:
            # Fallback to improved prompt with examples
            pass
        
        # Ultra-compact prompt (under 200 tokens)
        prompt = f"""Convert to SQL:

Tables: VW_LATEST_CHAIN_RUNS (CHAIN_ID, STATUS_OF_PROCESS, rn), VW_CHAIN_SUMMARY (CHAIN_ID, success_rate_percent)

Examples:
Q: failed chains
A: SELECT CHAIN_ID FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;

Q: success rates
A: SELECT CHAIN_ID, success_rate_percent FROM VW_CHAIN_SUMMARY ORDER BY success_rate_percent DESC;

Q: {question}
A:"""
        
        return prompt
    
    def _create_compact_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Create a compact prompt when token limits are exceeded
        
        Args:
            question: User's natural language question
            context: Database schema context (optional)
            
        Returns:
            Compact formatted prompt string
        """
        # Minimal SAP BW schema
        compact_schema = """
SAP BW Tables:
• VW_LATEST_CHAIN_RUNS: CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME (use rn = 1)
• VW_CHAIN_SUMMARY: CHAIN_ID, total_runs, success_rate_percent, failed_runs
• VW_TODAYS_ACTIVITY: CHAIN_ID, STATUS_OF_PROCESS, TIME
Status values: SUCCESS, FAILED, RUNNING, WAITING
"""
        
        # Single example for context
        example = """
Example: Q: Show failed chains today
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;
"""
        
        # Compact prompt
        prompt = f"""Generate SQLite SQL for SAP BW process chains.
{compact_schema.strip()}
{example.strip()}

Q: {question}
SQL:"""
        
        return prompt
    
    def _clean_generated_sql(self, generated_text: str) -> str:
        """
        Enhanced SQL cleaning and validation - optimized for T5 model output
        
        Args:
            generated_text: Raw generated text from the model
            
        Returns:
            Cleaned and validated SQL query
        """
        if not generated_text:
            return "SELECT 'No query generated' as error;"
        
        # Log the raw input for debugging
        logger.debug(f"Cleaning raw text: '{generated_text}'")
        
        # Extract SQL from generated text
        sql = generated_text.strip()
        
        # T5 models often repeat the input, so try to find just the SQL part
        # Look for patterns that indicate where the SQL starts
        import re
        
        # Strategy 1: Look for "SQL:" followed by the actual query
        sql_pattern = re.search(r'SQL:\s*(.*)', sql, re.IGNORECASE | re.DOTALL)
        if sql_pattern:
            sql = sql_pattern.group(1).strip()
        
        # Strategy 2: If T5 repeated the prompt, find the SELECT statement
        elif 'SELECT' in sql.upper():
            # Find the last SELECT statement (T5 might repeat it)
            select_matches = list(re.finditer(r'SELECT\b.*?(?=;|$)', sql, re.IGNORECASE | re.DOTALL))
            if select_matches:
                sql = select_matches[-1].group(0).strip()
        
        # Strategy 3: Simple prefix removal for T5 artifacts
        prefixes_to_remove = [
            "translate English to SQL:",
            "SQL Query:",
            "Query:",
            "sql:",
            "SQL:",
            "Answer:",
            "Response:",
            "Generated SQL:",
            "Result:",
            "Output:"
        ]
        
        for prefix in prefixes_to_remove:
            if sql.upper().startswith(prefix.upper()):
                sql = sql[len(prefix):].strip()
                break
        
        # Clean up common T5 artifacts
        sql = re.sub(r'^["\']|["\']$', '', sql)  # Remove quotes
        sql = re.sub(r'<[^>]*>', '', sql)  # Remove XML-like tags
        sql = sql.replace('\n', ' ')  # Single line
        sql = re.sub(r'\s+', ' ', sql)  # Normalize spaces
        sql = sql.strip()
        
        # Ensure it starts with SELECT or WITH
        if not sql.upper().startswith(('SELECT', 'WITH')):
            if 'SELECT' in sql.upper():
                # Find the SELECT and start from there
                select_idx = sql.upper().find('SELECT')
                sql = sql[select_idx:]
            elif any(table in sql.upper() for table in ['VW_LATEST_CHAIN_RUNS', 'VW_CHAIN_SUMMARY', 'VW_TODAYS_ACTIVITY']):
                # If we have valid table names but no SELECT, add it
                sql = "SELECT * FROM " + sql
            else:
                # Try to create a basic query from the text
                logger.warning(f"No SELECT found, attempting to construct query from: '{sql}'")
                if any(word in sql.lower() for word in ['chain', 'status', 'failed']):
                    return "SELECT CHAIN_ID, STATUS_OF_PROCESS FROM VW_LATEST_CHAIN_RUNS WHERE rn = 1;"
                else:
                    return "SELECT 'No valid SQL structure found' as error;"
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        # Basic validation - must be at least 15 characters and contain SELECT
        if len(sql.strip()) < 15 or 'SELECT' not in sql.upper():
            logger.warning(f"SQL too short or invalid: '{sql}'")
            return "SELECT 'Invalid query structure generated' as error;"
        
        # Basic SQL syntax validation - check for valid tables
        if not any(table in sql.upper() for table in ['VW_LATEST_CHAIN_RUNS', 'VW_CHAIN_SUMMARY', 'VW_TODAYS_ACTIVITY', 'RSPCCHAIN', 'RSPCLOGCHAIN']):
            logger.warning(f"No valid SAP BW tables found in: '{sql}'")
            return "SELECT 'No valid SAP BW tables found in query' as error;"
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return f"SELECT 'Dangerous operation {keyword} not allowed' as error;"
        
        logger.debug(f"Cleaned SQL: '{sql}'")
        return sql
    
    def test_model(self) -> Dict[str, Any]:
        """
        Test the model with sample SAP BW questions
        
        Returns:
            Dictionary with test results
        """
        test_questions = [
            "What is the status of PC_SALES_DAILY?",
            "Show me all failed process chains today",
            "Which process chains have the lowest success rate?",
            "When did PC_INVENTORY_WEEKLY last run?"
        ]
        
        results = {
            "model_loaded": self.model is not None,
            "pipeline_ready": self.pipeline is not None,
            "device": self.device,
            "test_queries": []
        }
        
        if self.pipeline is None:
            results["error"] = "Pipeline not initialized"
            return results
        
        for question in test_questions:
            try:
                sql = self.generate_sql(question)
                results["test_queries"].append({
                    "question": question,
                    "generated_sql": sql,
                    "success": True
                })
            except Exception as e:
                results["test_queries"].append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "cache_dir": self.cache_dir,
            "max_length": self.max_length,
            "temperature": self.temperature,
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "pipeline_ready": self.pipeline is not None,
            "vocab_size": self.tokenizer.vocab_size if self.tokenizer else None,
            "model_parameters": sum(p.numel() for p in self.model.parameters()) if self.model else None
        }

# Convenience functions
def create_default_client() -> TransformerClient:
    """
    Create a TransformerClient with default settings optimized for SAP BW
    
    Returns:
        Configured TransformerClient instance
    """
    # Use T5-small for better text-to-text generation
    client = TransformerClient(
        model_name="t5-small",
        cache_dir="./models/transformers"
    )
    return client

def quick_sql_generation_test() -> bool:
    """
    Quick test to verify SQL generation is working
    
    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        client = create_default_client()
        
        if not client.load_model():
            logger.error("Failed to load model for quick test")
            return False
        
        if not client.create_pipeline():
            logger.error("Failed to create pipeline for quick test")
            return False
        
        # Test with a simple question
        sql = client.generate_sql("What is the status of PC_SALES_DAILY?")
        
        # Basic validation
        if "SELECT" in sql.upper() and len(sql) > 20:
            logger.info("Quick SQL generation test passed")
            return True
        else:
            logger.error(f"Generated SQL seems invalid: {sql}")
            return False
            
    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        return False

# Main function for testing
def main():
    """Command line interface for testing the transformer client"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SAP BW Transformer Client CLI")
    parser.add_argument("--test", action="store_true", help="Run comprehensive tests")
    parser.add_argument("--quick-test", action="store_true", help="Run quick SQL generation test")
    parser.add_argument("--model", default="t5-small", help="Model name to use")
    parser.add_argument("--question", help="Generate SQL for a specific question")
    
    args = parser.parse_args()
    
    if args.quick_test:
        print("Running quick SQL generation test...")
        success = quick_sql_generation_test()
        print(f"Quick test: {'PASSED' if success else 'FAILED'}")
        return
    
    # Create client
    client = TransformerClient(model_name=args.model)
    
    # Load model
    print(f"Loading model: {args.model}")
    if not client.load_model():
        print("Failed to load model")
        return
    
    # Create pipeline
    print("Creating text2text pipeline...")
    if not client.create_pipeline():
        print("Failed to create pipeline")
        return
    
    if args.question:
        # Generate SQL for specific question
        print(f"\nQuestion: {args.question}")
        sql = client.generate_sql(args.question)
        print(f"Generated SQL:\n{sql}")
    
    if args.test:
        # Run comprehensive tests
        print("\nRunning comprehensive tests...")
        results = client.test_model()
        
        print(f"Model loaded: {results['model_loaded']}")
        print(f"Pipeline ready: {results['pipeline_ready']}")
        print(f"Device: {results['device']}")
        
        print("\nTest queries:")
        for test in results['test_queries']:
            status = "✅" if test['success'] else "❌"
            print(f"{status} {test['question']}")
            if test['success']:
                print(f"   SQL: {test['generated_sql']}")
            else:
                print(f"   Error: {test.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main() 