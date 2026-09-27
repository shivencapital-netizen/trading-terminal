from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candles_1m import Candle1m
from app.models.backtest_conversation import BacktestConversation
from app.services.ai_backtest_query import (
    AIProviderNotConfigured,
    AIProviderUnavailable,
    AIResponseInvalid,
    get_ai_provider_status,
    parse_backtest_question,
)

router = APIRouter()
NEW_YORK = ZoneInfo("America/New_York")


class CloseMoveRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=15)
    years: int = Field(ge=1, le=20)
    threshold_percent: float = Field(gt=0, le=100)


class BacktestQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@router.get("/assistant-status")
def assistant_status():
    return get_ai_provider_status()


@router.post("/ask")
def ask_backtest_question(request: BacktestQuestionRequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Enter a backtest question.")

    try:
        interpretation = parse_backtest_question(question)
    except AIProviderNotConfigured as error:
        raise HTTPException(
            status_code=503,
            detail="The local AI service is not configured. Check AI_API_BASE_URL and AI_MODEL in backend/.env.",
        ) from error
    except AIProviderUnavailable as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except AIResponseInvalid as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    if interpretation.get("supported") is not True:
        reason = interpretation.get("reason") or "This question type is not supported yet."
        raise HTTPException(
            status_code=422,
            detail=f"{reason} Try asking for daily close-to-close percentage moves.",
        )

    try:
        close_move_request = CloseMoveRequest(
            symbol=interpretation["symbol"],
            years=interpretation["years"],
            threshold_percent=interpretation["threshold_percent"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="The hosted AI could not interpret this question. Please rephrase it.",
        ) from error

    result = analyze_close_moves(close_move_request, db)
    result["question"] = question
    result["interpretation"] = {
        "symbol": close_move_request.symbol.strip().upper(),
        "years": close_move_request.years,
        "threshold_percent": close_move_request.threshold_percent,
    }
    conversation = BacktestConversation(
        question=question,
        symbol=result["symbol"],
        years=result["years"],
        threshold_percent=result["threshold_percent"],
        result=result,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    result["conversation_id"] = conversation.id
    result["created_at"] = conversation.created_at.isoformat()
    return result


@router.get("/history")
def list_backtest_history(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 100)
    conversations = (
        db.query(BacktestConversation)
        .order_by(BacktestConversation.created_at.desc(), BacktestConversation.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": conversation.id,
            "question": conversation.question,
            "symbol": conversation.symbol,
            "years": conversation.years,
            "threshold_percent": float(conversation.threshold_percent),
            "positive_count": conversation.result["positive_count"],
            "negative_count": conversation.result["negative_count"],
            "created_at": conversation.created_at.isoformat(),
        }
        for conversation in conversations
    ]


@router.get("/history/{conversation_id}")
def get_backtest_history(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(BacktestConversation).filter(
        BacktestConversation.id == conversation_id
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Backtest history was not found.")
    return {
        **conversation.result,
        "conversation_id": conversation.id,
        "created_at": conversation.created_at.isoformat(),
    }


@router.post("/close-moves")
def analyze_close_moves(request: CloseMoveRequest, db: Session = Depends(get_db)):
    symbol = request.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=422, detail="A symbol is required.")

    today = datetime.now(NEW_YORK).date()
    try:
        start_date = today.replace(year=today.year - request.years)
    except ValueError:
        start_date = today.replace(year=today.year - request.years, day=28)
    fetch_start = datetime.combine(start_date - timedelta(days=10), time.min, tzinfo=NEW_YORK)
    fetch_end = datetime.combine(today, time.min, tzinfo=NEW_YORK)
    local_timestamp = func.timezone("America/New_York", Candle1m.start_time)
    local_day = func.date(local_timestamp)
    local_minutes = func.extract("hour", local_timestamp) * 60 + func.extract("minute", local_timestamp)

    daily_last_bar = (
        db.query(
            local_day.label("trading_day"),
            func.max(Candle1m.start_time).label("last_bar_time"),
        )
        .filter(
            Candle1m.symbol == symbol,
            Candle1m.start_time >= fetch_start,
            Candle1m.start_time < fetch_end,
            local_minutes >= 570,
            local_minutes < 960,
        )
        .group_by(local_day)
        .subquery()
    )
    daily_closes = (
        db.query(daily_last_bar.c.trading_day, Candle1m.close)
        .join(daily_last_bar, Candle1m.start_time == daily_last_bar.c.last_bar_time)
        .filter(Candle1m.symbol == symbol)
        .order_by(daily_last_bar.c.trading_day)
        .all()
    )

    if len(daily_closes) < 2:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough regular-session daily candle data found for {symbol}.",
        )

    threshold = request.threshold_percent
    previous_close = None
    analyzed_days = 0
    first_analyzed_day = None
    last_analyzed_day = None
    positive_events = []
    negative_events = []

    for trading_day, close in daily_closes:
        close = float(close)
        if previous_close is not None and trading_day >= start_date:
            change = (close - previous_close) / previous_close * 100
            analyzed_days += 1
            first_analyzed_day = first_analyzed_day or trading_day
            last_analyzed_day = trading_day
            event = {
                "date": trading_day.isoformat(),
                "previous_close": round(previous_close, 4),
                "close": round(close, 4),
                "change_percent": round(change, 3),
            }
            if change > threshold:
                positive_events.append(event)
            elif change < -threshold:
                negative_events.append(event)
        previous_close = close

    return {
        "symbol": symbol,
        "years": request.years,
        "threshold_percent": threshold,
        "start_date": start_date.isoformat(),
        "end_date": (today - timedelta(days=1)).isoformat(),
        "analyzed_sessions": analyzed_days,
        "data_start_date": first_analyzed_day.isoformat() if first_analyzed_day else None,
        "data_end_date": last_analyzed_day.isoformat() if last_analyzed_day else None,
        "positive_count": len(positive_events),
        "negative_count": len(negative_events),
        "positive_events": positive_events,
        "negative_events": negative_events,
        "methodology": (
            "Daily close-to-close change uses the last stored 1-minute close during "
            "the 9:30 AM–4:00 PM America/New_York regular session. The current "
            "incomplete session is excluded. Threshold comparisons are strict."
        ),
    }
