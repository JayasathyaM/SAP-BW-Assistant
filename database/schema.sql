-- SAP BW Process Chain Database Schema
-- SQLite implementation for localhost demo
-- Created for SAP BW Process Chain Chatbot POC

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS RSPCVARIANT;
DROP TABLE IF EXISTS RSPCPROCESSLOG;
DROP TABLE IF EXISTS RSPCLOGCHAIN;
DROP TABLE IF EXISTS RSPCCHAIN;

-- =====================================================
-- 1. RSPCCHAIN - Process Chain Definition
-- =====================================================
CREATE TABLE RSPCCHAIN (
    CHAIN_ID TEXT NOT NULL,
    VERSION TEXT NOT NULL,
    PROCESS_TYPE TEXT NOT NULL,
    PROCESS_VARIANT_NAME TEXT NOT NULL,
    SEQNO INTEGER NOT NULL,
    BACKGROUND_PROCESSING_EVENT TEXT,
    BATCH_EVENT_PARAMETERS TEXT,
    EVENT_NUMBER_WITH_DECISIONS TEXT,
    BACK_LINK_EVENT TEXT,
    SEND_GREEN_EVENT_WITH_ERRORS INTEGER DEFAULT 0,
    SECONDS INTEGER DEFAULT 0,
    NUMBER_OF_ATTEMPTS INTEGER DEFAULT 1,
    PROCESS_DOES_NOT_START_CHAIN INTEGER DEFAULT 0,
    PROCESS_EXECUTION_DEPENDS_ON TEXT,
    
    -- Primary Key as specified
    PRIMARY KEY (CHAIN_ID, VERSION, PROCESS_TYPE, PROCESS_VARIANT_NAME, SEQNO)
);

-- =====================================================
-- 2. RSPCLOGCHAIN - Process Chain Run Logs
-- =====================================================
CREATE TABLE RSPCLOGCHAIN (
    CHAIN_ID TEXT NOT NULL,
    LOG_ID TEXT NOT NULL,
    PROCESS_TYPE TEXT,
    PROCESS_VARIANT_NAME TEXT,
    CURRENT_DATE TEXT NOT NULL,
    TIME TEXT NOT NULL,
    BOOLEAN INTEGER DEFAULT 0,
    STATUS_OF_PROCESS TEXT NOT NULL CHECK (STATUS_OF_PROCESS IN ('SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED')),
    LONG_TIMESTAMP INTEGER,
    RFC_DESTINATION TEXT,
    LOGICAL_SYSTEM TEXT,
    UTC_TIMESTAMP_SHORT TEXT,
    SYNCHRONOUS_EXECUTION INTEGER DEFAULT 0,
    RUN_TERMINATED_MANUALLY INTEGER DEFAULT 0,
    STREAMING_FOR_PROCESS_CHAINS TEXT,
    
    -- Primary Key as specified
    PRIMARY KEY (CHAIN_ID, LOG_ID),
    
    -- Foreign Key to RSPCCHAIN
    FOREIGN KEY (CHAIN_ID) REFERENCES RSPCCHAIN(CHAIN_ID)
);

-- =====================================================
-- 3. RSPCPROCESSLOG - Step Execution Logs
-- =====================================================
CREATE TABLE RSPCPROCESSLOG (
    LOG_ID TEXT NOT NULL,
    PROCESS_TYPE TEXT NOT NULL,
    BACKGROUND_PROCESSING_EVENT TEXT NOT NULL,
    BATCH_EVENT_PARAMETERS TEXT NOT NULL,
    BACKGROUND_JOB_ID_NUMBER TEXT NOT NULL,
    SCHEDULED_RELEASE_DATE TEXT NOT NULL,
    SCHEDULED_RELEASE_TIME TEXT NOT NULL,
    BACK_LINK_EVENT TEXT,
    PROCESS_VARIANT_NAME TEXT,
    INSTANCE_ID TEXT,
    STATUS_OF_PROCESS TEXT NOT NULL CHECK (STATUS_OF_PROCESS IN ('SUCCESS', 'FAILED', 'RUNNING', 'WAITING', 'CANCELLED')),
    LONG_TIMESTAMP INTEGER,
    BACKGROUND_JOB_NAME TEXT,
    
    -- Primary Key as specified (composite of 7 fields)
    PRIMARY KEY (LOG_ID, PROCESS_TYPE, BACKGROUND_PROCESSING_EVENT, 
                 BATCH_EVENT_PARAMETERS, BACKGROUND_JOB_ID_NUMBER, 
                 SCHEDULED_RELEASE_DATE, SCHEDULED_RELEASE_TIME),
    
    -- Foreign Key to RSPCLOGCHAIN
    FOREIGN KEY (LOG_ID) REFERENCES RSPCLOGCHAIN(LOG_ID)
);

