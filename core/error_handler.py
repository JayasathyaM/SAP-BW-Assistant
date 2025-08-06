"""
SAP BW Chatbot Error Handler

This module provides comprehensive error handling for the SAP BW chatbot,
categorizing errors and providing user-friendly messages with suggested solutions.
"""

import logging
import traceback
import sys
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from datetime import datetime
# import psycopg2  # Removed for SQLite migration
from sqlalchemy.exc import SQLAlchemyError  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Categories of errors in the SAP BW chatbot"""
    DATABASE = "database"          # Database connection/query errors
    AI_MODEL = "ai_model"         # AI model loading/generation errors
    VALIDATION = "validation"      # SQL validation/security errors
    INPUT = "input"               # User input errors
    SYSTEM = "system"             # System/infrastructure errors
    BUSINESS = "business"         # Business logic errors
    CONFIGURATION = "configuration"  # Configuration errors
    NETWORK = "network"           # Network connectivity errors

class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"           # Minor issues, system continues
    MEDIUM = "medium"     # Significant issues, degraded functionality
    HIGH = "high"         # Major issues, feature unavailable
    CRITICAL = "critical" # System-breaking issues

class ChatbotError(Exception):
    """Base exception class for chatbot errors"""
    
    def __init__(self, 
                 message: str,
                 category: ErrorCategory,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 user_message: Optional[str] = None,
                 suggestions: Optional[List[str]] = None,
                 technical_details: Optional[str] = None):
        """
        Initialize a chatbot error
        
        Args:
            message: Technical error message
            category: Error category
            severity: Error severity
            user_message: User-friendly message
            suggestions: List of suggested solutions
            technical_details: Technical details for logging
        """
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.suggestions = suggestions or []
        self.technical_details = technical_details
        self.timestamp = datetime.now()
        self.error_id = self._generate_error_id()
    
    def _generate_user_message(self) -> str:
        """Generate a user-friendly message based on category"""
        
        category_messages = {
            ErrorCategory.DATABASE: "I'm having trouble connecting to the database right now.",
            ErrorCategory.AI_MODEL: "I'm experiencing issues with the AI processing.",
            ErrorCategory.VALIDATION: "There's an issue with the query I generated.",
            ErrorCategory.INPUT: "I couldn't understand your question properly.",
            ErrorCategory.SYSTEM: "I'm experiencing a technical issue.",
            ErrorCategory.BUSINESS: "I found an issue with the process chain data.",
            ErrorCategory.CONFIGURATION: "There's a configuration problem.",
            ErrorCategory.NETWORK: "I'm having connectivity issues."
        }
        
        return category_messages.get(self.category, "I encountered an unexpected issue.")
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID for tracking"""
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        category_code = self.category.value[:3].upper()
        severity_code = self.severity.value[0].upper()
        return f"ERR_{category_code}_{severity_code}_{timestamp_str}"

