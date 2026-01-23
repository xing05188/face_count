<script lang="ts" setup>
import axios from "axios"
import { ref } from "vue"

const API_BASE_URL = import.meta.env.VITE_BASE_URL || "/api"

const file = ref<File | null>(null)
const imageUrl = ref<string>("")
const resultUrl = ref<string>("")
const faceCount = ref<number>(0)
const loading = ref<boolean>(false)
const error = ref<string>("")
const fileInput = ref<HTMLInputElement | null>(null)

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    file.value = target.files[0]
    imageUrl.value = URL.createObjectURL(file.value)
    resultUrl.value = ""
    faceCount.value = 0
    error.value = ""
  }
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

    const response = await axios.post(`${API_BASE_URL}/detect`, formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      },
      responseType: "blob"
    })

    faceCount.value = Number.parseInt(response.headers["x-face-count"] || "0")
    resultUrl.value = URL.createObjectURL(response.data)
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || "检测失败"
  } finally {
    loading.value = false
  }
}

function reset() {
  file.value = null
  imageUrl.value = ""
  resultUrl.value = ""
  faceCount.value = 0
  error.value = ""
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
          <div v-else-if="resultUrl" class="result-content">
            <div class="face-count">
              <span class="count-number">{{ faceCount }}</span>
              <span class="count-label">个人脸</span>
            </div>
            <img :src="resultUrl" class="result-image">
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

.preview-image,
.result-image {
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
