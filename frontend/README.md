<div align="center">
  <img alt="logo" width="120" height="120" src="./src/common/assets/images/layouts/logo.png">
  <h1>基于人脸检测的人数统计系统</h1>
</div>

## 项目简介

FaceCount是一个基于Vue 3和TypeScript构建的人脸检测与人数统计系统，提供实时视频流处理、人脸识别、多目标追踪和人数统计分析功能。该项目旨在为智能安防、人员管理、客流统计等场景提供一个高效、准确的Web可视化平台，支持多摄像头并发监控和实时数据分析。

## 技术栈

- **前端框架**: Vue 3.5+
- **构建工具**: Vite 7+
- **路由管理**: Vue Router
- **状态管理**: Pinia
- **UI组件库**: Element Plus
- **图表库**: ECharts
- **CSS预处理器**: Scss
- **开发语言**: TypeScript
- **包管理工具**: pnpm
- **网络请求**: Axios

## 功能特性

### 核心技术

- **YOLOv8**: 高精度人脸检测算法，准确率98%+
- **DeepSORT**: 多目标追踪算法，支持长时间稳定追踪
- **OpenCV**: 实时视频流处理，支持GPU加速
- **FFmpeg**: 多路视频流并发处理，FPS可达60+
- **TensorRT**: 模型量化优化，推理速度提升3倍

### 主要功能

- **实时检测**: 实时人脸检测与识别，支持多摄像头并发
- **人数统计**: 实时统计区域内人数变化，支持历史数据查询
- **多目标追踪**: 基于DeepSORT的多目标追踪，防止重复计数
- **热力图分析**: 生成人员分布热力图，可视化人员流动趋势
- **异常报警**: 人数超限、陌生人闯入等异常情况实时报警
- **历史回放**: 支持历史视频回放和数据分析
- **数据导出**: 支持统计数据导出为Excel、CSV格式

### 数据可视化

- **实时监控**: 多路视频流实时预览，支持分屏显示
- **统计图表**: 人数变化曲线图、时段分布图、趋势分析图
- **热力图展示**: 区域人员分布热力图，支持时间维度切换
- **性能监控**: 检测准确率、FPS、延迟等性能指标实时展示
- **响应式图表**: 自适应窗口大小的ECharts图表

### 用户体验

- **响应式设计**: 适配不同屏幕尺寸，支持移动端访问
- **多主题支持**: 支持正常、暗黑和深蓝主题
- **权限管理**: 基于角色的访问控制，支持多用户管理
- **实时通知**: 系统消息、报警通知和待办事项提醒
- **水印保护**: 支持系统水印功能，保护数据安全

## 项目结构

```
├─ src
│  ├─ common             # 通用目录
│  │  ├─ apis            # 通用接口
│  │  │  ├─ detection    # 人脸检测相关API
│  │  │  ├─ statistics   # 统计分析相关API
│  │  │  ├─ video        # 视频流相关API
│  │  │  └─ alarm        # 报警相关API
│  │  ├─ assets          # 静态资源
│  │  │  ├─ images       # 图片资源
│  │  │  └─ styles       # 样式文件
│  │  ├─ components      # 通用组件
│  │  ├─ composables     # 组合式函数
│  │  ├─ constants       # 常量
│  │  └─ utils           # 工具函数
│  ├─ http               # 网络请求配置
│  ├─ layouts            # 布局组件
│  ├─ pages              # 页面组件
│  │  ├─ dashboard       # 仪表盘页面
│  │  ├─ monitor         # 实时监控页面
│  │  ├─ statistics      # 统计分析页面
│  │  ├─ heatmap         # 热力图页面
│  │  ├─ history         # 历史数据页面
│  │  └─ settings        # 系统设置页面
│  ├─ pinia              # 状态管理
│  ├─ plugins            # 插件
│  ├─ router             # 路由配置
│  ├─ App.vue            # 入口页面
│  └─ main.ts            # 入口文件
```

## 开发指南

### 环境要求

- Node.js 20.19+ 或 22.12+
- pnpm 10+

### 本地开发

```bash
# 克隆项目
git clone https://github.com/xing05188/face_count.git

# 进入项目目录
cd face_count

# 安装依赖
pnpm i

# 启动开发服务器
pnpm dev
```

### 构建部署

```bash
# 构建生产环境
pnpm build

# 预览构建结果
pnpm preview
```

### 代码检查

```bash
# 代码校验和格式化
pnpm lint
```

## API接口

项目提供了丰富的API接口用于人脸检测和人数统计：

### 检测相关API

- **实时检测**
  - `/api/detection/start` - 启动人脸检测
  - `/api/detection/stop` - 停止人脸检测
  - `/api/detection/status` - 获取检测状态
  - `/api/detection/stream` - 获取实时检测视频流

- **人脸识别**
  - `/api/detection/face/recognize` - 人脸识别
  - `/api/detection/face/register` - 注册人脸
  - `/api/detection/face/delete/{id}` - 删除人脸
  - `/api/detection/face/list` - 获取已注册人脸列表

### 统计分析API

- **人数统计**
  - `/api/statistics/current` - 获取当前人数
  - `/api/statistics/history` - 获取历史统计数据
  - `/api/statistics/trend` - 获取人数变化趋势
  - `/api/statistics/peak` - 获取高峰时段统计

- **时段分析**
  - `/api/statistics/hourly` - 按小时统计人数
  - `/api/statistics/daily` - 按天统计人数
  - `/api/statistics/weekly` - 按周统计人数
  - `/api/statistics/monthly` - 按月统计人数

- **区域分析**
  - `/api/statistics/zone/{id}` - 获取指定区域人数
  - `/api/statistics/zone/list` - 获取所有区域统计
  - `/api/statistics/zone/compare` - 区域人数对比分析

### 视频流API

- **视频管理**
  - `/api/video/stream/list` - 获取视频流列表
  - `/api/video/stream/add` - 添加视频流
  - `/api/video/stream/delete/{id}` - 删除视频流
  - `/api/video/stream/update/{id}` - 更新视频流配置

- **摄像头管理**
  - `/api/video/camera/list` - 获取摄像头列表
  - `/api/video/camera/add` - 添加摄像头
  - `/api/video/camera/delete/{id}` - 删除摄像头
  - `/api/video/camera/status/{id}` - 获取摄像头状态

### 报警相关API

- **报警管理**
  - `/api/alarm/list` - 获取报警记录
  - `/api/alarm/config` - 获取报警配置
  - `/api/alarm/config/update` - 更新报警配置
  - `/api/alarm/clear` - 清除报警记录

- **报警类型**
  - 人数超限报警
  - 陌生人闯入报警
  - 检测异常报警
  - 设备离线报警

### 数据导出API

- **数据导出**
  - `/api/export/statistics/excel` - 导出统计数据为Excel
  - `/api/export/statistics/csv` - 导出统计数据为CSV
  - `/api/export/alarm/excel` - 导出报警记录为Excel
  - `/api/export/history/video` - 导出历史视频

### 系统管理API

- **用户管理**
  - `/api/user/list` - 获取用户列表
  - `/api/user/add` - 添加用户
  - `/api/user/update/{id}` - 更新用户信息
  - `/api/user/delete/{id}` - 删除用户

- **权限管理**
  - `/api/permission/list` - 获取权限列表
  - `/api/role/list` - 获取角色列表
  - `/api/role/permission/{id}` - 获取角色权限
  - `/api/role/permission/update` - 更新角色权限

## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至 [您的邮箱]

---

<div align="center">
  <p>感谢使用基于人脸检测的人数统计系统！</p>
</div>
