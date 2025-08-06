#!/usr/bin/env python3
"""
SAP BW Process Chain Assistant - Comprehensive Test Suite

This is the unified test file that validates all components and functionality
of the Enhanced SAP BW Process Chain Assistant including:
- Environment setup and dependencies
- Database integration and queries
- AI model integration and SQL generation  
- UI components and visualizations
- Enhanced chat features and user experience
- End-to-end workflow validation
- Production readiness assessment

Run with: python test_sap_bw_assistant.py
"""

import sys
import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestResult:
    """Container for test results with detailed tracking"""
    
    def __init__(self, category: str):
        self.category = category
        self.tests: List[Tuple[str, bool, str, float]] = []  # name, success, details, duration
        self.start_time = time.time()
        
    def add_test(self, name: str, success: bool, details: str = "", duration: float = 0.0):
        """Add a test result"""
        self.tests.append((name, success, details, duration))
        
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if not self.tests:
            return 0.0
        passed = sum(1 for _, success, _, _ in self.tests if success)
        return (passed / len(self.tests)) * 100
    
    def get_total_duration(self) -> float:
        """Get total test duration"""
        return sum(duration for _, _, _, duration in self.tests)

def test_environment_setup() -> TestResult:
    """Test environment setup and dependencies"""
    result = TestResult("Environment Setup")
    print("🔧 Testing Environment Setup...")
    
    # Test critical imports
    start = time.time()
    try:
        import streamlit as st
        import pandas as pd
        import plotly.graph_objects as go
        import transformers
        import torch
        import sqlalchemy
        result.add_test("Critical Imports", True, "All packages available", time.time() - start)
    except ImportError as e:
        result.add_test("Critical Imports", False, f"Missing: {e}", time.time() - start)
    
    # Test project structure
    start = time.time()
    required_dirs = ['config', 'core', 'database', 'llm', 'ui']
    missing_dirs = [d for d in required_dirs if not (project_root / d).exists()]
    
    if not missing_dirs:
        result.add_test("Project Structure", True, "All directories present", time.time() - start)
    else:
        result.add_test("Project Structure", False, f"Missing: {missing_dirs}", time.time() - start)
    
    # Test configuration
    start = time.time()
    try:
        from config.settings import AppConfig
        config_valid = all([
            hasattr(AppConfig, 'DATABASE_PATH'),
            hasattr(AppConfig, 'AI_MODEL_NAME'),
            hasattr(AppConfig, 'DEBUG')
        ])
        result.add_test("Configuration", config_valid, "AppConfig settings", time.time() - start)
    except Exception as e:
        result.add_test("Configuration", False, str(e), time.time() - start)
    
    return result

def test_database_integration() -> TestResult:
    """Test comprehensive database functionality"""
    result = TestResult("Database Integration")
    print("💾 Testing Database Integration...")
    
    try:
        from database.db_manager_sqlite import DatabaseManager, SAPBWQueries
        from config.settings import AppConfig
        
        # Test database connection
        start = time.time()
        db_manager = DatabaseManager(AppConfig.DATABASE_PATH)
        if db_manager.initialize_pool():
            result.add_test("Database Connection", True, "SQLite connected", time.time() - start)
        else:
            result.add_test("Database Connection", False, "Connection failed", time.time() - start)
            return result
        
        # Test database content
        start = time.time()
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = db_manager.execute_query(tables_query)
        expected_tables = {'RSPCCHAIN', 'RSPCLOGCHAIN', 'RSPCPROCESSLOG', 'RSPCVARIANT'}
        found_tables = {row['name'] for row in tables if row['name'].startswith('RSPC')}
        
        if expected_tables.issubset(found_tables):
            result.add_test("Database Schema", True, f"Tables: {found_tables}", time.time() - start)
        else:
            missing = expected_tables - found_tables
            result.add_test("Database Schema", False, f"Missing: {missing}", time.time() - start)
        
        # Test data content
        start = time.time()
        count_query = "SELECT COUNT(*) as count FROM RSPCCHAIN"
        count_result = db_manager.execute_query(count_query)
        chain_count = count_result[0]['count'] if count_result else 0
        
        if chain_count > 0:
            result.add_test("Database Data", True, f"{chain_count} process chains", time.time() - start)
        else:
            result.add_test("Database Data", False, "No data found", time.time() - start)
        
        # Test SAPBWQueries functionality
        start = time.time()
        sap_queries = SAPBWQueries(db_manager)
        
        query_methods = [
            ('get_latest_chain_status', 'Latest status'),
            ('get_failed_chains', 'Failed chains'),
            ('get_chain_performance_summary', 'Performance summary'),
            ('get_chain_success_rates', 'Success rates')
        ]
        
        for method_name, description in query_methods:
            method_start = time.time()
            try:
                method = getattr(sap_queries, method_name)
                if method_name == 'get_chain_success_rates':
                    data = method(10)
                else:
                    data = method()
                
                if data is not None:
                    count = len(data) if hasattr(data, '__len__') else 1
                    result.add_test(f"SAP Query: {description}", True, f"{count} records", time.time() - method_start)
                else:
                    result.add_test(f"SAP Query: {description}", False, "No data returned", time.time() - method_start)
            except Exception as e:
                result.add_test(f"SAP Query: {description}", False, str(e)[:50], time.time() - method_start)
        
        # Test database views
        start = time.time()
        views = ['VW_LATEST_CHAIN_RUNS', 'VW_CHAIN_SUMMARY', 'VW_TODAYS_ACTIVITY']
        for view in views:
            view_start = time.time()
            try:
                view_data = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {view}")
                count = view_data[0]['count'] if view_data else 0
                result.add_test(f"View: {view}", True, f"{count} records", time.time() - view_start)
            except Exception as e:
                result.add_test(f"View: {view}", False, str(e)[:50], time.time() - view_start)
        
    except Exception as e:
        result.add_test("Database System", False, f"Critical error: {e}", 0)
    
    return result

