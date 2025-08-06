"""
SAP BW Security Manager

This module provides comprehensive security controls for the SAP BW chatbot,
including access control, audit logging, and advanced security validations.
"""

import hashlib
import hmac
import logging
import re
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access levels for different user types"""
    GUEST = "guest"           # Limited read-only access
    USER = "user"             # Standard user access
    ANALYST = "analyst"       # Enhanced analytical access
    ADMIN = "admin"           # Administrative access
    SYSTEM = "system"         # System-level access

class SecurityEvent(Enum):
    """Types of security events to log"""
    LOGIN_ATTEMPT = "login_attempt"
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_QUERY = "suspicious_query"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    DATA_ACCESS = "data_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SESSION_TIMEOUT = "session_timeout"

class SecurityViolation:
    """Represents a security violation"""
    
    def __init__(self,
                 violation_type: SecurityEvent,
                 severity: str,
                 message: str,
                 user_id: Optional[str] = None,
                 ip_address: Optional[str] = None,
                 additional_data: Optional[Dict] = None):
        """
        Initialize a security violation
        
        Args:
            violation_type: Type of security violation
            severity: Severity level (low, medium, high, critical)
            message: Description of the violation
            user_id: User identifier if available
            ip_address: IP address if available
            additional_data: Additional context data
        """
        self.violation_type = violation_type
        self.severity = severity
        self.message = message
        self.user_id = user_id
        self.ip_address = ip_address
        self.additional_data = additional_data or {}
        self.timestamp = datetime.now()
        self.violation_id = self._generate_violation_id()
    
    def _generate_violation_id(self) -> str:
        """Generate unique violation ID"""
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        violation_code = self.violation_type.value[:3].upper()
        return f"SEC_{violation_code}_{timestamp_str}"

class UserSession:
    """Represents a user session"""
    
    def __init__(self, 
                 user_id: str,
                 access_level: AccessLevel,
                 ip_address: Optional[str] = None,
                 session_timeout: int = 1800):  # 30 minutes
        """
        Initialize a user session
        
        Args:
            user_id: User identifier
            access_level: User's access level
            ip_address: IP address
            session_timeout: Session timeout in seconds
        """
        self.user_id = user_id
        self.access_level = access_level
        self.ip_address = ip_address
        self.session_timeout = session_timeout
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.session_id = self._generate_session_id()
        self.query_count = 0
        self.data_accessed = set()
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        data = f"{self.user_id}_{self.created_at}_{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.last_activity + timedelta(seconds=self.session_timeout)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.query_count += 1

class SecurityManager:
    """
    Comprehensive security manager for SAP BW chatbot
    """
    
    # Permission matrix: what each access level can do
    PERMISSIONS = {
        AccessLevel.GUEST: {
            'tables': {'vw_chain_summary'},
            'operations': {'select'},
            'max_rows': 100,
            'rate_limit': 10,  # queries per minute
            'sensitive_columns': set()
        },
        AccessLevel.USER: {
            'tables': {'vw_latest_chain_runs', 'vw_chain_summary', 'vw_todays_activity'},
            'operations': {'select'},
            'max_rows': 1000,
            'rate_limit': 30,
            'sensitive_columns': set()
        },
        AccessLevel.ANALYST: {
            'tables': {'vw_latest_chain_runs', 'vw_chain_summary', 'vw_todays_activity', 
                      'rspcchain', 'rspclogchain'},
            'operations': {'select'},
            'max_rows': 5000,
            'rate_limit': 60,
            'sensitive_columns': set()
        },
        AccessLevel.ADMIN: {
            'tables': {'vw_latest_chain_runs', 'vw_chain_summary', 'vw_todays_activity',
                      'rspcchain', 'rspclogchain', 'rspcprocesslog', 'rspcvariant'},
            'operations': {'select'},
            'max_rows': 10000,
            'rate_limit': 120,
            'sensitive_columns': set()
        }
    }
    
    # Advanced SQL injection patterns
    ADVANCED_INJECTION_PATTERNS = [
        r'(union\s+select|union\s+all\s+select)',
        r'(exec\s*\(|execute\s*\()',
        r'(sp_|xp_|fn_)',
        r'(waitfor\s+delay|benchmark\s*\()',
        r'(load_file\s*\(|into\s+outfile)',
        r'(@@version|@@servername)',
        r'(information_schema|sys\.)',
        r'(script\s*:|javascript\s*:)',
        r'(<script|<iframe|<object)',
        r'(drop\s+table|truncate\s+table)',
        r'(insert\s+into|update\s+.*\s+set)',
        r'(delete\s+from)',
        r'(\|\||&&|;\s*\w+|\|\s*\w+)',
        r'(0x[0-9a-f]+)',
        r'(char\s*\(\s*\d+\s*\))',
        r'(concat\s*\(.*\|\|)',
        r'(sleep\s*\(\s*\d+\s*\))',
        r'(pg_sleep\s*\(\s*\d+\s*\))'
    ]
    
    def __init__(self, 
                 enable_audit: bool = True,
                 session_timeout: int = 1800,
                 rate_limit_window: int = 60):
        """
        Initialize the security manager
        
        Args:
            enable_audit: Whether to enable audit logging
            session_timeout: Default session timeout in seconds
            rate_limit_window: Rate limiting window in seconds
        """
        self.enable_audit = enable_audit
        self.session_timeout = session_timeout
        self.rate_limit_window = rate_limit_window
        
        # Session management
        self.active_sessions: Dict[str, UserSession] = {}
        
        # Rate limiting
        self.rate_limit_tracker = defaultdict(list)
        
        # Security audit log
        self.security_events: List[SecurityViolation] = []
        self.blocked_ips: Set[str] = set()
        
        # Compiled regex patterns for performance
        self.injection_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in self.ADVANCED_INJECTION_PATTERNS]
        
        logger.info("SecurityManager initialized")
    
    def create_session(self, 
                      user_id: str, 
                      access_level: AccessLevel,
                      ip_address: Optional[str] = None) -> UserSession:
        """
        Create a new user session
        
        Args:
            user_id: User identifier
            access_level: User's access level
            ip_address: User's IP address
            
        Returns:
            UserSession object
        """
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        # Check if IP is blocked
        if ip_address and ip_address in self.blocked_ips:
            self._log_security_event(
                SecurityEvent.ACCESS_DENIED,
                "high",
                f"Access denied for blocked IP: {ip_address}",
                user_id,
                ip_address
            )
            raise PermissionError("Access denied")
        
        # Create new session
        session = UserSession(user_id, access_level, ip_address, self.session_timeout)
        self.active_sessions[session.session_id] = session
        
        self._log_security_event(
            SecurityEvent.LOGIN_ATTEMPT,
            "low",
            f"User session created for {user_id}",
            user_id,
            ip_address
        )
        
        logger.info(f"Session created for user {user_id} with access level {access_level.value}")
        return session
    
    def validate_session(self, session_id: str) -> Optional[UserSession]:
        """
        Validate and return session if valid
        
        Args:
            session_id: Session identifier
            
        Returns:
            UserSession if valid, None otherwise
        """
        session = self.active_sessions.get(session_id)
        
        if not session:
            return None
        
        if session.is_expired():
            self._log_security_event(
                SecurityEvent.SESSION_TIMEOUT,
                "low",
                f"Session expired for user {session.user_id}",
                session.user_id,
                session.ip_address
            )
            del self.active_sessions[session_id]
            return None
        
        session.update_activity()
        return session
    
    def validate_input(self, user_input: str) -> bool:
        """
        Validate user input for security threats
        
        Args:
            user_input: User input to validate
            
        Returns:
            True if input is safe, False otherwise
        """
        if not user_input or not user_input.strip():
            return False
        
        # Check for XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False
        
        # Check for SQL injection patterns
        sql_injection_patterns = [
            r"';\s*drop\s+table",
            r"';\s*delete\s+from",
            r"';\s*insert\s+into",
            r"';\s*update\s+.*\s+set",
            r"union\s+.*\s+select",
            r"'.*or.*'.*'.*='",
        ]
        
        for pattern in sql_injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False
        
        return True

    def check_sql_security(self, sql: str, session: UserSession) -> Dict[str, Any]:
        """
        Comprehensive SQL security check
        
        Args:
            sql: SQL query to check
            session: User session
            
        Returns:
            Security check result
        """
        result = {
            "is_safe": True,
            "violations": [],
            "risk_score": 0.0,
            "allowed": True
        }
        
        # Advanced SQL injection detection
        injection_violations = self._detect_sql_injection(sql, session)
        result["violations"].extend(injection_violations)
        
        # Permission-based access control
        access_violations = self._check_access_permissions(sql, session)
        result["violations"].extend(access_violations)
        
        # Rate limiting
        rate_violations = self._check_rate_limits(session)
        result["violations"].extend(rate_violations)
        
        # Calculate risk score
        result["risk_score"] = self._calculate_risk_score(result["violations"])
        
        # Determine if query should be allowed
        result["is_safe"] = len([v for v in result["violations"] if v.severity in ["high", "critical"]]) == 0
        result["allowed"] = result["is_safe"] and len(rate_violations) == 0
        
        # Log security events
        for violation in result["violations"]:
            if violation.severity in ["high", "critical"]:
                self._log_security_event(
                    violation.violation_type,
                    violation.severity,
                    violation.message,
                    session.user_id,
                    session.ip_address,
                    {"sql": sql[:200]}  # Log first 200 chars
                )
        
        return result
    
    def _detect_sql_injection(self, sql: str, session: UserSession) -> List[SecurityViolation]:
        """Detect SQL injection attempts"""
        violations = []
        sql_lower = sql.lower()
        
        for pattern in self.injection_patterns:
            if pattern.search(sql):
                violations.append(SecurityViolation(
                    SecurityEvent.SQL_INJECTION_ATTEMPT,
                    "critical",
                    f"SQL injection pattern detected: {pattern.pattern}",
                    session.user_id,
                    session.ip_address,
                    {"pattern": pattern.pattern, "sql_snippet": sql[:100]}
                ))
        
        # Check for suspicious comment patterns
        if '--' in sql or '/*' in sql:
            # Allow legitimate comments but flag suspicious ones
            comment_patterns = [
                r'--\s*\w+\s*=',  # Comments with assignments
                r'/\*.*?(union|select|drop).*?\*/',  # Comments hiding SQL
            ]
            for pattern in comment_patterns:
                if re.search(pattern, sql_lower):
                    violations.append(SecurityViolation(
                        SecurityEvent.SUSPICIOUS_QUERY,
                        "medium",
                        "Suspicious comment pattern in SQL",
                        session.user_id,
                        session.ip_address
                    ))
        
        # Check for encoded content
        if re.search(r'(0x[0-9a-f]{4,}|%[0-9a-f]{2})', sql_lower):
            violations.append(SecurityViolation(
                SecurityEvent.SUSPICIOUS_QUERY,
                "high",
                "Encoded content detected in SQL",
                session.user_id,
                session.ip_address
            ))
        
        return violations
    
    def _check_access_permissions(self, sql: str, session: UserSession) -> List[SecurityViolation]:
        """Check access permissions based on user level"""
        violations = []
        permissions = self.PERMISSIONS.get(session.access_level, {})
        
        # Extract table names from SQL
        table_pattern = r'(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        tables = set(re.findall(table_pattern, sql.lower()))
        
        # Check table access
        allowed_tables = permissions.get('tables', set())
        for table in tables:
            if table not in allowed_tables:
                violations.append(SecurityViolation(
                    SecurityEvent.ACCESS_DENIED,
                    "high",
                    f"Access denied to table '{table}' for access level {session.access_level.value}",
                    session.user_id,
                    session.ip_address,
                    {"table": table, "access_level": session.access_level.value}
                ))
        
        # Check operation permissions
        allowed_operations = permissions.get('operations', set())
        if not sql.lower().strip().startswith('select') and 'select' not in allowed_operations:
            violations.append(SecurityViolation(
                SecurityEvent.PRIVILEGE_ESCALATION,
                "critical",
                f"Unauthorized operation attempted by {session.access_level.value}",
                session.user_id,
                session.ip_address
            ))
        
        # Check for LIMIT clause if max_rows is enforced
        max_rows = permissions.get('max_rows', 1000)
        if 'limit' not in sql.lower() and max_rows < 10000:
            violations.append(SecurityViolation(
                SecurityEvent.SUSPICIOUS_QUERY,
                "medium",
                f"Query without LIMIT clause may return too many rows (max: {max_rows})",
                session.user_id,
                session.ip_address,
                {"max_rows": max_rows}
            ))
        
        return violations
    
    def _check_rate_limits(self, session: UserSession) -> List[SecurityViolation]:
        """Check rate limiting for the session"""
        violations = []
        permissions = self.PERMISSIONS.get(session.access_level, {})
        rate_limit = permissions.get('rate_limit', 30)
        
        user_key = f"{session.user_id}_{session.ip_address}"
        current_time = time.time()
        
        # Clean old entries
        self.rate_limit_tracker[user_key] = [
            timestamp for timestamp in self.rate_limit_tracker[user_key]
            if current_time - timestamp < self.rate_limit_window
        ]
        
        # Check current rate
        if len(self.rate_limit_tracker[user_key]) >= rate_limit:
            violations.append(SecurityViolation(
                SecurityEvent.RATE_LIMIT_EXCEEDED,
                "medium",
                f"Rate limit exceeded: {len(self.rate_limit_tracker[user_key])}/{rate_limit} queries per minute",
                session.user_id,
                session.ip_address,
                {"rate_limit": rate_limit, "current_count": len(self.rate_limit_tracker[user_key])}
            ))
        
        # Add current request
        self.rate_limit_tracker[user_key].append(current_time)
        
        return violations
    
    def _calculate_risk_score(self, violations: List[SecurityViolation]) -> float:
        """Calculate overall risk score from violations"""
        severity_weights = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.7,
            "critical": 1.0
        }
        
        total_score = sum(severity_weights.get(v.severity, 0.5) for v in violations)
        return min(1.0, total_score)
    
    def _log_security_event(self,
                           event_type: SecurityEvent,
                           severity: str,
                           message: str,
                           user_id: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           additional_data: Optional[Dict] = None):
        """Log a security event"""
        if not self.enable_audit:
            return
        
        violation = SecurityViolation(
            event_type,
            severity,
            message,
            user_id,
            ip_address,
            additional_data
        )
        
        self.security_events.append(violation)
        
        # Log to system logger
        log_message = f"Security Event [{violation.violation_id}]: {message}"
        if user_id:
            log_message += f" | User: {user_id}"
        if ip_address:
            log_message += f" | IP: {ip_address}"
        
        if severity == "critical":
            logger.critical(log_message)
        elif severity == "high":
            logger.error(log_message)
        elif severity == "medium":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = [
            sid for sid, session in self.active_sessions.items()
            if session.is_expired()
        ]
        
        for sid in expired_sessions:
            del self.active_sessions[sid]
    
    def mask_sensitive_data(self, data: Dict[str, Any], session: UserSession) -> Dict[str, Any]:
        """
        Mask sensitive data based on user access level
        
        Args:
            data: Data to potentially mask
            session: User session
            
        Returns:
            Data with sensitive information masked
        """
        permissions = self.PERMISSIONS.get(session.access_level, {})
        sensitive_columns = permissions.get('sensitive_columns', set())
        
        masked_data = data.copy()
        
        for column in sensitive_columns:
            if column in masked_data:
                masked_data[column] = "***MASKED***"
        
        return masked_data
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary and statistics"""
        current_time = datetime.now()
        last_hour = current_time - timedelta(hours=1)
        last_day = current_time - timedelta(days=1)
        
        recent_events = [e for e in self.security_events if e.timestamp > last_hour]
        daily_events = [e for e in self.security_events if e.timestamp > last_day]
        
        return {
            "active_sessions": len(self.active_sessions),
            "blocked_ips": len(self.blocked_ips),
            "total_security_events": len(self.security_events),
            "events_last_hour": len(recent_events),
            "events_last_day": len(daily_events),
            "critical_events_today": len([e for e in daily_events if e.severity == "critical"]),
            "top_violation_types": self._get_top_violation_types(daily_events)
        }
    
    def _get_top_violation_types(self, events: List[SecurityViolation]) -> Dict[str, int]:
        """Get top violation types from events"""
        violation_counts = defaultdict(int)
        for event in events:
            violation_counts[event.violation_type.value] += 1
        
        return dict(sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5])

