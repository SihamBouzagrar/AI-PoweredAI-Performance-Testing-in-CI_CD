@echo off
REM Script de test complet : generation JMX + execution JMeter
REM Usage: scripts\start_test.bat chemin\vers\openapi.yaml [threads] [rampup] [loops]

echo ========================================
echo    AI Performance Test - Execution
echo ========================================
echo.

REM Verification des parametres
if "%1"=="" (
    echo Usage: %~nx0 ^<fichier_openapi^> [threads] [rampup] [loops]
    echo.
    echo Exemple: %~nx0 mon_api.yaml 50 10 5
    exit /b 1
)

set OPENAPI_FILE=%1
set THREADS=%2
set RAMPUP=%3
set LOOPS=%4

REM Verifier que le fichier OpenAPI existe
if not exist "%OPENAPI_FILE%" (
    echo ERREUR: Fichier OpenAPI introuvable: %OPENAPI_FILE%
    exit /b 1
)

REM Verifier que le serveur IA tourne
echo [1/4] Verification du serveur IA...
curl -s http://localhost:8000/health >nul
if %errorlevel% neq 0 (
    echo ERREUR: Le serveur IA n'est pas accessible sur http://localhost:8000
    echo Demarrez le serveur avec : uvicorn app:app --host 0.0.0.0 --port 8000
    exit /b 1
)
echo OK - Serveur IA accessible

REM Envoyer la spec OpenAPI au serveur IA
echo [2/4] Envoi de la spec OpenAPI au generateur IA...
set CURL_CMD=curl -s -X POST -F "file=@%OPENAPI_FILE%"
if not "%THREADS%"=="" set CURL_CMD=%CURL_CMD% -F "threads=%THREADS%"
if not "%RAMPUP%"=="" set CURL_CMD=%CURL_CMD% -F "rampUp=%RAMPUP%"
if not "%LOOPS%"=="" set CURL_CMD=%CURL_CMD% -F "loops=%LOOPS%"
%CURL_CMD% http://localhost:8000/generateScenario

echo.
echo [3/4] Surveillance du job...
echo Verifiez le statut avec : curl http://localhost:8000/status/JOB_ID

echo.
echo [4/4] Pour telecharger les resultats :
echo   curl -o results.jtl http://localhost:8000/download/JOB_ID/jtl
echo   curl -o report.zip http://localhost:8000/download/JOB_ID/report
echo   curl -o jmeter.log http://localhost:8000/download/JOB_ID/log

echo.
echo ========================================
echo    Test lance avec succes !
echo ========================================
