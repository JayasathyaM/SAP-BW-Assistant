"""
SAP BW Business Rules Engine

This module enforces SAP BW specific business rules and provides business context
for process chain queries and operations.
"""

import re
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime, time, timedelta
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleType(Enum):
    """Types of business rules"""
    NAMING = "naming"               # Naming conventions
    STATUS = "status"               # Status validation
    PERFORMANCE = "performance"     # Performance rules
    OPERATIONAL = "operational"     # Operational constraints
    DATA_QUALITY = "data_quality"   # Data quality checks
    ACCESS = "access"               # Access control rules

class RuleSeverity(Enum):
    """Severity levels for rule violations"""
    INFO = "info"                   # Informational
    WARNING = "warning"             # Warning but allowed
    ERROR = "error"                 # Error, should be blocked
    CRITICAL = "critical"           # Critical violation

class RuleViolation:
    """Represents a business rule violation"""
    
    def __init__(self, 
                 rule_id: str,
                 rule_type: RuleType,
                 severity: RuleSeverity,
                 message: str,
                 suggestion: Optional[str] = None,
                 data_context: Optional[Dict] = None):
        """
        Initialize a rule violation
        
        Args:
            rule_id: Unique identifier for the rule
            rule_type: Type of rule violated
            severity: Severity of the violation
            message: Description of the violation
            suggestion: Suggested fix
            data_context: Relevant data context
        """
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.severity = severity
        self.message = message
        self.suggestion = suggestion
        self.data_context = data_context or {}
        self.timestamp = datetime.now()

