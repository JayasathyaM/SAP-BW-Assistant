# SAP BW Process Chain Chatbot POC

A localhost-only demonstration chatbot for SAP BW process chain management using PostgreSQL, Hugging Face Transformers, and Streamlit.

## 🎯 Project Overview

This is a **proof of concept** chatbot that answers questions about SAP BW process chains using:
- **PostgreSQL** database with mock SAP BW data
- **Hugging Face Transformers** for local AI processing
- **Streamlit** for the web interface
- **100% Local** - no cloud services or external APIs

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 12 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JayasathyaM/SAP-BW-Assistant.git
   cd SAP-BW-Assistant
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy env.template .env
   # Edit .env file with your database credentials
   ```

5. **Set up database** (Coming in Phase 1)
   ```bash
   # Instructions will be added as development progresses
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
SAP-BW-Assistant/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── env.template             # Environment variables template
├── README.md               # This file
│
├── database/               # Database components
│   ├── __init__.py
│   ├── schema.sql         # PostgreSQL schema (Phase 1)
│   ├── db_manager.py      # Database connections (Phase 1)
│   └── sample_data.py     # Mock data generator (Phase 1)
│
├── llm/                   # AI/ML components
│   ├── __init__.py
│   ├── ollama_client.py   # Hugging Face integration (Phase 2)
│   └── query_processor.py # NL to SQL conversion (Phase 2)
│
├── ui/                    # User interface
│   ├── __init__.py
│   ├── chat_interface.py  # Chat components (Phase 4)
│   └── dashboard.py       # Dashboard widgets (Phase 4)
│
├── core/                  # Business logic
│   ├── __init__.py
│   ├── query_validator.py # SQL validation (Phase 3)
│   └── error_handler.py   # Error handling (Phase 3)
│
├── config/               # Configuration
│   ├── __init__.py
│   └── settings.py       # App settings (Phase 1)
│
└── tests/               # Test suites
    ├── __init__.py
    └── test_*.py        # Unit tests (Phase 5)
```

## 🔧 Development Status

### ✅ Completed
- [x] Project structure and documentation
- [x] Basic Streamlit app framework
- [x] Requirements definition

### 🚧 In Progress
- [ ] Database schema creation (Phase 1)
- [ ] Mock data generation (Phase 1)
- [ ] AI model integration (Phase 2)

### 📋 Planned
- [ ] Chat interface (Phase 4)
- [ ] Dashboard widgets (Phase 4)
- [ ] Testing suite (Phase 5)

## 🎮 Demo Features

When complete, the chatbot will support:

### Status Queries
- "What's the status of process chain PC_SALES_DAILY?"
- "Show me all failed process chains today"
- "When did PC_INVENTORY last run?"

### Analytical Queries
- "Which process chains fail most often?"
- "Show me process chain performance this month"
- "What are the longest running chains?"

## 📊 Database Schema

The system models 4 core SAP BW tables:
- **RSPCLOGCHAIN** - Process Chain Run Logs
- **RSPCCHAIN** - Process Chain Definition
- **RSPCPROCESSLOG** - Step Execution Logs
- **RSPCVARIANT** - Variant Parameter Definitions

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **AI/ML**: Hugging Face Transformers
- **Language**: Python 3.9+
- **Visualization**: Plotly, Altair

## 📚 Documentation

- [EXECUTION_PLAN.md](EXECUTION_PLAN.md) - Comprehensive development roadmap
- [TASK_TEMPLATE.md](TASK_TEMPLATE.md) - Task execution guidelines
- [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md) - Detailed requirements

## 🤝 Development Guidelines

1. Follow the task template for all development
2. Update progress in GitHub commits
3. Test each component before integration
4. Document all decisions and learnings

## 📄 License

This is a proof of concept project for demonstration purposes.

## 🆘 Support

For questions or issues, please check:
1. The troubleshooting section in documentation
2. GitHub issues
3. Project requirements document

---

*This is a localhost-only demonstration system. No real SAP BW data is used.* 