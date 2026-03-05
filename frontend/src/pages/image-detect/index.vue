<script lang="ts" setup>
import axios from "axios"
import { nextTick, ref } from "vue"

const API_BASE_URL = import.meta.env.VITE_BASE_URL || "/api"

const file = ref<File | null>(null)
const imageUrl = ref<string>("")
const faceCount = ref<number>(0)
const loading = ref<boolean>(false)
const error = ref<string>("")
const fileInput = ref<HTMLInputElement | null>(null)
const resultCanvasRef = ref<HTMLCanvasElement | null>(null)
const resultImageRef = ref<HTMLImageElement | null>(null)
const latestDetections = ref<DetectionItem[]>([])

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

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    if (imageUrl.value) {
      URL.revokeObjectURL(imageUrl.value)
    }
    file.value = target.files[0]
    imageUrl.value = URL.createObjectURL(file.value)
    faceCount.value = 0
    error.value = ""
    latestDetections.value = []
    void nextTick(() => {
      drawDetectionsOnCanvas([])
    })
  }
}

function drawDetectionsOnCanvas(results: DetectionItem[]) {
  if (!resultCanvasRef.value || !resultImageRef.value) return
  const imgEl = resultImageRef.value
  if (!imgEl.complete || imgEl.naturalWidth <= 0 || imgEl.naturalHeight <= 0) return

  const canvas = resultCanvasRef.value
  const ctx = canvas.getContext("2d")
  if (!ctx) return

  canvas.width = imgEl.naturalWidth
  canvas.height = imgEl.naturalHeight
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  ctx.lineWidth = 3
  ctx.font = "18px sans-serif"
  results.forEach((item) => {
    const { x1, y1, x2, y2 } = item.box
    const w = Math.max(0, x2 - x1)
    const h = Math.max(0, y2 - y1)
    const label = `${item.name} ${(item.confidence * 100).toFixed(1)}%`

    ctx.strokeStyle = "#1e88e5"
    ctx.fillStyle = "rgba(30, 136, 229, 0.15)"
    ctx.strokeRect(x1, y1, w, h)
    ctx.fillRect(x1, y1, w, h)

    const textWidth = ctx.measureText(label).width
    const textY = Math.max(0, y1 - 28)
    ctx.fillStyle = "#1e88e5"
    ctx.fillRect(x1, textY, textWidth + 16, 28)
    ctx.fillStyle = "#ffffff"
    ctx.fillText(label, x1 + 8, textY + 20)
  })
}

function onResultImageLoaded() {
  drawDetectionsOnCanvas(latestDetections.value)
}

async function detectImage() {
  if (!file.value) {
    error.value = "请先选择图片"
    return
  }

  loading.value = true
  error.value = ""

  try {
    const formData = new FormData()
    formData.append("file", file.value)

    const response = await axios.post<DetectionResponse>(`${API_BASE_URL}/detect?response_mode=compact`, formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    })

    const imageResult = response.data.images?.[0]
    if (!imageResult) {
      throw new Error("后端未返回检测结果")
    }

    faceCount.value = imageResult.face_count || 0
    latestDetections.value = imageResult.results || []
    await nextTick()
    drawDetectionsOnCanvas(latestDetections.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || "检测失败"
  } finally {
    loading.value = false
  }
}

function reset() {
  file.value = null
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value)
  }
  imageUrl.value = ""
  faceCount.value = 0
  error.value = ""
  latestDetections.value = []
  const canvas = resultCanvasRef.value
  const ctx = canvas?.getContext("2d")
  if (canvas && ctx) {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}
</script>

<template>
  <div class="image-detect-container">
    <h1>图片人脸检测</h1>
    <div class="content-wrapper">
      <div class="left-panel">
        <div class="upload-section">
          <h2>导入图片</h2>
          <div class="upload-area" @click="fileInput?.click()">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileChange"
              style="display: none"
            >
            <div v-if="!imageUrl" class="upload-placeholder">
              <div class="upload-icon">
                📷
              </div>
              <p>点击或拖拽上传图片</p>
            </div>
            <img v-else :src="imageUrl" class="preview-image">
          </div>
          <div class="button-group">
            <button @click="detectImage" :disabled="loading || !file" class="detect-button">
              {{ loading ? "检测中..." : "开始检测" }}
            </button>
            <button @click="reset" :disabled="loading" class="reset-button">
              重置
            </button>
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
          <div v-else-if="imageUrl" class="result-content">
            <div class="face-count">
              <span class="count-number">{{ faceCount }}</span>
              <span class="count-label">个人脸</span>
            </div>
            <div class="result-image">
              <div class="result-stage">
                <img
                  ref="resultImageRef"
                  :src="imageUrl"
                  class="result-base-image"
                  alt="检测原图"
                  @load="onResultImageLoaded"
                >
                <canvas ref="resultCanvasRef" class="result-canvas" />
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
.image-detect-container {
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
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
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

.preview-image {
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

.detect-button,
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
  align-items: center;
  justify-content: center;
  gap: 30px;
  flex: 1;
  min-height: 0;
}

.result-image {
  flex: 1;
  width: 100%;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-stage {
  position: relative;
  display: inline-block;
  max-width: 100%;
  max-height: 100%;
}

.result-base-image {
  display: block;
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  object-fit: contain;
}

.result-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  pointer-events: none;
}

.face-count {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  padding: 15px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.count-number {
  font-size: 32px;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.count-label {
  font-size: 18px;
  opacity: 0.95;
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
