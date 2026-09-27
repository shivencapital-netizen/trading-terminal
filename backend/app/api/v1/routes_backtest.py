from datetime import datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
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
    years: int | None = Field(default=None, ge=1, le=20)
    lookback_trading_days: int | None = Field(default=None, ge=1, le=10000)
    timeframe: Literal["day", "week"] = "day"
    threshold_percent: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_lookback(self):
        if (self.years is None) == (self.lookback_trading_days is None):
            raise ValueError("Specify exactly one lookback: years or trading days.")
        return self


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
            lookback_trading_days=interpretation.get("lookback_trading_days"),
            timeframe=interpretation.get("timeframe", "day"),
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
        "lookback_trading_days": close_move_request.lookback_trading_days,
        "timeframe": close_move_request.timeframe,
        "threshold_percent": close_move_request.threshold_percent,
    }
    conversation = BacktestConversation(
        question=question,
        symbol=result["symbol"],
        years=result["years"] or 0,
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
            "timeframe": conversation.result.get("timeframe", "day"),
            "period_label": conversation.result.get("period_label", ""),
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
    if request.lookback_trading_days is not None:
        requested_days = request.lookback_trading_days
        start_date = today - timedelta(days=requested_days * 2 + 30)
        period_label = f"last {requested_days} trading days"
    else:
        requested_days = None
        try:
            start_date = today.replace(year=today.year - request.years)
        except ValueError:
            start_date = today.replace(year=today.year - request.years, day=28)
        period_label = f"last {request.years} years"
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

    lookback_start = start_date
    if requested_days is not None:
        if len(daily_closes) > requested_days:
            lookback_start = daily_closes[-requested_days][0]
            daily_closes = daily_closes[-(requested_days + 8):]
        elif daily_closes:
            lookback_start = daily_closes[0][0]

    if len(daily_closes) < 2:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough regular-session daily candle data found for {symbol}.",
        )

    threshold = request.threshold_percent
    period_closes = daily_closes
    if request.timeframe == "week":
        week_closes = {}
        for trading_day, close in daily_closes:
            iso_year, iso_week, _ = trading_day.isocalendar()
            week_closes[(iso_year, iso_week)] = (trading_day, close)
        period_closes = list(week_closes.values())

    analyzed_periods = 0
    first_analyzed_day = None
    last_analyzed_day = None
    positive_events = []
    negative_events = []

    previous_close = None
    previous_period_close = None
    for trading_day, close in period_closes:
        close = float(close)
        current_previous_close = previous_close
        if request.timeframe == "week":
            current_previous_close = previous_period_close
        if current_previous_close is not None and trading_day >= lookback_start:
            change = (close - float(current_previous_close)) / float(current_previous_close) * 100
            analyzed_periods += 1
            first_analyzed_day = first_analyzed_day or trading_day
            last_analyzed_day = trading_day
            event = {
                "date": trading_day.isoformat(),
                "previous_close": round(float(current_previous_close), 4),
                "close": round(close, 4),
                "change_percent": round(change, 3),
            }
            if change > threshold:
                positive_events.append(event)
            elif change < -threshold:
                negative_events.append(event)
        previous_close = close
        previous_period_close = close

    if analyzed_periods == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough {request.timeframe} close data found for {symbol} in this range.",
        )

    expected_periods = (
        max(1, requested_days // 5) if requested_days is not None and request.timeframe == "week"
        else max(1, requested_days - 1) if requested_days is not None
        else request.years * (50 if request.timeframe == "week" else 250)
    )
    if requested_days is not None and daily_closes:
        start_date = lookback_start

    return {
        "symbol": symbol,
        "years": request.years or 0,
        "lookback_trading_days": requested_days,
        "timeframe": request.timeframe,
        "period_label": period_label,
        "threshold_percent": threshold,
        "start_date": start_date.isoformat(),
        "end_date": (today - timedelta(days=1)).isoformat(),
        "analyzed_sessions": analyzed_periods,
        "expected_periods": expected_periods,
        "data_start_date": first_analyzed_day.isoformat() if first_analyzed_day else None,
        "data_end_date": last_analyzed_day.isoformat() if last_analyzed_day else None,
        "positive_count": len(positive_events),
        "negative_count": len(negative_events),
        "positive_events": positive_events,
        "negative_events": negative_events,
        "methodology": (
            (
                "Weekly close-to-close change compares each week's last stored "
                "regular-session close to the previous week's last stored regular-session "
                "close. "
                if request.timeframe == "week"
                else "Daily close-to-close change compares consecutive regular-session closes. "
            )
            + "Closes use the last stored 1-minute bar during the 9:30 AM–4:00 PM "
            "America/New_York session. The current incomplete session is excluded. "
            "Threshold comparisons are strict; a 0% threshold includes every positive gain and negative loss."
        ),
    }