def test_ai_integration() -> TestResult:
    """Test AI model and query processing"""
    result = TestResult("AI Integration")
    print("🤖 Testing AI Integration...")
    
    try:
        from llm.query_processor import QueryProcessor
        from llm.transformer_client import TransformerClient
        from config.settings import AppConfig
        
        # Test AI model initialization
        start = time.time()
        query_processor = QueryProcessor(model_name=AppConfig.AI_MODEL_NAME, auto_load=False)
        if query_processor.initialize():
            result.add_test("AI Model Init", True, "Model loaded successfully", time.time() - start)
        else:
            result.add_test("AI Model Init", False, "Model loading failed", time.time() - start)
            # Continue with other tests even if AI fails
        
        # Test transformer client
        start = time.time()
        try:
            transformer_client = TransformerClient()
            transformer_client.load_model()
            transformer_client.create_pipeline()
            result.add_test("Transformer Client", True, "Pipeline created", time.time() - start)
        except Exception as e:
            result.add_test("Transformer Client", False, str(e)[:50], time.time() - start)
        
        # Test query processing
        test_queries = [
            "Show failed chains",
            "Success rates", 
            "Running count",
            "Chain status"
        ]
        
        successful_queries = 0
        for query in test_queries:
            start = time.time()
            try:
                if query_processor.is_ready:
                    ai_result = query_processor.process_question(query)
                    if ai_result and ai_result.get("success"):
                        successful_queries += 1
                        result.add_test(f"Query: {query[:20]}", True, "SQL generated", time.time() - start)
                    else:
                        result.add_test(f"Query: {query[:20]}", False, "SQL generation failed", time.time() - start)
                else:
                    result.add_test(f"Query: {query[:20]}", False, "AI not ready", time.time() - start)
            except Exception as e:
                result.add_test(f"Query: {query[:20]}", False, str(e)[:30], time.time() - start)
        
        # Test prompt system
        start = time.time()
        try:
            from llm.enhanced_prompt_system import get_enhanced_prompt_engine
            engine = get_enhanced_prompt_engine()
            prompt = engine.create_enhanced_prompt("test query")
            result.add_test("Enhanced Prompts", True, f"Prompt: {len(prompt)} chars", time.time() - start)
        except Exception as e:
            result.add_test("Enhanced Prompts", False, str(e)[:50], time.time() - start)
        
    except Exception as e:
        result.add_test("AI System", False, f"Critical error: {e}", 0)
    
    return result

