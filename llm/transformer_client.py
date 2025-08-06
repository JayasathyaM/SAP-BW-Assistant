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
        self.max_length = 512
        self.temperature = 0.1
        self.top_p = 0.9
        
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
            
            # Get pad token ID safely
            pad_token_id = getattr(self.tokenizer, 'eos_token_id', None)
            if pad_token_id is None:
                pad_token_id = getattr(self.tokenizer, 'pad_token_id', 0)
            
            # Generate SQL
            result = self.pipeline(
                prompt,
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=pad_token_id
            )
            
            # Extract generated text
            generated_sql = result[0]['generated_text']
            
            # Clean up the generated SQL
            cleaned_sql = self._clean_generated_sql(generated_sql)
            
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
        
        # Compact high-quality prompt (under 400 tokens)
        prompt = f"""Generate SQLite SQL for SAP BW process chains.

SCHEMA:
• VW_LATEST_CHAIN_RUNS: CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, rn
• VW_CHAIN_SUMMARY: CHAIN_ID, success_rate_percent, total_runs
• VW_TODAYS_ACTIVITY: CHAIN_ID, STATUS_OF_PROCESS, TIME

EXAMPLES:
Q: Show failed chains
SQL: SELECT CHAIN_ID, STATUS_OF_PROCESS FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;

Q: Success rates  
SQL: SELECT CHAIN_ID, success_rate_percent FROM VW_CHAIN_SUMMARY ORDER BY success_rate_percent DESC;

Q: Running count
SQL: SELECT COUNT(*) as count FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'RUNNING' AND rn = 1;

RULES: Use WHERE rn = 1 for latest runs. Use STATUS_OF_PROCESS not STATUS.

Question: {question}
SQL:"""
        
        return prompt
    
    def _clean_generated_sql(self, generated_text: str) -> str:
        """
        Enhanced SQL cleaning and validation
        
        Args:
            generated_text: Raw generated text from the model
            
        Returns:
            Cleaned and validated SQL query
        """
        if not generated_text:
            return "SELECT 'No query generated' as error;"
        
        # Extract SQL from generated text
        sql = generated_text.strip()
        
        # Remove common prefixes and artifacts
        prefixes_to_remove = [
            "SQL Query:",
            "Query:",
            "sql:",
            "SQL:",
            "Answer:",
            "Response:",
            "Generated SQL:",
            "Result:"
        ]
        
        for prefix in prefixes_to_remove:
            if sql.upper().startswith(prefix.upper()):
                sql = sql[len(prefix):].strip()
                break
        
        # Remove schema descriptions that the model sometimes generates
        import re
        
        # Remove lines that look like schema descriptions
        sql_lines = sql.split('\n')
        clean_lines = []
        
        for line in sql_lines:
            line = line.strip()
            
            # Skip lines that are clearly not SQL
            if (': Process chain' in line or 
                'RSPCCHAIN:' in line or 
                'RSPCLOGCHAIN:' in line or
                line.startswith('-') or
                'definitions' in line.lower() or
                'logs' in line.lower() and ':' in line):
                continue
            
            # Keep actual SQL lines
            if line and (line.upper().startswith(('SELECT', 'FROM', 'WHERE', 'ORDER', 'GROUP', 'HAVING')) or
                        'SELECT' in line.upper() or
                        any(col in line.upper() for col in ['CHAIN_ID', 'STATUS_OF_PROCESS', 'COUNT'])):
                clean_lines.append(line)
        
        sql = ' '.join(clean_lines).strip()
        
        # If we still don't have valid SQL, try to extract it more aggressively
        if not sql or len(sql) < 10:
            # Look for SELECT statements in the original text
            select_match = re.search(r'SELECT.*?;', generated_text, re.IGNORECASE | re.DOTALL)
            if select_match:
                sql = select_match.group(0)
            else:
                return "SELECT 'Failed to parse generated query' as error;"
        
        # Ensure it starts with SELECT (most common case)
        if not sql.upper().startswith(('SELECT', 'WITH')):
            if 'SELECT' in sql.upper():
                # Find the SELECT and start from there
                select_idx = sql.upper().find('SELECT')
                sql = sql[select_idx:]
            else:
                sql = "SELECT " + sql
        
        # Clean up multiple spaces and line breaks
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        # Final validation
        if len(sql.strip()) < 15 or 'SELECT' not in sql.upper():
            return "SELECT 'Invalid query structure generated' as error;"
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return f"SELECT 'Dangerous operation {keyword} not allowed' as error;"
        
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