<script lang="ts" setup>
import axios from "axios"
import { onMounted, ref } from "vue"

const message = ref<string>("")
const loading = ref<boolean>(false)
const error = ref<string>("")

async function testApi() {
  loading.value = true
  error.value = ""
  try {
    const response = await axios.get("http://localhost:8000/hello")
    message.value = response.data.message
  } catch (err: any) {
    error.value = err.message || "请求失败"
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  testApi()
})
</script>

<template>
  <div class="api-test-container">
    <h1>API 测试页面</h1>
    <div class="test-content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      <div v-else-if="error" class="error">
        错误: {{ error }}
      </div>
      <div v-else class="success">
        <h3>API 响应:</h3>
        <p>{{ message }}</p>
      </div>
      <button @click="testApi" :disabled="loading" class="test-button">
        {{ loading ? "加载中..." : "重新测试" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.api-test-container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
}

.test-content {
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.loading {
  text-align: center;
  color: #666;
  font-size: 16px;
}

.error {
  color: #f56c6c;
  text-align: center;
  padding: 10px;
  background-color: #fef0f0;
  border-radius: 4px;
}

.success {
  text-align: center;
}

.success h3 {
  margin-bottom: 10px;
  color: #409eff;
}

.success p {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.test-button {
  display: block;
  margin: 20px auto 0;
  padding: 10px 30px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.test-button:hover:not(:disabled) {
  background-color: #66b1ff;
}

.test-button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}
</style>