class ErrorHandler:
    """
    Comprehensive error handler for the SAP BW chatbot
    """
    
    def __init__(self, log_errors: bool = True, include_suggestions: bool = True):
        """
        Initialize the error handler
        
        Args:
            log_errors: Whether to log errors automatically
            include_suggestions: Whether to include suggestions in responses
        """
        self.log_errors = log_errors
        self.include_suggestions = include_suggestions
        self.error_counts = {}  # Track error frequency
        self.recent_errors = []  # Store recent errors for analysis
        
        logger.info("ErrorHandler initialized")
    
    def handle_error(self, 
                    error: Union[Exception, ChatbotError], 
                    context: Optional[str] = None,
                    user_question: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle an error and return structured response
        
        Args:
            error: Exception or ChatbotError to handle
            context: Additional context about where the error occurred
            user_question: The user's original question if available
            
        Returns:
            Dictionary with error information and response
        """
        try:
            # Convert to ChatbotError if needed
            if not isinstance(error, ChatbotError):
                chatbot_error = self._convert_to_chatbot_error(error, context)
            else:
                chatbot_error = error
            
            # Log the error if enabled
            if self.log_errors:
                self._log_error(chatbot_error, context, user_question)
            
            # Track error for analysis
            self._track_error(chatbot_error)
            
            # Generate response
            response = self._generate_error_response(chatbot_error, user_question)
            
            return response
            
        except Exception as handler_error:
            # Fallback if error handler itself fails
            logger.error(f"Error handler failed: {handler_error}")
            return self._generate_fallback_response(str(error))
    
    def _convert_to_chatbot_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Convert generic exceptions to ChatbotError"""
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Database errors
        if isinstance(error, SQLAlchemyError):
            return self._handle_database_error(error, context)
        
        # AI/ML model errors
        elif 'transformers' in error_message.lower() or 'torch' in error_message.lower():
            return self._handle_ai_model_error(error, context)
        
        # Import errors
        elif isinstance(error, ImportError):
            return self._handle_import_error(error, context)
        
        # File/IO errors
        elif isinstance(error, (FileNotFoundError, PermissionError, IOError)):
            return self._handle_file_error(error, context)
        
        # Memory errors
        elif isinstance(error, MemoryError):
            return self._handle_memory_error(error, context)
        
        # Value/Type errors (often input-related)
        elif isinstance(error, (ValueError, TypeError)):
            return self._handle_input_error(error, context)
        
        # Generic system errors
        else:
            return ChatbotError(
                message=error_message,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                technical_details=traceback.format_exc()
            )
    
    def _handle_database_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Handle database-specific errors"""
        
        error_message = str(error).lower()
        
        if 'connection' in error_message or 'connect' in error_message:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                user_message="I can't connect to the SAP BW database right now.",
                suggestions=[
                    "Check if SQLite database file is accessible",
                    "Verify database connection settings",
                    "Try again in a few moments",
                    "Contact your administrator if the issue persists"
                ]
            )
        
        elif 'timeout' in error_message:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.MEDIUM,
                user_message="The database query took too long to complete.",
                suggestions=[
                    "Try a more specific query",
                    "Use filters to limit the data",
                    "Ask for a summary instead of detailed results"
                ]
            )
        
        elif 'permission' in error_message or 'access' in error_message:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                user_message="I don't have permission to access the requested data.",
                suggestions=[
                    "Check your access permissions",
                    "Contact your administrator",
                    "Try a different query"
                ]
            )
        
        else:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.MEDIUM,
                user_message="I encountered a database error while processing your request.",
                suggestions=[
                    "Try rephrasing your question",
                    "Check if you're asking about valid process chains",
                    "Try again in a moment"
                ]
            )
    
    def _handle_ai_model_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Handle AI model-specific errors"""
        
        error_message = str(error).lower()
        
        if 'model' in error_message and 'not found' in error_message:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.AI_MODEL,
                severity=ErrorSeverity.HIGH,
                user_message="The AI model couldn't be loaded.",
                suggestions=[
                    "Wait for the model to download and initialize",
                    "Check your internet connection",
                    "Restart the application",
                    "Contact support if the issue persists"
                ]
            )
        
        elif 'cuda' in error_message or 'gpu' in error_message:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.AI_MODEL,
                severity=ErrorSeverity.LOW,
                user_message="GPU acceleration isn't available, using CPU instead.",
                suggestions=[
                    "Performance may be slower on CPU",
                    "Consider installing CUDA for better performance"
                ]
            )
        
        elif 'memory' in error_message or 'out of memory' in error_message:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.AI_MODEL,
                severity=ErrorSeverity.HIGH,
                user_message="The AI model ran out of memory processing your request.",
                suggestions=[
                    "Try a shorter, simpler question",
                    "Restart the application",
                    "Close other applications to free up memory"
                ]
            )
        
        else:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.AI_MODEL,
                severity=ErrorSeverity.MEDIUM,
                user_message="I'm having trouble processing your question with AI.",
                suggestions=[
                    "Try rephrasing your question",
                    "Use simpler language",
                    "Try again in a moment"
                ]
            )
    
    def _handle_import_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Handle import/dependency errors"""
        
        missing_module = str(error).replace("No module named ", "").strip("'\"")
        
        return ChatbotError(
            message=str(error),
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            user_message=f"A required component ({missing_module}) is not installed.",
            suggestions=[
                f"Install the missing package: pip install {missing_module}",
                "Check your virtual environment",
                "Reinstall the application dependencies",
                "Contact your administrator"
            ]
        )
    
    def _handle_file_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Handle file/IO errors"""
        
        if isinstance(error, FileNotFoundError):
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                user_message="A required file is missing.",
                suggestions=[
                    "Check if all application files are present",
                    "Reinstall the application",
                    "Check file permissions"
                ]
            )
        
        elif isinstance(error, PermissionError):
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                user_message="I don't have permission to access a required file.",
                suggestions=[
                    "Check file permissions",
                    "Run as administrator if needed",
                    "Contact your system administrator"
                ]
            )
        
        else:
            return ChatbotError(
                message=str(error),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                user_message="I encountered a file system error.",
                suggestions=[
                    "Check available disk space",
                    "Try again in a moment",
                    "Contact support if the issue persists"
                ]
            )
    
    def _handle_memory_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Handle memory-related errors"""
        
        return ChatbotError(
            message=str(error),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            user_message="The system ran out of memory.",
            suggestions=[
                "Close other applications",
                "Restart the application",
                "Try a simpler query",
                "Contact support for memory optimization"
            ]
        )
    
    def _handle_input_error(self, error: Exception, context: Optional[str] = None) -> ChatbotError:
        """Handle input/validation errors"""
        
        return ChatbotError(
            message=str(error),
            category=ErrorCategory.INPUT,
            severity=ErrorSeverity.LOW,
            user_message="I couldn't understand your question properly.",
            suggestions=[
                "Try rephrasing your question",
                "Be more specific about what you want to know",
                "Ask for 'help' to see example questions",
                "Use simple, clear language"
            ]
        )
    
    def _log_error(self, error: ChatbotError, context: Optional[str] = None, user_question: Optional[str] = None):
        """Log error details for debugging"""
        
        log_message = f"Error {error.error_id}: {str(error)}"
        if context:
            log_message += f" | Context: {context}"
        if user_question:
            log_message += f" | User Question: {user_question}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Log technical details if available
        if error.technical_details:
            logger.debug(f"Technical details for {error.error_id}: {error.technical_details}")
    
    def _track_error(self, error: ChatbotError):
        """Track error for analysis and monitoring"""
        
        # Count errors by category
        category_key = error.category.value
        self.error_counts[category_key] = self.error_counts.get(category_key, 0) + 1
        
        # Store recent errors (keep last 100)
        self.recent_errors.append(error)
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
    
    def _generate_error_response(self, error: ChatbotError, user_question: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured error response"""
        
        response = {
            "success": False,
            "error_id": error.error_id,
            "error_category": error.category.value,
            "error_severity": error.severity.value,
            "user_message": error.user_message,
            "timestamp": error.timestamp.isoformat(),
            "suggestions": error.suggestions if self.include_suggestions else [],
        }
        
        # Add context if available
        if user_question:
            response["original_question"] = user_question
        
        # Add fallback options based on error type
        response["fallback_options"] = self._get_fallback_options(error)
        
        return response
    
    def _get_fallback_options(self, error: ChatbotError) -> List[str]:
        """Get fallback options based on error type"""
        
        fallback_options = {
            ErrorCategory.DATABASE: [
                "Try asking a simpler question",
                "Ask for general help",
                "Check system status"
            ],
            ErrorCategory.AI_MODEL: [
                "Use predefined queries",
                "Browse available process chains",
                "Try again later"
            ],
            ErrorCategory.INPUT: [
                "Use example questions",
                "Try different keywords",
                "Ask for help"
            ]
        }
        
        return fallback_options.get(error.category, [
            "Try asking a different question",
            "Ask for help",
            "Contact support"
        ])
    
    def _generate_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """Generate fallback response when error handler fails"""
        
        return {
            "success": False,
            "error_id": "FALLBACK_ERROR",
            "error_category": "system",
            "error_severity": "high",
            "user_message": "I'm experiencing technical difficulties. Please try again later.",
            "timestamp": datetime.now().isoformat(),
            "suggestions": [
                "Try again in a few moments",
                "Restart the application",
                "Contact support"
            ],
            "fallback_options": [
                "Ask for help",
                "Try a simple question",
                "Contact administrator"
            ]
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "errors_by_category": self.error_counts.copy(),
            "recent_error_count": len(self.recent_errors),
            "most_common_category": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }

