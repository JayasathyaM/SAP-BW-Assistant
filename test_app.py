import streamlit as st

st.title("🧪 Test App - SAP BW Chatbot")
st.write("✅ If you can see this, Streamlit is working!")
st.write("🔗 Now try running: `streamlit run main.py`")

# Test basic imports
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent / "src"))
    from ui.login_page import show_login_page
    st.success("✅ All imports successful!")
except Exception as e:
    st.error(f"❌ Import error: {e}") 