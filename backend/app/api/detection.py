from fastapi import APIRouter, File, UploadFile, HTTPException, Query, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from app.services.detection_service import face_detection_service
import cv2
import numpy as np
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["检测"])

def _resize_keep_aspect(img: np.ndarray, max_w: int) -> np.ndarray:
    """将图像按比例缩小到 max_w（不放大），用于提升推理速度。"""
    if max_w <= 0:
        return img
    h, w = img.shape[:2]
    if w <= max_w:
        return img
    new_w = max_w
    new_h = int(h * (new_w / w))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

def _decode_image_bytes(contents: bytes) -> np.ndarray:
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="图片为空")
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="无法解码图片，请检查图片格式")
    return img


def _detect_to_payload(img: np.ndarray, response_mode: str, max_width: int):
    frame = _resize_keep_aspect(img, max_w=max_width) if max_width > 0 else img
    results = face_detection_service.detect(frame)
    payload = face_detection_service.serialize_results_payload(results, mode=response_mode)
    face_count = payload["images"][0]["face_count"] if payload.get("images") else 0
    return payload, face_count

@router.post(
    "/detect",
    description="上传图片并返回检测 JSON（不返回标注图）。"
)
async def detect_faces(
    file: UploadFile = File(..., description="要检测的图片文件，支持 jpg、png 等格式"),
    response_mode: str = Query("compact", regex="^(compact|full)$", description="响应模式：compact 或 full"),
    max_width: int = Query(0, ge=0, le=1920, description="检测前最大宽度；0 表示不额外缩放")
):
    try:
        contents = await file.read()
        img = _decode_image_bytes(contents)
        payload, face_count = await asyncio.to_thread(_detect_to_payload, img, response_mode, max_width)
        return JSONResponse(content=payload, headers={"X-Face-Count": str(face_count)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@router.post(
    "/detect/frame",
    description="上传单帧图片二进制并返回检测 JSON（低开销，适合视频抽帧场景）。"
)
async def detect_frame(
    request: Request,
    response_mode: str = Query("compact", regex="^(compact|full)$", description="响应模式：compact 或 full"),
    max_width: int = Query(640, ge=160, le=1920, description="检测前最大宽度，建议 480~960")
):
    try:
        contents = await request.body()
        img = _decode_image_bytes(contents)
        payload, face_count = await asyncio.to_thread(_detect_to_payload, img, response_mode, max_width)
        return JSONResponse(content=payload, headers={"X-Face-Count": str(face_count)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"帧检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"帧检测失败: {str(e)}")

@router.websocket("/detect/camera")
async def detect_camera_stream(websocket: WebSocket):
    """
    摄像头实时检测API
    使用WebSocket实现双向通信：
    - 前端发送图像帧（二进制JPEG数据）
    - 后端返回检测 JSON（用于前端绘制）
    """
    await websocket.accept()
    logger.info("摄像头检测WebSocket连接已建立")

    response_mode = websocket.query_params.get("mode", "compact")
    if response_mode not in {"compact", "full"}:
        await websocket.send_json({"type": "error", "message": "mode 仅支持 compact 或 full"})
        await websocket.close(code=1003)
        return

    frame_count = 0
    max_width = 640
    
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
                
                frame_count += 1

                payload, _ = await asyncio.to_thread(_detect_to_payload, img, response_mode, max_width)
                image_payload = payload["images"][0] if payload.get("images") else {
                    "shape": [0, 0],
                    "face_count": 0,
                    "results": []
                }
                logger.info(f"当前第 {frame_count} 帧，检测到 {image_payload['face_count']} 个人脸")
                message = {
                    "type": "result",
                    "frame_index": frame_count,
                    "mode": response_mode,
                    "shape": image_payload.get("shape", [0, 0]),
                    "face_count": image_payload.get("face_count", 0),
                    "results": image_payload.get("results", []),
                }
                if response_mode == "full":
                    message["speed"] = image_payload.get("speed", {})
                    message["metadata"] = payload.get("metadata", {})
                try:
                    await websocket.send_json(message)
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
        logger.info(f"摄像头检测会话结束，共处理 {frame_count} 帧")
