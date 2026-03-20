@echo off
title Deploy to Vercel - Paulo E-Store
color 0A

echo ========================================
echo    DEPLOYING TO VERCEL
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed!
    echo Please install Node.js from https://nodejs.org
    echo After installing, restart this script.
    pause
    exit /b
)

REM Check if Vercel CLI is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing Vercel CLI...
    npm i -g vercel
)

REM Check if logged in
echo Checking Vercel login status...
vercel whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo Please login to Vercel...
    echo A browser window will open for authentication.
    vercel login
    if %errorlevel% neq 0 (
        echo ❌ Login failed. Please try again.
        pause
        exit /b
    )
)

echo.
echo Step 1: Creating necessary folders...
if not exist "api" mkdir api
if not exist "static\images" mkdir static\images
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
if not exist "templates\errors" mkdir templates\errors
if not exist "templates\admin" mkdir templates\admin

echo.
echo Step 2: Checking files...
if not exist "api\index.py" (
    echo ❌ api\index.py is missing!
    pause
    exit /b
)
if not exist "vercel.json" (
    echo ❌ vercel.json is missing!
    pause
    exit /b
)
if not exist "requirements.txt" (
    echo ❌ requirements.txt is missing!
    pause
    exit /b
)

echo ✅ All required files present.

echo.
echo ========================================
echo IMPORTANT: Environment Variables Needed
echo ========================================
echo.
echo You will need to set these environment variables:
echo.
echo 1. SECRET_KEY (generate a random string)
echo 2. DATABASE_URL: postgresql://postgres:mFxwM5qnfYFABSD9@db.jhnpanznxoanclyrzvqx.supabase.co:5432/postgres
echo 3. CLOUDINARY_CLOUD_NAME: dapuaw0u6
echo 4. CLOUDINARY_API_KEY: 738952696443951
echo 5. CLOUDINARY_API_SECRET: CzRSL1UUAnGoOI1xnrc1NwlMIiU
echo 6. ADMIN_USERNAME: admin
echo 7. ADMIN_PASSWORD: Admin123!
echo 8. ADMIN_EMAIL: admin@paulo-store.com
echo 9. WHATSAPP_NUMBER: 2347088028747
echo.
echo Press any key to continue with deployment...
pause > nul

echo.
echo Step 3: Deploying to Vercel...
echo.
vercel --prod

if %errorlevel% neq 0 (
    echo.
    echo ❌ Deployment failed! Check the error above.
    echo.
    echo Possible solutions:
    echo 1. Make sure you're logged in: vercel login
    echo 2. Check your internet connection
    echo 3. Verify all environment variables are set correctly
    pause
    exit /b
)

echo.
echo ========================================
echo ✅ DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Your site is now live at:
echo https://paulo-ecommerce.vercel.app
echo.
echo Admin Login:
echo https://paulo-ecommerce.vercel.app/admin/login
echo Username: admin
echo Password: Newpassword123
echo.
echo To view deployment logs, visit:
echo https://vercel.com/your-username/paulo-ecommerce
echo.
pause