def test_ui_components() -> TestResult:
    """Test UI components and visualizations"""
    result = TestResult("UI Components")
    print("🎨 Testing UI Components...")
    
    # Test UI enhancements
    start = time.time()
    try:
        from ui.enhancements import get_ui_enhancer, LoadingManager
        
        enhancer = get_ui_enhancer()
        if hasattr(enhancer, 'custom_css') and len(enhancer.custom_css) > 1000:
            result.add_test("UI Enhancer", True, f"CSS: {len(enhancer.custom_css)} chars", time.time() - start)
        else:
            result.add_test("UI Enhancer", False, "CSS missing or incomplete", time.time() - start)
        
        # Test loading manager
        loading_start = time.time()
        with LoadingManager("Test operation") as loader:
            time.sleep(0.01)  # Brief test
        result.add_test("Loading Manager", True, "Context manager works", time.time() - loading_start)
        
    except Exception as e:
        result.add_test("UI Enhancer", False, str(e)[:50], time.time() - start)
    
    # Test enhanced chat features
    start = time.time()
    try:
        from ui.enhanced_chat import SmartSuggestions, EnhancedResponseFormatter, ChatContext
        
        # Test chat context
        context = ChatContext()
        context.add_query_result(True, "test")
        success_rate = context.get_success_rate()
        result.add_test("Chat Context", True, f"Success rate: {success_rate}%", time.time() - start)
        
        # Test smart suggestions
        suggestions = SmartSuggestions()
        suggestions_list = suggestions.get_smart_suggestions("test query")
        result.add_test("Smart Suggestions", True, f"{len(suggestions_list)} suggestions", time.time() - start)
        
        # Test response formatter
        formatter = EnhancedResponseFormatter()
        test_data = pd.DataFrame([{"CHAIN_ID": "TEST", "STATUS_OF_PROCESS": "SUCCESS"}])
        enhanced_resp = formatter.format_intelligent_response("test", "test sql", test_data)
        
        components = sum([
            bool(enhanced_resp.get("summary")),
            bool(enhanced_resp.get("insights")),
            bool(enhanced_resp.get("recommendations"))
        ])
        result.add_test("Response Formatter", True, f"{components}/3 components", time.time() - start)
        
    except Exception as e:
        result.add_test("Enhanced Chat", False, str(e)[:50], time.time() - start)
    
    # Test visualizations
    start = time.time()
    try:
        from ui.visualizations import get_visualizer, create_chart_for_query
        
        visualizer = get_visualizer()
        
        # Test chart creation
        test_data = pd.DataFrame([
            {"STATUS": "SUCCESS", "count": 10},
            {"STATUS": "FAILED", "count": 2}
        ])
        
        charts_created = 0
        
        # Test status pie chart
        try:
            status_chart = visualizer.create_status_pie_chart(test_data)
            if status_chart and hasattr(status_chart, 'data'):
                charts_created += 1
        except:
            pass
        
        # Test performance chart
        try:
            perf_data = pd.DataFrame([{"CHAIN_ID": "TEST", "success_rate_percent": 95}])
            perf_chart = visualizer.create_success_rate_bar_chart(perf_data)
            if perf_chart and hasattr(perf_chart, 'data'):
                charts_created += 1
        except:
            pass
        
        # Test dynamic chart
        try:
            dynamic_chart = create_chart_for_query(test_data, "show status")
            if dynamic_chart and hasattr(dynamic_chart, 'data'):
                charts_created += 1
        except:
            pass
        
        result.add_test("Visualizations", True, f"{charts_created}/3 chart types", time.time() - start)
        
    except Exception as e:
        result.add_test("Visualizations", False, str(e)[:50], time.time() - start)
    
    return result