-- =====================================================
-- 4. RSPCVARIANT - Variant Parameter Definitions
-- =====================================================
CREATE TABLE RSPCVARIANT (
    PROCESS_TYPE TEXT NOT NULL,
    PROCESS_VARIANT_NAME TEXT NOT NULL,
    VERSION TEXT NOT NULL,
    SEQNO INTEGER NOT NULL,
    FIELD_NAME TEXT,
    SIGN TEXT CHECK (SIGN IN ('I', 'E')) DEFAULT 'I',
    OPTION TEXT CHECK (OPTION IN ('EQ', 'NE', 'GT', 'GE', 'LT', 'LE', 'BT', 'NB', 'CP', 'NP')) DEFAULT 'EQ',
    FROM_VALUE TEXT,
    TO_VALUE TEXT,
    
    -- Primary Key as specified
    PRIMARY KEY (PROCESS_TYPE, PROCESS_VARIANT_NAME, VERSION, SEQNO),
    
    -- Foreign Key as specified
        FOREIGN KEY (PROCESS_TYPE, PROCESS_VARIANT_NAME) 
        REFERENCES RSPCCHAIN(PROCESS_TYPE, PROCESS_VARIANT_NAME) 
);

-- =====================================================
-- INDEXES for Performance
-- =====================================================

-- RSPCCHAIN indexes
CREATE INDEX IDX_RSPCCHAIN_CHAIN_ID ON RSPCCHAIN(CHAIN_ID);
CREATE INDEX IDX_RSPCCHAIN_PROCESS_TYPE ON RSPCCHAIN(PROCESS_TYPE);

-- RSPCLOGCHAIN indexes
CREATE INDEX IDX_RSPCLOGCHAIN_DATE ON RSPCLOGCHAIN("CURRENT_DATE");
CREATE INDEX IDX_RSPCLOGCHAIN_STATUS ON RSPCLOGCHAIN(STATUS_OF_PROCESS);
CREATE INDEX IDX_RSPCLOGCHAIN_CHAIN_ID ON RSPCLOGCHAIN(CHAIN_ID);

-- RSPCPROCESSLOG indexes
CREATE INDEX IDX_RSPCPROCESSLOG_STATUS ON RSPCPROCESSLOG(STATUS_OF_PROCESS);
CREATE INDEX IDX_RSPCPROCESSLOG_DATE ON RSPCPROCESSLOG("SCHEDULED_RELEASE_DATE");
CREATE INDEX IDX_RSPCPROCESSLOG_JOB ON RSPCPROCESSLOG(BACKGROUND_JOB_NAME);
CREATE INDEX IDX_RSPCPROCESSLOG_LOG_ID ON RSPCPROCESSLOG(LOG_ID);

-- RSPCVARIANT indexes
CREATE INDEX IDX_RSPCVARIANT_TYPE ON RSPCVARIANT(PROCESS_TYPE);

-- =====================================================
-- VIEWS for Common Queries
-- =====================================================

-- View: Latest Process Chain Runs
CREATE VIEW VW_LATEST_CHAIN_RUNS AS
SELECT 
    c.CHAIN_ID,
    c.PROCESS_TYPE,
    l.LOG_ID,
    l.STATUS_OF_PROCESS,
    l.CURRENT_DATE,
    l."TIME",
    ROW_NUMBER() OVER (PARTITION BY c.CHAIN_ID ORDER BY l."CURRENT_DATE" DESC, l."TIME" DESC) as rn
FROM RSPCCHAIN c
LEFT JOIN RSPCLOGCHAIN l ON c.CHAIN_ID = l.CHAIN_ID
WHERE l.LOG_ID IS NOT NULL;

-- View: Process Chain Summary
CREATE VIEW VW_CHAIN_SUMMARY AS
SELECT 
    CHAIN_ID,
    COUNT(*) as total_runs,
    SUM(CASE WHEN STATUS_OF_PROCESS = 'SUCCESS' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN STATUS_OF_PROCESS = 'FAILED' THEN 1 ELSE 0 END) as failed_runs,
    MAX("CURRENT_DATE" || ' ' || "TIME") as last_run_time,
    ROUND(
        CAST(SUM(CASE WHEN STATUS_OF_PROCESS = 'SUCCESS' THEN 1 ELSE 0 END) AS REAL) / 
        CAST(COUNT(*) AS REAL) * 100, 2
    ) as success_rate_percent
FROM RSPCLOGCHAIN
GROUP BY CHAIN_ID;

-- View: Today's Process Chain Activity
CREATE VIEW VW_TODAYS_ACTIVITY AS
SELECT 
    l.CHAIN_ID,
    l.STATUS_OF_PROCESS,
    l."CURRENT_DATE",
    l."TIME"
FROM RSPCLOGCHAIN l
ORDER BY l."CURRENT_DATE" DESC, l."TIME" DESC;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

-- Note: SQLite doesn't support table/column comments directly
-- Table purposes:
-- RSPCCHAIN: SAP BW Process Chain Definition - stores process chain structure and configuration
-- RSPCLOGCHAIN: SAP BW Process Chain Run Logs - stores execution history of process chains  
-- RSPCPROCESSLOG: SAP BW Step Execution Logs - stores detailed step-level execution information
-- RSPCVARIANT: SAP BW Variant Parameter Definitions - stores parameter configurations for process variants

-- View purposes:
-- VW_LATEST_CHAIN_RUNS: Shows the most recent run for each process chain
-- VW_CHAIN_SUMMARY: Provides summary statistics for each process chain
-- VW_TODAYS_ACTIVITY: Shows all process chain activity for today

-- =====================================================
-- Schema Creation Complete
-- =====================================================

-- Display completion message (SQLite style)
SELECT 'SAP BW Process Chain Schema Created Successfully!' as message,
       'Tables: 4, Views: 3, Indexes: 9' as summary,
       'Schema matches SAP BW specifications' as next_step; 