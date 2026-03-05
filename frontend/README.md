<div align="center">
  <h1>前端</h1>
</div>

## 当前已实现的前端页面

- 图片检测页面：上传图片并消费后端 JSON 结果，在前端叠加绘制预测框（使用 `POST /api/detect`）
- 视频检测页面：播放视频时前端抽帧上传，消费后端 JSON 结果并叠加绘制预测框（使用 `POST /api/detect/frame`）
- 摄像头实时检测页面：使用浏览器摄像头，通过 WebSocket 与后端 `/api/detect/camera` 通信，实时消费 JSON 结果并绘制预测框

这些页面位于 `frontend/src/pages/`，对应文件为 `image-detect`, `video-detect`, `camera-detect`。

## 如何运行（最简步骤）

要求：Node.js（建议 20+），`pnpm`。

```bash
cd frontend
pnpm i
# 如需指定后端地址，可在 .env 中设置 `VITE_BASE_URL`（例如： http://localhost:8080）
pnpm dev
```

打开浏览器访问前端开发地址 `http://localhost:80`，并确保后端已运行。

## 说明

- 前端默认通过 `VITE_BASE_URL` 与后端通信，请根据实际后端地址调整。
