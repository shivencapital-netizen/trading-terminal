from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_trades():
    return {"message": "Trades router working"}
