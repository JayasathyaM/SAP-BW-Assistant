# SAP BW Process Chain Chatbot POC - Requirements & Core Components

## Project Overview
Local chatbot application for SAP BW process chains using open-source AI models, SQLite database, and Streamlit UI. Handles simple status queries and analytical queries about process chain execution.

## System Requirements

### Hardware Requirements
- **RAM**: 8GB minimum (12GB+ recommended for smooth AI model performance)
- **Storage**: 2GB free space (for AI models and database)
- **OS**: Windows 10/11, macOS, or Linux

### Software Requirements
- **Python**: 3.9+ 
- **Ollama**: For local AI model hosting
- **Git**: For version control

## Python Dependencies (requirements.txt)

```txt
# Core Framework
streamlit>=1.28.0

# Database
sqlite3  # Built into Python
pandas>=2.0.0

# AI/ML
ollama>=0.1.0
langchain>=0.1.0
langchain-community>=0.0.10

# Data Visualization
plotly>=5.15.0
altair>=5.0.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
typing-extensions>=4.7.0

# Development
pytest>=7.4.0
black>=23.0.0
```

## Core Architecture

### System Flow
```
[User Input] → [Streamlit UI] → [Query Processor] → [AI Model] → [SQL Generator] → [SQLite DB] → [Response Formatter] → [UI Display]
```

### Component Structure

```
SAP-BW-Assistant/
├── app.py                     # Main Streamlit application entry point
├── requirements.txt           # Python dependencies
├── README.md                 # Project documentation
├── .env                      # Environment variables (API keys, configs)
├── .gitignore               # Git ignore file
│
├── database/
│   ├── __init__.py
│   ├── schema.sql           # SQLite database schema
│   ├── db_manager.py        # Database connection and operations
│   ├── sample_data.py       # Generate mock SAP BW data
│   └── data_loader.py       # Load data into SQLite
│
├── llm/
│   ├── __init__.py
│   ├── ollama_client.py     # Ollama AI model integration
│   ├── prompt_templates.py  # AI prompts for SQL generation
│   └── query_processor.py   # Convert natural language to SQL
│
├── ui/
│   ├── __init__.py
│   ├── chat_interface.py    # Streamlit chat components
│   ├── dashboard.py         # Analytics dashboard widgets
│   └── utils.py            # UI utility functions
│
├── core/
│   ├── __init__.py
│   ├── query_validator.py   # Validate and sanitize SQL queries
│   ├── response_formatter.py # Format AI responses for display
│   └── error_handler.py     # Error handling and logging
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Application configuration
│   └── constants.py         # SAP BW constants and mappings
│
└── tests/
    ├── __init__.py
    ├── test_database.py      # Database tests
    ├── test_llm.py          # AI model tests
    └── test_ui.py           # UI tests
```

## Database Schema

### Tables Overview
1. **RSPCLOGCHAIN** - Process Chain Run Logs
2. **RSPCCHAIN** - Process Chain Definition  
3. **RSPCPROCESSLOG** - Step Execution Logs
4. **RSPCVARIANT** - Variant Parameter Definitions

### Key Relationships
- RSPCLOGCHAIN.CHAIN_ID → RSPCCHAIN.CHAIN_ID
- RSPCPROCESSLOG.LOG_ID → RSPCLOGCHAIN.LOG_ID
- RSPCVARIANT.(PROCESS_TYPE, PROCESS_VARIANT_NAME) → RSPCCHAIN.(PROCESS_TYPE, PROCESS_VARIANT_NAME)

## AI Model Configuration

### Recommended Models (Ollama)
1. **llama3.1:8b** (Primary) - Best balance of performance and resource usage
2. **codellama:7b** (Secondary) - Good for SQL generation
3. **mistral:7b** (Alternative) - Lightweight option

### Model Installation Commands
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download recommended model
ollama pull llama3.1:8b
```

## Feature Specifications

### Core Features
- ✅ **Natural Language Chat Interface**
- ✅ **SQL Query Generation from Questions**
- ✅ **Real-time Process Chain Status**
- ✅ **Analytical Queries with Visualizations**
- ✅ **Query History and Bookmarks**
- ✅ **Data Export (CSV/Excel)**

### Supported Query Types

#### Status Queries
- "What's the status of process chain PC_SALES_DAILY?"
- "Show me all failed chains today"
- "When did PC_INVENTORY last run?"

#### Analytical Queries  
- "Which process chains fail most often?"
- "Show me process chain performance this month"
- "What are the longest running chains?"

### UI Components

#### Left Panel - Chat Interface
- Chat input box
- Message history
- Suggested queries
- Query bookmarks

#### Right Panel - Dashboard
- Live KPI metrics
- Dynamic charts (failures, performance)
- Data tables
- Export buttons

## Development Phases

### Phase 1: Foundation
1. Set up project structure
2. Create SQLite database schema
3. Generate sample data
4. Basic Streamlit app framework

### Phase 2: AI Integration
1. Install and configure Ollama
2. Implement query processing
3. Test SQL generation accuracy
4. Add error handling

### Phase 3: UI Development
1. Build chat interface
2. Add dashboard widgets
3. Implement data visualization
4. Add export functionality

### Phase 4: Testing & Optimization
1. Unit tests for core components
2. Performance optimization
3. User experience improvements
4. Documentation

## Configuration Settings

### Environment Variables (.env)
```
# Database
DATABASE_PATH=./database/sap_bw.db

# AI Model
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# UI
STREAMLIT_THEME=dark
DEBUG_MODE=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/chatbot.log
```

### Application Settings
- **Max Query Results**: 1000 rows
- **Chat History Limit**: 100 messages
- **Session Timeout**: 30 minutes
- **Export Formats**: CSV, Excel, JSON

## Security Considerations
- SQL injection prevention through parameterized queries
- Input validation and sanitization
- Local-only operation (no external data transmission)
- User session management

## Performance Targets
- **Query Response Time**: < 3 seconds
- **AI Model Load Time**: < 30 seconds
- **UI Responsiveness**: < 1 second for interactions
- **Database Query Time**: < 500ms

## Success Metrics
- **Accuracy**: 90%+ correct SQL generation
- **User Experience**: Intuitive chat interface
- **Performance**: Fast response times
- **Reliability**: Stable operation without crashes 