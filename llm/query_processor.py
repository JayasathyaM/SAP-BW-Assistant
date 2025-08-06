"""
SAP BW Query Processor

This module provides the main interface for converting natural language
questions into SQL queries for SAP BW process chains.
"""

import sys
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.transformer_client import TransformerClient
from llm.prompt_templates import PromptTemplates, QueryType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryProcessor:
    """
    Main processor for converting natural language to SAP BW SQL queries
    """
    
    def __init__(self, 
                 model_name: str = "t5-small",
                 cache_dir: Optional[str] = None,
                 auto_load: bool = True):
        """
        Initialize the query processor
        
        Args:
            model_name: Hugging Face model name to use
            cache_dir: Directory to cache models
            auto_load: Whether to automatically load the model
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        
        # Initialize transformer client
        self.transformer_client = TransformerClient(
            model_name=model_name,
            cache_dir=cache_dir
        )
        
        # Track initialization status
        self.is_ready = False
        self.initialization_error = None
        
        # Query statistics
        self.query_count = 0
        self.successful_queries = 0
        self.failed_queries = 0
        
        # Auto-load if requested
        if auto_load:
            self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize the AI model and pipeline
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Initializing SAP BW Query Processor...")
            
            # Load transformer model
            if not self.transformer_client.load_model():
                self.initialization_error = "Failed to load transformer model"
                return False
            
            # Create pipeline
            if not self.transformer_client.create_pipeline():
                self.initialization_error = "Failed to create inference pipeline"
                return False
            
            self.is_ready = True
            logger.info("Query processor initialized successfully")
            return True
            
        except Exception as e:
            self.initialization_error = f"Initialization failed: {e}"
            logger.error(self.initialization_error)
            return False
    
    def process_question(self, 
                        question: str, 
                        context: Optional[str] = None,
                        validate: bool = True) -> Dict[str, Any]:
        """
        Process a natural language question and return SQL query with metadata
        
        Args:
            question: Natural language question about SAP BW process chains
            context: Optional additional context
            validate: Whether to validate the generated SQL
            
        Returns:
            Dictionary containing SQL query and processing metadata
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": f"Processor not ready: {self.initialization_error}",
                "sql": None,
                "question": question
            }
        
        try:
            self.query_count += 1
            
            # Classify the question type
            question_type = PromptTemplates.classify_question(question)
            
            # Get optimized prompt
            prompt = PromptTemplates.get_prompt_for_question(question, context)
            
            # Generate SQL using transformer
            generated_sql = self.transformer_client.generate_sql(question, context)
            
            # Validate if requested
            validation_result = None
            if validate:
                validation_result = PromptTemplates.validate_generated_sql(generated_sql, question)
            
            # Prepare result
            result = {
                "success": True,
                "sql": generated_sql,
                "question": question,
                "question_type": question_type.value,
                "prompt_used": len(prompt),  # Just the length, not full prompt
                "validation": validation_result,
                "confidence": self._estimate_confidence(generated_sql, question),
                "processing_notes": []
            }
            
            # Add processing notes
            if validation_result and not validation_result["is_valid"]:
                result["processing_notes"].append("Generated SQL failed validation")
            
            if len(generated_sql) < 20:
                result["processing_notes"].append("Generated SQL seems very short")
            
            self.successful_queries += 1
            logger.info(f"Successfully processed question: '{question[:50]}...'")
            
            return result
            
        except Exception as e:
            self.failed_queries += 1
            error_msg = f"Failed to process question: {e}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "sql": "SELECT 'Error processing question' as error_message;",
                "question": question,
                "question_type": "unknown"
            }
    
    def process_multiple_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple questions in batch
        
        Args:
            questions: List of natural language questions
            
        Returns:
            List of result dictionaries
        """
        results = []
        for question in questions:
            result = self.process_question(question)
            results.append(result)
        
        return results
    
    def _estimate_confidence(self, sql: str, question: str) -> float:
        """
        Estimate confidence in the generated SQL
        
        Args:
            sql: Generated SQL query
            question: Original question
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Check SQL structure
        if sql.upper().startswith('SELECT'):
            confidence += 0.2
        
        # Check for appropriate keywords
        question_lower = question.lower()
        sql_upper = sql.upper()
        
        if 'status' in question_lower and ('STATUS_OF_PROCESS' in sql_upper or 'VW_LATEST_CHAIN_RUNS' in sql_upper):
            confidence += 0.2
        
        if 'failed' in question_lower and ('FAILED' in sql_upper):
            confidence += 0.15
        
        if 'success rate' in question_lower and ('VW_CHAIN_SUMMARY' in sql_upper):
            confidence += 0.2
        
        # Check for specific chain mentions
        if any(chain_pattern in question_lower for chain_pattern in ['pc_', 'chain_']) and 'WHERE' in sql_upper:
            confidence += 0.1
        
        # Penalize very short queries
        if len(sql) < 30:
            confidence -= 0.2
        
        # Penalize queries with errors
        if 'error' in sql.lower():
            confidence = 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics
        
        Returns:
            Dictionary with statistics
        """
        success_rate = 0.0
        if self.query_count > 0:
            success_rate = self.successful_queries / self.query_count
        
        return {
            "total_queries": self.query_count,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": success_rate,
            "is_ready": self.is_ready,
            "model_name": self.model_name,
            "initialization_error": self.initialization_error
        }
    
    def get_example_questions(self) -> Dict[str, List[str]]:
        """
        Get example questions organized by type
        
        Returns:
            Dictionary with example questions
        """
        return PromptTemplates.get_example_questions()
    
    def test_with_examples(self) -> Dict[str, Any]:
        """
        Test the processor with example questions
        
        Returns:
            Dictionary with test results
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Processor not initialized"
            }
        
        example_questions = self.get_example_questions()
        test_results = {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        for category, questions in example_questions.items():
            test_results["test_details"][category] = []
            
            for question in questions[:2]:  # Test first 2 questions from each category
                result = self.process_question(question)
                test_results["total_tests"] += 1
                
                if result["success"]:
                    test_results["successful_tests"] += 1
                else:
                    test_results["failed_tests"] += 1
                
                test_results["test_details"][category].append({
                    "question": question,
                    "success": result["success"],
                    "sql": result.get("sql", ""),
                    "confidence": result.get("confidence", 0.0),
                    "error": result.get("error", None)
                })
        
        test_results["success_rate"] = (
            test_results["successful_tests"] / test_results["total_tests"] 
            if test_results["total_tests"] > 0 else 0.0
        )
        
        return test_results

# Convenience functions
def create_processor(model_name: str = "t5-small") -> QueryProcessor:
    """
    Create a QueryProcessor with default settings
    
    Args:
        model_name: Hugging Face model to use
        
    Returns:
        Configured QueryProcessor instance
    """
    return QueryProcessor(model_name=model_name, auto_load=False)

def quick_query_test(question: str) -> Dict[str, Any]:
    """
    Quick test with a single question
    
    Args:
        question: Natural language question to test
        
    Returns:
        Query result dictionary
    """
    processor = create_processor()
    
    if not processor.initialize():
        return {
            "success": False,
            "error": "Failed to initialize processor"
        }
    
    return processor.process_question(question)

# Main function for testing
def main():
    """Command line interface for testing the query processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SAP BW Query Processor CLI")
    parser.add_argument("--test", action="store_true", help="Run comprehensive tests")
    parser.add_argument("--question", help="Process a specific question")
    parser.add_argument("--model", default="t5-small", help="Model name to use")
    parser.add_argument("--examples", action="store_true", help="Show example questions")
    
    args = parser.parse_args()
    
    if args.examples:
        examples = PromptTemplates.get_example_questions()
        print("Example Questions by Category:")
        print("=" * 40)
        for category, questions in examples.items():
            print(f"\n{category.upper()}:")
            for i, question in enumerate(questions, 1):
                print(f"  {i}. {question}")
        return
    
    # Create processor
    processor = QueryProcessor(model_name=args.model, auto_load=False)
    
    print(f"Initializing query processor with model: {args.model}")
    if not processor.initialize():
        print(f"Failed to initialize: {processor.initialization_error}")
        return
    
    print("Query processor ready!")
    
    if args.question:
        # Process specific question
        print(f"\nProcessing question: {args.question}")
        result = processor.process_question(args.question)
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Question type: {result['question_type']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Generated SQL:\n{result['sql']}")
            
            if result.get('validation'):
                validation = result['validation']
                print(f"Validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
                if validation['warnings']:
                    print(f"Warnings: {validation['warnings']}")
                if validation['errors']:
                    print(f"Errors: {validation['errors']}")
        else:
            print(f"Error: {result['error']}")
    
    if args.test:
        # Run comprehensive tests
        print("\nRunning comprehensive tests...")
        test_results = processor.test_with_examples()
        
        print(f"Test Results:")
        print(f"  Total tests: {test_results['total_tests']}")
        print(f"  Successful: {test_results['successful_tests']}")
        print(f"  Failed: {test_results['failed_tests']}")
        print(f"  Success rate: {test_results['success_rate']:.1%}")
        
        print("\nTest Details:")
        for category, tests in test_results['test_details'].items():
            print(f"\n{category.upper()}:")
            for test in tests:
                status = "✅" if test['success'] else "❌"
                confidence = test.get('confidence', 0.0)
                print(f"  {status} {test['question']} (confidence: {confidence:.2f})")
                if not test['success']:
                    print(f"     Error: {test.get('error', 'Unknown error')}")
        
        # Show overall statistics
        stats = processor.get_statistics()
        print(f"\nProcessor Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 