@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
cls

:MENU
cls
echo =====================================================================
echo    OBITUARIUM - PORTAL DE NOTAS DE PESAR E MEMORIA PUBLICA
echo =====================================================================
echo.
echo Escolha a opcao desejada:
echo.
echo [1] Abrir Portal Web no Navegador (index.html)
echo [2] Minerar Novas Notas de Pesar e Atualizar CSV (Fontes Oficiais)
echo [3] Testar Mineracao em Modo Seguro (--dry-run)
echo [4] Instalar / Reparar Dependencias Python (Multi-Maquinas)
echo [5] Sair
echo.
echo =====================================================================
set /p opcao="Digite a opcao desejada [1-5]: "

if "%opcao%"=="1" goto OPCAO_1
if "%opcao%"=="2" goto OPCAO_2
if "%opcao%"=="3" goto OPCAO_3
if "%opcao%"=="4" goto OPCAO_4
if "%opcao%"=="5" goto SAIR
goto MENU

:OPCAO_1
cls
echo Abrindo o portal Obituarium no navegador padrao...
start "" "%~dp0index.html"
goto MENU

:OPCAO_2
cls
echo [1/2] Minerando notas de pesar e alimentando a base CSV cronologica...
echo.
python "%~dp0auto_minerador_obituario.py"
echo.
echo [OK] Base CSV do mes corrente atualizada.
pause
goto MENU

:OPCAO_3
cls
echo Executando mineracao em modo de teste (--dry-run)...
echo.
python "%~dp0auto_minerador_obituario.py" --dry-run
echo.
pause
goto MENU

:OPCAO_4
cls
echo =====================================================================
echo    INSTALANDO / REPARANDO DEPENDENCIAS PYTHON (MULTI-MAQUINAS)
echo =====================================================================
echo.
python -m pip install -r "%~dp0requirements.txt"
echo.
echo [OK] Dependencias verificadas e instaladas com sucesso.
pause
goto MENU

:SAIR
exit /b 0
