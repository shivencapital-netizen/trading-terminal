from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_greeks():
    return {"message": "Greeks router working"}
