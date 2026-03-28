@echo off
echo ===================================================
echo telephonIA — Build complet Windows
echo ===================================================

echo.
echo [1/3] Build frontend React...
cd frontend
call npm install
call npm run build
cd ..

echo.
echo [2/3] Copie static vers web/static...
if not exist src\telephonia\web\static mkdir src\telephonia\web\static
xcopy /E /Y /I frontend\dist\* src\telephonia\web\static\

echo.
echo [3/3] Build PyInstaller...
poetry run python scripts/build_bundle.py

echo.
echo ===================================================
echo Done. Fichier : dist\telephonIA.exe
echo ===================================================
pause
