<script lang="ts" setup>
import { computed, nextTick, onUnmounted, ref } from "vue"

const API_BASE_URL = import.meta.env.VITE_BASE_URL || "/api"

interface StatsData {
  analyzed_frames: number
  current_face_count: number
}

interface DetectionBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

interface DetectionItem {
  name: string
  class: number
  confidence: number
  box: DetectionBox
}

interface DetectionImageResult {
  shape: [number, number]
  face_count: number
  results: DetectionItem[]
}

interface DetectionResponse {
  mode: "compact" | "full"
  images: DetectionImageResult[]
}

const file = ref<File | null>(null)
const originalVideoUrl = ref<string>("")
const stats = ref<StatsData | null>(null)
const loading = ref<boolean>(false)
const error = ref<string>("")
const fileInput = ref<HTMLInputElement | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
const overlayCanvasRef = ref<HTMLCanvasElement | null>(null)
const captureCanvasRef = ref<HTMLCanvasElement | null>(null)
const currentFrameIndex = ref<number>(0)
const currentFaceCount = ref<number>(0)
const isDetecting = ref<boolean>(false)
const connected = ref<boolean>(false)
const selectedFps = ref<number>(12)
const fpsOptions = [8, 10, 12, 15]

let detectTimer: number | null = null
let sending = false
let awaitingResult = false
let ws: WebSocket | null = null
let analyzedFrames = 0
let lastCapturedVideoTime = 0
const VIDEO_SEND_MAX_WIDTH = 640
const VIDEO_SEND_JPEG_QUALITY = 0.65
const MAX_RESULT_LAG_SEC = 0.6

const canStart = computed(() => !loading.value && !!file.value && !isDetecting.value)
const canStop = computed(() => isDetecting.value)

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    if (originalVideoUrl.value) {
      URL.revokeObjectURL(originalVideoUrl.value)
    }
    file.value = target.files[0]
    originalVideoUrl.value = URL.createObjectURL(file.value)
    reset()
  }
}

