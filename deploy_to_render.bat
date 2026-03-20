@echo off
echo ========================================
echo    DEPLOY TO RENDER
echo ========================================
echo.
echo Step 1: Creating necessary files...
echo python-3.9.18 > runtime.txt
echo.
echo Step 2: Committing to GitHub...
git add .
git commit -m "Deploy to Render"
git push
echo.
echo ========================================
echo Files pushed to GitHub!
echo.
echo Next steps:
echo 1. Go to https://render.com
echo 2. Click "New +" -> "Web Service"
echo 3. Connect your GitHub repo
echo 4. Use these settings:
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: gunicorn run:app
echo 5. Add environment variables listed above
echo 6. Click "Create Web Service"
echo.
pause