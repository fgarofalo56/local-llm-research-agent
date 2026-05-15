@echo off
REM =============================================================================
REM check-ports.bat
REM Pre-flight port conflict detection for Local LLM Research Agent (Windows)
REM
REM Checks all configured host ports against:
REM   1. Running Docker containers (via docker ps --filter publish=PORT)
REM   2. Host processes listening on those ports (via netstat)
REM
REM Usage:
REM   docker\check-ports.bat          - Check with defaults / .env values
REM   docker\check-ports.bat --fix    - Auto-suggest and write free ports to .env
REM =============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "ENV_FILE=%PROJECT_ROOT%\.env"
set "FIX_MODE=false"
set "HAS_CONFLICTS=false"
set "FIX_COUNT=0"

if "%~1"=="--fix" set "FIX_MODE=true"

REM ---------------------------------------------------------------------------
REM Load .env variables (skip comment lines, strip inline comments, trim)
REM ---------------------------------------------------------------------------
if exist "%ENV_FILE%" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
        if not "%%a"=="" if not "%%b"=="" (
            set "_key=%%a"
            set "_rawval=%%b"
            REM Strip inline comments: keep only text before first #
            for /f "tokens=1 delims=#" %%v in ("!_rawval!") do set "_rawval=%%v"
            REM Trim trailing whitespace by extracting first token
            for /f "tokens=1" %%t in ("!_rawval!") do set "_cleanval=%%t"
            REM Trim leading whitespace from key
            for /f "tokens=1" %%k in ("!_key!") do set "_key=%%k"
            REM Only set if not already defined
            if not defined !_key! set "!_key!=!_cleanval!"
        )
    )
)

REM ---------------------------------------------------------------------------
REM Default port values (used if not in .env)
REM ---------------------------------------------------------------------------
if not defined MSSQL_PORT set "MSSQL_PORT=1433"
if not defined BACKEND_DB_PORT set "BACKEND_DB_PORT=1434"
if not defined API_PORT set "API_PORT=8000"
if not defined STREAMLIT_PORT set "STREAMLIT_PORT=8501"
if not defined FRONTEND_PORT set "FRONTEND_PORT=5173"
if not defined REDIS_PORT set "REDIS_PORT=6379"
if not defined REDIS_INSIGHT_PORT set "REDIS_INSIGHT_PORT=8001"
if not defined SUPERSET_PORT set "SUPERSET_PORT=8088"

echo.
echo ============================================================
echo   Port Conflict Check - Local LLM Research Agent
echo ============================================================
echo.

if exist "%ENV_FILE%" (
    echo   Using .env: %ENV_FILE%
) else (
    echo   No .env found, using defaults from docker-compose.yml
)
echo.

echo   SERVICE                PORT   STATUS     DETAILS
echo   ---------------------- ------ ---------- ----------------------------

REM ---------------------------------------------------------------------------
REM Check each port (description is pre-padded with spaces to align columns)
REM ---------------------------------------------------------------------------

call :check_port "SQL Server 2022       " !MSSQL_PORT!         MSSQL_PORT
call :check_port "SQL Server 2025       " !BACKEND_DB_PORT!    BACKEND_DB_PORT
call :check_port "FastAPI Backend       " !API_PORT!           API_PORT
call :check_port "Streamlit UI          " !STREAMLIT_PORT!     STREAMLIT_PORT
call :check_port "React Frontend        " !FRONTEND_PORT!      FRONTEND_PORT
call :check_port "Redis Stack           " !REDIS_PORT!         REDIS_PORT
call :check_port "RedisInsight GUI      " !REDIS_INSIGHT_PORT! REDIS_INSIGHT_PORT
call :check_port "Apache Superset       " !SUPERSET_PORT!      SUPERSET_PORT

echo.

REM ---------------------------------------------------------------------------
REM Apply fixes or show guidance
REM ---------------------------------------------------------------------------
if "!FIX_MODE!"=="true" if !FIX_COUNT! GTR 0 (
    echo ------------------------------------------------------------
    echo   Applying port fixes to .env...
    echo ------------------------------------------------------------

    if not exist "!ENV_FILE!" (
        if exist "!PROJECT_ROOT!\.env.example" (
            copy "!PROJECT_ROOT!\.env.example" "!ENV_FILE!" >nul
            echo   Created .env from .env.example
        ) else (
            echo. > "!ENV_FILE!"
            echo   Created empty .env
        )
    )

    for /L %%i in (1,1,!FIX_COUNT!) do (
        set "fix_var=!FIX_VAR_%%i!"
        set "fix_val=!FIX_VAL_%%i!"
        set "fix_old=!FIX_OLD_%%i!"
        set "fix_who=!FIX_WHO_%%i!"

        REM Check if variable exists in .env already
        findstr /b /c:"!fix_var!=" "!ENV_FILE!" >nul 2>&1
        if !errorlevel! equ 0 (
            REM Replace existing line using PowerShell for reliability
            powershell -NoProfile -Command "$f='!ENV_FILE!'; $k='!fix_var!'; $v='!fix_val!'; $o='!fix_old!'; $w='!fix_who!'; (Get-Content $f) -replace \"^$k=.*\", \"$k=$v  # was $o, conflict: $w\" | Set-Content $f"
            echo   Updated: !fix_var!=!fix_val!
        ) else (
            REM Append new line - no parentheses in comment
            echo !fix_var!=!fix_val!  # was !fix_old!, conflict: !fix_who!>> "!ENV_FILE!"
            echo   Added:   !fix_var!=!fix_val!
        )
    )

    echo.
    echo   .env updated. You can now start containers without conflicts.
    echo.
    goto :end
)

