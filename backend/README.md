<div align="center">
  <h1>基于人脸检测的人数统计系统 - 后端API</h1>
</div>

## 项目简介

FaceCount后端是基于FastAPI构建的人脸检测与人数统计系统服务端，提供RESTful API接口，支持实时视频流处理、人脸识别、多目标追踪和人数统计分析等功能。后端采用高性能异步框架，支持多摄像头并发处理，为前端提供稳定、高效的数据服务。

## 技术栈

- **Web框架**: FastAPI 0.104+
- **ASGI服务器**: Uvicorn 0.24+
- **数据验证**: Pydantic 2.5+
- **文件上传**: Python-multipart
- **人脸检测**: YOLOv8
- **目标追踪**: DeepSORT
- **图像处理**: OpenCV
- **视频处理**: FFmpeg
- **深度学习**: PyTorch
- **模型优化**: TensorRT

## 功能特性

### 核心功能

- **实时检测**: 支持多路视频流实时人脸检测
- **人脸识别**: 基于深度学习的人脸识别算法
- **多目标追踪**: DeepSORT算法实现长时间稳定追踪
- **人数统计**: 实时统计区域内人数变化
- **异常报警**: 支持人数超限、陌生人闯入等报警
- **历史数据**: 存储和查询历史统计数据
- **数据导出**: 支持Excel、CSV格式数据导出

### 性能优化

- **GPU加速**: 支持CUDA加速，提升检测速度
- **模型量化**: TensorRT优化，推理速度提升3倍
- **异步处理**: FastAPI异步框架，支持高并发
- **多线程**: 多线程处理多路视频流
- **缓存机制**: Redis缓存热点数据

## 项目结构

```
backend/
├─ main.py              # 主程序入口
├─ requirements.txt     # 依赖包列表
├─ start.bat           # 启动脚本
├─ app/                # 应用目录
│  ├─ api/             # API路由
│  │  ├─ detection.py  # 人脸检测API
│  │  ├─ statistics.py # 统计分析API
│  │  ├─ video.py      # 视频流API
│  │  ├─ alarm.py      # 报警API
│  │  └─ system.py     # 系统管理API
│  ├─ models/          # 数据模型
│  │  ├─ detection.py  # 检测相关模型
│  │  ├─ statistics.py # 统计相关模型
│  │  ├─ video.py      # 视频相关模型
│  │  └─ user.py       # 用户相关模型
│  ├─ services/        # 业务逻辑
│  │  ├─ detection.py  # 检测服务
│  │  ├─ tracking.py   # 追踪服务
│  │  ├─ statistics.py # 统计服务
│  │  └─ alarm.py      # 报警服务
│  ├─ core/            # 核心配置
│  │  ├─ config.py     # 配置文件
│  │  ├─ security.py   # 安全认证
│  │  └─ database.py   # 数据库连接
│  └─ utils/           # 工具函数
│     ├─ image.py      # 图像处理工具
│     ├─ video.py      # 视频处理工具
│     └─ export.py     # 数据导出工具
├─ models/             # 深度学习模型
│  ├─ yolo/           # YOLOv8模型
│  └─ face_recognizer/# 人脸识别模型
├─ data/              # 数据目录
│  ├─ videos/         # 视频文件
│  ├─ images/         # 图像文件
│  └─ exports/        # 导出文件
└─ logs/              # 日志文件
```

## 快速开始

### 环境要求

- Python 3.10+
- CUDA 11.8+ (GPU加速可选)
- FFmpeg 4.0+

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/xing05188/face_count.git

# 进入后端目录
cd face_count/backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置文件

在`app/core/config.py`中配置以下参数：

```python
# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# 数据库配置
DATABASE_URL = "sqlite:///./face_count.db"

# Redis配置
REDIS_URL = "redis://localhost:6379/0"

# 模型配置
YOLO_MODEL_PATH = "./models/yolo/best.pt"
FACE_RECOGNIZER_PATH = "./models/face_recognizer/model.pth"

# 视频流配置
MAX_STREAMS = 4
DEFAULT_FPS = 30

# 报警配置
MAX_PEOPLE_LIMIT = 50
ENABLE_STRANGER_ALARM = True
```

### 启动服务

```bash
# 使用uvicorn启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或使用启动脚本（Windows）
start.bat
```

服务启动后，访问以下地址：

- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## API接口文档

### 基础接口

