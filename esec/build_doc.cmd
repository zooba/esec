@echo off
set DOTPATH=none
if exist "%ProgramFiles%\Graphviz2.26.3\bin\dot.exe" set DOTPATH=%ProgramFiles%\Graphviz2.26.3\bin\dot.exe
if exist "%ProgramFiles(x86)%\Graphviz2.26.3\bin\dot.exe" set DOTPATH=%ProgramFiles(x86)%\Graphviz2.26.3\bin\dot.exe

if "%DOTPATH%"=="none" (
    epydoc -v --no-frames --docformat="restructuredtext" --include-log esec esdlc %*
) else (
    epydoc -v --no-frames --docformat="restructuredtext" --include-log --dotpath="%DOTPATH%" --graph-font="sans" esec esdlc %*
)
