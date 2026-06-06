from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_positions():
    return {"message": "Positions router working"}
