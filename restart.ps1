Write-Host "正在重启服务..." -ForegroundColor Cyan
docker-compose restart
Write-Host "服务已重启" -ForegroundColor Cyan
Write-Host "前端: http://localhost" -ForegroundColor Cyan
Write-Host "后端: http://localhost:8080/docs" -ForegroundColor Cyan
