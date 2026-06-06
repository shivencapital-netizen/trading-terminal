from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_backtest():
    return {"message": "Backtest router working"}
