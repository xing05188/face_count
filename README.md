<div align="center">
  <h1>FaceCount</h1>
</div>

本仓库包含前端与后端两部分。本次文档仅列出当前代码中已实现并可运行的功能，以及最小运行步骤。

## 当前已实现的功能

- 后端（见 `backend`）：
  - 健康检查：`GET /`
  - 简单测试：`GET /api/hello`
  - 图片人脸检测（JSON）：`POST /api/detect`
  - 视频抽帧检测（JSON）：`POST /api/detect/frame`
  - 摄像头实时检测（WebSocket）：`/api/detect/camera`

- 前端（见 `frontend`）：
  - 图片检测页面（上传图片，前端绘制预测框）
  - 视频检测页面（前端抽帧上传，返回 JSON 后实时绘制预测框）
  - 摄像头实时检测页面（通过浏览器摄像头向后端 WebSocket 发送帧并显示结果）

## 如何运行（最简步骤）

1) 启动后端：

```powershell
cd backend
start.bat
```

2) 启动前端（在另一个终端）：

```bash
cd frontend
pnpm dev
```

3) 打开浏览器：

- 前端页面： http://localhost:80
- 后端 Swagger： http://localhost:8080/docs

## 说明

- 前端默认通过 `VITE_BASE_URL` 与后端通信，请根据实际后端地址调整。
- 后端依赖模型文件（见 `backend/app/models/yolo/`），请确保模型存在，且在需要 GPU 加速时配置好 CUDA 与 PyTorch。