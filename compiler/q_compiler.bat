@echo off
REM Wrapper to call python stub. Usage: q_compiler <job_dir>
SET PY=%~dp0\..\..\Scripts\python.exe
REM Try to find Python from the running environment, else fallback to system python
if exist "%PY%" (
  "%PY%" "%~dp0q_compiler_stub.py" %1 %2 %3 %4 %5
) else (
  python "%~dp0q_compiler_stub.py" %1 %2 %3 %4 %5
)
