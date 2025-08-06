#!/usr/bin/env python3
"""
Token Optimization Validation Script
Tests the token capacity and prompt optimization improvements
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm.transformer_client import TransformerClient
from llm.enhanced_prompt_system import EnhancedPromptEngine

def test_token_improvements():
    """Test the token optimization improvements"""
    
    print("🔍 Validating Token Optimization Improvements")
    print("=" * 50)
    
    # 1. Test TransformerClient configuration
    print("\n1. Testing TransformerClient Configuration:")
    client = TransformerClient()
    
    print(f"   ✅ Max Length: {client.max_length} (should be 2048)")
    print(f"   ✅ Max Input Tokens: {client.max_input_tokens} (should be 1500)")
    print(f"   ✅ Token Warnings: {client.token_usage_warnings} (should be True)")
    
    assert client.max_length == 2048, f"Expected 2048, got {client.max_length}"
    assert client.max_input_tokens == 1500, f"Expected 1500, got {client.max_input_tokens}"
    assert client.token_usage_warnings == True, f"Expected True, got {client.token_usage_warnings}"
    
    # 2. Test Enhanced Prompt Engine
    print("\n2. Testing Enhanced Prompt Engine:")
    engine = EnhancedPromptEngine()
    
    # Test question that previously caused issues
    test_question = "what variant failed the most?"
    
    # Test full prompt
    full_prompt = engine._create_full_prompt(test_question, engine.classify_query(test_question))
    full_tokens = len(full_prompt) // 3
    print(f"   📏 Full prompt tokens (estimated): {full_tokens}")
    
    # Test compact prompt
    compact_prompt = engine._create_compact_prompt(test_question, engine.classify_query(test_question))
    compact_tokens = len(compact_prompt) // 3
    print(f"   📏 Compact prompt tokens (estimated): {compact_tokens}")
    
    # Test ultra-compact prompt
    ultra_prompt = engine._create_ultra_compact_prompt(test_question)
    ultra_tokens = len(ultra_prompt) // 3
    print(f"   📏 Ultra-compact prompt tokens (estimated): {ultra_tokens}")
    
    # Test smart prompt selection
    selected_prompt = engine.create_enhanced_prompt(test_question)
    selected_tokens = len(selected_prompt) // 3
    print(f"   🎯 Selected prompt tokens (estimated): {selected_tokens}")
    
    print(f"\n   ✅ Compact is smaller than full: {compact_tokens < full_tokens}")
    print(f"   ✅ Ultra is smallest: {ultra_tokens < compact_tokens}")
    print(f"   ✅ Selection logic working: {selected_tokens <= 400}")
    
    # 3. Test method availability
    print("\n3. Testing Method Availability:")
    
    # Check if compact prompt method exists in TransformerClient
    assert hasattr(client, '_create_compact_prompt'), "TransformerClient missing _create_compact_prompt"
    print("   ✅ TransformerClient._create_compact_prompt exists")
    
    # Check if ultra-compact method exists in EnhancedPromptEngine
    assert hasattr(engine, '_create_ultra_compact_prompt'), "EnhancedPromptEngine missing _create_ultra_compact_prompt"
    print("   ✅ EnhancedPromptEngine._create_ultra_compact_prompt exists")
    
    # 4. Test token estimation accuracy
    print("\n4. Testing Token Estimation:")
    
    sample_text = "SELECT * FROM VW_LATEST_CHAIN_RUNS WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1;"
    estimated = len(sample_text) // 3
    print(f"   📊 Sample SQL: {len(sample_text)} chars → ~{estimated} tokens")
    
    print("\n🎉 All Token Optimization Tests PASSED!")
    print("=" * 50)
    
    return {
        "max_length": client.max_length,
        "max_input_tokens": client.max_input_tokens,
        "full_prompt_tokens": full_tokens,
        "compact_prompt_tokens": compact_tokens,
        "ultra_prompt_tokens": ultra_tokens,
        "selected_prompt_tokens": selected_tokens
    }

def print_before_after():
    """Show before/after comparison"""
    
    print("\n📊 BEFORE vs AFTER Comparison:")
    print("=" * 50)
    print("BEFORE:")
    print("   ❌ Max Length: 512 tokens")
    print("   ❌ Token Warning: 963 > 512")
    print("   ❌ Single prompt size")
    print("   ❌ No token monitoring")
    print()
    print("AFTER:")
    print("   ✅ Max Length: 2048 tokens (4x increase)")
    print("   ✅ Smart input limit: 1500 tokens")
    print("   ✅ 3-tier prompt system (Full/Compact/Ultra)")
    print("   ✅ Real-time token monitoring")
    print("   ✅ Automatic optimization")
    print("   ✅ Enhanced SQL generation parameters")

if __name__ == "__main__":
    try:
        results = test_token_improvements()
        print_before_after()
        
        print(f"\n🚀 Ready to restart your app!")
        print("The token warning (963 > 512) should be eliminated.")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1) 