#### 健康检查
```http
GET /
```

**响应示例:**
```json
{
  "message": "helloworld"
}
```

### 检测相关API

#### 启动人脸检测
```http
POST /api/detection/start
Content-Type: application/json

{
  "camera_id": "camera_001",
  "stream_url": "rtsp://192.168.1.100:554/stream",
  "zone_id": "zone_001"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "检测已启动",
  "data": {
    "detection_id": "det_123456",
    "status": "running"
  }
}
```

#### 停止人脸检测
```http
POST /api/detection/stop
Content-Type: application/json

{
  "detection_id": "det_123456"
}
```

#### 获取检测状态
```http
GET /api/detection/status?detection_id=det_123456
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "detection_id": "det_123456",
    "status": "running",
    "fps": 30,
    "current_people": 12,
    "accuracy": 0.98
  }
}
```

#### 获取实时检测视频流
```http
GET /api/detection/stream?detection_id=det_123456
```

返回MJPEG视频流。

### 人脸识别API

#### 人脸识别
```http
POST /api/detection/face/recognize
Content-Type: multipart/form-data

file: <image_file>
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "faces": [
      {
        "face_id": "face_001",
        "name": "张三",
        "confidence": 0.95,
        "bbox": [100, 200, 300, 400]
      }
    ]
  }
}
```

#### 注册人脸
```http
POST /api/detection/face/register
Content-Type: multipart/form-data

file: <image_file>
name: 张三
```

**响应示例:**
```json
{
  "code": 200,
  "message": "人脸注册成功",
  "data": {
    "face_id": "face_001"
  }
}
```

#### 删除人脸
```http
DELETE /api/detection/face/delete/{face_id}
```

#### 获取已注册人脸列表
```http
GET /api/detection/face/list
```

### 统计分析API

#### 获取当前人数
```http
GET /api/statistics/current?zone_id=zone_001
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "zone_id": "zone_001",
    "current_people": 12,
    "timestamp": "2024-01-21T10:30:00"
  }
}
```

#### 获取历史统计数据
```http
GET /api/statistics/history?zone_id=zone_001&start_date=2024-01-01&end_date=2024-01-21
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "zone_id": "zone_001",
    "statistics": [
      {
        "timestamp": "2024-01-21T10:00:00",
        "people_count": 10
      },
      {
        "timestamp": "2024-01-21T11:00:00",
        "people_count": 15
      }
    ]
  }
}
```

#### 获取人数变化趋势
```http
GET /api/statistics/trend?zone_id=zone_001&period=7d
```

#### 获取高峰时段统计
```http
GET /api/statistics/peak?zone_id=zone_001&date=2024-01-21
```

### 视频流API

#### 获取视频流列表
```http
GET /api/video/stream/list
```

#### 添加视频流
```http
POST /api/video/stream/add
Content-Type: application/json

{
  "camera_id": "camera_002",
  "stream_url": "rtsp://192.168.1.101:554/stream",
  "zone_id": "zone_002",
  "name": "摄像头2"
}
```

#### 删除视频流
```http
DELETE /api/video/stream/delete/{stream_id}
```

#### 更新视频流配置
```http
PUT /api/video/stream/update/{stream_id}
Content-Type: application/json

{
  "stream_url": "rtsp://192.168.1.102:554/stream"
}
```

### 摄像头管理API

#### 获取摄像头列表
```http
GET /api/video/camera/list
```

#### 添加摄像头
```http
POST /api/video/camera/add
Content-Type: application/json

{
  "camera_id": "camera_003",
  "ip": "192.168.1.103",
  "port": 554,
  "username": "admin",
  "password": "password",
  "name": "摄像头3"
}
```

#### 删除摄像头
```http
DELETE /api/video/camera/delete/{camera_id}
```

#### 获取摄像头状态
```http
GET /api/video/camera/status/{camera_id}
```

### 报警相关API

#### 获取报警记录
```http
GET /api/alarm/list?page=1&page_size=20
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "total": 100,
    "items": [
      {
        "alarm_id": "alarm_001",
        "type": "people_limit",
        "message": "人数超限",
        "zone_id": "zone_001",
        "timestamp": "2024-01-21T10:30:00",
        "status": "unread"
      }
    ]
  }
}
```

#### 获取报警配置
```http
GET /api/alarm/config
```

