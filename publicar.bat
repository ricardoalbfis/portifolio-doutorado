@echo off
cd /d "%~dp0"

echo Verificando alteracoes...
git add -A

git diff --cached --quiet
if %errorlevel%==0 (
    echo Nada novo para publicar.
    pause
    exit /b 0
)

for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATA=%%a-%%b-%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set HORA=%%a-%%b

git commit -m "Atualiza portfolio (%DATA% %HORA%)"
git push

echo.
echo Publicado. O site atualiza em 1-2 minutos em:
echo https://ricardoalbfis.github.io/portifolio-doutorado/
pause