# Convenience functions
def create_guest_session(ip_address: Optional[str] = None) -> UserSession:
    """Create a guest session"""
    manager = SecurityManager()
    return manager.create_session("guest", AccessLevel.GUEST, ip_address)

def create_user_session(user_id: str, ip_address: Optional[str] = None) -> UserSession:
    """Create a standard user session"""
    manager = SecurityManager()
    return manager.create_session(user_id, AccessLevel.USER, ip_address)

def validate_sql_security(sql: str, session: UserSession) -> bool:
    """Quick validation of SQL security"""
    manager = SecurityManager()
    result = manager.check_sql_security(sql, session)
    return result["allowed"]

# Test function
def test_security_manager():
    """Test the security manager"""
    
    manager = SecurityManager()
    
    print("Testing Security Manager")
    print("=" * 50)
    
    # Test session creation
    print("\n🔐 Testing Session Management:")
    user_session = manager.create_session("test_user", AccessLevel.USER, "192.168.1.1")
    print(f"  Session created: {user_session.session_id[:16]}...")
    print(f"  Access level: {user_session.access_level.value}")
    
    # Test SQL security checks
    print("\n🛡️ Testing SQL Security:")
    
    test_queries = [
        ("SELECT * FROM vw_latest_chain_runs;", "Valid query"),
        ("SELECT * FROM vw_latest_chain_runs; DROP TABLE users;", "SQL injection"),
        ("SELECT * FROM secret_table;", "Unauthorized table"),
        ("SELECT * FROM vw_latest_chain_runs WHERE 1=1;", "Suspicious pattern")
    ]
    
    for sql, description in test_queries:
        result = manager.check_sql_security(sql, user_session)
        status = "✅ SAFE" if result["allowed"] else "❌ BLOCKED"
        risk = result["risk_score"]
        
        print(f"  {status} {description} (risk: {risk:.2f})")
        for violation in result["violations"][:1]:  # Show first violation
            print(f"    • {violation.message}")
    
    # Test rate limiting
    print("\n⏱️ Testing Rate Limiting:")
    for i in range(35):  # Exceed rate limit
        result = manager.check_sql_security("SELECT COUNT(*) FROM vw_chain_summary;", user_session)
        if not result["allowed"]:
            print(f"  Rate limit triggered after {i+1} requests")
            break
    
    # Show security summary
    print("\n📊 Security Summary:")
    summary = manager.get_security_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_security_manager() 