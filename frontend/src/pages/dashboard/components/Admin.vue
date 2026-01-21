<script lang="ts" setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useUserStore } from "@/pinia/stores/user"

// const router = useRouter()
const userStore = useUserStore()

// // 快速访问入口
// const quickAccess = ref([
// ])

// // 跳转到指定路由
// function navigateTo(route: string) {
//   router.push(route)
// }
</script>

<template>
  <div class="dashboard-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1>欢迎回来，{{ userStore.username }}</h1>
      <p>基于人脸检测的人数统计系统</p>
    </div>

    <!-- 快速访问 -->
    <div class="quick-access-section">
      <h2>快速访问</h2>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px);
}

.welcome-section {
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #409eff, #36a3f7);
  color: white;
  border-radius: 8px;
  text-align: center;

  h1 {
    margin: 0 0 5px 0;
    font-size: 24px;
    font-weight: 600;
  }

  p {
    margin: 0;
    font-size: 16px;
    opacity: 0.9;
  }
}

.quick-access-section {
  h2 {
    margin: 0 0 20px 0;
    font-size: 18px;
    color: #303133;
  }
}

.quick-access-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 120px;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  }

  .card-content {
    display: flex;
    align-items: center;
    height: 100%;

    .card-icon {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 15px;

      .el-icon {
        font-size: 24px;
        color: white;
      }
    }

    .card-info {
      flex: 1;

      .card-title {
        font-size: 16px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 5px;
      }

      .card-desc {
        font-size: 13px;
        color: #909399;
      }
    }
  }
}
</style>