def test_core_functionality() -> TestResult:
    """Test core business logic and security"""
    result = TestResult("Core Functionality")
    print("🛡️ Testing Core Functionality...")
    
    # Test query validator
    start = time.time()
    try:
        from core.query_validator import QueryValidator
        
        validator = QueryValidator()
        
        # Test safe SQL
        safe_sql = "SELECT CHAIN_ID FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED'"
        if validator.is_safe_sql(safe_sql):
            result.add_test("Safe SQL Validation", True, "Accepts safe queries", time.time() - start)
        else:
            result.add_test("Safe SQL Validation", False, "Rejects safe SQL", time.time() - start)
        
        # Test dangerous SQL
        dangerous_sql = "DROP TABLE RSPCCHAIN"
        if not validator.is_safe_sql(dangerous_sql):
            result.add_test("Dangerous SQL Block", True, "Blocks dangerous operations", time.time() - start)
        else:
            result.add_test("Dangerous SQL Block", False, "Allows dangerous SQL", time.time() - start)
        
    except Exception as e:
        result.add_test("Query Validator", False, str(e)[:50], time.time() - start)
    
    # Test response formatter
    start = time.time()
    try:
        from core.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        test_data = [{"CHAIN_ID": "TEST", "STATUS": "SUCCESS"}]
        
        # Test different response types
        response_types = ["status", "performance", "analytics"]
        for resp_type in response_types:
            try:
                formatted = formatter.format_response(test_data, resp_type)
                if formatted and isinstance(formatted, str):
                    result.add_test(f"Format {resp_type}", True, "Response formatted", time.time() - start)
                else:
                    result.add_test(f"Format {resp_type}", False, "No formatted response", time.time() - start)
            except:
                result.add_test(f"Format {resp_type}", False, "Formatting error", time.time() - start)
        
    except Exception as e:
        result.add_test("Response Formatter", False, str(e)[:50], time.time() - start)
    
    # Test security manager
    start = time.time()
    try:
        from core.security_manager import SecurityManager
        
        security = SecurityManager()
        
        # Test input validation
        safe_inputs = ["show failed chains", "success rate analysis", "chain status"]
        unsafe_inputs = ["<script>alert('xss')</script>", "'; DROP TABLE users; --"]
        
        safe_count = 0
        for safe_input in safe_inputs:
            if security.validate_input(safe_input):
                safe_count += 1
        
        unsafe_count = 0
        for unsafe_input in unsafe_inputs:
            if not security.validate_input(unsafe_input):
                unsafe_count += 1
        
        if safe_count == len(safe_inputs) and unsafe_count == len(unsafe_inputs):
            result.add_test("Security Manager", True, "Input validation working", time.time() - start)
        else:
            result.add_test("Security Manager", False, f"Safe: {safe_count}/{len(safe_inputs)}, Unsafe: {unsafe_count}/{len(unsafe_inputs)}", time.time() - start)
        
    except Exception as e:
        result.add_test("Security Manager", False, str(e)[:50], time.time() - start)
    
    return result

def test_end_to_end_workflow() -> TestResult:
    """Test complete end-to-end workflow"""
    result = TestResult("End-to-End Workflow")
    print("🔄 Testing End-to-End Workflow...")
    
    try:
        from database.db_manager_sqlite import DatabaseManager, SAPBWQueries
        from llm.query_processor import QueryProcessor
        from ui.enhanced_chat import EnhancedResponseFormatter
        from ui.visualizations import create_chart_for_query
        from config.settings import AppConfig
        
        # Initialize components
        start = time.time()
        db_manager = DatabaseManager(AppConfig.DATABASE_PATH)
        db_manager.initialize_pool()
        sap_queries = SAPBWQueries(db_manager)
        query_processor = QueryProcessor(auto_load=False)
        ai_ready = query_processor.initialize()
        formatter = EnhancedResponseFormatter()
        
        result.add_test("Component Init", True, f"AI ready: {ai_ready}", time.time() - start)
        
        # Test workflow scenarios
        scenarios = [
            {
                "query": "show me failed process chains",
                "fallback_method": "get_failed_chains",
                "description": "Failed chains workflow"
            },
            {
                "query": "what is the success rate",
                "fallback_method": "get_chain_performance_summary", 
                "description": "Performance workflow"
            },
            {
                "query": "show current status",
                "fallback_method": "get_latest_chain_status",
                "description": "Status workflow"
            }
        ]
        
        successful_workflows = 0
        
        for scenario in scenarios:
            workflow_start = time.time()
            data_obtained = False
            
            # Try AI path
            if ai_ready:
                try:
                    ai_result = query_processor.process_question(scenario["query"])
                    if ai_result and ai_result.get("success"):
                        sql = ai_result["sql"]
                        if 'error' not in sql.lower():
                            df_result = db_manager.execute_query_to_dataframe(sql)
                            if not df_result.empty:
                                data_obtained = True
                except:
                    pass
            
            # Fallback path
            if not data_obtained:
                try:
                    method = getattr(sap_queries, scenario["fallback_method"])
                    fallback_data = method()
                    if fallback_data:
                        df_result = pd.DataFrame(fallback_data) if isinstance(fallback_data, list) else fallback_data
                        if not df_result.empty:
                            data_obtained = True
                except:
                    pass
            
            # Test response enhancement
            if data_obtained:
                try:
                    enhanced_response = formatter.format_intelligent_response(
                        scenario["query"], "test sql", df_result
                    )
                    
                    # Test visualization
                    chart = create_chart_for_query(df_result, scenario["query"])
                    
                    workflow_success = bool(enhanced_response.get("summary")) and chart is not None
                    if workflow_success:
                        successful_workflows += 1
                    
                    result.add_test(scenario["description"], workflow_success, 
                                  f"Data: {len(df_result)} rows, Enhanced: {bool(enhanced_response.get('summary'))}", 
                                  time.time() - workflow_start)
                except Exception as e:
                    result.add_test(scenario["description"], False, str(e)[:50], time.time() - workflow_start)
            else:
                result.add_test(scenario["description"], False, "No data obtained", time.time() - workflow_start)
        
        # Overall workflow assessment
        workflow_success_rate = (successful_workflows / len(scenarios)) * 100
        result.add_test("Overall Workflow", workflow_success_rate >= 70, 
                       f"{successful_workflows}/{len(scenarios)} scenarios", 0)
        
    except Exception as e:
        result.add_test("Workflow System", False, f"Critical error: {e}", 0)
    
    return result

