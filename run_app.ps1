# SAP BW Assistant - Groq Powered Launcher
# This script properly activates the virtual environment and runs the app

Write-Host "🚀 Starting SAP BW Assistant - Groq Powered" -ForegroundColor Green

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Load environment variables from .env file
Write-Host "Loading environment variables from .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            Write-Host "✅ Loaded: $($matches[1])" -ForegroundColor Green
        }
    }
} else {
    Write-Host "⚠️ .env file not found. Please create one with GROQ_API_KEY" -ForegroundColor Yellow
}

# Verify Groq installation
Write-Host "Verifying Groq installation..." -ForegroundColor Yellow
python -c "import groq; print('✅ Groq module found:', groq.__version__)"

# Run the Streamlit app
Write-Host "🚀 Launching Streamlit app..." -ForegroundColor Green
python -m streamlit run app.py 