@echo off
REM dBank Data Layer Setup Script for Windows
setlocal EnableDelayedExpansion

echo ==========================================
echo 🏦 dBank Data Layer Setup
echo ==========================================
echo.

REM Check Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)
echo ✅ Docker found

REM Check Docker Compose
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not installed.
    exit /b 1
)
echo ✅ Docker Compose found

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed. Please install Python 3.9+ first.
    exit /b 1
)
echo ✅ Python found

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found.
    if exist .env.example (
        copy .env.example .env
        echo ✅ .env file created from template
    ) else (
        echo ❌ .env.example not found
        exit /b 1
    )
)

REM Step 1: Start PostgreSQL
echo.
echo ▶ Step 1: Starting PostgreSQL database...
docker-compose up -d

echo Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

docker exec dbank_postgres pg_isready -U dbank_user -d dbank >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ PostgreSQL is running
) else (
    echo ❌ PostgreSQL failed to start
    exit /b 1
)

REM Step 2: Create database schema
echo.
echo ▶ Step 2: Creating database schema...
if exist data_layer\sql\01_create_schema.sql (
    docker exec -i dbank_postgres psql -U dbank_user -d dbank < data_layer\sql\01_create_schema.sql >nul 2>nul
    echo ✅ Database schema created
) else (
    echo ❌ Schema file not found
    exit /b 1
)

REM Step 3: Set up Python environment
echo.
echo ▶ Step 3: Setting up Python environment...
if not exist venv (
    python3.11 -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ⚠️  Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
if exist requirements.txt (
    echo Installing Python dependencies...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ❌ requirements.txt not found
    exit /b 1
)

REM Step 4: Generate sample data
echo.
echo ▶ Step 4: Generating sample data...
if exist data_layer\scripts\generate_sample_data.py (
    cd data_layer\scripts
    python generate_sample_data.py
    cd ..\..
    echo ✅ Sample data generated
) else (
    echo ❌ Data generator script not found
    exit /b 1
)

REM Step 5: Load data into PostgreSQL
echo.
echo ▶ Step 5: Loading data into PostgreSQL...
if exist data_layer\scripts\load_data_to_postgres.py (
    cd data_layer\scripts
    python load_data_to_postgres.py
    cd ..\..
    echo ✅ Data loaded successfully
) else (
    echo ❌ Data loader script not found
    exit /b 1
)

REM Step 6: Verify data
echo.
echo ▶ Step 6: Verifying data...
if exist data_layer\scripts\verify_data.py (
    cd data_layer\scripts
    python verify_data.py
    cd ..\..
) else (
    echo ⚠️  Verification script not found, skipping
)

echo.
echo ==========================================
echo 🎉 Setup Complete!
echo ==========================================
echo.
echo 📊 Database Info:
echo    Host: localhost
echo    Port: 5432
echo    Database: dbank
echo    User: dbank_user
echo    Password: dbank_pass_2025
echo.
echo 🔗 Connect:
echo    docker exec -it dbank_postgres psql -U dbank_user -d dbank
echo.
echo 🚀 Next Steps:
echo    1. Set up dbt transformations
echo    2. Create knowledge base documents
echo    3. Build vector store
echo    4. Implement MCP server
echo    5. Create FastAPI RAG system
echo.
echo 💡 To stop: docker-compose stop
echo 💡 To restart: docker-compose start
echo.

pause