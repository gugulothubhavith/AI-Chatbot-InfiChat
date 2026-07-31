@echo off
TITLE InfiChat Test Runner
cd /d "%~dp0.."

echo ==================================================
echo      InfiChat - Test Runner
echo ==================================================
echo.
echo  Setting up test environment...
set ENVIRONMENT=test
set DATABASE_URL=sqlite:///./test_infichat.db
set SECRET_KEY=test-secret-key
set ALLOWED_ORIGINS=http://testserver

echo  Installing test dependencies...
pip install pytest httpx pytest-asyncio pytest-cov 2>nul

echo.
echo  Running tests...
python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing 2>&1

echo.
echo  Cleaning up...
del /f test_infichat.db test_infichat.db-wal test_infichat.db-shm 2>nul

echo.
echo  Done.
pause
