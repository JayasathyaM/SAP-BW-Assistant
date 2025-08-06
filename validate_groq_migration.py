#!/usr/bin/env python3
"""
Groq Migration Validation Script
Tests the migration from T5-small to Groq API for SAP BW SQL generation
"""

import sys
import os
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm.groq_client import GroqClient
from llm.query_processor import QueryProcessor
from llm.groq_prompts import GroqPromptEngine
from config.settings import AppConfig

def test_groq_api_connection():
    """Test basic Groq API connectivity"""
    print("🔗 Testing Groq API Connection")
    print("-" * 40)
    
    # Check API key
    api_key = AppConfig.GROQ_API_KEY
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}..." if len(api_key) > 10 else f"✅ API Key: {api_key}")
    
    # Test connection
    client = GroqClient(api_key=api_key)
    if client.initialize():
        print("✅ Groq API connection successful")
        
        # Test connection details
        test_result = client.test_connection()
        if test_result["success"]:
            print(f"✅ Model: {test_result['model']}")
            print(f"✅ Response time: {test_result['response_time']}s")
            return True
        else:
            print(f"❌ Connection test failed: {test_result['error']}")
            return False
    else:
        print(f"❌ Failed to initialize Groq client: {client.initialization_error}")
        return False

def test_sql_generation():
    """Test SQL generation capabilities"""
    print("\n🔧 Testing SQL Generation")
    print("-" * 40)
    
    # Test questions that previously failed with T5
    test_questions = [
        "name all the chains",
        "what variant failed the most",
        "show failed chains today",
        "what is the success rate of all chains",
        "which chains are currently running"
    ]
    
    client = GroqClient()
    if not client.initialize():
        print("❌ Cannot test SQL generation - Groq client failed to initialize")
        return False
    
    successful_generations = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: '{question}'")
        
        start_time = time.time()
        sql = client.generate_sql(question)
        generation_time = time.time() - start_time
        
        print(f"⏱️  Generation time: {generation_time:.2f}s")
        print(f"📊 Generated SQL: {sql}")
        
        # Validate SQL quality
        if sql.startswith("SELECT 'Error:") or sql.startswith("SELECT 'No valid"):
            print("❌ SQL generation failed")
        elif "SELECT" in sql.upper() and any(table in sql.upper() for table in ['VW_LATEST_CHAIN_RUNS', 'VW_CHAIN_SUMMARY']):
            print("✅ Valid SQL generated")
            successful_generations += 1
        else:
            print("⚠️  SQL generated but quality uncertain")
    
    success_rate = (successful_generations / len(test_questions)) * 100
    print(f"\n📈 Success Rate: {success_rate:.1f}% ({successful_generations}/{len(test_questions)})")
    
    return success_rate >= 80  # 80% success rate threshold

def test_query_processor():
    """Test the updated QueryProcessor"""
    print("\n🎯 Testing QueryProcessor Integration")
    print("-" * 40)
    
    processor = QueryProcessor()
    
    if not processor.initialize():
        print(f"❌ QueryProcessor failed to initialize: {processor.initialization_error}")
        return False
    
    print("✅ QueryProcessor initialized successfully")
    print(f"✅ Model: {processor.model_name}")
    print(f"✅ Ready status: {processor.is_ready}")
    
    # Test question processing
    test_question = "show all failed process chains"
    print(f"\n📝 Testing question: '{test_question}'")
    
    result = processor.process_question(test_question)
    
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"✅ Question type: {result['question_type']}")
        print(f"✅ Confidence: {result['confidence']:.2f}")
        print(f"✅ Model used: {result['model_used']}")
        print(f"📊 Generated SQL: {result['sql']}")
        
        if result['processing_notes']:
            print(f"📝 Notes: {result['processing_notes']}")
    else:
        print(f"❌ Processing failed: {result.get('processing_notes', 'Unknown error')}")
    
    return result['success']

