import os
from pathlib import Path
import torch

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = os.path.join(BASE_DIR, "models", "yolo", "yolov6m-face.pt")

# 检测参数
CONFIDENCE_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
MAX_DETECTIONS = 100

# 性能优化参数
MAX_IMAGE_SIZE = 1920  # 最大图片尺寸（长边），超过会缩放
IMAGE_QUALITY = 85  # JPEG质量 (1-100)
VIDEO_FRAME_SKIP = 1  # 视频帧采样间隔（1=处理所有帧，2=每2帧处理1帧）
VIDEO_BATCH_SIZE = 4  # 视频批处理大小（如果GPU内存足够可以增加，CPU建议1-2）
USE_HALF_PRECISION = True  # 使用半精度推理（FP16），可提升速度
USE_TORCH_COMPILE = True  # 使用torch.compile优化模型（PyTorch 2.0+）
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # 自动检测GPU
