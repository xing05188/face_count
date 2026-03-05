<div align="center">
  <h1>后端</h1>
</div>

## 当前已实现的功能

- 健康检查：`GET /`（返回欢迎信息）
- 简单测试：`GET /api/hello`（返回 `{"message": "helloworld"}`）
- 图片人脸检测：`POST /api/detect`，上传图片，返回检测 JSON；响应头 `X-Face-Count` 为检测到的人脸数
- 视频抽帧检测：`POST /api/detect/frame`，上传单帧图片二进制（`image/jpeg`），返回检测 JSON
- 摄像头实时检测（WebSocket）：`ws(s)://<host>/api/detect/camera`，客户端发送 JPEG 帧，服务端返回 JSON 检测结果

（以上接口由 `app.services.detection_service.FaceDetectionService` 使用 YOLO 实现）

## 如何运行（最简步骤）

要求：Python 3.10+。请确认 `backend/app/models/yolo/yolov6m-face.pt` 或等效模型文件存在。

在 `backend` 目录下：

```powershell
# 创建并激活虚拟环境
# 安装依赖
pip install -r requirements.txt
# 启动服务（开发）
start.bat
```

访问：

- 根接口： http://localhost:8080/
- Swagger 文档： http://localhost:8080/docs

## 注意

- 若需 GPU 加速，请确保系统已安装对应 CUDA 与 cuDNN，且 PyTorch 支持 GPU。
- 本文档仅列出代码中可直接调用的接口与最简运行方法，未列出的功能并未在当前代码中发现或未完全实现。