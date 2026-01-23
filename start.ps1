Write-Host "正在启动服务..." -ForegroundColor Green
docker-compose up -d
Write-Host "服务已启动" -ForegroundColor Green
Write-Host "前端: http://localhost" -ForegroundColor Cyan
Write-Host "后端: http://localhost:8080/docs" -ForegroundColor Cyan
