from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.detection import router as detection_router
from app.api.test import router as test_router

app = FastAPI(
    title="基于人脸检测的人数统计系统 API",
    description="提供人脸检测、人数统计等功能的API接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(detection_router)
app.include_router(test_router)

@app.get("/")
def read_root():
    return {
        "message": "欢迎使用基于人脸检测的人数统计系统",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("基于人脸检测的人数统计系统 API")
    print("=" * 50)
    print("")
    print("API文档:")
    print("  - Swagger UI: http://localhost:8080/docs")
    print("  - ReDoc:      http://localhost:8080/redoc")
    print("")
    print("=" * 50)
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
