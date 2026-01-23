from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["系统"])

@router.get(
    "/hello",
    description="返回简单的 Hello World 消息"
    )
def hello():
    return {"message": "helloworld"}
