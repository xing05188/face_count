<script lang="ts" setup>
import { ref } from "vue"

const API_BASE_URL = import.meta.env.VITE_BASE_URL || "/api"

interface StatsData {
  total_frames: number
  processing_time_seconds: number
  frame_counts: number[]
}

const file = ref<File | null>(null)
const originalVideoUrl = ref<string>("")
const processedVideoUrl = ref<string>("")
const stats = ref<StatsData | null>(null)
const loading = ref<boolean>(false)
const error = ref<string>("")
const fileInput = ref<HTMLInputElement | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
const currentFrameIndex = ref<number>(0)
const currentFaceCount = ref<number>(0)

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    file.value = target.files[0]
    originalVideoUrl.value = URL.createObjectURL(file.value)
    reset()
  }
}

function onTimeUpdate() {
  if (!videoRef.value || !stats.value) return

  const video = videoRef.value
  const currentTime = video.currentTime
  const duration = video.duration

  if (duration > 0) {
    const frameIndex = Math.floor((currentTime / duration) * stats.value.total_frames)
    currentFrameIndex.value = Math.min(frameIndex, stats.value.total_frames - 1)
    currentFaceCount.value = stats.value.frame_counts[currentFrameIndex.value] || 0
  }
}

function onVideoLoaded() {
  console.log("Video loaded successfully")
  console.log("Video duration:", videoRef.value?.duration)
  console.log("Video readyState:", videoRef.value?.readyState)
}

function onVideoError(event: Event) {
  console.error("Video error:", event)
  const video = event.target as HTMLVideoElement
  console.error("Video error code:", video.error?.code)
  console.error("Video error message:", video.error?.message)
  error.value = `视频加载失败: ${video.error?.message || "未知错误"}`
}

async function detectVideo() {
  if (!file.value) {
    error.value = "请先选择视频"
    return
  }

  loading.value = true
  error.value = ""
  stats.value = null
  processedVideoUrl.value = ""
  currentFrameIndex.value = 0
  currentFaceCount.value = 0

  try {
    const formData = new FormData()
    formData.append("file", file.value)

    const response = await fetch(`${API_BASE_URL}/detect/video?output_format=mp4`, {
      method: "POST",
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || "检测失败")
    }
    const faceCountsHeader = response.headers.get("X-Frame-Counts")
    const totalFramesHeader = response.headers.get("X-Total-Frames")
    const processingTimeHeader = response.headers.get("X-Processing-Time")

    console.log("Face counts header:", faceCountsHeader)
    console.log("Total frames header:", totalFramesHeader)
    console.log("Processing time header:", processingTimeHeader)

    const faceCounts = faceCountsHeader ? JSON.parse(faceCountsHeader) : []
    const totalFrames = Number.parseInt(totalFramesHeader || "0")
    const processingTime = Number.parseFloat(processingTimeHeader || "0")

    stats.value = {
      total_frames: totalFrames,
      processing_time_seconds: processingTime,
      frame_counts: faceCounts
    }

    console.log("Stats:", stats.value)

    const videoBlob = await response.blob()
    console.log("Video blob size:", videoBlob.size)
    console.log("Video blob type:", videoBlob.type)

    if (videoBlob.size === 0) {
      throw new Error("返回的视频文件为空")
    }

    processedVideoUrl.value = URL.createObjectURL(videoBlob)
    console.log("Processed video URL:", processedVideoUrl.value)
  } catch (err: any) {
    console.error("Detection error:", err)
    error.value = err.message || "检测失败"
  } finally {
    loading.value = false
  }
}

function reset() {
  stats.value = null
  error.value = ""
  processedVideoUrl.value = ""
  currentFrameIndex.value = 0
  currentFaceCount.value = 0
}
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
            <button @click="detectVideo" :disabled="loading || !file" class="detect-button">
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
          <div v-else-if="stats" class="result-content">
            <div class="stats-info">
              <div class="stat-item">
                <span class="stat-label">当前帧</span>
                <span class="stat-value">{{ currentFrameIndex + 1 }} / {{ stats.total_frames }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">当前帧人脸数</span>
                <span class="stat-value">{{ currentFaceCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">处理耗时</span>
                <span class="stat-value">{{ stats.processing_time_seconds }}s</span>
              </div>
            </div>
            <div class="video-player">
              <h3>处理后的视频</h3>
              <div v-if="!processedVideoUrl" class="no-video">
                <p>等待视频处理...</p>
              </div>
              <video
                v-else
                ref="videoRef"
                :src="processedVideoUrl"
                class="result-video"
                controls
                @timeupdate="onTimeUpdate"
                @loadedmetadata="onVideoLoaded"
                @error="onVideoError"
              >
                您的浏览器不支持视频播放
              </video>
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

.no-video {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  background: #e4e7ed;
  border-radius: 8px;
  color: #909399;
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
  font-size: 32px;
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
