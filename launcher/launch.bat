@echo off
setlocal
set "ROOT=%~dp0.."

echo 正在启动新能源汽车LCC估算系统...

REM 优先使用交付目录内的 Python 3.11 虚拟环境
if exist "%ROOT%\.venv311\Scripts\python.exe" (
  "%ROOT%\.venv311\Scripts\python.exe" "%ROOT%\src\main.py"
  goto :eof
)

REM 其次尝试运行交付目录中的可执行文件
if exist "%ROOT%\main.exe" (
  "%ROOT%\main.exe"
  goto :eof
)

REM 最后再尝试系统 Python
for /f %%P in ('where python 2^>NUL ^| findstr /R "python.exe"') do set "PY=%%P"
if defined PY (
  echo 未检测到本地交付环境，正在尝试系统 Python：%PY%
  "%PY%" "%ROOT%\src\main.py"
  goto :eof
)

echo 启动失败：未找到可用的 Python 运行环境。
echo 建议直接使用交付目录内的 .venv311 环境，或补充 main.exe 后再交付。
pause