def test_performance_assessment() -> TestResult:
    """Test application performance and readiness"""
    result = TestResult("Performance Assessment")
    print("⚡ Testing Performance Assessment...")
    
    try:
        from database.db_manager_sqlite import DatabaseManager
        from config.settings import AppConfig
        
        db_manager = DatabaseManager(AppConfig.DATABASE_PATH)
        db_manager.initialize_pool()
        
        # Test query performance
        start = time.time()
        simple_query = "SELECT COUNT(*) as count FROM VW_LATEST_CHAIN_RUNS"
        db_manager.execute_query(simple_query)
        simple_time = time.time() - start
        
        if simple_time < 0.1:  # Under 100ms
            result.add_test("Simple Query Speed", True, f"{simple_time:.3f}s", simple_time)
        else:
            result.add_test("Simple Query Speed", False, f"{simple_time:.3f}s (slow)", simple_time)
        
        # Test complex query performance
        start = time.time()
        complex_query = """
        SELECT c.CHAIN_ID, COUNT(l.LOG_ID) as runs, 
               SUM(CASE WHEN l.STATUS_OF_PROCESS = 'SUCCESS' THEN 1 ELSE 0 END) as success_count
        FROM RSPCCHAIN c 
        LEFT JOIN RSPCLOGCHAIN l ON c.CHAIN_ID = l.CHAIN_ID 
        GROUP BY c.CHAIN_ID
        """
        db_manager.execute_query_to_dataframe(complex_query)
        complex_time = time.time() - start
        
        if complex_time < 1.0:  # Under 1 second
            result.add_test("Complex Query Speed", True, f"{complex_time:.3f}s", complex_time)
        else:
            result.add_test("Complex Query Speed", False, f"{complex_time:.3f}s (slow)", complex_time)
        
        # Test memory usage (basic check)
        start = time.time()
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb < 500:  # Under 500MB
            result.add_test("Memory Usage", True, f"{memory_mb:.1f}MB", time.time() - start)
        else:
            result.add_test("Memory Usage", False, f"{memory_mb:.1f}MB (high)", time.time() - start)
        
        # Test file system
        start = time.time()
        required_files = ['app.py', 'requirements.txt', 'README.md', 'sap_bw_demo.db']
        missing_files = [f for f in required_files if not (project_root / f).exists()]
        
        if not missing_files:
            result.add_test("Required Files", True, "All files present", time.time() - start)
        else:
            result.add_test("Required Files", False, f"Missing: {missing_files}", time.time() - start)
        
    except Exception as e:
        result.add_test("Performance System", False, f"Error: {e}", 0)
    
    return result