if "!HAS_CONFLICTS!"=="true" (
    echo ------------------------------------------------------------
    echo   CONFLICTS DETECTED!
    echo ------------------------------------------------------------
    echo.
    echo   Options to resolve:
    echo.
    echo   1. Auto-fix: Run with --fix flag to auto-assign free ports:
    echo        docker\check-ports.bat --fix
    echo.
    echo   2. Manual: Edit .env and change the conflicting port variables:
    echo        Example: API_PORT=8200
    echo.
    echo   3. Stop conflicting containers first:
    echo        docker stop [container-name]
    echo.
    exit /b 1
) else (
    echo   All ports are available. Safe to start containers.
    echo.
)

goto :end

REM ===========================================================================
REM Subroutine: check_port "description" port var_name
REM Uses: docker ps --filter publish=PORT  (simple, no port string parsing)
REM ===========================================================================
:check_port
set "svc_desc=%~1"
set "svc_port=%~2"
set "svc_var=%~3"
set "conflict_name="

REM Use Docker's built-in port filter to find containers publishing this port
REM Exclude our own containers (local-agent-*) from conflict detection
for /f "tokens=*" %%c in ('docker ps --filter "publish=!svc_port!" --format "{{.Names}}" 2^>nul') do (
    set "_cname=%%c"
    REM Check if this is NOT our own container
    set "_is_own=false"
    echo !_cname! | findstr /b /c:"local-agent-" >nul 2>&1
    if !errorlevel! equ 0 set "_is_own=true"
    if "!_is_own!"=="false" set "conflict_name=!_cname!"
)

if not "!conflict_name!"=="" (
    set "HAS_CONFLICTS=true"
    echo   !svc_desc! !svc_port!   CONFLICT   Container: !conflict_name!

    if "!FIX_MODE!"=="true" (
        call :find_free_port !svc_port!
        if not "!_free_port!"=="" (
            set /a FIX_COUNT+=1
            set "FIX_VAR_!FIX_COUNT!=!svc_var!"
            set "FIX_VAL_!FIX_COUNT!=!_free_port!"
            set "FIX_OLD_!FIX_COUNT!=!svc_port!"
            set "FIX_WHO_!FIX_COUNT!=!conflict_name!"
            echo                            -^> FIX    Will use port !_free_port!
        )
    )
    goto :eof
)

REM Check host port via netstat (LISTENING on this exact port)
netstat -ano 2>nul | findstr /c:"LISTENING" | findstr /c:":!svc_port! " >nul 2>&1
if !errorlevel! equ 0 (
    REM Netstat found the port, but check if it's our own Docker container
    REM (Docker maps ports to host, so netstat sees them as LISTENING)
    set "_is_own_port=false"
    for /f "tokens=*" %%o in ('docker ps --filter "publish=!svc_port!" --format "{{.Names}}" 2^>nul') do (
        echo %%o | findstr /b /c:"local-agent-" >nul 2>&1
        if !errorlevel! equ 0 set "_is_own_port=true"
    )
    if "!_is_own_port!"=="true" (
        echo   !svc_desc! !svc_port!   OK         own container
        goto :eof
    )
    set "HAS_CONFLICTS=true"
    echo   !svc_desc! !svc_port!   CONFLICT   Host process using port

    if "!FIX_MODE!"=="true" (
        call :find_free_port !svc_port!
        if not "!_free_port!"=="" (
            set /a FIX_COUNT+=1
            set "FIX_VAR_!FIX_COUNT!=!svc_var!"
            set "FIX_VAL_!FIX_COUNT!=!_free_port!"
            set "FIX_OLD_!FIX_COUNT!=!svc_port!"
            set "FIX_WHO_!FIX_COUNT!=host-process"
            echo                            -^> FIX    Will use port !_free_port!
        )
    )
    goto :eof
)

echo   !svc_desc! !svc_port!   OK
goto :eof

REM ===========================================================================
REM Subroutine: find_free_port start_port
REM Sets !_free_port! to the next available port, empty if none found
REM ===========================================================================
:find_free_port
set "_free_port="
set "_fp_port=%~1"
set /a "_fp_max=%~1 + 100"

:_fp_loop
set /a _fp_port+=1
if !_fp_port! GTR !_fp_max! (
    set "_free_port="
    goto :eof
)

set "_fp_in_use=false"

REM Check if any Docker container publishes this port
for /f "tokens=*" %%c in ('docker ps --filter "publish=!_fp_port!" --format "{{.Names}}" 2^>nul') do (
    set "_fp_in_use=true"
)

REM Check if host process is using this port
if "!_fp_in_use!"=="false" (
    netstat -ano 2>nul | findstr /c:"LISTENING" | findstr /c:":!_fp_port! " >nul 2>&1
    if !errorlevel! equ 0 set "_fp_in_use=true"
)

if "!_fp_in_use!"=="false" (
    set "_free_port=!_fp_port!"
    goto :eof
)

goto :_fp_loop

:end
endlocal
exit /b 0
