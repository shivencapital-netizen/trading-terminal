from fastapi import APIRouter
from app.services.load_sp500 import load_sp500

router = APIRouter()

@router.post("/load_sp500")
def load_sp500_symbols():
    count = load_sp500()
    return {"message": f"Loaded {count} S&P 500 symbols"}
