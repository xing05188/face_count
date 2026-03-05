<script lang="ts" setup>
import { computed, nextTick, onUnmounted, ref } from "vue"

const API_BASE_URL = import.meta.env.VITE_BASE_URL || "/api"

interface StatsData {
  frame_index: number
  face_count: number
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

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const resultCanvasRef = ref<HTMLCanvasElement | null>(null)

const loading = ref(false)
const error = ref("")

const ws = ref<WebSocket | null>(null)
const stream = ref<MediaStream | null>(null)

const isDetecting = ref(false)
const connected = ref(false)

const stats = ref<StatsData | null>(null)
const frameCount = ref(0)

const cameraReady = ref(false)
const resultReady = ref(false)
const selectedFps = ref<number>(12)
const fpsOptions = [8, 10, 12, 15]

let sendTimer: number | null = null
let sending = false
let awaitingResult = false
let lastSentFrameBlob: Blob | null = null

// 发送分辨率（固定缩放能显著提速）
const SEND_WIDTH = 640
const SEND_HEIGHT = 480
// JPEG 质量（越低越快）
const SEND_JPEG_QUALITY = 0.75

const canStart = computed(() => !loading.value && !isDetecting.value)
const canStop = computed(() => isDetecting.value)

function cleanupResultCanvas() {
  const canvas = resultCanvasRef.value
  const ctx = canvas?.getContext("2d")
  if (canvas && ctx) {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
  resultReady.value = false
  awaitingResult = false
  lastSentFrameBlob = null
}

function stopSendLoop() {
  if (sendTimer !== null) {
    window.clearInterval(sendTimer)
    sendTimer = null
  }
  sending = false
  awaitingResult = false
}

function stopWebSocket() {
  try {
    ws.value?.close()
  } finally {
    ws.value = null
    connected.value = false
  }
}

function stopCamera() {
  cameraReady.value = false
  const s = stream.value
  stream.value = null
  if (videoRef.value) videoRef.value.srcObject = null
  if (s) s.getTracks().forEach(t => t.stop())
}

function updateFps(nextFps: number) {
  selectedFps.value = nextFps
  if (isDetecting.value) {
    startSendLoop()
  }
}

async function waitForVideoReady(timeoutMs = 5000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const v = videoRef.value
    if (v && v.videoWidth > 0 && v.videoHeight > 0 && !v.paused) {
      return
    }
    await new Promise(r => setTimeout(r, 50))
  }
  throw new Error("摄像头视频未就绪（videoWidth=0），请检查权限/设备占用")
}

async function startCamera() {
  error.value = ""
  cameraReady.value = false

  const constraints: MediaStreamConstraints = {
    video: {
      width: { ideal: SEND_WIDTH },
      height: { ideal: SEND_HEIGHT },
      facingMode: "user"
    },
    audio: false
  }

  stream.value = await navigator.mediaDevices.getUserMedia(constraints)

  await nextTick()
  const v = videoRef.value
  if (!v) throw new Error("视频元素未初始化")

  v.srcObject = stream.value
  v.muted = true
  v.playsInline = true

  // 关键：必须显式 play，并等待 videoWidth/Height > 0
  await v.play()
  await waitForVideoReady()
  cameraReady.value = true
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  const host = window.location.host
  const wsUrl = `${protocol}//${host}${API_BASE_URL}/detect/camera?mode=compact`

  const socket = new WebSocket(wsUrl)
  socket.binaryType = "arraybuffer"
  ws.value = socket

  socket.onopen = () => {
    connected.value = true
  }

  socket.onerror = () => {
    error.value = "WebSocket 连接错误"
  }

  socket.onclose = () => {
    connected.value = false
  }

  socket.onmessage = async (event) => {
    // 兼容旧模式：忽略二进制帧
    if (event.data instanceof ArrayBuffer) {
      return
    }

    // 文本：统计信息 / 错误
    try {
      const data = JSON.parse(event.data as string)
      if (data.type === "result") {
        awaitingResult = false
        frameCount.value = data.frame_index
        stats.value = {
          frame_index: data.frame_index,
          face_count: data.face_count
        }
        if (lastSentFrameBlob) {
          await drawFrameWithDetections(lastSentFrameBlob, data.results || [])
          resultReady.value = true
        }
      } else if (data.type === "stats") {
        // 兼容旧消息结构
        awaitingResult = false
        frameCount.value = data.frame_index
        stats.value = {
          frame_index: data.frame_index,
          face_count: data.face_count
        }
      } else if (data.type === "error") {
        awaitingResult = false
        error.value = data.message || "服务端错误"
      }
    } catch {
      // ignore
    }
  }
}

async function drawFrameWithDetections(frameBlob: Blob, detections: DetectionItem[]) {
  const canvas = resultCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext("2d")
  if (!ctx) return

  const bitmap = await createImageBitmap(frameBlob)
  canvas.width = bitmap.width
  canvas.height = bitmap.height
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  bitmap.close()

  ctx.lineWidth = 2
  ctx.font = "16px sans-serif"
  detections.forEach((item) => {
    const { x1, y1, x2, y2 } = item.box
    const w = Math.max(0, x2 - x1)
    const h = Math.max(0, y2 - y1)
    const label = `${item.name} ${(item.confidence * 100).toFixed(1)}%`

    ctx.strokeStyle = "#00c853"
    ctx.fillStyle = "rgba(0, 200, 83, 0.2)"
    ctx.strokeRect(x1, y1, w, h)
    ctx.fillRect(x1, y1, w, h)

    const textWidth = ctx.measureText(label).width
    const textY = Math.max(0, y1 - 24)
    ctx.fillStyle = "#00c853"
    ctx.fillRect(x1, textY, textWidth + 12, 24)
    ctx.fillStyle = "#ffffff"
    ctx.fillText(label, x1 + 6, textY + 17)
  })
}

async function sendOneFrame() {
  if (sending) return
  if (awaitingResult) return
  const socket = ws.value
  const v = videoRef.value
  const canvas = canvasRef.value
  if (!socket || socket.readyState !== WebSocket.OPEN) return
  if (!v || !canvas) return
  if (!cameraReady.value) return
  if (v.videoWidth <= 0 || v.videoHeight <= 0) return

  sending = true
  try {
    // 固定缩放到 SEND_WIDTH/SEND_HEIGHT（提升速度 & 降低带宽）
    if (canvas.width !== SEND_WIDTH || canvas.height !== SEND_HEIGHT) {
      canvas.width = SEND_WIDTH
      canvas.height = SEND_HEIGHT
    }
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    ctx.drawImage(v, 0, 0, SEND_WIDTH, SEND_HEIGHT)

    const blob: Blob | null = await new Promise((resolve) => {
      canvas.toBlob(b => resolve(b), "image/jpeg", SEND_JPEG_QUALITY)
    })
    if (!blob) return

    lastSentFrameBlob = blob
    awaitingResult = true
    const buf = await blob.arrayBuffer()
    socket.send(buf)
  } finally {
    sending = false
  }
}

function startSendLoop() {
  stopSendLoop()
  const intervalMs = Math.max(66, Math.round(1000 / selectedFps.value))
  sendTimer = window.setInterval(() => {
    void sendOneFrame()
  }, intervalMs)
}

async function startDetection() {
  if (!canStart.value) return

  loading.value = true
  error.value = ""
  cleanupResultCanvas()
  stats.value = null
  frameCount.value = 0

  try {
    await startCamera()
    connectWebSocket()

    // 等待 WS open，最多 3 秒
    const start = Date.now()
    while (!connected.value && Date.now() - start < 3000) {
      await new Promise(r => setTimeout(r, 50))
    }
    if (!connected.value) throw new Error("WebSocket 连接失败")

    isDetecting.value = true
    startSendLoop()
  } catch (e: any) {
    error.value = e?.message || "启动检测失败"
    stopDetection()
  } finally {
    loading.value = false
  }
}

function stopDetection() {
  isDetecting.value = false
  stopSendLoop()
  stopWebSocket()
  stopCamera()
}

function reset() {
  stopDetection()
  error.value = ""
  stats.value = null
  frameCount.value = 0
  cleanupResultCanvas()
}

onUnmounted(() => {
  stopDetection()
  cleanupResultCanvas()
})
</script>

<template>
  <div class="camera-detect-container">
    <h1>摄像头实时检测</h1>
    <div class="content-wrapper">
      <div class="left-panel">
        <div class="camera-section">
          <h2>摄像头画面</h2>
          <div class="video-container">
            <video ref="videoRef" class="camera-video" autoplay playsinline muted />
            <div v-if="!cameraReady" class="placeholder overlay">
              <p>{{ loading ? "正在启动摄像头..." : "等待摄像头启动..." }}</p>
            </div>
            <canvas ref="canvasRef" style="display: none" />
          </div>
          <div class="button-group">
            <button @click="startDetection" :disabled="!canStart" class="start-button">
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
            <label class="fps-label" for="camera-fps-select">检测帧率</label>
            <select
              id="camera-fps-select"
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
          <div v-if="loading && !isDetecting" class="loading">
            <div class="spinner" />
            <p>正在启动摄像头...</p>
          </div>
          <div v-else-if="isDetecting" class="result-content">
            <div class="stats-info">
              <div class="stat-item">
                <span class="stat-label">当前帧</span>
                <span class="stat-value">{{ frameCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">当前人脸数</span>
                <span class="stat-value">{{ stats?.face_count || 0 }}</span>
              </div>
            </div>
            <div class="result-image">
              <h3>检测结果</h3>
              <div class="image-container">
                <canvas ref="resultCanvasRef" class="result-img" />
                <div v-if="!resultReady" class="placeholder overlay">
                  <p>{{ isDetecting ? "等待检测结果..." : "检测结果" }}</p>
                </div>
              </div>
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
.camera-detect-container {
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

.camera-section,
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

.video-container {
  border: 3px dashed #dcdfe6;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  min-height: 300px;
  background: #fafafa;
  position: relative;
}

.camera-video {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  object-fit: contain;
  display: block;
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

.start-button,
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

.start-button {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.start-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #85ce61 0%, #67c23a 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
}

.start-button:disabled {
  background: #b3e19d;
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

.result-image {
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  flex-shrink: 0;
}

.image-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: #fff;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  position: relative;
}

.result-img {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  object-fit: contain;
  display: block;
}

.stats-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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
  font-size: 14px;
  opacity: 0.95;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
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

.overlay {
  position: absolute;
  inset: 20px;
  z-index: 2;
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