class BusinessRulesEngine:
    """
    SAP BW specific business rules engine
    """
    
    # SAP BW Process Chain Naming Conventions
    VALID_CHAIN_PREFIXES = {
        'PC_': 'Standard Process Chain',
        'ZPC_': 'Custom Process Chain',
        'TPC_': 'Test Process Chain',
        'DPC_': 'Development Process Chain'
    }
    
    # Valid Process Types
    VALID_PROCESS_TYPES = {
        'LOADING': 'Data Loading Process',
        'DTP': 'Data Transfer Process',
        'CHAIN': 'Process Chain',
        'ABAP': 'ABAP Program',
        'ATTRIBUTE': 'Attribute Change Run',
        'HIERARCHY': 'Hierarchy Change Run',
        'COMPRESS': 'Compression',
        'DELETE': 'Delete Request'
    }
    
    # Valid Status Transitions
    STATUS_TRANSITIONS = {
        'WAITING': ['RUNNING', 'CANCELLED'],
        'RUNNING': ['SUCCESS', 'FAILED', 'CANCELLED'],
        'SUCCESS': ['WAITING'],  # Can be restarted
        'FAILED': ['WAITING', 'RUNNING'],  # Can be restarted or rerun
        'CANCELLED': ['WAITING', 'RUNNING']  # Can be restarted
    }
    
    # Business Hours Configuration
    BUSINESS_HOURS = {
        'start': time(8, 0),    # 8:00 AM
        'end': time(18, 0),     # 6:00 PM
        'timezone': 'UTC'
    }
    
    # Performance Thresholds
    PERFORMANCE_THRESHOLDS = {
        'max_query_rows': 10000,
        'max_execution_time_minutes': 30,
        'warning_execution_time_minutes': 15,
        'max_concurrent_chains': 5
    }
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the business rules engine
        
        Args:
            strict_mode: Whether to enforce strict compliance
        """
        self.strict_mode = strict_mode
        self.rule_violations = []
        self.enabled_rules = set()
        
        # Enable all rules by default
        self._enable_all_rules()
        
        logger.info(f"BusinessRulesEngine initialized (strict_mode: {strict_mode})")
    
    def _enable_all_rules(self):
        """Enable all available business rules"""
        rule_types = [rule_type.value for rule_type in RuleType]
        self.enabled_rules.update(rule_types)
    
    def validate_process_chain_data(self, df: pd.DataFrame) -> List[RuleViolation]:
        """
        Validate process chain data against business rules
        
        Args:
            df: DataFrame containing process chain data
            
        Returns:
            List of rule violations
        """
        violations = []
        
        if df.empty:
            return violations
        
        # Check naming conventions
        if 'naming' in self.enabled_rules:
            violations.extend(self._check_naming_conventions(df))
        
        # Check status consistency
        if 'status' in self.enabled_rules:
            violations.extend(self._check_status_rules(df))
        
        # Check data quality
        if 'data_quality' in self.enabled_rules:
            violations.extend(self._check_data_quality(df))
        
        # Check performance implications
        if 'performance' in self.enabled_rules:
            violations.extend(self._check_performance_rules(df))
        
        # Check operational constraints
        if 'operational' in self.enabled_rules:
            violations.extend(self._check_operational_rules(df))
        
        return violations
    
    def _check_naming_conventions(self, df: pd.DataFrame) -> List[RuleViolation]:
        """Check SAP BW naming conventions"""
        violations = []
        
        if 'chain_id' not in df.columns:
            return violations
        
        for _, row in df.iterrows():
            chain_id = str(row['chain_id'])
            
            # Check if chain ID follows naming convention
            valid_prefix = False
            for prefix, description in self.VALID_CHAIN_PREFIXES.items():
                if chain_id.startswith(prefix):
                    valid_prefix = True
                    break
            
            if not valid_prefix:
                violations.append(RuleViolation(
                    rule_id="NAMING_001",
                    rule_type=RuleType.NAMING,
                    severity=RuleSeverity.WARNING,
                    message=f"Chain ID '{chain_id}' doesn't follow SAP BW naming convention",
                    suggestion="Use prefixes like PC_, ZPC_, TPC_, or DPC_",
                    data_context={"chain_id": chain_id}
                ))
            
            # Check chain ID length
            if len(chain_id) > 30:
                violations.append(RuleViolation(
                    rule_id="NAMING_002",
                    rule_type=RuleType.NAMING,
                    severity=RuleSeverity.ERROR,
                    message=f"Chain ID '{chain_id}' exceeds maximum length of 30 characters",
                    suggestion="Shorten the chain ID",
                    data_context={"chain_id": chain_id, "length": len(chain_id)}
                ))
            
            # Check for special characters
            if not re.match(r'^[A-Z0-9_]+$', chain_id):
                violations.append(RuleViolation(
                    rule_id="NAMING_003",
                    rule_type=RuleType.NAMING,
                    severity=RuleSeverity.ERROR,
                    message=f"Chain ID '{chain_id}' contains invalid characters",
                    suggestion="Use only uppercase letters, numbers, and underscores",
                    data_context={"chain_id": chain_id}
                ))
        
        return violations
    
    def _check_status_rules(self, df: pd.DataFrame) -> List[RuleViolation]:
        """Check status-related business rules"""
        violations = []
        
        if 'status_of_process' not in df.columns:
            return violations
        
        valid_statuses = {'SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED'}
        
        for _, row in df.iterrows():
            status = str(row['status_of_process']).upper()
            chain_id = row.get('chain_id', 'Unknown')
            
            # Check if status is valid
            if status not in valid_statuses:
                violations.append(RuleViolation(
                    rule_id="STATUS_001",
                    rule_type=RuleType.STATUS,
                    severity=RuleSeverity.ERROR,
                    message=f"Invalid status '{status}' for chain '{chain_id}'",
                    suggestion=f"Use one of: {', '.join(valid_statuses)}",
                    data_context={"chain_id": chain_id, "status": status}
                ))
            
            # Check for long-running processes
            if status == 'RUNNING' and 'current_date' in df.columns:
                try:
                    run_date = pd.to_datetime(row['current_date'])
                    if run_date < datetime.now() - timedelta(hours=24):
                        violations.append(RuleViolation(
                            rule_id="STATUS_002",
                            rule_type=RuleType.STATUS,
                            severity=RuleSeverity.WARNING,
                            message=f"Chain '{chain_id}' has been running for over 24 hours",
                            suggestion="Check if the process is stuck and needs intervention",
                            data_context={"chain_id": chain_id, "run_date": str(run_date)}
                        ))
                except:
                    pass  # Skip if date parsing fails
            
            # Check for excessive failures
            if status == 'FAILED':
                # This would require historical data analysis
                violations.append(RuleViolation(
                    rule_id="STATUS_003",
                    rule_type=RuleType.STATUS,
                    severity=RuleSeverity.INFO,
                    message=f"Chain '{chain_id}' has failed",
                    suggestion="Review error logs and consider process chain maintenance",
                    data_context={"chain_id": chain_id}
                ))
        
        return violations
    
    def _check_data_quality(self, df: pd.DataFrame) -> List[RuleViolation]:
        """Check data quality rules"""
        violations = []
        
        # Check for missing required fields
        required_fields = ['chain_id', 'status_of_process']
        for field in required_fields:
            if field not in df.columns:
                violations.append(RuleViolation(
                    rule_id="DATA_001",
                    rule_type=RuleType.DATA_QUALITY,
                    severity=RuleSeverity.ERROR,
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Ensure '{field}' is included in the data",
                    data_context={"missing_field": field}
                ))
            elif df[field].isnull().any():
                null_count = df[field].isnull().sum()
                violations.append(RuleViolation(
                    rule_id="DATA_002",
                    rule_type=RuleType.DATA_QUALITY,
                    severity=RuleSeverity.WARNING,
                    message=f"Field '{field}' has {null_count} null values",
                    suggestion=f"Clean up null values in '{field}'",
                    data_context={"field": field, "null_count": null_count}
                ))
        
        # Check for duplicate chain IDs in current runs
        if 'chain_id' in df.columns and 'status_of_process' in df.columns:
            running_chains = df[df['status_of_process'] == 'RUNNING']
            duplicates = running_chains[running_chains.duplicated('chain_id', keep=False)]
            
            if not duplicates.empty:
                for chain_id in duplicates['chain_id'].unique():
                    violations.append(RuleViolation(
                        rule_id="DATA_003",
                        rule_type=RuleType.DATA_QUALITY,
                        severity=RuleSeverity.ERROR,
                        message=f"Multiple running instances found for chain '{chain_id}'",
                        suggestion="Investigate concurrent executions",
                        data_context={"chain_id": chain_id}
                    ))
        
        return violations
    
    def _check_performance_rules(self, df: pd.DataFrame) -> List[RuleViolation]:
        """Check performance-related rules"""
        violations = []
        
        # Check dataset size
        if len(df) > self.PERFORMANCE_THRESHOLDS['max_query_rows']:
            violations.append(RuleViolation(
                rule_id="PERF_001",
                rule_type=RuleType.PERFORMANCE,
                severity=RuleSeverity.WARNING,
                message=f"Large dataset returned ({len(df)} rows)",
                suggestion="Consider using filters to limit results",
                data_context={"row_count": len(df)}
            ))
        
        # Check for SELECT * patterns (if column info available)
        if len(df.columns) > 10:
            violations.append(RuleViolation(
                rule_id="PERF_002",
                rule_type=RuleType.PERFORMANCE,
                severity=RuleSeverity.INFO,
                message=f"Query returns many columns ({len(df.columns)})",
                suggestion="Select only necessary columns for better performance",
                data_context={"column_count": len(df.columns)}
            ))
        
        # Check execution time if available
        if 'execution_duration' in df.columns:
            long_running = df[df['execution_duration'] > self.PERFORMANCE_THRESHOLDS['warning_execution_time_minutes'] * 60]
            if not long_running.empty:
                for _, row in long_running.iterrows():
                    chain_id = row.get('chain_id', 'Unknown')
                    duration_minutes = row['execution_duration'] / 60
                    violations.append(RuleViolation(
                        rule_id="PERF_003",
                        rule_type=RuleType.PERFORMANCE,
                        severity=RuleSeverity.WARNING,
                        message=f"Chain '{chain_id}' has long execution time ({duration_minutes:.1f} minutes)",
                        suggestion="Review process chain for optimization opportunities",
                        data_context={"chain_id": chain_id, "duration_minutes": duration_minutes}
                    ))
        
        return violations
    
    def _check_operational_rules(self, df: pd.DataFrame) -> List[RuleViolation]:
        """Check operational constraints"""
        violations = []
        
        # Check business hours execution
        if 'time' in df.columns:
            for _, row in df.iterrows():
                try:
                    execution_time = pd.to_datetime(row['time']).time()
                    if not (self.BUSINESS_HOURS['start'] <= execution_time <= self.BUSINESS_HOURS['end']):
                        chain_id = row.get('chain_id', 'Unknown')
                        violations.append(RuleViolation(
                            rule_id="OPS_001",
                            rule_type=RuleType.OPERATIONAL,
                            severity=RuleSeverity.INFO,
                            message=f"Chain '{chain_id}' executed outside business hours",
                            suggestion="Consider scheduling during business hours for better support",
                            data_context={"chain_id": chain_id, "execution_time": str(execution_time)}
                        ))
                except:
                    pass  # Skip if time parsing fails
        
        # Check for concurrent executions
        if 'status_of_process' in df.columns:
            running_count = len(df[df['status_of_process'] == 'RUNNING'])
            if running_count > self.PERFORMANCE_THRESHOLDS['max_concurrent_chains']:
                violations.append(RuleViolation(
                    rule_id="OPS_002",
                    rule_type=RuleType.OPERATIONAL,
                    severity=RuleSeverity.WARNING,
                    message=f"High number of concurrent executions ({running_count})",
                    suggestion="Monitor system resources and consider scheduling optimization",
                    data_context={"concurrent_count": running_count}
                ))
        
        return violations
    
    def get_business_context(self, chain_id: str) -> Dict[str, Any]:
        """
        Get business context for a specific process chain
        
        Args:
            chain_id: Process chain identifier
            
        Returns:
            Dictionary with business context
        """
        context = {
            "chain_id": chain_id,
            "naming_compliance": self._check_chain_naming(chain_id),
            "recommended_schedule": self._get_recommended_schedule(chain_id),
            "business_impact": self._assess_business_impact(chain_id),
            "dependencies": self._get_chain_dependencies(chain_id)
        }
        
        return context
    
    def _check_chain_naming(self, chain_id: str) -> Dict[str, Any]:
        """Check naming compliance for a chain"""
        
        compliance = {
            "is_compliant": False,
            "prefix": None,
            "description": None,
            "suggestions": []
        }
        
        for prefix, description in self.VALID_CHAIN_PREFIXES.items():
            if chain_id.startswith(prefix):
                compliance["is_compliant"] = True
                compliance["prefix"] = prefix
                compliance["description"] = description
                break
        
        if not compliance["is_compliant"]:
            compliance["suggestions"] = [
                "Use PC_ for standard process chains",
                "Use ZPC_ for custom process chains",
                "Use TPC_ for test process chains"
            ]
        
        return compliance
    
    def _get_recommended_schedule(self, chain_id: str) -> Dict[str, Any]:
        """Get recommended scheduling for a chain"""
        
        # Basic recommendations based on chain type
        if 'DAILY' in chain_id.upper():
            return {
                "frequency": "daily",
                "recommended_time": "02:00",
                "avoid_times": ["08:00-18:00"],
                "reason": "Daily chains should run during off-peak hours"
            }
        elif 'WEEKLY' in chain_id.upper():
            return {
                "frequency": "weekly",
                "recommended_time": "Saturday 01:00",
                "avoid_times": ["Monday-Friday 08:00-18:00"],
                "reason": "Weekly chains should run during weekends"
            }
        elif 'MONTHLY' in chain_id.upper():
            return {
                "frequency": "monthly",
                "recommended_time": "First Sunday 00:00",
                "avoid_times": ["Business days"],
                "reason": "Monthly chains should run during maintenance windows"
            }
        else:
            return {
                "frequency": "as_needed",
                "recommended_time": "off_peak_hours",
                "avoid_times": ["08:00-18:00"],
                "reason": "Schedule during low system usage"
            }
    
    def _assess_business_impact(self, chain_id: str) -> Dict[str, Any]:
        """Assess business impact of a chain"""
        
        impact = {
            "level": "medium",
            "affected_areas": [],
            "criticality": "normal",
            "recovery_time": "4 hours"
        }
        
        # Assess based on chain name patterns
        if any(keyword in chain_id.upper() for keyword in ['SALES', 'REVENUE', 'FINANCE']):
            impact["level"] = "high"
            impact["affected_areas"] = ["Sales Reports", "Financial Analytics"]
            impact["criticality"] = "high"
            impact["recovery_time"] = "1 hour"
        
        elif any(keyword in chain_id.upper() for keyword in ['INVENTORY', 'WAREHOUSE', 'LOGISTICS']):
            impact["level"] = "medium"
            impact["affected_areas"] = ["Inventory Management", "Warehouse Operations"]
            impact["criticality"] = "medium"
            impact["recovery_time"] = "2 hours"
        
        elif any(keyword in chain_id.upper() for keyword in ['TEST', 'DEV', 'SANDBOX']):
            impact["level"] = "low"
            impact["affected_areas"] = ["Development", "Testing"]
            impact["criticality"] = "low"
            impact["recovery_time"] = "8 hours"
        
        return impact
    
    def _get_chain_dependencies(self, chain_id: str) -> List[str]:
        """Get potential dependencies for a chain"""
        
        # This would typically query dependency tables
        # For now, return basic assumptions based on naming
        dependencies = []
        
        if 'MASTER' in chain_id.upper():
            dependencies.append("Master Data Loading")
        
        if 'TRANS' in chain_id.upper():
            dependencies.append("Transactional Data Loading")
        
        if 'AGGREGATE' in chain_id.upper():
            dependencies.extend(["Master Data", "Transactional Data"])
        
        return dependencies

# Convenience functions
def validate_data(df: pd.DataFrame, strict_mode: bool = False) -> List[RuleViolation]:
    """
    Convenience function to validate data against business rules
    
    Args:
        df: DataFrame to validate
        strict_mode: Whether to use strict validation
        
    Returns:
        List of rule violations
    """
    engine = BusinessRulesEngine(strict_mode)
    return engine.validate_process_chain_data(df)

def get_chain_context(chain_id: str) -> Dict[str, Any]:
    """
    Get business context for a process chain
    
    Args:
        chain_id: Process chain identifier
        
    Returns:
        Business context dictionary
    """
    engine = BusinessRulesEngine()
    return engine.get_business_context(chain_id)

def check_naming_compliance(chain_id: str) -> bool:
    """
    Quick check if a chain ID follows naming conventions
    
    Args:
        chain_id: Process chain identifier
        
    Returns:
        True if compliant, False otherwise
    """
    context = get_chain_context(chain_id)
    return context["naming_compliance"]["is_compliant"]

# Test function
def test_business_rules():
    """Test the business rules engine"""
    
    # Sample data
    test_data = pd.DataFrame({
        'chain_id': ['PC_SALES_DAILY', 'invalid_chain', 'ZPC_CUSTOM_WEEKLY'],
        'status_of_process': ['SUCCESS', 'INVALID_STATUS', 'RUNNING'],
        'current_date': ['2024-01-15', '2024-01-14', '2024-01-15'],
        'time': ['02:30:00', '14:30:00', '08:00:00']
    })
    
    engine = BusinessRulesEngine(strict_mode=False)
    
    print("Testing Business Rules Engine")
    print("=" * 50)
    
    violations = engine.validate_process_chain_data(test_data)
    
    print(f"Found {len(violations)} rule violations:\n")
    
    for violation in violations:
        severity_emoji = {
            RuleSeverity.INFO: "ℹ️",
            RuleSeverity.WARNING: "⚠️",
            RuleSeverity.ERROR: "❌",
            RuleSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(violation.severity, "❓")
        print(f"{emoji} [{violation.rule_id}] {violation.message}")
        if violation.suggestion:
            print(f"   💡 Suggestion: {violation.suggestion}")
        print()
    
    # Test business context
    print("Testing Business Context:")
    print("-" * 30)
    
    context = engine.get_business_context("PC_SALES_DAILY")
    print(f"Chain: PC_SALES_DAILY")
    print(f"Naming Compliant: {context['naming_compliance']['is_compliant']}")
    print(f"Business Impact: {context['business_impact']['level']}")
    print(f"Recommended Schedule: {context['recommended_schedule']['frequency']}")

if __name__ == "__main__":
    test_business_rules() 