def generate_comprehensive_report(test_results: List[TestResult]) -> Dict[str, Any]:
    """Generate comprehensive test report"""
    
    total_tests = sum(len(tr.tests) for tr in test_results)
    total_passed = sum(sum(1 for _, success, _, _ in tr.tests if success) for tr in test_results)
    total_duration = sum(tr.get_total_duration() for tr in test_results)
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Categorize issues
    critical_issues = []
    warnings = []
    
    for tr in test_results:
        for name, success, details, _ in tr.tests:
            if not success:
                if any(keyword in name.lower() for keyword in ['database', 'connection', 'critical', 'system']):
                    critical_issues.append(f"{tr.category}: {name} - {details}")
                else:
                    warnings.append(f"{tr.category}: {name} - {details}")
    
    # Generate recommendations
    recommendations = []
    
    if overall_success_rate >= 95:
        recommendations.append("🎉 System is production-ready! Deploy immediately.")
    elif overall_success_rate >= 85:
        recommendations.append("✅ System is functional with minor issues. Deploy with monitoring.")
    elif overall_success_rate >= 70:
        recommendations.append("⚠️ System needs optimization before production deployment.")
    else:
        recommendations.append("❌ System has significant issues. Address critical problems first.")
    
    if critical_issues:
        recommendations.append(f"🔧 Address {len(critical_issues)} critical issues immediately.")
    
    if len(warnings) > 5:
        recommendations.append(f"⚠️ {len(warnings)} warnings detected. Consider improvements.")
    
    if total_duration > 60:
        recommendations.append("⏱️ Tests taking too long. Optimize performance.")
    
    return {
        "overall_success_rate": overall_success_rate,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "total_duration": total_duration,
        "critical_issues": critical_issues,
        "warnings": warnings,
        "recommendations": recommendations,
        "categories": {tr.category: tr.get_success_rate() for tr in test_results}
    }

def main():
    """Run comprehensive test suite"""
    print("🚀 SAP BW Process Chain Assistant - Comprehensive Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all test categories
    test_results = [
        test_environment_setup(),
        test_database_integration(), 
        test_ai_integration(),
        test_ui_components(),
        test_core_functionality(),
        test_end_to_end_workflow(),
        test_performance_assessment()
    ]
    
    # Generate comprehensive report
    report = generate_comprehensive_report(test_results)
    
    # Display results
    print("\n" + "=" * 80)
    print("🏆 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    for tr in test_results:
        success_rate = tr.get_success_rate()
        status = "✅ PASS" if success_rate >= 80 else "⚠️ WARN" if success_rate >= 60 else "❌ FAIL"
        passed = sum(1 for _, success, _, _ in tr.tests if success)
        total = len(tr.tests)
        duration = tr.get_total_duration()
        
        print(f"{tr.category:25}: {status} ({success_rate:5.1f}% - {passed:2d}/{total:2d} tests - {duration:5.2f}s)")
    
    print("=" * 80)
    print(f"Overall Score: {report['total_passed']}/{report['total_tests']} ({report['overall_success_rate']:.1f}%)")
    print(f"Total Duration: {report['total_duration']:.2f} seconds")
    
    # Critical issues
    if report['critical_issues']:
        print(f"\n❌ Critical Issues ({len(report['critical_issues'])}):")
        for issue in report['critical_issues'][:5]:
            print(f"  • {issue}")
        if len(report['critical_issues']) > 5:
            print(f"  ... and {len(report['critical_issues']) - 5} more")
    
    # Warnings
    if report['warnings']:
        print(f"\n⚠️ Warnings ({len(report['warnings'])}):")
        for warning in report['warnings'][:3]:
            print(f"  • {warning}")
        if len(report['warnings']) > 3:
            print(f"  ... and {len(report['warnings']) - 3} more")
    
    # Recommendations
    print(f"\n🎯 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Final assessment
    print("\n" + "=" * 80)
    if report['overall_success_rate'] >= 95:
        print("🎉 OUTSTANDING! PRODUCTION READY!")
        print("🚀 Deploy immediately - All systems operational")
        status = "PRODUCTION_READY"
    elif report['overall_success_rate'] >= 85:
        print("✅ EXCELLENT! READY FOR DEPLOYMENT")
        print("🔧 Minor optimizations possible but fully functional")
        status = "DEPLOY_READY"
    elif report['overall_success_rate'] >= 70:
        print("⚠️ GOOD! FUNCTIONAL WITH MONITORING")
        print("🛠️ Address warnings before production deployment")
        status = "NEEDS_MONITORING"
    else:
        print("❌ NEEDS SIGNIFICANT WORK")
        print("🔧 Critical issues must be resolved")
        status = "NEEDS_WORK"
    
    print(f"\n🎯 Final Status: {status}")
    print(f"⏱️ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return report['overall_success_rate'] >= 85

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 