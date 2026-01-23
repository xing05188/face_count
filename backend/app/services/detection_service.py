from ultralytics import YOLO
from app.core.config import (
    MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD, 
    MAX_IMAGE_SIZE, USE_HALF_PRECISION, DEVICE,
    USE_TORCH_COMPILE, MAX_DETECTIONS
)
import cv2
import logging
import numpy as np
import os
import tempfile
import torch
from typing import List, Tuple
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceDetectionService:
    def __init__(self):
        try:
            # 检测可用设备
            self.device = DEVICE
            if self.device == "cuda" and not torch.cuda.is_available():
                self.device = "cpu"
                logger.warning("CUDA不可用，使用CPU模式")
            
            # 加载模型并移动到指定设备
            logger.info("正在加载模型...")
            self.model = YOLO(MODEL_PATH)
            self.model.to(self.device)
            
            # 设置模型为评估模式以优化推理速度
            if hasattr(self.model.model, 'eval'):
                self.model.model.eval()
            
            # 使用torch.compile优化（PyTorch 2.0+）
            if USE_TORCH_COMPILE and self.device == "cuda" and hasattr(torch, 'compile'):
                try:
                    logger.info("正在编译模型以优化性能...")
                    self.model.model = torch.compile(self.model.model, mode='reduce-overhead')
                    logger.info("模型编译成功")
                except Exception as e:
                    logger.warning(f"模型编译失败，使用标准模式: {e}")
            
            # 预热模型（首次推理通常较慢）
            logger.info("正在预热模型...")
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(
                source=dummy_img,
                conf=CONFIDENCE_THRESHOLD,
                iou=IOU_THRESHOLD,
                device=self.device,
                half=USE_HALF_PRECISION if self.device == "cuda" else False,
                verbose=False,
                max_det=MAX_DETECTIONS,
            )
            
            # 如果使用CUDA，设置优化选项
            if self.device == "cuda":
                torch.backends.cudnn.benchmark = True  # 优化卷积操作
                torch.backends.cudnn.deterministic = False
            
            logger.info(f"模型加载成功: {MODEL_PATH}")
            logger.info(f"使用设备: {self.device}")
            if self.device == "cuda":
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def _resize_image_if_needed(self, image):
        """如果图片过大，进行缩放以提升处理速度"""
        h, w = image.shape[:2]
        max_dim = max(h, w)
        
        if max_dim > MAX_IMAGE_SIZE:
            scale = MAX_IMAGE_SIZE / max_dim
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            logger.debug(f"图片已缩放: {w}x{h} -> {new_w}x{new_h}")
        
        return image
    
    def detect(self, image):
        if image is None:
            logger.error("输入图片为空")
            raise ValueError("输入图片为空")
        
        try:
            # 缩放图片以提升速度
            image = self._resize_image_if_needed(image)
            
            # 优化后的预测参数
            # 使用imgsz=640以匹配模型训练尺寸，提升速度
            results = self.model.predict(
                source=image,
                conf=CONFIDENCE_THRESHOLD,
                iou=IOU_THRESHOLD,
                device=self.device,
                half=USE_HALF_PRECISION if self.device == "cuda" else False,
                imgsz=640,  # 固定输入尺寸以提升速度
                save=False,
                show=False,
                verbose=False,
                max_det=MAX_DETECTIONS,
                agnostic_nms=False,  # 非类别无关的NMS，速度更快
            )
            
            face_count = len(results[0].boxes) if len(results) > 0 else 0
            logger.debug(f"检测完成，检测到 {face_count} 个人脸")
            return results
        except Exception as e:
            logger.error(f"检测失败: {e}")
            raise
    
    def detect_video_file(self, video_bytes: bytes, output_format: str = "avi") -> Tuple[bytes, dict]:
        """
        处理视频文件，返回处理后的视频文件字节和统计信息
        
        Args:
            video_bytes: 视频文件的字节数据
            output_format: 输出格式，默认avi
            
        Returns:
            Tuple[bytes, dict]: (处理后的视频文件字节, 统计信息字典)
        """
        if video_bytes is None or len(video_bytes) == 0:
            logger.error("输入视频为空")
            raise ValueError("输入视频为空")
        
        temp_input = None
        temp_output = None
        start_time = time.time()
        
        try:
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_input.write(video_bytes)
            temp_input.close()
            
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format}')
            temp_output.close()
            
            logger.info(f"开始处理视频文件: {temp_input.name}")
            logger.info(f"输出路径: {temp_output.name}")
            
            cap = cv2.VideoCapture(temp_input.name)
            if not cap.isOpened():
                raise ValueError("无法打开视频")
            
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if output_format.lower() == 'avi':
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
            else:
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                # fourcc = cv2.VideoWriter_fourcc(*'h264')
            
            out = cv2.VideoWriter(temp_output.name, fourcc, fps, (width, height))
            
            frame_counts = []
            
            stream_results = self.model.predict(
                source=temp_input.name,
                conf=CONFIDENCE_THRESHOLD,
                iou=IOU_THRESHOLD,
                device=self.device,
                half=USE_HALF_PRECISION if self.device == "cuda" else False,
                imgsz=640,
                save=False,
                stream=True,
                show=False,
                verbose=False,
                max_det=MAX_DETECTIONS,
                agnostic_nms=False,
            )
            
            for result in stream_results:
                if hasattr(result, 'orig_img') and result.orig_img is not None:
                    annotated_frame = result.plot()
                    out.write(annotated_frame)
                    
                    face_count = len(result.boxes) if result.boxes is not None else 0
                    frame_counts.append(face_count)
            
            cap.release()
            out.release()
            
            with open(temp_output.name, 'rb') as f:
                output_video_bytes = f.read()
            
            elapsed_time = time.time() - start_time
            
            stats = {
                "frame_counts": frame_counts,
                "total_frames": len(frame_counts),
                "processing_time_seconds": round(elapsed_time, 2)
            }

            logger.info(f"视频处理完成，耗时 {elapsed_time:.2f}秒")
            return output_video_bytes, stats
            
        except Exception as e:
            logger.error(f"视频文件处理失败: {e}", exc_info=True)
            raise
        finally:
            if temp_input and os.path.exists(temp_input.name):
                try:
                    os.unlink(temp_input.name)
                except Exception as e:
                    logger.warning(f"删除临时输入文件失败: {e}")
            
            if temp_output and os.path.exists(temp_output.name):
                try:
                    os.unlink(temp_output.name)
                except Exception as e:
                    logger.warning(f"删除临时输出文件失败: {e}")
    
face_detection_service = FaceDetectionService()
