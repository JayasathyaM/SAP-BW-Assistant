"""
SAP BW Chatbot - Setup Verification Test

This script tests if all required dependencies are properly installed.
Run with: python test_setup.py
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    
    print("🧪 Testing SAP BW Chatbot Setup...")
    print("=" * 50)
    
    # Test basic Python
    print(f"✅ Python version: {sys.version}")
    
    # Test required packages
    packages_to_test = [
        ("streamlit", "Streamlit UI framework"),
        ("pandas", "Data manipulation"),
        ("psycopg2", "PostgreSQL driver"),
        ("sqlalchemy", "Database ORM"),
        ("transformers", "Hugging Face AI models"),
        ("torch", "PyTorch ML framework"),
        ("plotly", "Data visualization"),
        ("pydantic", "Data validation")
    ]
    
    results = []
    
    for package, description in packages_to_test:
        try:
            __import__(package)
            print(f"✅ {package:15} - {description}")
            results.append((package, True))
        except ImportError as e:
            print(f"❌ {package:15} - {description} (Error: {e})")
            results.append((package, False))
    
    print("=" * 50)
    
    # Summary
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"📊 Setup Results: {successful}/{total} packages installed")
    
    if successful == total:
        print("🎉 All packages installed successfully!")
        print("✅ Ready to run: streamlit run app.py")
        return True
    else:
        print("⚠️  Some packages missing. Install with: pip install -r requirements.txt")
        return False

def test_project_structure():
    """Test if project structure is correct"""
    
    print("\n🏗️  Testing Project Structure...")
    print("=" * 50)
    
    required_dirs = ["database", "llm", "ui", "core", "config", "tests"]
    required_files = ["app.py", "requirements.txt", "README.md", "env.template"]
    
    # Test directories
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory: {directory}/")
        else:
            print(f"❌ Missing directory: {directory}/")
    
    # Test files
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ File: {file}")
        else:
            print(f"❌ Missing file: {file}")

if __name__ == "__main__":
    print("🚀 SAP BW Process Chain Chatbot - Setup Verification")
    print("=" * 60)
    
    # Test project structure
    test_project_structure()
    
    # Test package imports
    success = test_imports()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 SETUP COMPLETE! You can now run the chatbot.")
        print("📋 Next steps:")
        print("   1. Run: streamlit run app.py")
        print("   2. Open browser to localhost:8501")
        print("   3. Start Phase 1 development (database setup)")
    else:
        print("🔧 SETUP INCOMPLETE. Please install missing packages.")
        print("📋 Run: pip install -r requirements.txt")
    
    print("=" * 60) 