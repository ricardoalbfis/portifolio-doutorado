@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set RASCUNHOS=C:\Users\Ricardo\Documents\GitHub\rascunhos-portifolio

echo ============================================
echo   Publicar notebook/arquivo no portfolio
echo ============================================
echo.
echo Arquivos disponiveis em %RASCUNHOS%:
echo.
dir /b "%RASCUNHOS%" 2>nul
echo.
set /p ARQUIVO="Nome do arquivo a publicar (com extensao, ex: meu_notebook.ipynb): "

if not exist "%RASCUNHOS%\%ARQUIVO%" (
    echo.
    echo Arquivo nao encontrado em %RASCUNHOS%.
    pause
    exit /b 1
)

echo.
echo Para onde vai?
echo   1. Relatividade Geral / Capitulo 1  ( notebooks )
echo   2. Relatividade Geral / Capitulo 2  ( notebooks )
echo   3. Relatividade Geral / Capitulo 3  ( notebooks )
echo   4. Relatividade Geral / Exercicios resolvidos ( PDF )
echo   5. Cosmologia / notebooks
echo   6. Outro caminho (informar manualmente)
set /p OPCAO="Escolha (1-6): "

if "%OPCAO%"=="1" set DEST=relatividade-geral\notebooks\capitulo-01
if "%OPCAO%"=="2" set DEST=relatividade-geral\notebooks\capitulo-02
if "%OPCAO%"=="3" set DEST=relatividade-geral\notebooks\capitulo-03
if "%OPCAO%"=="4" set DEST=relatividade-geral\exercicios-resolvidos
if "%OPCAO%"=="5" set DEST=cosmologia\notebooks
if "%OPCAO%"=="6" set /p DEST="Caminho dentro do repositorio (ex: relatividade-geral\notebooks\capitulo-03): "

if not defined DEST (
    echo Opcao invalida.
    pause
    exit /b 1
)

if not exist "%DEST%" mkdir "%DEST%"

copy /Y "%RASCUNHOS%\%ARQUIVO%" "%DEST%\%ARQUIVO%" >nul

echo.
echo Copiado para %DEST%\%ARQUIVO%
echo O arquivo original em rascunhos-portifolio NAO foi alterado.
echo.
echo Publicando no GitHub...
echo.

git add -A
git commit -m "Publica %ARQUIVO% em %DEST%"
git push

echo.
echo ============================================
echo Feito. O site atualiza em 1-2 minutos.
echo Se este e um item novo, avise para eu adicionar
echo o card correspondente na pagina (index.html).
echo ============================================
pause
