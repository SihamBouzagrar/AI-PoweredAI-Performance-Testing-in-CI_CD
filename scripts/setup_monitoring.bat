@echo off
REM Script de demarrage de l infrastructure de monitoring
REM Usage: scripts\setup_monitoring.bat

echo ========================================
echo    AI Performance Testing - Monitoring
echo ========================================
echo.
echo Demarrage de Prometheus + Grafana + Serveur IA
echo.

REM Verifier que Docker est installe
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Docker n'est pas installe.
    echo Veuillez installer Docker Desktop depuis https://www.docker.com/products/docker-desktop/
    exit /b 1
)

REM Verifier le fichier .env
if not exist .env (
    echo Creation du fichier .env depuis .env.example...
    copy .env.example .env
    echo.
    echo ATTENTION: Veuillez editer le fichier .env et ajouter votre cle GROQ_API_KEY
    echo.
)

REM Demarrer les services
echo Demarrage des conteneurs Docker...
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    Services demarres avec succes !
    echo ========================================
    echo.
    echo Serveur IA     : http://localhost:8000
    echo Prometheus     : http://localhost:9090
    echo Grafana        : http://localhost:3000
    echo.
    echo Pour voir les logs :
    echo   docker-compose logs -f
    echo.
    echo Pour arreter :
    echo   docker-compose down
) else (
    echo ERREUR lors du demarrage des services.
    echo Verifiez les logs avec : docker-compose logs
)

pause
