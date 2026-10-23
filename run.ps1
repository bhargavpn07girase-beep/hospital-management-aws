Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting Hospital Management System (Healthcare AWS)      " -ForegroundColor Cyan
Write-Host "  Local Web Interface: http://localhost:5000               " -ForegroundColor Green
Write-Host "  Default Admin: username: admin | password: admin123       " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" app.py
} else {
    python app.py
}