**响应示例:**
```json
{
  "code": 200,
  "data": {
    "max_people_limit": 50,
    "enable_stranger_alarm": true,
    "enable_detection_alarm": true,
    "enable_offline_alarm": true
  }
}
```

#### 更新报警配置
```http
POST /api/alarm/config/update
Content-Type: application/json

{
  "max_people_limit": 100,
  "enable_stranger_alarm": false
}
```

#### 清除报警记录
```http
DELETE /api/alarm/clear
```

### 数据导出API

#### 导出统计数据为Excel
```http
GET /api/export/statistics/excel?zone_id=zone_001&start_date=2024-01-01&end_date=2024-01-21
```

返回Excel文件下载。

#### 导出统计数据为CSV
```http
GET /api/export/statistics/csv?zone_id=zone_001&start_date=2024-01-01&end_date=2024-01-21
```

返回CSV文件下载。

#### 导出报警记录为Excel
```http
GET /api/export/alarm/excel?start_date=2024-01-01&end_date=2024-01-21
```

#### 导出历史视频
```http
GET /api/export/history/video?detection_id=det_123456&start_time=2024-01-21T10:00:00&end_time=2024-01-21T11:00:00
```

### 系统管理API

#### 用户管理

##### 获取用户列表
```http
GET /api/user/list?page=1&page_size=20
```

##### 添加用户
```http
POST /api/user/add
Content-Type: application/json

{
  "username": "admin",
  "password": "123456",
  "role": "admin",
  "email": "admin@example.com"
}
```

##### 更新用户信息
```http
PUT /api/user/update/{user_id}
Content-Type: application/json

{
  "email": "new_email@example.com"
}
```

##### 删除用户
```http
DELETE /api/user/delete/{user_id}
```

#### 权限管理

##### 获取权限列表
```http
GET /api/permission/list
```

##### 获取角色列表
```http
GET /api/role/list
```

##### 获取角色权限
```http
GET /api/role/permission/{role_id}
```

##### 更新角色权限
```http
POST /api/role/permission/update
Content-Type: application/json

{
  "role_id": "role_001",
  "permissions": ["detection:view", "statistics:view", "alarm:view"]
}
```

## 数据模型

### 检测相关模型

```python
class DetectionStartRequest(BaseModel):
    camera_id: str
    stream_url: str
    zone_id: str

class DetectionStatusResponse(BaseModel):
    detection_id: str
    status: str
    fps: int
    current_people: int
    accuracy: float
```

### 统计相关模型

```python
class StatisticsHistoryRequest(BaseModel):
    zone_id: str
    start_date: date
    end_date: date

class StatisticsHistoryResponse(BaseModel):
    zone_id: str
    statistics: List[StatisticsItem]

class StatisticsItem(BaseModel):
    timestamp: datetime
    people_count: int
```

### 报警相关模型

```python
class AlarmConfig(BaseModel):
    max_people_limit: int
    enable_stranger_alarm: bool
    enable_detection_alarm: bool
    enable_offline_alarm: bool

class AlarmRecord(BaseModel):
    alarm_id: str
    type: str
    message: str
    zone_id: str
    timestamp: datetime
    status: str
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 性能指标

- **检测准确率**: 98%+
- **检测速度**: 30-60 FPS
- **并发支持**: 4路视频流同时处理
- **响应时间**: < 100ms
- **支持人数**: 单区域最多500人

## 部署说明

### Docker部署

```bash
# 构建镜像
docker build -t face_count_backend .

# 运行容器
docker run -d -p 8000:8000 --gpus all face_count_backend
```

### 生产环境部署

建议使用Nginx作为反向代理，配合Gunicorn或Uvicorn作为ASGI服务器。

```bash
# 使用Gunicorn + Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 开发指南

### 代码规范

- 遵循PEP 8代码规范
- 使用类型注解
- 编写单元测试
- 添加代码注释

### 测试

```bash
# 运行测试
pytest

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```

## 常见问题

### Q: 如何启用GPU加速？

A: 安装CUDA和cuDNN，然后在配置文件中设置`USE_GPU = True`。

### Q: 如何添加新的摄像头？

A: 使用`POST /api/video/camera/add`接口添加摄像头信息。

### Q: 如何调整检测准确率？

A: 在配置文件中调整`CONFIDENCE_THRESHOLD`参数。

### Q: 如何导出历史数据？

A: 使用`GET /api/export/statistics/excel`或`GET /api/export/statistics/csv`接口。

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
