@echo off
:: EarnNexus Automated Validation Control Deck for Windows 10 Pro
:: Visual Aesthetic: Deep Matte Black Background (0) with Crisp Gold Output Text (6)
color 06
title EarnNexus Core Engine Validator

echo ========================================================================
echo [START] Launching Complete System Verification Core (Windows 10 Pro)
echo ========================================================================

:: Phase 1: Native Environment Path Integrities
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [CRITICAL ERROR] Python 3 execution engine not found on current PATH.
    echo Please resolve system configuration settings or install Python 3.10+.
    pause
    exit /b 1
)

:: Phase 2: Runtime Sandbox Containerization Setup
cd /d "%~dp0\.."
if not exist "venv" (
    echo [ENVIRONMENT] Provisioning lightweight local virtual isolation workspace...
    python -m venv venv
)

echo [ENVIRONMENT] Activating network runtime shell links...
call venv\Scripts\activate

echo [DEPENDENCY] Confirming system driver configurations...
python -m pip install --upgrade pip --quiet
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
) else (
    pip install psycopg2-binary==2.9.9 --quiet
)

:: Phase 3: Execute Diagnostic Matrix
echo [VALIDATION] Initializing live transaction testing runner script...
python scripts/verify_live_api.py

echo ========================================================================
echo [COMPLETE] System validation sequence exited cleanly.
echo ========================================================================
pause
