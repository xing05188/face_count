from fastapi import APIRouter, File, UploadFile, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from app.services.detection_service import face_detection_service
import io
import cv2
import numpy as np
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["检测"])

def _resize_keep_aspect(img: np.ndarray, max_w: int) -> np.ndarray:
    """将图像按比例缩小到 max_w（不放大），用于提升推理/编码速度。"""
    if max_w <= 0:
        return img
    h, w = img.shape[:2]
    if w <= max_w:
        return img
    new_w = max_w
    new_h = int(h * (new_w / w))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

async def _detect_plot_encode(img: np.ndarray, jpeg_quality: int = 75, max_w: int = 640):
    """
    在线程池执行：缩放 -> 推理 -> 绘制 -> JPEG编码
    返回: (jpeg_bytes, face_count)
    """
    def _work():
        frame = _resize_keep_aspect(img, max_w=max_w)
        results = face_detection_service.detect(frame)
        face_count = len(results[0].boxes) if len(results) > 0 and len(results[0].boxes) > 0 else 0
        annotated = results[0].plot() if face_count > 0 else frame
        ok, img_encoded = cv2.imencode(".jpg", annotated, [
            int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality),
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1
        ])
        if not ok:
            raise ValueError("图像编码失败")
        return img_encoded.tobytes(), face_count

    return await asyncio.to_thread(_work)

@router.post(
    "/detect",
    description="上传图片，返回带检测框的图片和检测到的人脸个数。图片通过响应头 X-Face-Count 返回人脸个数。"
)
async def detect_faces(file: UploadFile = File(..., description="要检测的图片文件，支持 jpg、png 等格式")):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="无法解码图片，请检查图片格式")
        
        results = face_detection_service.detect(img)
        
        if len(results) == 0 or len(results[0].boxes) == 0:
            # 如果没有检测到人脸，直接返回原图，避免重新编码
            return StreamingResponse(
                    io.BytesIO(contents),
                    media_type=file.content_type or "image/jpeg",
                    headers={"X-Face-Count": "0"}
                )
        
        annotated_frame = results[0].plot()
        face_count = len(results[0].boxes)
        
        # 使用优化的JPEG编码参数
        _, img_encoded = cv2.imencode('.jpg', annotated_frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 85,
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1  # 启用JPEG优化
        ])
        img_bytes = img_encoded.tobytes()
        
        return StreamingResponse(
                io.BytesIO(img_bytes),
                media_type="image/jpeg",
                headers={"X-Face-Count": str(face_count)}
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@router.post(
    "/detect/video",
    description="上传视频文件（MP4/AVI等），返回处理后的视频文件（AVI格式）和统计信息。使用model.predict直接处理，性能最优。"
)
async def detect_video(
    file: UploadFile = File(..., description="要检测的视频文件，支持 mp4、avi 等格式"),
    output_format: str = Query("avi", description="输出视频格式：avi（默认）或 mp4")
):
    try:
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="视频文件为空")
        
        # 使用model.predict直接处理视频文件
        output_video_bytes, stats = face_detection_service.detect_video_file(contents, output_format)
        
        # 返回处理后的视频文件和统计信息
        return Response(
            content=output_video_bytes,
            media_type="video/x-msvideo" if output_format.lower() == "avi" else "video/mp4",
            headers={
                "X-Frame-Counts": json.dumps(stats["frame_counts"], ensure_ascii=False),
                "X-Total-Frames": str(stats["total_frames"]),
                "X-Processing-Time": str(stats["processing_time_seconds"])
            }
        )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"视频检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频检测失败: {str(e)}")

@router.websocket("/detect/camera")
async def detect_camera_stream(websocket: WebSocket):
    """
    摄像头实时检测API
    使用WebSocket实现双向通信：
    - 前端发送图像帧（二进制JPEG数据）
    - 后端返回检测结果（二进制JPEG数据）
    - 统计信息通过JSON消息发送
    """
    await websocket.accept()
    logger.info("摄像头检测WebSocket连接已建立")
    
    frame_count = 0
    total_faces = 0
    start_time = asyncio.get_running_loop().time()
    # 可按需调整：后端最大处理宽度、JPEG质量
    max_width = 640
    jpeg_quality = 75
    
    try:
        while True:
            # 接收前端发送的二进制图像数据
            data = await websocket.receive_bytes()
            
            try:
                # 解码图像
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "无法解码图像"
                    })
                    continue
                
                # 推理/绘制/编码：放到线程池，避免阻塞事件循环（关键性能点）
                img_bytes_result, face_count = await _detect_plot_encode(
                    img, jpeg_quality=jpeg_quality, max_w=max_width
                )

                frame_count += 1
                total_faces += face_count
                
                # 计算FPS
                elapsed = asyncio.get_running_loop().time() - start_time
                fps = round(frame_count / elapsed, 2) if elapsed > 0 else 0
                
                # 先发送统计信息（JSON），再发送图像（二进制）
                # 这样可以确保前端能正确配对消息
                stats_message = {
                    "type": "stats",
                    "frame_index": frame_count,
                    "face_count": face_count,
                    "fps": fps,
                    "total_faces": total_faces
                }
                try:
                    await websocket.send_json(stats_message)
                    # 发送处理后的图像（二进制）
                    await websocket.send_bytes(img_bytes_result)
                except WebSocketDisconnect:
                    raise
                
            except Exception as e:
                logger.exception("图像处理失败")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"图像处理失败: {str(e)}"
                    })
                except WebSocketDisconnect:
                    raise
                
    except WebSocketDisconnect:
        logger.info("摄像头检测WebSocket连接已断开")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"服务器错误: {str(e)}"
            })
        except:
            pass
    finally:
        logger.info(f"摄像头检测会话结束，共处理 {frame_count} 帧，检测到 {total_faces} 个人脸")
