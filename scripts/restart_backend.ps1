# Stop existing uvicorn processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2

# Start uvicorn in background
Set-Location "E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent"
Start-Process -NoNewWindow -FilePath "uv" -ArgumentList "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"

Write-Host "Backend restart initiated"
