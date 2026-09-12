@echo off
setlocal enabledelayedexpansion
set RASCUNHOS=C:\Users\Ricardo\Documents\GitHub\rascunhos-portifolio
set /p ARQUIVO="Nome: "
echo Voce digitou: [%ARQUIVO%]
if exist "%RASCUNHOS%\%ARQUIVO%" echo EXISTE
if not exist "%RASCUNHOS%\%ARQUIVO%" echo NAO EXISTE