def test_prompt_optimization():
    """Test Llama3-optimized prompts"""
    print("\n🎨 Testing Prompt Optimization")
    print("-" * 40)
    
    engine = GroqPromptEngine()
    
    # Test question classification
    test_cases = [
        ("show failed chains", "failure_investigation"),
        ("what are the success rates", "performance_analysis"),
        ("list all chains", "chain_listing"),
        ("current status", "status_check")
    ]
    
    classification_success = 0
    
    for question, expected_type in test_cases:
        classified_type = engine.classify_question(question)
        print(f"📝 '{question}' → {classified_type.value}")
        
        if expected_type in classified_type.value:
            print("✅ Classification correct")
            classification_success += 1
        else:
            print(f"⚠️  Expected: {expected_type}")
    
    # Test prompt generation
    sample_question = "show failed chains today"
    prompt = engine.create_optimized_prompt(sample_question)
    
    print(f"\n📋 Sample prompt length: {len(prompt)} characters")
    
    # Check prompt quality
    prompt_quality_checks = [
        ("Contains schema", "VW_LATEST_CHAIN_RUNS" in prompt),
        ("Contains examples", "Example" in prompt),
        ("Contains instructions", "Instructions" in prompt or "REQUIREMENTS" in prompt),
        ("Question included", sample_question in prompt)
    ]
    
    passed_checks = 0
    for check_name, passed in prompt_quality_checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if passed:
            passed_checks += 1
    
    classification_rate = (classification_success / len(test_cases)) * 100
    prompt_quality = (passed_checks / len(prompt_quality_checks)) * 100
    
    print(f"\n📈 Classification accuracy: {classification_rate:.1f}%")
    print(f"📈 Prompt quality: {prompt_quality:.1f}%")
    
    return classification_rate >= 75 and prompt_quality >= 75

def test_performance_comparison():
    """Compare performance with previous T5 baseline"""
    print("\n⚡ Performance Analysis")
    print("-" * 40)
    
    client = GroqClient()
    if not client.initialize():
        print("❌ Cannot test performance - Groq client not available")
        return False
    
    # Test response times
    test_questions = [
        "show failed chains",
        "list all process chains",
        "what is the success rate"
    ]
    
    total_time = 0
    successful_requests = 0
    
    for question in test_questions:
        start_time = time.time()
        sql = client.generate_sql(question)
        end_time = time.time()
        
        response_time = end_time - start_time
        total_time += response_time
        
        if not sql.startswith("SELECT 'Error:"):
            successful_requests += 1
        
        print(f"📝 '{question}' → {response_time:.2f}s")
    
    avg_response_time = total_time / len(test_questions)
    success_rate = (successful_requests / len(test_questions)) * 100
    
    print(f"\n📊 Average response time: {avg_response_time:.2f}s")
    print(f"📊 Success rate: {success_rate:.1f}%")
    
    # Compare with T5 baseline (T5 was ~5-10s locally)
    print(f"\n📈 Performance vs T5 baseline:")
    print(f"✅ Response time: {'FASTER' if avg_response_time < 5 else 'SLOWER'} ({avg_response_time:.2f}s vs ~8s)")
    print(f"✅ Quality: {'BETTER' if success_rate > 60 else 'SIMILAR'} ({success_rate:.1f}% vs ~40%)")
    
    return avg_response_time < 10 and success_rate > 60

def run_comprehensive_validation():
    """Run all validation tests"""
    print("🚀 Groq Migration Validation")
    print("=" * 50)
    
    tests = [
        ("API Connection", test_groq_api_connection),
        ("SQL Generation", test_sql_generation),
        ("QueryProcessor", test_query_processor),
        ("Prompt Optimization", test_prompt_optimization),
        ("Performance", test_performance_comparison)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Tests...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"🏁 {test_name}: {status}")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    overall_success = passed_tests / total_tests
    print(f"\n🎯 Overall Success: {passed_tests}/{total_tests} ({overall_success*100:.1f}%)")
    
    if overall_success >= 0.8:
        print("🎉 MIGRATION SUCCESSFUL! Groq integration is ready for production.")
        return True
    else:
        print("⚠️  MIGRATION NEEDS ATTENTION. Some tests failed.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1) 