# Convenience functions
def handle_error(error: Union[Exception, ChatbotError], 
                context: Optional[str] = None,
                user_question: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to handle an error
    
    Args:
        error: Exception to handle
        context: Additional context
        user_question: User's original question
        
    Returns:
        Error response dictionary
    """
    handler = ErrorHandler()
    return handler.handle_error(error, context, user_question)

def create_validation_error(message: str, suggestions: Optional[List[str]] = None) -> ChatbotError:
    """Create a validation error"""
    return ChatbotError(
        message=message,
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        suggestions=suggestions or ["Check your query", "Try a different approach"]
    )

def create_input_error(message: str, suggestions: Optional[List[str]] = None) -> ChatbotError:
    """Create an input error"""
    return ChatbotError(
        message=message,
        category=ErrorCategory.INPUT,
        severity=ErrorSeverity.LOW,
        suggestions=suggestions or ["Rephrase your question", "Try different keywords"]
    )

# Test function
def test_error_handler():
    """Test the error handler with various error types"""
    
    handler = ErrorHandler()
    
    print("Testing Error Handler")
    print("=" * 50)
    
    # Test different error types
    test_errors = [
        (ConnectionError("Database connection failed"), "Database connection"),
        (ImportError("No module named 'torch'"), "Missing dependency"),
        (ValueError("Invalid input provided"), "Input validation"),
        (MemoryError("Out of memory"), "Memory issue"),
        (FileNotFoundError("Config file not found"), "File missing")
    ]
    
    for error, description in test_errors:
        print(f"\n🧪 Testing: {description}")
        response = handler.handle_error(error, context="test", user_question="What's the status?")
        
        print(f"  Error ID: {response['error_id']}")
        print(f"  Category: {response['error_category']}")
        print(f"  Severity: {response['error_severity']}")
        print(f"  User Message: {response['user_message']}")
        print(f"  Suggestions: {len(response['suggestions'])}")
    
    # Show statistics
    print(f"\n📊 Error Statistics:")
    stats = handler.get_error_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_error_handler() 