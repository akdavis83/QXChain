@echo off
echo Installing QXChain Dependencies...
echo =====================================

echo Installing core packages...
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install websockets==12.0
pip install requests==2.31.0
pip install pydantic==2.5.0

echo Installing cryptography packages...
pip install cryptography==41.0.7
pip install ecdsa==0.18.0
pip install base58==2.1.1

echo Installing scientific packages...
pip install numpy==1.24.3
pip install scipy==1.11.4

echo Installing networking packages...
pip install aiohttp==3.9.1
pip install aiosqlite==0.19.0
pip install python-multipart==0.0.6

echo Installing utility packages...
pip install jinja2==3.1.2
pip install structlog==23.2.0
pip install rich==13.7.0

echo.
echo =====================================
echo Installation complete!
echo.
echo To start QXChain:
echo   python node.py --api-port 8000
echo.
echo To test installation:
echo   python -c "import fastapi, uvicorn; print('QXChain ready!')"
echo.
pause