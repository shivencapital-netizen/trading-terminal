from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_users():
    return {"message": "Users router working"}