function clearOverlay() {
  const canvas = overlayCanvasRef.value
  const ctx = canvas?.getContext("2d")
  if (canvas && ctx) {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}

function stopLoop() {
  if (detectTimer !== null) {
    window.clearInterval(detectTimer)
    detectTimer = null
  }
  sending = false
  awaitingResult = false
}

function stopWebSocket() {
  try {
    ws?.close()
  } finally {
    ws = null
    connected.value = false
  }
}

function stopDetection() {
  isDetecting.value = false
  stopLoop()
  stopWebSocket()
}

function updateFps(nextFps: number) {
  selectedFps.value = nextFps
  if (isDetecting.value) {
    startLoop()
  }
}

async function onVideoLoaded() {
  const video = videoRef.value
  if (!video) return
  const overlay = overlayCanvasRef.value
  if (!overlay) return

  overlay.width = video.videoWidth || 0
  overlay.height = video.videoHeight || 0
  await nextTick()
}

function onVideoError(event: Event) {
  const video = event.target as HTMLVideoElement
  error.value = `视频加载失败: ${video.error?.message || "未知错误"}`
  stopDetection()
}

function drawDetections(results: DetectionItem[], shape: [number, number]) {
  const canvas = overlayCanvasRef.value
  const video = videoRef.value
  if (!canvas || !video) return
  const ctx = canvas.getContext("2d")
  if (!ctx) return

  const srcH = shape?.[0] || video.videoHeight || canvas.height
  const srcW = shape?.[1] || video.videoWidth || canvas.width
  const scaleX = srcW > 0 ? canvas.width / srcW : 1
  const scaleY = srcH > 0 ? canvas.height / srcH : 1

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.lineWidth = 2
  ctx.font = "16px sans-serif"

  results.forEach((item) => {
    const x1 = item.box.x1 * scaleX
    const y1 = item.box.y1 * scaleY
    const x2 = item.box.x2 * scaleX
    const y2 = item.box.y2 * scaleY
    const w = Math.max(0, x2 - x1)
    const h = Math.max(0, y2 - y1)
    const label = `${item.name} ${(item.confidence * 100).toFixed(1)}%`

    ctx.strokeStyle = "#ff1744"
    ctx.fillStyle = "rgba(255, 23, 68, 0.18)"
    ctx.strokeRect(x1, y1, w, h)
    ctx.fillRect(x1, y1, w, h)

    const textWidth = ctx.measureText(label).width
    const textY = Math.max(0, y1 - 24)
    ctx.fillStyle = "#ff1744"
    ctx.fillRect(x1, textY, textWidth + 12, 24)
    ctx.fillStyle = "#ffffff"
    ctx.fillText(label, x1 + 6, textY + 17)
  })
}

async function detectCurrentFrame() {
  if (sending || awaitingResult) return
  const video = videoRef.value
  const captureCanvas = captureCanvasRef.value
  if (!video || !captureCanvas || video.readyState < 2 || video.paused || video.ended) return
  if (!ws || ws.readyState !== WebSocket.OPEN) return

  sending = true
  try {
    // 控制上传分辨率，减少带宽与推理时延
    const srcW = video.videoWidth
    const srcH = video.videoHeight
    if (!srcW || !srcH) return

    const maxW = VIDEO_SEND_MAX_WIDTH
    const scale = srcW > maxW ? maxW / srcW : 1
    const sendW = Math.max(1, Math.round(srcW * scale))
    const sendH = Math.max(1, Math.round(srcH * scale))

    captureCanvas.width = sendW
    captureCanvas.height = sendH
    const ctx = captureCanvas.getContext("2d")
    if (!ctx) return
    ctx.drawImage(video, 0, 0, sendW, sendH)

    const capturedVideoTime = video.currentTime
    const frameBlob = await new Promise<Blob | null>((resolve) => {
      captureCanvas.toBlob((blob) => resolve(blob), "image/jpeg", VIDEO_SEND_JPEG_QUALITY)
    })
    if (!frameBlob) return

    lastCapturedVideoTime = capturedVideoTime
    awaitingResult = true
    ws.send(await frameBlob.arrayBuffer())
  } catch (err: any) {
    error.value = err?.message || "检测失败"
  } finally {
    sending = false
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  const host = window.location.host
  const wsUrl = `${protocol}//${host}${API_BASE_URL}/detect/camera?mode=compact`

  const socket = new WebSocket(wsUrl)
  socket.binaryType = "arraybuffer"
  ws = socket

  socket.onopen = () => {
    connected.value = true
  }

  socket.onerror = () => {
    error.value = "WebSocket 连接错误"
  }

  socket.onclose = () => {
    connected.value = false
  }

  socket.onmessage = (event) => {
    if (event.data instanceof ArrayBuffer) {
      // 兼容旧消息，当前后端仅返回 JSON
      return
    }
    try {
      const data = JSON.parse(event.data as string)
      if (data.type === "error") {
        awaitingResult = false
        error.value = data.message || "服务端错误"
        return
      }
      if (data.type !== "result") return

      const video = videoRef.value
      if (!video) return

      if (Math.abs(video.currentTime - lastCapturedVideoTime) > MAX_RESULT_LAG_SEC) {
        awaitingResult = false
        return
      }

      const imageResult = {
        shape: data.shape as [number, number],
        face_count: Number(data.face_count || 0),
        results: Array.isArray(data.results) ? data.results : [],
      }

      analyzedFrames += 1
      currentFrameIndex.value = analyzedFrames
      currentFaceCount.value = imageResult.face_count || 0
      stats.value = {
        analyzed_frames: analyzedFrames,
        current_face_count: currentFaceCount.value,
      }

      drawDetections(imageResult.results || [], imageResult.shape || [0, 0])
      awaitingResult = false
    } catch {
      awaitingResult = false
    }
  }
}

function startLoop() {
  stopLoop()
  const interval = Math.max(66, Math.round(1000 / selectedFps.value))
  detectTimer = window.setInterval(() => {
    void detectCurrentFrame()
  }, interval)
}

async function detectVideo() {
  if (!file.value || !videoRef.value) {
    error.value = "请先选择视频"
    return
  }

  loading.value = true
  error.value = ""
  clearOverlay()
  currentFrameIndex.value = 0
  currentFaceCount.value = 0
  analyzedFrames = 0
  stats.value = {
    analyzed_frames: 0,
    current_face_count: 0,
  }

  try {
    const video = videoRef.value
    connectWebSocket()
    const start = Date.now()
    while (!connected.value && Date.now() - start < 3000) {
      await new Promise((resolve) => setTimeout(resolve, 50))
    }
    if (!connected.value) {
      throw new Error("WebSocket 连接失败")
    }
    await video.play()
    isDetecting.value = true
    startLoop()
  } catch (err: any) {
    error.value = err.message || "检测失败"
    stopDetection()
  } finally {
    loading.value = false
  }
}

function reset() {
  stopDetection()
  stats.value = null
  error.value = ""
  currentFrameIndex.value = 0
  currentFaceCount.value = 0
  analyzedFrames = 0
  clearOverlay()
}

onUnmounted(() => {
  stopDetection()
  if (originalVideoUrl.value) {
    URL.revokeObjectURL(originalVideoUrl.value)
  }
})
</script>

<template>
  <div class="video-detect-container">
    <h1>视频人脸检测</h1>
    <div class="content-wrapper">
      <div class="left-panel">
        <div class="upload-section">
          <h2>导入视频</h2>
          <div class="upload-area" @click="fileInput?.click()">
            <input
              ref="fileInput"
              type="file"
              accept="video/*"
              @change="handleFileChange"
              style="display: none"
            >
            <div v-if="!originalVideoUrl" class="upload-placeholder">
              <div class="upload-icon">
                🎬
              </div>
              <p>点击或拖拽上传视频</p>
            </div>
            <video v-else :src="originalVideoUrl" class="preview-video" controls />
          </div>
          <div class="button-group">
            <button @click="detectVideo" :disabled="!canStart" class="detect-button">
              {{ loading ? "启动中..." : isDetecting ? "检测中" : "开始检测" }}
            </button>
            <button @click="stopDetection" :disabled="!canStop" class="stop-button">
              停止检测
            </button>
            <button @click="reset" :disabled="loading" class="reset-button">
              重置
            </button>
          </div>
          <div class="fps-row">
            <label class="fps-label" for="video-fps-select">检测帧率</label>
            <select
              id="video-fps-select"
              class="fps-select"
              :disabled="loading"
              :value="selectedFps"
              @change="updateFps(Number(($event.target as HTMLSelectElement).value))"
            >
              <option v-for="fps in fpsOptions" :key="fps" :value="fps">
                {{ fps }} FPS
              </option>
            </select>
          </div>
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>
      <div class="right-panel">
        <div class="result-section">
          <h2>检测结果</h2>
          <div v-if="loading" class="loading">
            <div class="spinner" />
            <p>检测中，请稍候...</p>
          </div>
          <div v-else-if="originalVideoUrl" class="result-content">
            <div class="stats-info">
              <div class="stat-item">
                <span class="stat-label">已分析帧数</span>
                <span class="stat-value">{{ stats?.analyzed_frames || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">当前帧人脸数</span>
                <span class="stat-value">{{ currentFaceCount }}</span>
              </div>
            </div>
            <div class="video-player">
              <h3>抽帧检测结果（前端绘制）</h3>
              <div class="video-stage">
                <video
                  ref="videoRef"
                  :src="originalVideoUrl"
                  class="result-video"
                  controls
                  @loadedmetadata="onVideoLoaded"
                  @error="onVideoError"
                >
                  您的浏览器不支持视频播放
                </video>
                <canvas ref="overlayCanvasRef" class="overlay-canvas" />
              </div>
              <canvas ref="captureCanvasRef" style="display: none" />
            </div>
          </div>
          <div v-else class="placeholder">
            <p>检测结果</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-detect-container {
  padding: 20px;
  width: 100%;
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
  font-size: 28px;
  flex-shrink: 0;
}

.content-wrapper {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.left-panel {
  flex: 1;
}

.right-panel {
  flex: 1.5;
}

.upload-section,
.result-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
}

h2 {
  margin-bottom: 20px;
  color: #409eff;
  font-size: 22px;
  flex-shrink: 0;
}

h3 {
  margin-bottom: 15px;
  color: #333;
  font-size: 18px;
}

.upload-area {
  border: 3px dashed #dcdfe6;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  min-height: 0;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.upload-icon {
  font-size: 64px;
}

.upload-placeholder p {
  color: #909399;
  font-size: 16px;
}

.preview-video,
.result-video {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  object-fit: contain;
}

.button-group {
  display: flex;
  gap: 15px;
  margin-top: 20px;
  flex-shrink: 0;
}

.fps-row {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.fps-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.fps-select {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  background: #fff;
  color: #303133;
}

.fps-select:focus {
  outline: none;
  border-color: #409eff;
}

.detect-button,
.stop-button,
.reset-button {
  flex: 1;
  padding: 16px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.detect-button {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
}

.detect-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.detect-button:disabled {
  background: #a0cfff;
  cursor: not-allowed;
  transform: none;
}

.stop-button {
  background: linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%);
  color: white;
}

.stop-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #f0c78a 0%, #e6a23c 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.4);
}

.stop-button:disabled {
  background: #f5dab1;
  cursor: not-allowed;
  transform: none;
}

.reset-button {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
  color: white;
}

.reset-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #f78989 0%, #f56c6c 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
}

.reset-button:disabled {
  background: #fab6b6;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  color: #f56c6c;
  border-radius: 8px;
  font-size: 15px;
  border-left: 4px solid #f56c6c;
  flex-shrink: 0;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.video-player {
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  flex-shrink: 0;
}

.video-stage {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.result-video {
  display: block;
  width: 100%;
  max-height: 480px;
  background: #111;
}

.overlay-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.debug-info {
  padding: 10px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.debug-info p {
  margin: 0;
}

.stats-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 15px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  backdrop-filter: blur(10px);
}

.stat-label {
  font-size: 15px;
  opacity: 0.95;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 26px;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  font-size: 18px;
  background: #f5f7fa;
  border-radius: 8px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 25px;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
